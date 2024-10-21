import fitz
import streamlit as st
import pandas as pd

from utils import (
    process_docx,
    process_csv,
    process_pdf,
    extract_text_from_pages_single_threaded,
    extract_tables_from_pdf,
    extract_images_from_pages,
    extract_charts_from_pdf,
    parse_page_range,
)


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
        extracted_tables = extract_tables_from_pdf(pdf_bytes, page_indices)
        if extracted_tables:
            message = f"Extracted tables from pages {page_range_str or 'all'}."
            return {"tables": extracted_tables, "message": message}
        else:
            return {"error": "No tables found."}
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


# Streamlit UI
st.title("Document Processing Tool")

uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "csv"])

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]

    if file_type == "pdf":
        page_range_str = st.text_input("Enter page range (e.g., 1-3,5):")
        extraction_category = st.selectbox("Select extraction category", ["Text", "Tables", "Images"])

        if st.button("Process PDF"):
            result = process_pdf(uploaded_file, page_range_str, extraction_category)

            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["message"])

                # Store the extracted tables in session state
                if "tables" in result:
                    # Initialize session state for tables if not already set
                    if 'extracted_tables' not in st.session_state:
                        st.session_state.extracted_tables = []

                    # Append new tables to the session state
                    st.session_state.extracted_tables.extend(result["tables"])

                    # Display extracted tables as DataFrame and allow download as CSV
                    for idx, table in enumerate(st.session_state.extracted_tables):  # Use session state
                        st.text(f"Table {idx + 1}")
                        st.dataframe(table)

    elif file_type == "docx":
        st.write("Processing DOCX...")
        text = process_docx(uploaded_file)
        st.text_area("Extracted Text:", text)

    elif file_type == "csv":
        st.write("Processing CSV...")
        text = process_csv(uploaded_file)
        st.text_area("Extracted Text:", text)
