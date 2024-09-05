from multiprocessing import Pool, cpu_count
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import csv
from spire.doc import Document
import tempfile

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

def extract_text_from_page_indices(pdf_bytes, indices):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in indices:
        page = doc.load_page(i)
        extracted_text += page.get_text("text")
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_bytes, pages=[i])
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

def process_pdf(file_obj):
    pdf_bytes = file_obj.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count
    if num_pages < 10:
        extracted_text = extract_text_from_pages_single_threaded(pdf_bytes)
    else:
        extracted_text = parallel_pdf_text_extraction(pdf_bytes, num_pages)
    return extracted_text

def process_csv(file_obj):
    file_obj.seek(0)
    reader = csv.reader(file_obj.read().decode('utf-8').splitlines())
    return "\n".join([",".join(row) for row in reader])
