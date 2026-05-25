// ── STATE ──
let extractedText = "";
let generatedResumeData = null;
let loadingInterval = null;

// ── DRAG & DROP ──
const uploadZone = document.getElementById("uploadZone");
uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("dragover"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
});

// ── FILE SELECT ──
function handleFileSelect(input) {
  if (input.files[0]) processFile(input.files[0]);
}

function processFile(file) {
  const allowed = [".pdf", ".docx", ".txt"];
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast("Only PDF, DOCX, or TXT files are supported.", "error");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("File too large. Max 10MB.", "error");
    return;
  }

  // Show file info
  document.getElementById("fileName").textContent = file.name;
  document.getElementById("fileSize").textContent = formatBytes(file.size);
  document.getElementById("fileStatus").style.display = "block";
  document.getElementById("extractedPreview").style.display = "none";
  document.getElementById("extractStatus").textContent = "⏳ Extracting text from resume...";
  extractedText = "";

  // Upload & extract
  const formData = new FormData();
  formData.append("resume_file", file);

  fetch("/extract-resume", { method: "POST", body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        document.getElementById("extractStatus").textContent = "❌ " + data.error;
        showToast(data.error, "error");
        return;
      }
      extractedText = data.text;
      document.getElementById("extractStatus").textContent = "✅ Resume text extracted successfully!";
      showExtractedPreview(data.text);
      showToast("Resume uploaded and extracted!", "success");
    })
    .catch(() => {
      document.getElementById("extractStatus").textContent = "❌ Failed to extract. Please try again.";
      showToast("Extraction failed. Try a different file.", "error");
    });
}

function showExtractedPreview(text) {
  const lines = text.split("\n").filter(l => l.trim().length > 2);
  const wordCount = text.split(/\s+/).length;
  const lineCount = lines.length;

  const info = document.getElementById("extractedInfo");
  info.innerHTML = `
    <span class="ei-chip">📝 ~${wordCount} words</span>
    <span class="ei-chip">📄 ${lineCount} lines extracted</span>
    <span class="ei-chip">✅ Ready for AI processing</span>
  `;

  document.getElementById("rawText").value = text;
  document.getElementById("extractedPreview").style.display = "block";
}

function toggleRaw() {
  const box = document.getElementById("rawTextBox");
  const btn = document.querySelector(".toggle-raw");
  if (box.style.display === "none") {
    box.style.display = "block";
    btn.textContent = "Hide raw text";
  } else {
    box.style.display = "none";
    btn.textContent = "View raw text";
  }
}

function removeFile() {
  extractedText = "";
  document.getElementById("resumeFile").value = "";
  document.getElementById("fileStatus").style.display = "none";
  document.getElementById("extractedPreview").style.display = "none";
  showToast("File removed.", "info");
}

// ── LOADING ANIMATION ──
function startLoading() {
  const steps = ["ls1", "ls2", "ls3", "ls4", "ls5"];
  steps.forEach(id => { const el = document.getElementById(id); el.classList.remove("active", "done"); });
  document.getElementById("ls1").classList.add("active");
  let current = 0;
  loadingInterval = setInterval(() => {
    if (current < steps.length - 1) {
      document.getElementById(steps[current]).classList.remove("active");
      document.getElementById(steps[current]).classList.add("done");
      current++;
      document.getElementById(steps[current]).classList.add("active");
    }
  }, 2800);
}

function stopLoading() {
  if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; }
}

// ── SHOW STATE ──
function showPreviewState(state) {
  ["emptyState", "loadingState", "errorState", "resumeOutput"].forEach(id => {
    document.getElementById(id).style.display = "none";
  });
  document.getElementById(state).style.display = "block";
}

function resetPreview() {
  showPreviewState("emptyState");
  document.getElementById("previewActions").style.display = "none";
}

// ── GENERATE RESUME ──
async function generateResume() {
  if (!extractedText.trim()) {
    showToast("Please upload your resume first.", "error");
    return;
  }
  const jd = document.getElementById("jobDescription").value.trim();
  if (!jd) {
    showToast("Please paste the job description.", "error");
    document.getElementById("jobDescription").focus();
    return;
  }

  const btn = document.getElementById("generateBtn");
  btn.disabled = true;
  document.getElementById("btnText").textContent = "Generating...";

  showPreviewState("loadingState");
  startLoading();

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: extractedText, job_description: jd })
    });
    const data = await res.json();
    stopLoading();

    if (data.error) {
      document.getElementById("errorMessage").textContent = data.error;
      showPreviewState("errorState");
      return;
    }

    generatedResumeData = data.resume;
    renderResume(data.resume);
    showPreviewState("resumeOutput");
    document.getElementById("previewActions").style.display = "flex";
    document.getElementById("previewPanel").scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Resume generated! 🎉", "success");

  } catch (err) {
    stopLoading();
    document.getElementById("errorMessage").textContent = "Network error. Check your connection and try again.";
    showPreviewState("errorState");
  } finally {
    btn.disabled = false;
    document.getElementById("btnText").textContent = "Generate ATS-Optimized Resume";
  }
}

// ── RENDER RESUME ──
function renderResume(r) {
  // ── ATS Banner ──
  const atsScore = r.ats_score || "N/A";
  const matched  = r.keywords_matched || r.keywords_added || [];
  const missing  = r.keywords_missing || [];
  const banner   = document.getElementById("atsBanner");

  let scoreCol, borderCol, label, labelCol;
  if      (atsScore >= 80) { scoreCol="rgba(34,197,94,0.1)";  borderCol="rgba(34,197,94,0.3)";  label="Strong Match"; labelCol="#4ade80"; }
  else if (atsScore >= 65) { scoreCol="rgba(234,179,8,0.1)";  borderCol="rgba(234,179,8,0.3)";  label="Good Match";   labelCol="#facc15"; }
  else                     { scoreCol="rgba(239,68,68,0.1)";  borderCol="rgba(239,68,68,0.3)";  label="Needs Work";   labelCol="#f87171"; }

  banner.style.cssText = `background:${scoreCol};border:1px solid ${borderCol};border-radius:10px;padding:14px 18px;margin-bottom:0`;
  banner.innerHTML = `
    <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
      <div style="text-align:center;min-width:70px">
        <div style="font-family:Syne,sans-serif;font-size:32px;font-weight:800;color:${labelCol};line-height:1">${atsScore}%</div>
        <div style="font-size:10px;font-weight:700;color:${labelCol};margin-top:3px;text-transform:uppercase;letter-spacing:1px">${label}</div>
        <div style="font-size:10px;color:var(--text3);margin-top:2px">ATS Score</div>
      </div>
      <div style="width:1px;background:rgba(255,255,255,0.08);align-self:stretch;margin:0 4px"></div>
      <div style="flex:1;min-width:200px">
        <div style="font-size:11px;font-weight:700;color:#4ade80;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">✓ Keywords Matched (${matched.length})</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">${matched.slice(0,12).map(k=>`<span style="background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);color:#4ade80;padding:2px 8px;border-radius:10px;font-size:10px">${esc(k)}</span>`).join("")}</div>
      </div>
      ${missing.length ? `<div style="flex:1;min-width:180px">
        <div style="font-size:11px;font-weight:700;color:#f87171;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">✗ Consider Adding (${missing.length})</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">${missing.slice(0,8).map(k=>`<span style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:#f87171;padding:2px 8px;border-radius:10px;font-size:10px">${esc(k)}</span>`).join("")}</div>
      </div>` : ""}
    </div>`;

  // ── Resume HTML ──
  let html = "";

  // ── HEADER — plain white, centred ──
  const curTitle = r.experience?.[0]?.title || "";
  const contactParts = [
    r.email    ? `<a href="mailto:${esc(r.email)}">${esc(r.email)}</a>` : "",
    r.phone    ? esc(r.phone)    : "",
    r.linkedin ? `<a href="https://${esc(r.linkedin)}" target="_blank">${esc(r.linkedin)}</a>` : "",
    r.location ? esc(r.location) : "",
  ].filter(Boolean);

  html += `<div class="r-header">
    <h1>${esc(r.name)}</h1>
    ${curTitle ? `<div class="r-subtitle">${esc(curTitle)}</div>` : ""}
    <div class="r-contact"><span>${contactParts.join(" &nbsp;|&nbsp; ")}</span></div>
  </div>`;

  // ── SUMMARY ──
  if (r.summary) {
    html += `<div class="r-section">
      <div class="r-section-title">Professional Summary</div>
      <p class="r-summary">${esc(r.summary)}</p>
    </div>`;
  }

  // ── TECHNICAL SKILLS — 2-col label|values table (matches template) ──
  const groups = r.skills?.groups    || [];
  const tech   = r.skills?.technical || [];
  const soft   = r.skills?.soft      || [];

  if (groups.length || tech.length) {
    html += `<div class="r-section"><div class="r-section-title">Technical Skills</div>`;
    html += `<table class="r-skills-table">`;

    if (groups.length) {
      // Use AI-provided grouped skills
      groups.forEach(g => {
        html += `<tr><td>${esc(g.label)}</td><td>${(g.values||[]).map(s=>esc(s)).join(", ")}</td></tr>`;
      });
    } else {
      // Fallback: auto-chunk flat list into sensible rows
      const defaultLabels = ["Programming Language","Backend Frameworks","AI / LLM","Databases","Developer Tools","Other"];
      const chunkSize = Math.ceil(tech.length / 5);
      for (let i = 0, li = 0; i < tech.length; i += chunkSize, li++) {
        const chunk = tech.slice(i, i + chunkSize);
        html += `<tr><td>${defaultLabels[li] || "Skills"}</td><td>${chunk.map(s=>esc(s)).join(", ")}</td></tr>`;
      }
      if (soft.length) {
        html += `<tr><td>Core Competencies</td><td>${soft.map(s=>esc(s)).join(", ")}</td></tr>`;
      }
    }
    html += `</table></div>`;
  }

  // ── PROFESSIONAL EXPERIENCE ──
  if (r.experience?.length) {
    html += `<div class="r-section"><div class="r-section-title">Professional Experience</div>`;
    r.experience.forEach(exp => {
      const right = [exp.duration, exp.location].filter(Boolean).join(" | ");
      html += `<div class="r-exp-item">
        <div class="r-exp-header">
          <div class="r-exp-left">
            <span class="r-exp-title">${esc(exp.title)}</span>
            ${exp.company ? ` &nbsp;|&nbsp; <span class="r-exp-company">${esc(exp.company)}</span>` : ""}
          </div>
          <div class="r-exp-right">${esc(right)}</div>
        </div>
        <ul class="r-exp-bullets">${(exp.bullets||[]).map(b=>`<li>${esc(b)}</li>`).join("")}</ul>
      </div>`;
    });
    html += `</div>`;
  }

  // ── KEY PROJECTS ──
  if (r.projects?.length) {
    html += `<div class="r-section"><div class="r-section-title">Key Projects</div>`;
    r.projects.forEach(p => {
      const metaParts = [];
      if (p.role) metaParts.push(`Role: ${esc(p.role)}`);
      if (p.tech?.length) metaParts.push(`Tech Stack: ${p.tech.map(t=>esc(t)).join(", ")}`);
      const bullets = p.bullets?.length ? p.bullets
        : (p.description ? p.description.split(/(?<=[.!?])\s+/).filter(s=>s.trim()) : []);
      html += `<div class="r-proj-item">
        <div class="r-proj-name">${esc(p.name)}</div>
        ${metaParts.length ? `<div class="r-proj-meta">${metaParts.join(" &nbsp;|&nbsp; ")}</div>` : ""}
        <ul class="r-proj-bullets">${bullets.map(b=>`<li>${esc(b)}</li>`).join("")}</ul>
      </div>`;
    });
    html += `</div>`;
  }

  // ── EDUCATION ──
  if (r.education?.length) {
    html += `<div class="r-section"><div class="r-section-title">Education</div>`;
    r.education.forEach(edu => {
      html += `<div class="r-edu-item">
        <div class="r-edu-left">
          <div class="degree">${esc(edu.degree)}</div>
          <div class="school">${esc(edu.institution)}</div>
        </div>
        <div class="r-edu-right">${edu.year ? `Graduated: ${esc(edu.year)}` : ""}${edu.gpa ? `<br>GPA: ${esc(edu.gpa)}` : ""}</div>
      </div>`;
    });
    html += `</div>`;
  }

  // ── CERTIFICATIONS ──
  if (r.certifications?.length) {
    html += `<div class="r-section"><div class="r-section-title">Certifications</div>
      <ul class="r-list">${r.certifications.map(c=>`<li>${esc(c)}</li>`).join("")}</ul>
    </div>`;
  }

  // ── ACHIEVEMENTS ──
  const achs = (r.achievements||[]).filter(a=>a.trim());
  if (achs.length) {
    html += `<div class="r-section"><div class="r-section-title">Achievements</div>
      <ul class="r-list">${achs.map(a=>`<li>${esc(a)}</li>`).join("")}</ul>
    </div>`;
  }

  // ── TECHNOLOGIES footer bar ──
  const techBar = r.technologies_bar?.length
    ? r.technologies_bar
    : [...new Set([...(r.skills?.technical||[]), ...(r.keywords_added||[])])];
  if (techBar.length) {
    html += `<div class="r-tech-footer">${techBar.slice(0,28).map(t=>esc(t)).join(" &nbsp;|&nbsp; ")}</div>`;
  }

  document.getElementById("resumeContent").innerHTML = html;

  // Hide improvements box (not needed in new design)
  document.getElementById("improvementsBox").style.display = "none";
}

function toggleImprovements() {
  const list = document.getElementById("impList");
  const arrow = document.getElementById("impArrow");
  list.style.display = list.style.display === "none" ? "block" : "none";
  arrow.textContent = list.style.display === "none" ? "▼" : "▲";
}

// ── COPY ──
function copyResume() {
  const text = document.getElementById("resumeContent").innerText;
  navigator.clipboard.writeText(text).then(() => showToast("Copied to clipboard!", "success"))
    .catch(() => showToast("Copy failed. Select and copy manually.", "error"));
}

// ── EXPORT PDF ──
async function exportPDF() {
  if (!generatedResumeData) { showToast("No resume to export.", "error"); return; }

  const btn = document.querySelector(".pdf-btn");
  btn.textContent = "⏳ Generating PDF...";
  btn.disabled = true;

  try {
    const res = await fetch("/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_data: generatedResumeData })
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.error || "PDF export failed.", "error");
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "tailored_resume.pdf"; a.click();
    URL.revokeObjectURL(url);
    showToast("PDF downloaded! 📄", "success");

  } catch (e) {
    showToast("PDF export failed. Try copying the text instead.", "error");
  } finally {
    btn.textContent = "⬇ Download PDF";
    btn.disabled = false;
  }
}

// ── HELPERS ──
function esc(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function showToast(msg, type = "info") {
  document.querySelector(".toast")?.remove();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  const c = { success: ["#1b5e20","#4caf50","#a5d6a7"], error: ["#4a1010","#e94560","#ff8a80"], info: ["#0d2137","#29b6f6","#81d4fa"] }[type] || ["#0d2137","#29b6f6","#81d4fa"];
  Object.assign(toast.style, {
    position: "fixed", bottom: "24px", right: "24px", zIndex: "9999",
    background: c[0], border: `1px solid ${c[1]}`, color: c[2],
    padding: "12px 18px", borderRadius: "10px", fontSize: "13px",
    fontFamily: "DM Sans, sans-serif", boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
    animation: "fadeUp 0.3s ease", maxWidth: "300px"
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// Ctrl+Enter shortcut
document.addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") generateResume(); });
