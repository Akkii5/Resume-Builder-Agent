import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file
from utils.resume_extractor import extract_resume_text
from utils.resume_generator import generate_resume
from utils.pdf_exporter import export_to_pdf
from config import GROQ_API_KEY

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract-resume", methods=["POST"])
def extract_resume():
    """Extract text/data from uploaded resume file."""
    if "resume_file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["resume_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".docx") or filename.endswith(".txt")):
        return jsonify({"error": "Only PDF, DOCX, or TXT files are supported."}), 400

    file_bytes = file.read()
    result = extract_resume_text(file_bytes, file.filename)
    return jsonify(result)


@app.route("/generate", methods=["POST"])
def generate():
    """Generate tailored resume using Groq AI."""
    data = request.get_json()
    resume_text = data.get("resume_text", "")
    job_description = data.get("job_description", "")

    if not resume_text:
        return jsonify({"error": "Resume text is required."}), 400
    if not job_description:
        return jsonify({"error": "Job description is required."}), 400

    result = generate_resume(GROQ_API_KEY, resume_text, job_description)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result)


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    """Export resume to PDF."""
    data = request.get_json()
    resume_data = data.get("resume_data", {})
    if not resume_data:
        return jsonify({"error": "No resume data provided."}), 400

    pdf_path = export_to_pdf(resume_data)
    if not pdf_path:
        return jsonify({"error": "PDF export failed."}), 500

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name="tailored_resume.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
