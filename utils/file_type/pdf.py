import os
import asyncio
import camelot
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile
from dotenv import load_dotenv
from urllib.parse import quote_plus
from multiprocessing import Pool, cpu_count
from utils.helpers import upload_image_to_s3, delete_all_objects, validate_page_range  # Helper functions

# Load environment variables from .env file
load_dotenv()


# Main async function to process PDF
async def process_pdf(file_obj, page_range_str=None, extraction_category=None):
    pdf_bytes = file_obj.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = doc.page_count

    # Validate the page range input, ensuring the pages exist
    page_indices = validate_page_range(page_range_str, num_pages)
    if "error" in page_indices:
        return page_indices

    # Get the corresponding extraction function based on category (Text, Tables, Images)
    extraction_func = get_extraction_function(extraction_category)

    # If the page range is large, process pages in parallel for efficiency
    if len(page_range_str or "") > 10:
        extracted_data = parallel_pdf_text_extraction(pdf_bytes, page_indices, extraction_func)
    else:
        extracted_data = await perform_extraction(extraction_func, pdf_bytes, page_indices, extraction_category)

    return generate_response(extracted_data, extraction_category, page_range_str, file_obj)


# Helper function to get the correct extraction function based on category (Text, Tables, or Images)
def get_extraction_function(category):
    extraction_functions = {
        "Text": extract_text_from_pdf,
        "Tables": extract_tables_from_pdf,
        "Images": extract_images_from_pdf
    }
    return extraction_functions.get(category)


# Function to handle the extraction process, based on the selected extraction category
async def perform_extraction(extraction_func, pdf_bytes, page_indices, category):
    if category == "Images":
        return await extraction_func(pdf_bytes, page_indices)  # Handle async image extraction
    return extraction_func(pdf_bytes, page_indices)  # Handle text or table extraction


# Function to generate the response to return after processing
def generate_response(extracted_data, category, page_range_str, file_obj):
    if not extracted_data:
        return {"error": f"No {category.lower()} found in pages {page_range_str or 'all'} of {file_obj.name}."}

    return {
        "data": extracted_data,
        "message": f"Extracted {category.lower()} from pages {page_range_str or 'all'} in {file_obj.name}."
    }


# Function to extract text from PDF using multiprocessing for large page ranges
def parallel_pdf_text_extraction(pdf_bytes, page_indices, extract_function):
    cpu = cpu_count()  # Get the number of CPU cores available
    seg_size = int(len(page_indices) / cpu + 1)  # Split page indices into segments
    indices_segments = [page_indices[i * seg_size:(i + 1) * seg_size] for i in range(cpu)]  # Split pages into smaller chunks

    # Use multiprocessing to process the PDF in parallel
    with Pool() as pool:
        results = pool.starmap(extract_function, [(pdf_bytes, idx_segment) for idx_segment in indices_segments])

    # Combine the results from each process
    combined_text = "".join(results)
    return combined_text


# Function to extract text from a specific set of PDF pages
def extract_text_from_pdf(pdf_bytes, indices):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in indices:
        page = doc.load_page(i)
        extracted_text += page.get_text("text")  # Extract text from the page

        # If no text is extracted, try OCR (Tesseract) for that page
        if not extracted_text.strip():
            extracted_text = extract_text_with_tesseract(pdf_bytes, pages=[i])

        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text


# Function to extract text from a PDF page using Tesseract (OCR)
def extract_text_with_tesseract(pdf_bytes, pages=None):
    extracted_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if pages is None else pages
    for i in page_range:
        page = doc.load_page(i)
        pix = page.get_pixmap()  # Convert page to image
        image = Image.open(BytesIO(pix.tobytes(output="png")))  # Create a PIL image from the page
        extracted_text += pytesseract.image_to_string(image)  # Perform OCR on the image
        extracted_text += f"\n--- End of Page {i + 1} ---\n"
    return extracted_text


# Function to extract tables from PDF using Camelot
def extract_tables_from_pdf(pdf_bytes, page_indices=None):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = doc.page_count

    if page_indices:
        page_indices = [i for i in page_indices if i < total_pages]
    else:
        page_indices = range(total_pages)

    extracted_tables_with_context = []

    # Save the PDF temporarily for Camelot to read
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name

    # Extract tables from each specified page
    for page_num in page_indices:
        page = doc.load_page(page_num)

        tables = camelot.read_pdf(tmp_file_path, pages=str(page_num + 1))  # Read tables from the page

        # For each table, extract context and metadata
        for i, table in enumerate(tables):
            parsing_report = table.parsing_report
            df = table.df

            page_text = page.get_text("blocks")
            left, top, right, bottom = table._bbox
            page_height = page.rect.height

            # Extract surrounding text (e.g., headers, captions) near the table
            surrounding_text = extract_surrounding_text(page_text, left, page_height - bottom, right, page_height - top)
            parsing_report["context"] = surrounding_text

            extracted_tables_with_context.append({
                "table": df,
                "parsing_report": parsing_report
            })

    return extracted_tables_with_context


# Function to extract surrounding text (e.g., captions) around a table in a PDF
def extract_surrounding_text(page_text, left, top, right, bottom):
    surrounding_text = []
    context_buffer = 25  # Smaller buffer for closer context only

    for block in page_text:
        x0, y0, x1, y1, text = block[:5]
        is_within_horizontal_range = (x0 < right and x1 > left)

        is_above_table = (y1 <= top and y1 >= top - context_buffer)
        is_below_table = (y0 >= bottom and y0 <= bottom + context_buffer)

        if is_within_horizontal_range and (is_above_table or is_below_table):
            surrounding_text.append(text)

    return " ".join(surrounding_text)


# Function to extract images from a PDF and upload them to S3
async def extract_images_from_pdf(pdf_bytes, page_indices=None):
    bucket_name = os.getenv("BUCKET_NAME")
    image_urls = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_range = range(doc.page_count) if page_indices is None else page_indices

    await delete_all_objects(bucket_name)

    tasks = []

    # Loop through each page and extract images
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
    return image_urls
