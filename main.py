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

    if file_type == "pdf":
        extraction_category = st.selectbox("Select extraction category", ["Text", "Tables", "Images"])
        page_range_str = st.text_input("Enter page range (e.g., 1-3,5):")

        if st.button("Process PDF"):
            with st.spinner("Processing PDF... Please wait."):
                result = asyncio.run(process_pdf(uploaded_file, page_range_str, extraction_category))

            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["message"])

                # Store the images and prompts in session state
                if extraction_category == "Images":
                    st.session_state.images = result.get("data", [])
                    st.session_state.prompts = [""] * len(st.session_state.images)  # Reset prompts based on number of images
                elif extraction_category == "Tables":
                    display_tables(result)
                else:
                    display_text(result)

    elif file_type == "docx":
        st.write("Processing DOCX...")
        with st.spinner("Processing DOCX... Please wait."):
            text = process_docx(uploaded_file)
        st.text_area("Extracted Text:", text)

    elif file_type == "csv":
        st.write("Processing CSV...")
        with st.spinner("Processing CSV... Please wait."):
            text = process_csv(uploaded_file)
        st.text_area("Extracted Text:", text)


# Call display_images() to show images and prompts
display_images()
