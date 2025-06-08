import sys
import os
import logging
import webbrowser
import json
from flask import Flask, render_template_string, send_file
import pdfkit
from threading import Timer
from datetime import datetime, timedelta
from logic.db_interface import get_all_classes, get_class_by_id, get_students_by_class, get_attendance_by_student, get_all_defaults
from PyQt5.QtGui import QFont

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Dynamically determine the base directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
logging.debug(f"Base directory dynamically determined: {base_dir}")

# Add the src directory to the Python path
src_path = os.path.join(base_dir, "src")
sys.path.append(src_path)
logging.debug(f"Added src directory to Python path: {src_path}")

# Create Flask app
app = Flask(__name__)

def get_html_style():
    defaults = get_all_defaults()
    font_family = defaults.get("form_font_family", "Segoe UI")
    font_size = int(defaults.get("form_font_size", 12))
    fg_color = defaults.get("form_fg_color", "#222222")
    bg_color = defaults.get("form_bg_color", "#e3f2fd")
    border_color = defaults.get("form_border_color", "#1976d2")
    return f"body {{ font-family: '{font_family}'; font-size: {font_size}pt; color: {fg_color}; background: {bg_color}; }} table, th, td {{ border: 1px solid {border_color}; }}"

@app.route("/")
def home():
    """Serve the HTML content."""
    # Load data from the database
    all_classes = get_all_classes()
    if not all_classes:
        return "<h2>No classes found in the database.</h2>"

    class_row = all_classes[0]
    class_id = class_row["class_no"]
    metadata = dict(class_row)  # All fields are top-level

    # Get students for this class
    students_list = get_students_by_class(class_id)
    students = {}
    for student_row in students_list:
        student_id = student_row["student_id"]
        attendance_records = get_attendance_by_student(student_id)
        attendance = {rec["date"]: rec["status"] for rec in attendance_records}
        student_row["attendance"] = attendance
        students[student_id] = student_row

    # Combine course_hours, class_time, and max_classes into a single field
    course_hours = metadata.get("course_hours", "N/A")
    class_time = metadata.get("class_time", "N/A")
    max_classes = metadata.get("max_classes", "N/A")
    metadata["course_hours_summary"] = f"{course_hours} Hours / {class_time} Hours per class / {max_classes} Classes"

    # Hide specific fields from metadata
    hidden_metadata_fields = {"teacher_no", "class_time", "max_classes", "rate", "ccp", "travel", "bonus", "notes", "class_no"}
    metadata = {key: value for key, value in metadata.items() if key not in hidden_metadata_fields}

    # Split metadata into two groups (update keys to lowercase/underscore)
    group1_fields = ["company", "consultant", "teacher", "room", "course_book"]
    group2_fields = ["course_hours_summary", "start_date", "finish_date", "days", "time"]

    # Prepare group1 and group2 metadata
    group1_metadata = {key: metadata.get(key, "N/A") for key in group1_fields}
    group2_metadata = {key: metadata.get(key, "N/A") for key in group2_fields}

    # Generate all class dates based on metadata
    def generate_class_dates(start_date, days, max_classes):
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        start_date = datetime.strptime(start_date, "%d/%m/%Y")
        class_days = [day_map[day.strip()] for day in days.split(",") if day.strip() in day_map]
        class_dates = []

        current_date = start_date
        while len(class_dates) < max_classes:
            if current_date.weekday() in class_days:
                class_dates.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)

        return class_dates

    # Extract metadata values
    start_date = metadata.get("start_date", "01/01/2025")
    days = metadata.get("days", "Monday, Wednesday")
    max_classes = int(metadata.get("max_classes", "20"))

    # Generate all class dates
    all_dates = generate_class_dates(start_date, days, max_classes)

    # Calculate running totals for attendance
    running_total_p = sum(
        sum(1 for status in student.get("attendance", {}).values() if status == "P")
        for student in students.values()
    )
    running_total_a = sum(
        sum(1 for status in student.get("attendance", {}).values() if status == "A")
        for student in students.values()
    )
    running_total_l = sum(
        sum(1 for status in student.get("attendance", {}).values() if status == "L")
        for student in students.values()
    )

    # Calculate running totals for each date
    class_time = int(metadata.get("class_time", "2"))  # Default to 2 if not provided
    running_totals = [class_time * (i + 1) for i in range(len(all_dates))]

    # Generate HTML content dynamically
    company_name = metadata.get("company", "N/A")
    html_content = f"""
    <html>
        <head>
            <title>Class Attendance - {class_id} - {company_name}</title>
            <style>
                {get_html_style()}
                h1, h2 {{ color: #333; }}
                .bottom-space {{ margin-bottom: 1in; }}
            </style>
        </head>
        <body>
            <h1>Class Attendance - {class_id} - {company_name}</h1>
            <div class="bottom-space">
                <table>
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                        <th>Field</th>
                        <th>Value</th>
                    </tr>
                    {"".join(
                        f"<tr>"
                        f"<td>{key1}</td><td>{value1}</td>"
                        f"<td>{key2}</td><td>{value2}</td>"
                        f"</tr>"
                        for (key1, value1), (key2, value2) in zip(group1_metadata.items(), group2_metadata.items())
                    )}
                </table>
                <h2>Students</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Nickname</th>
                        <th>Score</th>
                        <th>Pre-Test</th>
                        <th>Post-Test</th>
                        <th>P</th>
                        <th>A</th>
                        <th>L</th>
                        {"".join(f"<th>{date}</th>" for date in all_dates)}
                    </tr>
                    <tr>
                        <td colspan="6" style="font-weight: bold; text-align: right;">Running Total</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        {"".join(f"<td>{total}</td>" for total in running_totals)}
                    </tr>
                    {"".join(
                        f"<tr>"
                        f"<td>{idx + 1}</td>"
                        f"<td>{student.get('name', '')}</td>"
                        f"<td>{student.get('nickname', '')}</td>"
                        f"<td>{student.get('score', '')}</td>"
                        f"<td>{student.get('pre_test', '')}</td>"
                        f"<td>{student.get('post_test', '')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'P')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'A')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'L')}</td>"
                        + "".join(
                            f"<td>{student.get('attendance', {}).get(date, '-')}</td>"
                            for date in all_dates
                        )
                        + f"</tr>"
                        for idx, (student_id, student) in enumerate(students.items())
                    )}
                </table>
            </div>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route("/download-pdf")
def download_pdf():
    """Generate and serve a PDF from the latest DB data."""
    # Load data from the database (same as in home())
    all_classes = get_all_classes()
    if not all_classes:
        return "<h2>No classes found in the database.</h2>"

    class_row = all_classes[0]
    class_id = class_row["class_no"]
    metadata = dict(class_row)

    students_list = get_students_by_class(class_id)
    students = {}
    for student_row in students_list:
        student_id = student_row["student_id"]
        attendance_records = get_attendance_by_student(student_id)
        attendance = {rec["date"]: rec["status"] for rec in attendance_records}
        student_row["attendance"] = attendance
        students[student_id] = student_row

    course_hours = metadata.get("course_hours", "N/A")
    class_time = metadata.get("class_time", "N/A")
    max_classes = metadata.get("max_classes", "N/A")
    metadata["course_hours_summary"] = f"{course_hours} Hours / {class_time} Hours per class / {max_classes} Classes"

    hidden_metadata_fields = {"teacher_no", "class_time", "max_classes", "rate", "ccp", "travel", "bonus", "notes", "class_no"}
    metadata = {key: value for key, value in metadata.items() if key not in hidden_metadata_fields}

    group1_fields = ["company", "consultant", "teacher", "room", "course_book"]
    group2_fields = ["course_hours_summary", "start_date", "finish_date", "days", "time"]

    group1_metadata = {key: metadata.get(key, "N/A") for key in group1_fields}
    group2_metadata = {key: metadata.get(key, "N/A") for key in group2_fields}

    def generate_class_dates(start_date, days, max_classes):
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        start_date = datetime.strptime(start_date, "%d/%m/%Y")
        class_days = [day_map[day.strip()] for day in days.split(",") if day.strip() in day_map]
        class_dates = []

        current_date = start_date
        while len(class_dates) < max_classes:
            if current_date.weekday() in class_days:
                class_dates.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)

        return class_dates

    start_date = metadata.get("start_date", "01/01/2025")
    days = metadata.get("days", "Monday, Wednesday")
    max_classes = int(metadata.get("max_classes", "20"))
    all_dates = generate_class_dates(start_date, days, max_classes)

    class_time = int(metadata.get("class_time", "2"))
    running_totals = [class_time * (i + 1) for i in range(len(all_dates))]

    company_name = metadata.get("company", "N/A")
    html_content = f"""
    <html>
        <head>
            <title>Class Attendance - {class_id} - {company_name}</title>
            <style>
                {get_html_style()}
                h1, h2 {{ color: #333; }}
                .bottom-space {{ margin-bottom: 1in; }}
            </style>
        </head>
        <body>
            <h1>Class Attendance - {class_id} - {company_name}</h1>
            <div class="bottom-space">
                <table>
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                        <th>Field</th>
                        <th>Value</th>
                    </tr>
                    {"".join(
                        f"<tr>"
                        f"<td>{key1}</td><td>{value1}</td>"
                        f"<td>{key2}</td><td>{value2}</td>"
                        f"</tr>"
                        for (key1, value1), (key2, value2) in zip(group1_metadata.items(), group2_metadata.items())
                    )}
                </table>
                <h2>Students</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Nickname</th>
                        <th>Score</th>
                        <th>Pre-Test</th>
                        <th>Post-Test</th>
                        <th>P</th>
                        <th>A</th>
                        <th>L</th>
                        {"".join(f"<th>{date}</th>" for date in all_dates)}
                    </tr>
                    <tr>
                        <td colspan="6" style="font-weight: bold; text-align: right;">Running Total</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        {"".join(f"<td>{total}</td>" for total in running_totals)}
                    </tr>
                    {"".join(
                        f"<tr>"
                        f"<td>{idx + 1}</td>"
                        f"<td>{student.get('name', '')}</td>"
                        f"<td>{student.get('nickname', '')}</td>"
                        f"<td>{student.get('score', '')}</td>"
                        f"<td>{student.get('pre_test', '')}</td>"
                        f"<td>{student.get('post_test', '')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'P')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'A')}</td>"
                        + f"<td>{sum(1 for status in student.get('attendance', {}).values() if status == 'L')}</td>"
                        + "".join(
                            f"<td>{student.get('attendance', {}).get(date, '-')}</td>"
                            for date in all_dates
                        )
                        + f"</tr>"
                        for idx, (student_id, student) in enumerate(students.items())
                    )}
                </table>
            </div>
        </body>
    </html>
    """

    pdf_path = "mainform.pdf"
    pdfkit.from_string(html_content, pdf_path)
    return send_file(pdf_path, as_attachment=True)

def open_browser():
    """Open the default browser to the home route."""
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    logging.debug("Starting Flask app...")
    # Start the Flask app in a separate thread to ensure the browser opens reliably
    Timer(1.0, open_browser).start()
    app.run(debug=True, use_reloader=False)  # Set use_reloader=False to prevent double run
