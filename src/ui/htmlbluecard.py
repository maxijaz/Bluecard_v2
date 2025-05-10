import sys
import os
import logging
import webbrowser
import json
from flask import Flask, render_template_string, send_file
import pdfkit
from threading import Timer
from datetime import datetime, timedelta

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

@app.route("/")
def home():
    """Serve the HTML content."""
    # Load data from a temporary JSON file
    temp_data_file = os.path.join(base_dir, "temp_data.json")
    if os.path.exists(temp_data_file):
        with open(temp_data_file, "r", encoding="utf-8") as f:
            example_data = json.load(f)
    else:
        example_data = {"classes": {}}

    # Extract metadata and student details
    class_id = list(example_data.get("classes", {}).keys())[0]
    class_data = example_data["classes"].get(class_id, {})
    metadata = class_data.get("metadata", {})
    students = class_data.get("students", {})

    # Combine CourseHours, ClassTime, and MaxClasses into a single field
    course_hours = metadata.get("CourseHours", "N/A")
    class_time = metadata.get("ClassTime", "N/A")
    max_classes = metadata.get("MaxClasses", "N/A")
    metadata["CourseHours"] = f"{course_hours} Hours / {class_time} Hours per class / {max_classes} Classes"

    # Hide specific fields from metadata
    hidden_metadata_fields = {"teacherno", "classtime", "maxclasses", "rate", "ccp", "travel", "bonus", "notes", "class_no"}
    metadata = {key: value for key, value in metadata.items() if key.lower() not in hidden_metadata_fields}

    # Split metadata into two groups
    group1_fields = ["Company", "Consultant", "Teacher", "Room", "CourseBook"]
    group2_fields = ["CourseHours", "StartDate", "FinishDate", "Days", "Time"]

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
    start_date = metadata.get("StartDate", "01/01/2025")
    days = metadata.get("Days", "Monday, Wednesday")
    max_classes = int(metadata.get("MaxClasses", "20"))

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
    class_time = int(metadata.get("ClassTime", "2"))  # Default to 2 if not provided
    running_totals = [class_time * (i + 1) for i in range(len(all_dates))]

    # Generate HTML content dynamically
    company_name = metadata.get("Company", "N/A")
    html_content = f"""
    <html>
        <head>
            <title>Class Attendance - {class_id} - {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                h1, h2 {{ color: #333; }}
                .bottom-space {{ margin-bottom: 1in; }} /* Add 1-inch space below the table */
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
                        f"<td>{idx + 1}</td>"  # Running number
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
                        for idx, (student_id, student) in enumerate(students.items())  # Use enumerate for running number
                    )}
                </table>
            </div>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route("/download-pdf")
def download_pdf():
    """Generate and serve a PDF."""
    # Load data from a temporary JSON file
    temp_data_file = os.path.join(base_dir, "temp_data.json")
    if os.path.exists(temp_data_file):
        with open(temp_data_file, "r", encoding="utf-8") as f:
            example_data = json.load(f)
    else:
        example_data = {"classes": {}}

    # Generate PDF content dynamically
    pdf_path = "mainform.pdf"
    html_content = "<h1>PDF Content</h1><p>Generated PDF content.</p>"
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
