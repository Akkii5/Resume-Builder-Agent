# ⚡ AI Resume Builder v2

Upload your resume → Paste job description → Get a 95%+ ATS-optimized resume instantly.

---

## 📁 Project Structure

```
Resume_Agent/
├── app.py                     ← Flask server
├── config.py                  ← 🔑 PUT YOUR GROQ API KEY HERE
├── requirements.txt
├── templates/
│   └── index.html             ← UI
├── static/
│   ├── css/style.css
│   └── js/main.js
└── utils/
    ├── __init__.py
    ├── resume_extractor.py    ← Reads PDF/DOCX/TXT
    ├── resume_generator.py    ← Groq AI tailoring
    └── pdf_exporter.py        ← PDF via ReportLab (no system deps!)
```

---

## 🚀 Setup

### 1. Add your Groq API key
Open `config.py` and replace the placeholder:
```python
GROQ_API_KEY = "gsk_your_actual_key_here"
```
Get a free key at https://console.groq.com

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python app.py
```

Open http://localhost:5000

---

## 💡 How to Use

1. Upload your current resume (PDF, DOCX, or TXT)
2. Paste the job description you're applying for
3. Click **Generate ATS-Optimized Resume**
4. Download as PDF or copy the text

---

## ✅ What's New in v2

- No Groq API key on UI — stored in config.py
- Upload resume instead of typing everything manually
- PDF uses ReportLab (no system libraries, works on Windows!)
- ATS score + keywords added shown after generation
- Shows what the AI improved
