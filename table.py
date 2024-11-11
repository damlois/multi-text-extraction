import streamlit as st
import pandas as pd
from tabula import read_pdf
import tempfile

def main():
    st.title("PDF Table Extraction with Tabula-Py")

    # File upload
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        # Extract tables from PDF
        tables = read_pdf(tmp_file_path, pages="all", multiple_tables=True, pandas_options={'header': None})

        # Check if tables were found
        if tables:
            st.write(f"Extracted {len(tables)} tables from the PDF.")

            for idx, table in enumerate(tables):
                st.write(f"### Table {idx + 1}")
                st.dataframe(table)

                # Download the table as CSV
                csv_data = table.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"Download Table {idx + 1} as CSV",
                    data=csv_data,
                    file_name=f"table_{idx + 1}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No tables found in the uploaded PDF.")

if __name__ == "__main__":
    main()
