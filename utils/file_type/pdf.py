import os
import asyncio
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile
import pandas as pd
from tabula import read_pdf
from dotenv import load_dotenv
from urllib.parse import quote_plus
from multiprocessing import Pool, cpu_count
from model import process_images
from utils.helpers import parse_page_range, upload_image_to_s3

load_dotenv()


async def process_pdf(file_obj, page_range_str=None, extraction_category=None):
    pdf_bytes = file_obj.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count

    page_indices = parse_page_range(page_range_str, num_pages)
    if page_indices is None:
        return {"error": "Invalid page range or out of bounds. Please check the document page numbers."}

    if not page_indices:
        page_indices = list(range(num_pages))

    if extraction_category == "Text":
        extracted_text = extract_text_from_pdf(pdf_bytes, page_indices)
        if not extracted_text:
            return {"error": "No text found."}
        return {"data": extracted_text, "message": f"Extracted text from pages {page_range_str or 'all'}."}
    elif extraction_category == "Tables":
        extracted_tables = extract_tables_from_pdf(pdf_bytes, page_indices)
        if not extracted_tables:
            return {"error": "No tables found."}
        return {"data": extracted_tables, "message": f"Extracted tables from pages {page_range_str or 'all'}."}
    elif extraction_category == "Images":
        extracted_images = await extract_images_from_pdf(pdf_bytes, page_indices)
        if not extracted_images:
            return {"error": "No images found."}
        return {"data": extracted_images,
                "message": f"Extracted images from pages {page_range_str or 'all'}."}
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


def extract_tables_from_pdf(pdf_bytes, page_indices=None):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = doc.page_count

    if page_indices:
        page_indices = [i for i in page_indices if i < total_pages]
    else:
        page_indices = range(total_pages)

    extracted_tables_with_context = []

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name

    for page_num in page_indices:
        page = doc.load_page(page_num)
        page_text = page.get_text("blocks")

        tables = read_pdf(tmp_file_path, pages=str(page_num + 1), multiple_tables=True, output_format='json')

        for table_info in tables:
            top = table_info['top']
            left = table_info['left']
            width = table_info['width']
            height = table_info['height']
            bottom = top + height
            right = left + width

            table_bbox = (left, top, right, bottom)
            table_data = table_info['data']
            cleaned_table_data = []

            if isinstance(table_data, list):
                for row in table_data:
                    if isinstance(row, list):
                        cleaned_row = [cell.get('text', '') for cell in row if isinstance(cell, dict)]
                        cleaned_table_data.append(cleaned_row)

            df = pd.DataFrame(cleaned_table_data)

            surrounding_text = extract_surrounding_text(page_text, table_bbox)

            extracted_tables_with_context.append({
                "table": df,
                "context": surrounding_text
            })

    return extracted_tables_with_context


def extract_surrounding_text(page_text, table_bbox, context_buffer=50):
    surrounding_text = []

    for block in page_text:
        if len(block) >= 5:
            x0, y0, x1, y1, text = block[:5]

            if (
                    (y1 < table_bbox[1] + context_buffer and y0 > table_bbox[1] - context_buffer)
                    or (y0 > table_bbox[3] and y1 < table_bbox[3] + context_buffer)
            ):
                surrounding_text.append(text)

    return " ".join(surrounding_text)


async def extract_images_from_pdf(pdf_bytes, page_indices=None):
    bucket_name = os.getenv("BUCKET_NAME")
    image_urls = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if page_indices is None else page_indices

    tasks = []
    for i in page_range:
        page = doc.load_page(i)
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            pix = doc.extract_image(img[0])
            img_bytes = pix['image']
            img_ext = pix['ext']
            img_filename = f"page_{i + 1}_image_{img_index + 1}.{img_ext}"

            task = upload_image_to_s3(img_bytes, bucket_name, img_filename)
            tasks.append(task)

            image_url = f"https://{bucket_name}.s3.amazonaws.com/{quote_plus(img_filename)}"
            image_urls.append(image_url)

    await asyncio.gather(*tasks)
    return await process_images(image_urls)


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


def parallel_pdf_text_extraction(pdf_bytes, num_pages):
    cpu = cpu_count()
    seg_size = int(num_pages / cpu + 1)
    indices = [range(i * seg_size, min((i + 1) * seg_size, num_pages)) for i in range(cpu)]
    with Pool() as pool:
        results = pool.starmap(extract_text_from_pdf, [(pdf_bytes, idx) for idx in indices])
    combined_text = "".join(results)
    return combined_text
