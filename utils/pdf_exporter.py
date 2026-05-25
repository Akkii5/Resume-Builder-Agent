import tempfile


def export_to_pdf(resume_data: dict) -> str | None:
    """
    Single-page professional resume matching the sample template:
    - No colored backgrounds
    - Name + title + contact at top (plain)
    - Skills as a 2-column label|value table
    - Experience with role|company|date header
    - Projects with Role + Tech Stack line
    - Tight spacing to fit one page
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            HRFlowable, Table, TableStyle, KeepTogether
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp_path = tmp.name
        tmp.close()

        # ── Colours (no background colours — pure B&W professional) ──
        C_BLACK     = colors.HexColor("#111111")
        C_DARK      = colors.HexColor("#1e293b")
        C_GRAY      = colors.HexColor("#444444")
        C_LIGHT     = colors.HexColor("#777777")
        C_DIVIDER   = colors.HexColor("#333333")
        C_WHITE     = colors.white

        doc = SimpleDocTemplate(
            tmp_path,
            pagesize=A4,
            rightMargin=14*mm,
            leftMargin=14*mm,
            topMargin=11*mm,
            bottomMargin=10*mm,
        )
        PAGE_W, PAGE_H = A4
        usable_w = PAGE_W - 28*mm

        # ── Styles — tight leading to fit one page ──
        name_style = ParagraphStyle(
            "Name", fontSize=18, fontName="Helvetica-Bold",
            textColor=C_BLACK, leading=22, spaceAfter=1, alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "Sub", fontSize=10, fontName="Helvetica",
            textColor=C_DARK, leading=13, spaceAfter=2, alignment=TA_CENTER,
        )
        contact_style = ParagraphStyle(
            "Contact", fontSize=8.5, fontName="Helvetica",
            textColor=C_GRAY, leading=11, spaceAfter=0, alignment=TA_CENTER,
        )
        section_style = ParagraphStyle(
            "Sec", fontSize=9, fontName="Helvetica-Bold",
            textColor=C_BLACK, leading=11,
            spaceBefore=5, spaceAfter=2,
        )
        body_style = ParagraphStyle(
            "Body", fontSize=8.5, fontName="Helvetica",
            textColor=C_DARK, leading=12, spaceAfter=1,
        )
        bullet_style = ParagraphStyle(
            "Bul", fontSize=8.5, fontName="Helvetica",
            textColor=C_DARK, leading=12,
            leftIndent=10, spaceAfter=1.5,
        )
        exp_title_style = ParagraphStyle(
            "ExpT", fontSize=9, fontName="Helvetica-Bold",
            textColor=C_BLACK, leading=12, spaceAfter=1,
        )
        exp_meta_style = ParagraphStyle(
            "ExpM", fontSize=8.5, fontName="Helvetica",
            textColor=C_GRAY, leading=11, spaceAfter=2,
        )
        proj_title_style = ParagraphStyle(
            "ProjT", fontSize=9, fontName="Helvetica-Bold",
            textColor=C_BLACK, leading=12, spaceAfter=1,
        )
        proj_meta_style = ParagraphStyle(
            "ProjM", fontSize=8.5, fontName="Helvetica-Oblique",
            textColor=C_GRAY, leading=11, spaceAfter=2,
        )
        skill_label_style = ParagraphStyle(
            "SkL", fontSize=8.5, fontName="Helvetica-Bold",
            textColor=C_BLACK, leading=12,
        )
        skill_val_style = ParagraphStyle(
            "SkV", fontSize=8.5, fontName="Helvetica",
            textColor=C_DARK, leading=12,
        )
        tech_bar_style = ParagraphStyle(
            "Tech", fontSize=8, fontName="Helvetica",
            textColor=C_DARK, leading=11, spaceAfter=0, alignment=TA_CENTER,
        )
        edu_style = ParagraphStyle(
            "Edu", fontSize=8.5, fontName="Helvetica",
            textColor=C_DARK, leading=12, spaceAfter=1,
        )

        def thick_hr(after=4):
            return HRFlowable(width="100%", thickness=1.2, color=C_DIVIDER,
                               spaceBefore=2, spaceAfter=after)

        def thin_hr(after=3):
            return HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#bbbbbb"),
                               spaceBefore=1, spaceAfter=after)

        def section_head(text):
            return [Paragraph(text.upper(), section_style), thick_hr()]

        story = []

        # ══════════════════════════════════════════
        #  HEADER — name / title / contact (centred, no bg)
        # ══════════════════════════════════════════
        name = resume_data.get("name", "")
        story.append(Paragraph(name, name_style))

        # Subtitle: current job title
        exp_list = resume_data.get("experience", [])
        subtitle = ""
        if exp_list:
            subtitle = exp_list[0].get("title", "")
        # Add top skills to subtitle if available
        tech_skills = resume_data.get("skills", {}).get("technical", [])
        if subtitle and tech_skills:
            top3 = " | ".join(tech_skills[:3])
            subtitle = f"{subtitle} | {top3}"
        if subtitle:
            story.append(Paragraph(subtitle, subtitle_style))

        # Contact line
        parts = []
        if resume_data.get("email"):    parts.append(resume_data["email"])
        if resume_data.get("phone"):    parts.append(resume_data["phone"])
        if resume_data.get("linkedin"): parts.append(resume_data["linkedin"])
        if resume_data.get("location"): parts.append(resume_data["location"])
        if parts:
            story.append(Paragraph("  |  ".join(parts), contact_style))

        story.append(thick_hr(after=5))

        # ══════════════════════════════════════════
        #  PROFESSIONAL SUMMARY
        # ══════════════════════════════════════════
        if resume_data.get("summary"):
            story.extend(section_head("Professional Summary"))
            story.append(Paragraph(resume_data["summary"], body_style))

        # ══════════════════════════════════════════
        #  TECHNICAL SKILLS — 2-column table (label | values)
        # ══════════════════════════════════════════
        skills_obj = resume_data.get("skills", {})
        skill_groups = skills_obj.get("groups", [])

        # Fallback: if AI returned flat list, group them
        if not skill_groups:
            tech = skills_obj.get("technical", [])
            soft = skills_obj.get("soft", [])
            # Auto-group by category
            skill_groups = _auto_group_skills(tech, soft, resume_data)

        if skill_groups:
            story.extend(section_head("Technical Skills"))
            tdata = []
            for grp in skill_groups:
                label = grp.get("label", "")
                vals  = grp.get("values", [])
                tdata.append([
                    Paragraph(label, skill_label_style),
                    Paragraph(", ".join(vals), skill_val_style),
                ])
            skill_table = Table(tdata, colWidths=[usable_w*0.25, usable_w*0.75])
            skill_table.setStyle(TableStyle([
                ("VALIGN",       (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING",   (0,0), (-1,-1), 1),
                ("BOTTOMPADDING",(0,0), (-1,-1), 1),
            ]))
            story.append(skill_table)

        # ══════════════════════════════════════════
        #  PROFESSIONAL EXPERIENCE
        # ══════════════════════════════════════════
        if exp_list:
            story.extend(section_head("Professional Experience"))
            for exp in exp_list:
                block = []
                # "Title | Company   Date | Location" — same line using table
                title_co = f"<b>{exp.get('title','')}</b>  |  {exp.get('company','')}"
                dur_loc  = exp.get("duration","")
                if exp.get("location"):
                    dur_loc += f"  |  {exp['location']}"

                row = Table([[
                    Paragraph(title_co, exp_title_style),
                    Paragraph(dur_loc,  ParagraphStyle("DR", fontSize=8.5,
                        fontName="Helvetica", textColor=C_GRAY,
                        leading=12, alignment=TA_RIGHT)),
                ]], colWidths=[usable_w*0.65, usable_w*0.35])
                row.setStyle(TableStyle([
                    ("VALIGN",       (0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",  (0,0),(-1,-1),0),
                    ("RIGHTPADDING", (0,0),(-1,-1),0),
                    ("TOPPADDING",   (0,0),(-1,-1),0),
                    ("BOTTOMPADDING",(0,0),(-1,-1),1),
                ]))
                block.append(row)

                for b in exp.get("bullets", []):
                    block.append(Paragraph(f"\u2022  {b}", bullet_style))
                block.append(Spacer(1, 3))
                story.append(KeepTogether(block))

        # ══════════════════════════════════════════
        #  KEY PROJECTS
        # ══════════════════════════════════════════
        projects = resume_data.get("projects", [])
        if projects:
            story.extend(section_head("Key Projects"))
            for proj in projects:
                block = []
                block.append(Paragraph(proj.get("name",""), proj_title_style))

                # Role | Tech Stack line (like the template)
                role_tech_parts = []
                if proj.get("role"):
                    role_tech_parts.append(f"Role: {proj['role']}")
                tech_list = proj.get("tech", [])
                if tech_list:
                    role_tech_parts.append(f"Tech Stack: {', '.join(tech_list)}")
                if role_tech_parts:
                    block.append(Paragraph("  |  ".join(role_tech_parts), proj_meta_style))

                if proj.get("description"):
                    for line in proj["description"].split("\n"):
                        if line.strip():
                            block.append(Paragraph(f"\u2022  {line.strip()}", bullet_style))

                for b in proj.get("bullets", []):
                    block.append(Paragraph(f"\u2022  {b}", bullet_style))

                block.append(Spacer(1, 3))
                story.append(KeepTogether(block))

        # ══════════════════════════════════════════
        #  EDUCATION
        # ══════════════════════════════════════════
        education = resume_data.get("education", [])
        if education:
            story.extend(section_head("Education"))
            for edu in education:
                deg  = edu.get("degree", "")
                inst = edu.get("institution", "")
                yr   = edu.get("year", "")
                gpa  = edu.get("gpa", "")

                right = yr
                if gpa: right = f"Graduated: {yr}  |  GPA: {gpa}" if yr else f"GPA: {gpa}"
                elif yr: right = f"Graduated: {yr}"

                row = Table([[
                    Paragraph(f"<b>{deg}</b>", edu_style),
                    Paragraph(right, ParagraphStyle("YR", fontSize=8.5,
                        fontName="Helvetica", textColor=C_GRAY,
                        leading=12, alignment=TA_RIGHT)),
                ]], colWidths=[usable_w*0.70, usable_w*0.30])
                row.setStyle(TableStyle([
                    ("VALIGN",       (0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",  (0,0),(-1,-1),0),
                    ("RIGHTPADDING", (0,0),(-1,-1),0),
                    ("TOPPADDING",   (0,0),(-1,-1),0),
                    ("BOTTOMPADDING",(0,0),(-1,-1),1),
                ]))
                story.append(row)
                story.append(Paragraph(inst, edu_style))
                story.append(Spacer(1, 2))

        # ══════════════════════════════════════════
        #  CERTIFICATIONS
        # ══════════════════════════════════════════
        certs = resume_data.get("certifications", [])
        if certs:
            story.extend(section_head("Certifications"))
            for c in certs:
                story.append(Paragraph(f"\u2022  {c}", bullet_style))

        # ══════════════════════════════════════════
        #  TECHNOLOGIES (keyword bar at bottom)
        # ══════════════════════════════════════════
        all_tech = resume_data.get("technologies_bar", [])
        if not all_tech:
            # Build from skills + project techs
            seen = set()
            for t in tech_skills:
                if t.lower() not in seen:
                    all_tech.append(t); seen.add(t.lower())
            for proj in projects:
                for t in proj.get("tech", []):
                    if t.lower() not in seen:
                        all_tech.append(t); seen.add(t.lower())

        if all_tech:
            story.append(thin_hr(after=3))
            story.append(Paragraph(
                "  |  ".join(all_tech[:28]),
                tech_bar_style
            ))

        doc.build(story)
        return tmp_path

    except ImportError:
        print("PDF error: reportlab not installed.")
        return None
    except Exception as e:
        print(f"PDF export error: {e}")
        return None


def _auto_group_skills(tech: list, soft: list, resume_data: dict) -> list:
    """Auto-group flat skill lists into labelled categories matching the template."""
    groups = []

    # Categorise by keyword matching
    lang_kw    = {"python","javascript","typescript","java","go","rust","c++","c#","ruby","php","swift","kotlin","r","scala","bash","shell"}
    backend_kw = {"flask","django","fastapi","express","spring","rails","node","nodejs","rest","graphql","grpc","microservices","api"}
    ai_kw      = {"openai","langchain","llm","gpt","huggingface","transformers","rag","prompt","embedding","vector","ai","ml","nlp","generative","chatbot","voice bot","agent","conversational"}
    voice_kw   = {"bland","typebot","anythingllm","infobip","twilio","voicebot","voice bot","chatbot"}
    db_kw      = {"postgresql","mysql","mongodb","redis","sqlite","oracle","dynamodb","cassandra","sql","database","orm","sqlalchemy"}
    data_kw    = {"pandas","numpy","seaborn","matplotlib","scipy","sklearn","scikit","tensorflow","pytorch","spark"}
    devtools_kw= {"git","docker","kubernetes","postman","vs code","vscode","linux","aws","gcp","azure","ci","cd","jenkins","github","bitbucket","jira"}
    web_kw     = {"html","css","react","vue","angular","nextjs","tailwind","bootstrap","javascript","typescript"}

    cats = {
        "Programming Language": [],
        "Backend Frameworks":   [],
        "AI / LLM":             [],
        "Voice & Chatbot":      [],
        "Databases":            [],
        "Data & Analytics":     [],
        "Developer Tools":      [],
        "Web (Supporting)":     [],
        "Other":                [],
    }

    used = set()
    for sk in tech:
        skl = sk.lower()
        placed = False
        for kw in lang_kw:
            if kw in skl and sk not in used:
                cats["Programming Language"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in backend_kw:
            if kw in skl and sk not in used:
                cats["Backend Frameworks"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in voice_kw:
            if kw in skl and sk not in used:
                cats["Voice & Chatbot"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in ai_kw:
            if kw in skl and sk not in used:
                cats["AI / LLM"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in db_kw:
            if kw in skl and sk not in used:
                cats["Databases"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in data_kw:
            if kw in skl and sk not in used:
                cats["Data & Analytics"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in devtools_kw:
            if kw in skl and sk not in used:
                cats["Developer Tools"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        for kw in web_kw:
            if kw in skl and sk not in used:
                cats["Web (Supporting)"].append(sk); used.add(sk); placed=True; break
        if placed: continue
        if sk not in used:
            cats["Other"].append(sk); used.add(sk)

    for label, vals in cats.items():
        if vals:
            groups.append({"label": label, "values": vals})

    return groups
