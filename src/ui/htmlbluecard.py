import sys
import os
import logging
import webbrowser
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
    example_data = {
        "classes": {
            "OLO123": {
                "metadata": {
                    "Company": "Example Company",
                    "Consultant": "John Doe",
                    "Teacher": "Jane Smith",
                    "Room": "101",
                    "CourseBook": "Advanced Python",
                },
                "students": {},
            }
        }
    }
    # Here you would normally use the Mainform class to generate the HTML.
    # For now, we'll just return a simple HTML string for testing.
    html_content = """
    <html>
        <head><title>Bluecard App</title></head>
        <body>
            <h1>Welcome to the Bluecard App</h1>
            <p>Example content here...</p>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route("/download-pdf")
def download_pdf():
    """Generate and serve a PDF."""
    example_data = {
        "classes": {
            "OLO123": {
                "metadata": {
                    "Company": "Example Company",
                    "Consultant": "John Doe",
                    "Teacher": "Jane Smith",
                    "Room": "101",
                    "CourseBook": "Advanced Python",
                },
                "students": {},
            }
        }
    }
    # Normally you would generate the PDF from Mainform here, but we'll mock it.
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
