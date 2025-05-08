import sys
import os
import logging
import webbrowser
import json
from flask import Flask, render_template_string, send_file
import pdfkit
from threading import Timer

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

    # Collect all unique attendance dates
    all_dates = sorted(
        {date for student in students.values() for date in student.get("attendance", {}).keys()}
    )

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
            </style>
        </head>
        <body>
            <h1>Class Attendance - {class_id} - {company_name}</h1>
            <table>
                <tr><th>Field</th><th>Value</th></tr>
                {"".join(f"<tr><td>{key}</td><td>{value}</td></tr>" for key, value in metadata.items())}
            </table>
            <h2>Students</h2>
            <table>
                <tr>
                    <th>ID</th>
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
                {"".join(
                    f"<tr>"
                    f"<td>{student_id}</td>"
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
                    for student_id, student in students.items()
                )}
            </table>
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
