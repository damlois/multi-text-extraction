import streamlit as st
import pandas as pd

from model import summarize_image


def display_tables(result):
    if "data" in result:
        for idx, table_with_context in enumerate(result["data"]):
            parsing_report = table_with_context.get("parsing_report", "")
            table = table_with_context.get("table", None)

            if isinstance(table, pd.DataFrame):
                filtered_report = {k: v for k, v in parsing_report.items() if
                                   k not in ["whitespace", "order", "context"]}

                st.write(f"### Table {idx + 1}")
                st.markdown(f"**Context:** {parsing_report['context']}")
                st.write("Parsing Report:")
                st.json(filtered_report)
                st.dataframe(table)
            else:
                st.warning(f"Skipped a non-DataFrame item: {table}")


def display_images():
    # Check if images exist in session state
    if st.session_state.images:
        # Initialize prompts in session state as a dictionary if not already done
        if 'prompts' not in st.session_state or not isinstance(st.session_state.prompts, dict):
            st.session_state.prompts = {}  # Initialize as a dictionary

        for idx, image_url in enumerate(st.session_state.images):
            # Create two columns: one for the image and another for input, button, and result
            col1, col2 = st.columns([2, 3])  # Adjust column widths as needed

            # Add spacing between individual rows (images)
            st.markdown("<br>", unsafe_allow_html=True)  # Add a line break for spacing between images

            with col1:
                st.image(image_url, caption=f"Image {idx + 1}", use_column_width=True)

            # Add space between columns using markdown
            with st.container():
                st.markdown("<div style='width: 70px;'></div>", unsafe_allow_html=True)  # Add horizontal space

            with col2:
                # Maintain the prompt state using session state
                prompt_key = f"prompt_{idx}"  # Unique key for each image prompt

                # Initialize prompt in session state if not present
                if prompt_key not in st.session_state.prompts:
                    st.session_state.prompts[prompt_key] = ""  # Initialize if not present

                # Streamlit text input for user prompt
                prompt = st.text_input(
                    f"Ask a question about Image {idx + 1}:",
                    value=st.session_state.prompts[prompt_key],
                    key=prompt_key,
                    placeholder="Enter your question here"
                )

                # Streamlit submit button
                if st.button(f"Submit", key=f"submit_{idx}"):
                    if prompt:
                        # Store the prompt in session state
                        st.session_state.prompts[prompt_key] = prompt
                        # Get the summary for the specific image and prompt
                        result_text = summarize_image(image_url, prompt)
                        st.write(result_text)
                    else:
                        st.warning("Please enter a question before submitting.")


    # else:
    #     st.warning("No images found in the selected pages.")


def display_text(result):
    st.write("Extracted Data:", result["data"])
