import streamlit as st
import pandas as pd

def display_tables(result):
    if "data" in result:
        for idx, table_with_context in enumerate(result["data"]):
            context = table_with_context.get("context", "")
            table = table_with_context.get("table", None)

            if context:
                st.text(f"Context for Table {idx + 1}:")
                st.write(context)

            if isinstance(table, pd.DataFrame):
                st.text(f"Table {idx + 1}")
                st.dataframe(table)
            else:
                st.warning(f"Skipped a non-DataFrame item: {table}")

def display_images(result):
    if "data" in result:
        for idx, (image_url, extracted_text) in enumerate(result["data"]):
            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 2px solid #FFD700; border-radius: 10px; padding: 10px; display: flex; align-items: flex-start;">
                        <img src="{image_url}" style="width: 40%; border-radius: 8px; margin-right: 40px; object-fit: contain;" alt="Extracted Image {idx + 1}">
                        <div style="flex: 1; width: 55%;">
                            <h3 style="color: #007BFF;">Image {idx + 1}</h3>
                            <p style="font-family: Arial, sans-serif; font-size: 14px;">
                                {extracted_text if extracted_text else "No text extracted from this image."}
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.warning("No images found in the selected pages.")


def display_text(result):
    st.write("Extracted Data:", result["data"])
