import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import csv
import pandas as pd
from spire.doc import Document
import tempfile
from tabula import read_pdf


# Parse the page range input from the user
def parse_page_range(page_range_str, num_pages):
    try:
        if not page_range_str:  # Empty input, extract all pages
            return list(range(num_pages))
        pages = []
        ranges = page_range_str.split(',')
        for range_str in ranges:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                pages.extend(range(start - 1, end))  # Convert to zero-based index
            else:
                pages.append(int(range_str) - 1)  # Convert to zero-based index
        pages = [p for p in pages if 0 <= p < num_pages]  # Filter out-of-bound pages
        return pages if pages else None
    except (ValueError, TypeError):
        return None  # Invalid input


# Processing DOCX files
def process_docx(file_obj):
    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(file_obj.read())
        tmp_file_path = tmp_file.name

    # Load the temporary file using Spire.Doc
    document = Document()
    document.LoadFromFile(tmp_file_path)
    result_text = document.GetText()

    return result_text


# Processing CSV files
def process_csv(file_obj):
    file_obj.seek(0)
    reader = csv.reader(file_obj.read().decode('utf-8').splitlines())
    return "\n".join([",".join(row) for row in reader])

def process_pdf(file_obj, page_range_str=None, extraction_category=None):
    pdf_bytes = file_obj.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count

    # Parse the page range from the input string
    page_indices = parse_page_range(page_range_str, num_pages)
    if page_indices is None:
        return {"error": "Invalid page range or out of bounds. Please check the document page numbers."}

    if not page_indices:  # Extract all pages if no specific range provided
        page_indices = list(range(num_pages))  # All pages

    # Perform the extraction based on the selected category
    if extraction_category == "Text":
        extracted_text = extract_text_from_pdf(pdf_bytes, page_indices)
        if extracted_text:
            message = f"Extracted text from pages {page_range_str or 'all'}."
            return {"tables": extracted_text, "message": message}
        else:
            return {"error": "No text found."}
    elif extraction_category == "Tables":
        extracted_tables = extract_tables_from_pdf(pdf_bytes, page_indices)
        if extracted_tables:
            message = f"Extracted tables from pages {page_range_str or 'all'}."
            return {"tables": extracted_tables, "message": message}
        else:
            return {"error": "No tables found."}
    elif extraction_category == "Images":
        extracted_images = extract_images_from_pages(pdf_bytes, page_indices)
        if not extracted_images:
            return {"error": "No images found."}
        return {"images": extracted_images, "message": "Images extracted successfully."}
    elif extraction_category == "Charts & Graphs":
        extracted_images = extract_charts_from_pdf(pdf_bytes, page_indices)
        if not extracted_images:
            return {"error": "No charts or graphs found."}
        return {"images": extracted_images, "message": "Charts and graphs extracted successfully."}
    else:
        return {"error": "Invalid extraction category selected."}

def extract_text_from_pdf(pdf_bytes, indices):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in indices:
        page = doc.load_page(i)
        extracted_text += page.get_text("text")
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_bytes, pages=[i])
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text


def extract_text_from_pages_single_threaded(pdf_bytes):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count
    for i in range(num_pages):
        page = doc.load_page(i)
        extracted_text += page.get_text("text")
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_bytes)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text

def extract_text_with_tesseract(pdf_bytes, pages=None):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if pages is None else pages
    for i in page_range:
        page = doc.load_page(i)
        pix = page.get_pixmap()
        image = Image.open(BytesIO(pix.tobytes(output="png")))
        extracted_text += pytesseract.image_to_string(image)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text


def parallel_pdf_text_extraction(pdf_bytes, num_pages):
    cpu = cpu_count()
    seg_size = int(num_pages / cpu + 1)
    indices = [range(i * seg_size, min((i + 1) * seg_size, num_pages)) for i in range(cpu)]
    with Pool() as pool:
        results = pool.starmap(extract_text_from_page_indices, [(pdf_bytes, idx) for idx in indices])
    combined_text = "".join(results)
    return combined_text


# OCR with Tesseract for PDF pages with no text
def extract_text_with_tesseract(pdf_bytes, pages=None):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if pages is None else pages
    for i in page_range:
        page = doc.load_page(i)
        pix = page.get_pixmap()
        image = Image.open(BytesIO(pix.tobytes(output="png")))
        extracted_text += pytesseract.image_to_string(image)
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text


# Extract images from specific page indices of a PDF
def extract_images_from_pages(pdf_bytes, page_indices=None):
    extracted_images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if page_indices is None else page_indices
    for i in page_range:
        page = doc.load_page(i)
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            pix = doc.extract_image(img[0])
            img_bytes = pix['image']  # Extract the image bytes
            img_ext = pix['ext']
            img_filename = f"page_{i + 1}_image_{img_index + 1}.{img_ext}"
            image_stream = BytesIO(img_bytes)  # Create an in-memory bytes buffer
            extracted_images.append((img_filename, image_stream))
    return extracted_images


# Extract tables from specific page indices of a PDF using Camelot
# def extract_tables_from_pdf(pdf_bytes, page_indices=None):
#     # Write the PDF bytes to a temporary file for Camelot to process
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#         tmp_file.write(pdf_bytes)
#         tmp_file_path = tmp_file.name
#
#     extracted_tables = []
#     for page in page_indices:
#         tables = camelot.read_pdf(tmp_file_path, pages=str(page + 1))
#         if tables:
#             for table in tables:
#                 df = table.df
#                 extracted_tables.append(df)
#     return extracted_tables


def extract_tables_from_pdf(pdf_bytes, page_indices=None):
    # Write the PDF bytes to a temporary file for Tabula to process
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name

    extracted_tables = []

    # Tabula can process multiple pages in one call, so we gather all page indices
    page_range = ','.join(str(page + 1) for page in page_indices) if page_indices else 'all'

    # Use read_pdf to extract tables from the specified pages
    tables = read_pdf(tmp_file_path, pages=page_range, multiple_tables=True)

    for table in tables:
        # Convert to DataFrame
        df = pd.DataFrame(table)

        # Retain the header without altering it
        if not df.empty:
            extracted_tables.append(df)

    return extracted_tables

# Extract charts and graphs (as images) from a PDF
def extract_charts_from_pdf(pdf_bytes, page_indices=None):
    return extract_images_from_pages(pdf_bytes, page_indices)
