import streamlit as st

from utils import (
    process_docx,
    process_csv,
    process_pdf
)

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
