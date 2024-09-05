import streamlit as st
from utils import process_pdf, process_docx, process_csv
import time


def main():
    st.title("File Processing App")

    uploaded_files = st.file_uploader("Upload PDF, CSV, DOC, or DOCX files",
                                      type=['pdf', 'csv', 'doc', 'docx'],
                                      accept_multiple_files=True)

    if uploaded_files:
        if st.button("Submit"):
            start_time = time.time()

            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                st.write(f"Processing file: {file_name}")

                # Process PDF files
                if file_name.endswith('.pdf'):
                    result = process_pdf(uploaded_file)
                    st.write(f"PDF Processing Result for {file_name}:")
                    st.write(result)

                # Process DOC or DOCX files
                elif file_name.endswith(('.doc', '.docx')):
                    result = process_docx(uploaded_file)
                    st.write(f"DOC/DOCX Processing Result for {file_name}:")
                    st.write(result)

                # Process CSV files
                elif file_name.endswith('.csv'):
                    result = process_csv(uploaded_file)
                    st.write(f"CSV Processing Result for {file_name}:")
                    st.write(result)
                else:
                    st.error(f"Unsupported file type: {file_name}")

            end_time = time.time()
            total_time = end_time - start_time
            st.write(f"Total time taken for processing: {total_time:.2f} seconds")


if __name__ == "__main__":
    main()
