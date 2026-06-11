import PyPDF2
def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text