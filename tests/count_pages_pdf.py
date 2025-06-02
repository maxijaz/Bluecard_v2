import os
from pypdf import PdfReader

# Set your target folder path
folder_path = "H:\\"

# Get list of all PDF files
pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

total_pages = 0

for pdf_file in pdf_files:
    pdf_path = os.path.join(folder_path, pdf_file)
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        print(f"{pdf_file}: {num_pages} pages")
        total_pages += num_pages
    except Exception as e:
        print(f"Error reading {pdf_file}: {e}")

print(f"\nTotal pages across all PDFs: {total_pages}")
