from flask import (
    Flask,
    render_template,
    request,
    make_response,
    redirect
)

from flask_sqlalchemy import SQLAlchemy

from parser import extract_text
from generator import generate_response
from metadata import extract_metadata

from dotenv import load_dotenv

from xhtml2pdf import pisa
from io import BytesIO

import markdown
import os

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

with app.app_context():
    db.create_all()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# DATABASE MODEL
# ============================================================

class Analysis(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(200)
    )

    filepath = db.Column(
        db.String(500)
    )

    content = db.Column(
        db.Text
    )

    title = db.Column(
        db.String(500)
    )

    author = db.Column(
        db.String(500)
    )

    pages = db.Column(
        db.String(50)
    )

# ============================================================
# PARSER
# ============================================================

def parse_output(text):

    sections = {

        "SUMMARY": "",

        "CORE_IDEA": "",

        "TECH_STACK": "",

        "IMPLEMENTATION": "",

        "FOLDER_STRUCTURE": ""
    }

    current_section = None

    for line in text.splitlines():

        stripped = line.strip()

        clean = stripped.upper() \
                        .replace("*", "") \
                        .replace("#", "") \
                        .replace(":", "") \
                        .strip()

        # ====================================================
        # DETECT HEADERS
        # ====================================================

        if clean == "SUMMARY":

            current_section = "SUMMARY"
            continue

        elif clean in ["CORE IDEA", "CORE_IDEA"]:

            current_section = "CORE_IDEA"
            continue

        elif clean in ["TECH STACK", "TECH_STACK"]:

            current_section = "TECH_STACK"
            continue

        elif clean == "IMPLEMENTATION":

            current_section = "IMPLEMENTATION"
            continue

        elif clean in ["FOLDER STRUCTURE", "FOLDER_STRUCTURE"]:

            current_section = "FOLDER_STRUCTURE"
            continue

        # ====================================================
        # APPEND CONTENT
        # ====================================================

        if current_section:

            sections[current_section] += stripped + "\n"

    return sections

# ============================================================
# MARKDOWN CONVERSION
# ============================================================

def markdown_sections(parsed):

    for key in parsed:

        parsed[key] = markdown.markdown(

            parsed[key],

            extensions=[
                "fenced_code",
                "tables"
            ]
        )

    return parsed

# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    analyses = Analysis.query.order_by(
        Analysis.id.desc()
    ).all()

    return render_template(

        "index.html",

        analyses=analyses
    )

# ============================================================
# UPLOAD
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():

    if "pdf" not in request.files:

        return "No file uploaded"

    file = request.files["pdf"]

    if file.filename == "":

        return "No file selected"

    # ========================================================
    # SAVE FILE
    # ========================================================

    filepath = os.path.join(

        app.config["UPLOAD_FOLDER"],

        file.filename
    )

    file.save(filepath)

    # ========================================================
    # EXTRACT PDF TEXT
    # ========================================================

    paper_text = extract_text(filepath)

    # ========================================================
    # EXTRACT PDF METADATA
    # ========================================================

    pdf_metadata = extract_metadata(filepath)

    # ========================================================
    # GENERATE AI RESPONSE
    # ========================================================

    ai_output = generate_response(paper_text)

    # ========================================================
    # SAVE TO DATABASE
    # ========================================================

    analysis = Analysis(

        filename=file.filename,

        filepath=filepath,

        content=ai_output,

        title=pdf_metadata.get(
            "title",
            file.filename
        ),

        author=pdf_metadata.get(
            "author",
            "Unknown Author"
        ),

        pages=str(
            pdf_metadata.get(
                "pages",
                "-"
            )
        )
    )

    db.session.add(analysis)

    db.session.commit()

    # ========================================================
    # PARSE AI OUTPUT
    # ========================================================

    parsed = parse_output(ai_output)

    parsed = markdown_sections(parsed)

    # ========================================================
    # RECENT ANALYSES
    # ========================================================

    analyses = Analysis.query.order_by(
        Analysis.id.desc()
    ).all()

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(

        "result.html",

        data=parsed,

        analyses=analyses,

        metadata=pdf_metadata,

        analysis_id=analysis.id
    )

# ============================================================
# VIEW SAVED ANALYSIS
# ============================================================

@app.route("/analysis/<int:id>")
def analysis(id):

    analysis = Analysis.query.get_or_404(id)

    # ========================================================
    # PARSE CONTENT
    # ========================================================

    parsed = parse_output(
        analysis.content
    )

    parsed = markdown_sections(parsed)

    # ========================================================
    # SIDEBAR
    # ========================================================

    analyses = Analysis.query.order_by(
        Analysis.id.desc()
    ).all()

    # ========================================================
    # METADATA
    # ========================================================

    metadata = {

        "title":
        analysis.title
        if analysis.title
        else analysis.filename,

        "author":
        analysis.author
        if analysis.author
        else "Unknown Author",

        "pages":
        analysis.pages
        if analysis.pages
        else "-"
    }

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(

        "result.html",

        data=parsed,

        analyses=analyses,

        metadata=metadata,

        analysis_id=analysis.id
    )

# ============================================================
# DOWNLOAD PDF
# ============================================================

@app.route("/download/<int:id>")
def download(id):

    analysis = Analysis.query.get_or_404(id)

    parsed = parse_output(
        analysis.content
    )

    html = f"""

    <h1>{analysis.title}</h1>

    <h2>Summary</h2>
    <p>{parsed["SUMMARY"]}</p>

    <h2>Core Idea</h2>
    <p>{parsed["CORE_IDEA"]}</p>

    <h2>Tech Stack</h2>
    <p>{parsed["TECH_STACK"]}</p>

    <h2>Implementation</h2>
    <p>{parsed["IMPLEMENTATION"]}</p>

    <h2>Folder Structure</h2>
    <p>{parsed["FOLDER_STRUCTURE"]}</p>

    """

    pdf = BytesIO()

    pisa.CreatePDF(
        html,
        dest=pdf
    )

    response = make_response(
        pdf.getvalue()
    )

    response.headers["Content-Type"] = \
        "application/pdf"

    response.headers["Content-Disposition"] = \
        f"attachment; filename={analysis.title}.pdf"

    return response

# ============================================================
# DELETE ANALYSIS
# ============================================================

@app.route("/delete/<int:id>")
def delete(id):

    analysis = Analysis.query.get_or_404(id)

    # ========================================================
    # DELETE FILE
    # ========================================================

    if analysis.filepath and os.path.exists(
        analysis.filepath
    ):

        os.remove(analysis.filepath)

    # ========================================================
    # DELETE DATABASE ENTRY
    # ========================================================

    db.session.delete(analysis)

    db.session.commit()

    return redirect("/")

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)