import streamlit as st
import camelot
import pandas as pd
import tempfile
import fitz  # PyMuPDF

st.title("PDF Table and Surrounding Text Extractor")

# Function to extract surrounding text using coordinates
def extract_surrounding_text(page_text, left, top, right, bottom):
    surrounding_text = []
    context_buffer = 25  # Smaller buffer for closer context only

    st.text(f"left {left} top {top} right {right} bottom {bottom}")

    for block in page_text:
        x0, y0, x1, y1, text = block[:5]

        # Check if the block is horizontally aligned with the table
        is_within_horizontal_range = (x0 < right and x1 > left)

        # Check if the block is directly above the table within a small buffer
        is_above_table = (y1 <= top and y1 >= top - context_buffer)

        # Check if the block is directly below the table within a small buffer
        is_below_table = (y0 >= bottom and y0 <= bottom + context_buffer)

        # Append text if it's horizontally aligned and very close to the table
        if is_within_horizontal_range and (is_above_table or is_below_table):
            surrounding_text.append(text)

    return " ".join(surrounding_text)


# Step 1: Upload PDF
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    # Step 2: Parse the PDF tables
    tables = camelot.read_pdf(temp_path, pages='all')  # Optionally specify page range
    st.write(f"Total Tables Extracted: {len(tables)}")

    # Open the PDF with PyMuPDF to extract surrounding text
    with fitz.open(temp_path) as pdf:
        # Loop through each extracted table
        for i, table in enumerate(tables):
            st.write(f"### Table {i + 1}")

            # Display table parsing report
            parsing_report = table.parsing_report


            # Show a summary of the table
            # st.write("Table Shape:", table.shape)
            # st.write("Accuracy:", parsing_report['accuracy'])
            # st.write("Whitespace:", parsing_report['whitespace'])

            # Convert table to DataFrame
            df = table.df
            st.write("Extracted Table:")
            st.dataframe(df)

            # Extract surrounding text
            page_number = table.page
            page = pdf[page_number - 1]  # Pages are 0-indexed in PyMuPDF

            # Get all text blocks on the page
            page_text = page.get_text("blocks")

            # Logging for debugging
            st.write(f"Raw Bounding Box (left, top, right, bottom): {table._bbox}")

            # Camelot bbox format is typically in (left, top, right, bottom)
            left, top, right, bottom = table._bbox
            page_height = page.rect.height

            surrounding_text = extract_surrounding_text(page_text, left, page_height-bottom, right, page_height-top)
            parsing_report["context"] = surrounding_text
            st.write("Parsing Report:", parsing_report)
            # st.write("Surrounding Text (e.g., Caption or Header):")
            # st.write(surrounding_text if surrounding_text else "No surrounding text found.")


            # # Step 3: Download Options for each table
            # st.write("#### Download Options")
            #
            # # CSV Download
            # csv = df.to_csv(index=False).encode('utf-8')
            # st.download_button(
            #     label=f"Download Table {i + 1} as CSV",
            #     data=csv,
            #     file_name=f'table_{i + 1}.csv',
            #     mime='text/csv'
            # )
            #
            # # JSON Download
            # json_data = df.to_json(orient="records")
            # st.download_button(
            #     label=f"Download Table {i + 1} as JSON",
            #     data=json_data,
            #     file_name=f'table_{i + 1}.json',
            #     mime='application/json'
            # )

            # Uncomment these for additional formats if needed

            # # Excel Download
            # excel_data = df.to_excel(index=False, engine='openpyxl')
            # st.download_button(
            #     label=f"Download Table {i + 1} as Excel",
            #     data=excel_data,
            #     file_name=f'table_{i + 1}.xlsx',
            #     mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            # )

            # # HTML Download
            # html_data = df.to_html(index=False)
            # st.download_button(
            #     label=f"Download Table {i + 1} as HTML",
            #     data=html_data,
            #     file_name=f'table_{i + 1}.html',
            #     mime='text/html'
            # )

            # # Markdown Download
            # markdown_data = df.to_markdown(index=False)
            # st.download_button(
            #     label=f"Download Table {i + 1} as Markdown",
            #     data=markdown_data,
            #     file_name=f'table_{i + 1}.md',
            #     mime='text/markdown'
            # )
