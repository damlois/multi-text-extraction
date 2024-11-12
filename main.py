import streamlit as st
import asyncio
from utils.file_type.csv import process_csv
from utils.file_type.doc import process_docx
from utils.file_type.pdf import process_pdf
from utils.display import (display_tables, display_text, display_images)

# Initialize session state for prompts and images
if 'prompts' not in st.session_state:
    st.session_state.prompts = []

if 'images' not in st.session_state:
    st.session_state.images = []

st.title("Document Processing Tool")

uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "csv"])

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]

    # Process PDF files
    if file_type == "pdf":
        # Select field to choose the type of data to extract from the PDF
        extraction_category = st.selectbox("Select extraction category", ["Text", "Tables", "Images"])
        # Input field to specify page range for extraction
        page_range_str = st.text_input("Enter page range (e.g., 1-3,5):")

        # Button to trigger PDF processing
        if st.button("Process PDF"):
            with st.spinner("Processing PDF... Please wait."):
                # Call async function to process PDF
                result = asyncio.run(process_pdf(uploaded_file, page_range_str, extraction_category))

            # Handle any errors in the result
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["message"])

                # Store extracted data in session state based on extraction category
                if extraction_category == "Images":
                    st.session_state.images = result.get("data", [])  # Store images
                    st.session_state.prompts = [""] * len(st.session_state.images)  # Reset prompts for each image
                elif extraction_category == "Tables":
                    display_tables(result)
                else:
                    display_text(result)

    # Process DOCX files
    elif file_type == "docx":
        st.write("Processing DOCX...")
        with st.spinner("Processing DOCX... Please wait."):
            # Process DOCX and extract text
            text = process_docx(uploaded_file)
        st.text_area("Extracted Text:", text)

    # Process CSV files
    elif file_type == "csv":
        st.write("Processing CSV...")
        with st.spinner("Processing CSV... Please wait."):
            # Process CSV and extract text
            text = process_csv(uploaded_file)
        st.text_area("Extracted Text:", text)

# Call the display_images function to show any extracted images and associated prompts
display_images()
