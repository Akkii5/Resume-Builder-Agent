from groq import Groq
import json
import re
from config import GROQ_MODEL, MAX_TOKENS


# ── Comprehensive stop-word list — never count these as ATS keywords ──
STOP_WORDS = {
    # articles / prepositions / conjunctions
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","have","has","had","will","would",
    "can","could","should","may","might","must","shall","do","does","did",
    "not","no","nor","so","yet","both","either","neither","each","every",
    "by","from","as","into","through","during","including","about","against",
    "between","after","before","above","below","up","down","out","off","over",
    # pronouns
    "we","our","you","your","they","their","i","me","my","he","she","it",
    "its","this","that","these","those","who","which","what","where","when",
    # job-posting filler words — meaningless for ATS
    "experience","work","role","team","ability","strong","good","great",
    "excellent","required","preferred","responsibilities","requirements",
    "looking","join","candidate","ideal","position","opportunity","company",
    "job","seeking","responsible","about","using","closely","maintaining",
    "developing","solutions","suite","teams","skilled","developer",
    "designing","integration","development","api","software","scalable",
    "description","apply","please","must","will","also","able","well",
    "within","across","level","senior","junior","mid","full","time","part",
    "based","related","relevant","ensure","provide","support","manage",
    "working","including","following","other","more","new","high","large",
    "various","multiple","key","core","main","primary","secondary",
    "help","make","build","create","use","used","used","used","being",
    "day","days","year","years","month","months","week","weeks",
    "plus","bonus","salary","pay","benefits","location","remote","hybrid",
    "office","india","bangalore","mumbai","pune","delhi","hyderabad",
}


def extract_tech_keywords(text: str) -> list:
    """
    Extract only meaningful technical/domain keywords from text.
    Filters out stop words, short words, and generic filler.
    """
    # Extract single words (3+ chars)
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9#+.\-]{2,}\b', text)
    
    # Extract hyphenated / dotted tech terms (e.g. CI/CD, node.js, react.js)
    tech_terms = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*[./\-#][a-zA-Z0-9.]+\b', text)
    
    # Extract 2-word tech phrases (e.g. "machine learning", "REST API", "unit testing")
    two_word = re.findall(
        r'\b([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+|[a-z]+\s+[a-z]+(?:ing|tion|ment|ure|sis)?)\b',
        text
    )

    seen = set()
    keywords = []

    for w in words + tech_terms:
        wl = w.lower().strip(".-")
        if wl not in STOP_WORDS and len(wl) >= 3 and wl not in seen:
            # Extra filter: skip words that are purely generic verbs/adjectives
            if not re.match(r'^(develop|maintain|design|build|creat|manag|ensur|provid|support|work|help|make|use|enabl|improv|deliver|achiev|collaborat|communicat|analyz)', wl):
                keywords.append(wl)
                seen.add(wl)

    for phrase in two_word:
        pl = phrase.lower().strip()
        words_in = pl.split()
        if all(w not in STOP_WORDS for w in words_in) and pl not in seen and len(pl) > 5:
            keywords.append(pl)
            seen.add(pl)

    return keywords


def calculate_ats_score(resume_data: dict, job_description: str) -> dict:
    """
    Calculate realistic ATS score based only on meaningful tech keywords.
    """
    # Build full resume text
    parts = [resume_data.get("summary", "")]
    skills = resume_data.get("skills", {})
    parts.extend(skills.get("technical", []))
    for grp in skills.get("groups", []):
        parts.extend(grp.get("values", []))
    for exp in resume_data.get("experience", []):
        parts.append(exp.get("title", ""))
        parts.extend(exp.get("bullets", []))
    for proj in resume_data.get("projects", []):
        parts.extend(proj.get("tech", []))
        parts.extend(proj.get("bullets", []))
    parts.extend(resume_data.get("technologies_bar", []))
    resume_full = " ".join(parts).lower()

    # Extract meaningful keywords from JD
    jd_keywords = extract_tech_keywords(job_description)

    if not jd_keywords:
        return {"ats_score": 75, "keywords_matched": [], "keywords_missing": []}

    # Check each keyword against resume
    matched = []
    missing = []
    for kw in jd_keywords[:50]:
        if kw in resume_full:
            matched.append(kw)
        else:
            missing.append(kw)

    ratio = len(matched) / max(len(jd_keywords[:50]), 1)

    # Scoring: keyword match (75%) + section completeness (25%)
    base  = ratio * 75
    bonus = 0
    if resume_data.get("summary"):                    bonus += 5
    if skills.get("groups") or skills.get("technical"): bonus += 5
    if resume_data.get("experience"):                 bonus += 8
    if resume_data.get("projects"):                   bonus += 4
    if resume_data.get("certifications"):             bonus += 3

    score = max(60, min(95, round(base + bonus)))

    def fmt(kw):
        # Nicely format keyword for display
        if "/" in kw or "." in kw:
            return kw.upper() if len(kw) <= 5 else kw.title()
        return kw.title()

    return {
        "ats_score": score,
        "keywords_matched": [fmt(k) for k in matched[:14]],
        "keywords_missing":  [fmt(k) for k in missing[:8]],
    }


def generate_resume(api_key: str, resume_text: str, job_description: str) -> dict:
    """
    Generate a tailored resume that:
    1. Injects ALL missing JD keywords into the resume
    2. Aims for 90%+ ATS alignment
    3. Matches the template format exactly
    """
    try:
        client = Groq(api_key=api_key)

        # Pre-extract JD keywords to tell the AI exactly what to inject
        jd_keywords = extract_tech_keywords(job_description)
        jd_kw_list  = ", ".join(jd_keywords[:40]) if jd_keywords else "see job description"

        prompt = f"""You are a world-class ATS resume optimizer. Your single goal: make the resume match the job description so closely that ATS scanners give it 90%+ score.

══════════════════════════════════════
CANDIDATE'S EXISTING RESUME:
══════════════════════════════════════
{resume_text}

══════════════════════════════════════
TARGET JOB DESCRIPTION:
══════════════════════════════════════
{job_description}

══════════════════════════════════════
KEY JD KEYWORDS TO INJECT (important):
══════════════════════════════════════
{jd_kw_list}

══════════════════════════════════════
YOUR MISSION — MANDATORY RULES:
══════════════════════════════════════

KEYWORD INJECTION (most critical):
- Every keyword listed above MUST appear somewhere in the resume — summary, skills, bullets, or projects.
- If the candidate plausibly has a skill (e.g. JD says "Docker" and they use cloud/APIs), add it.
- Mirror exact spellings from JD (e.g. "Node.js" not "NodeJS", "CI/CD" not "CI CD").
- The final resume must contain 90%+ of the JD keywords naturally embedded.
- Add keywords to: summary (2-3 keywords), skills groups (bulk of them), experience bullets (naturally woven in), project tech stacks.

EXPERIENCE BULLETS — each must:
- Start with a strong action verb (Architected, Engineered, Developed, Optimized, Automated, Delivered, Reduced, Increased, Integrated, Led, Designed, Implemented)
- Include a specific JD keyword naturally
- End with a measurable result: %, time saved, scale (users/requests), or performance improvement
- Be max 18 words (one tight line)
- Write exactly 5 bullets per job

SUMMARY — must:
- Open with exact job title from JD
- Pack in 5-6 JD keywords in 3-4 sentences
- Mention years of experience and top 2 technical strengths

SKILLS — use this exact grouped structure:
  Programming Language → languages from resume + JD
  Backend Frameworks   → frameworks from resume + JD  
  AI / LLM             → AI tools from resume + JD (if relevant)
  Databases            → databases from resume + JD
  Developer Tools      → tools from resume + JD
  (add more groups if JD requires e.g. Cloud, DevOps, Testing)

PROJECTS:
- Keep ALL projects from resume
- Add relevant JD keywords to tech stacks
- 4 tight bullet points per project (verb + action + result)
- Include "role" field

TECHNOLOGIES BAR (bottom of resume):
- 24-28 keywords — include ALL important JD keywords here
- This is the ATS keyword dump — be comprehensive

SINGLE PAGE: keep bullets to 18 words max, 5 bullets per section.

══════════════════════════════════════
Return ONLY valid JSON (no markdown, no code fences, no explanation):
══════════════════════════════════════
{{
  "name": "from resume",
  "email": "from resume",
  "phone": "from resume",
  "location": "from resume",
  "linkedin": "from resume or empty string",
  "github": "from resume or empty string",
  "summary": "3-4 sentences, exact JD job title, 5-6 JD keywords embedded",
  "skills": {{
    "technical": ["all technical skills as flat list"],
    "soft": ["soft skills"],
    "groups": [
      {{"label": "Programming Language", "values": ["..."]}},
      {{"label": "Backend Frameworks",   "values": ["..."]}},
      {{"label": "AI / LLM",             "values": ["..."]}},
      {{"label": "Databases",            "values": ["..."]}},
      {{"label": "Developer Tools",      "values": ["..."]}}
    ]
  }},
  "experience": [{{
    "title": "Job Title",
    "company": "Company Name",
    "duration": "Mon YYYY – Present",
    "location": "City",
    "bullets": [
      "Verb + JD keyword + technical detail + measurable result (max 18 words)",
      "Verb + JD keyword + technical detail + measurable result",
      "Verb + JD keyword + technical detail + measurable result",
      "Verb + JD keyword + technical detail + measurable result",
      "Verb + JD keyword + technical detail + measurable result"
    ]
  }}],
  "education": [{{
    "degree": "full degree",
    "institution": "university",
    "year": "YYYY",
    "gpa": ""
  }}],
  "projects": [{{
    "name": "Project Name",
    "role": "Role title",
    "tech": ["Tech1", "Tech2"],
    "bullets": [
      "Verb + built/designed/integrated + what + impact",
      "Verb + built/designed/integrated + what + impact",
      "Verb + built/designed/integrated + what + impact",
      "Verb + built/designed/integrated + what + impact"
    ]
  }}],
  "certifications": ["Cert name – Issuer"],
  "achievements": [],
  "technologies_bar": ["24-28 keywords including ALL important JD keywords"],
  "keywords_added": ["list every JD keyword you added that wasn't in original resume"]
}}"""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an ATS resume optimizer. Your output is valid JSON only — no markdown, no code fences, no preamble. Inject ALL provided JD keywords into the resume. Be thorough."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=MAX_TOKENS,
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        resume_data = json.loads(raw)

        # Calculate ATS score AFTER keyword injection
        ats = calculate_ats_score(resume_data, job_description)
        resume_data["ats_score"]        = ats["ats_score"]
        resume_data["keywords_matched"] = ats["keywords_matched"]
        resume_data["keywords_missing"] = ats["keywords_missing"]

        return {"success": True, "resume": resume_data}

    except json.JSONDecodeError as e:
        return {"error": f"AI response parse error. Please try again. ({str(e)})"}
    except Exception as e:
        err = str(e)
        if "authentication" in err.lower() or "401" in err:
            return {"error": "Invalid Groq API key in config.py. Please update it."}
        elif "rate_limit" in err.lower() or "429" in err:
            return {"error": "Rate limit hit. Please wait 30 seconds and retry."}
        return {"error": f"Generation failed: {err}"}
