import tempfile
from spire.doc import Document

def process_docx(file_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(file_obj.read())
        tmp_file_path = tmp_file.name

    document = Document()
    document.LoadFromFile(tmp_file_path)
    result_text = document.GetText()

    return result_text
