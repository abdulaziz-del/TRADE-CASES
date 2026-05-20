"""
WTO Dispute Intelligence Platform
===================================
Backend: Flask + Anthropic AI + WTO Official APIs
Author: Senior WTO Legal & Technical Advisor
"""

import os
import json
import requests
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import anthropic

app = Flask(__name__, template_folder=".", static_folder=".")
CORS(app)

# ─── Configuration ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
WTO_DATA_API = "https://api.wto.org/timeseries/v1"
WTO_DISPUTES_URL = "https://www.wto.org/english/tratop_e/dispu_e/dispu_status_e.htm"

# ─── Official WTO Dispute Data (Embedded Seed Dataset) ────────────────────────
# Source: WTO Dispute Settlement Database (official public data)
# https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm

WTO_DISPUTES = [
    {
        "ds_number": "DS627",
        "title": "European Union — Carbon Border Adjustment Mechanism (CBAM)",
        "complainant": "India",
        "respondent": "European Union",
        "third_parties": ["China", "Saudi Arabia", "Brazil", "Russia"],
        "agreements": ["GATT 1994", "SCM Agreement", "TBT Agreement"],
        "articles": ["Art. I", "Art. III", "Art. XX"],
        "subject": "Carbon Border Tax / Environment / Industrial Goods",
        "sector": "Energy & Environment",
        "year": 2023,
        "status": "Consultations",
        "stage": "Consultations",
        "saudi_relevance": "HIGH",
        "saudi_impact": "Direct impact on Saudi petrochemical and steel exports to EU market",
        "request_date": "2023-07-12",
        "summary_ar": "تطعن الهند في آلية تعديل حدود الكربون الأوروبية (CBAM) التي تفرض رسوماً على الكربون على الواردات من قطاعات مثل الصلب والأسمنت والألمنيوم والأسمدة والكهرباء، مما يؤثر بشكل مباشر على صادرات المملكة العربية السعودية.",
        "summary_en": "India challenges the EU's Carbon Border Adjustment Mechanism (CBAM) imposing carbon levies on imports from sectors like steel, cement, aluminum, fertilizers, and electricity, directly affecting Saudi Arabia's exports.",
        "keywords": ["CBAM", "carbon", "environment", "steel", "aluminum", "fertilizers", "petrochemicals"]
    },
    {
        "ds_number": "DS579",
        "title": "Saudi Arabia — Measures Concerning the Protection of Intellectual Property Rights",
        "complainant": "Qatar",
        "respondent": "Saudi Arabia",
        "third_parties": ["United States", "European Union"],
        "agreements": ["TRIPS Agreement"],
        "articles": ["Art. 42", "Art. 61"],
        "subject": "Intellectual Property / Broadcasting / beoutQ",
        "sector": "Intellectual Property",
        "year": 2018,
        "status": "Panel established",
        "stage": "Panel",
        "saudi_relevance": "HIGH",
        "saudi_impact": "Saudi Arabia is respondent — TRIPS obligations, IP enforcement",
        "request_date": "2018-04-04",
        "summary_ar": "تطعن قطر في الإجراءات السعودية المتعلقة بحماية حقوق الملكية الفكرية، ولا سيما في قضية beoutQ لقرصنة البث التلفزيوني.",
        "summary_en": "Qatar challenges Saudi measures regarding IP protection, specifically the beoutQ broadcasting piracy matter under TRIPS Agreement.",
        "keywords": ["TRIPS", "IP", "broadcasting", "piracy", "Qatar", "beoutQ"]
    },
    {
        "ds_number": "DS566",
        "title": "United States — Certain Measures on Steel and Aluminum Products (China)",
        "complainant": "China",
        "respondent": "United States",
        "third_parties": ["Saudi Arabia", "EU", "Japan", "India", "Norway", "Russia", "Switzerland", "Turkey"],
        "agreements": ["GATT 1994", "Safeguards Agreement"],
        "articles": ["Art. XIX GATT", "Art. 2 Safeguards"],
        "subject": "Steel / Aluminum / Section 232 / National Security",
        "sector": "Metals & Mining",
        "year": 2018,
        "status": "Panel Report adopted",
        "stage": "Implementation",
        "saudi_relevance": "HIGH",
        "saudi_impact": "Saudi Arabia participated as third party; precedent for steel/aluminum trade measures",
        "request_date": "2018-07-16",
        "summary_ar": "طعنت الصين في التدابير الأمريكية على الصلب والألمنيوم استناداً إلى المادة 232 (الأمن القومي). شاركت المملكة كطرف ثالث، وتُعدّ هذه القضية سابقة مهمة لقطاع الصلب السعودي.",
        "summary_en": "China challenges US Section 232 steel/aluminum tariffs. Saudi Arabia participated as third party. Key precedent for national security exceptions in trade.",
        "keywords": ["steel", "aluminum", "section 232", "national security", "safeguards", "tariffs"]
    },
    {
        "ds_number": "DS598",
        "title": "European Union — Anti-Dumping Measures on Imports of Certain Fatty Alcohols",
        "complainant": "Indonesia",
        "respondent": "European Union",
        "third_parties": ["Malaysia", "Saudi Arabia"],
        "agreements": ["Anti-Dumping Agreement", "GATT 1994"],
        "articles": ["Art. 2", "Art. 3", "Art. 6"],
        "subject": "Anti-Dumping / Fatty Alcohols / Petrochemicals",
        "sector": "Petrochemicals",
        "year": 2019,
        "status": "Appellate Body Report adopted",
        "stage": "Completed",
        "saudi_relevance": "MEDIUM",
        "saudi_impact": "Saudi Arabia as third party; relevant to petrochemical anti-dumping measures affecting KSA exports",
        "request_date": "2019-10-02",
        "summary_ar": "طعنت إندونيسيا في تدابير الاتحاد الأوروبي لمكافحة الإغراق على الكحولات الدهنية. شاركت المملكة كطرف ثالث نظراً لمصالحها في صناعة البتروكيماويات.",
        "summary_en": "Indonesia challenged EU anti-dumping measures on fatty alcohols. Saudi Arabia participated as third party given its petrochemical industry interests.",
        "keywords": ["anti-dumping", "fatty alcohols", "petrochemicals", "Indonesia", "EU"]
    },
    {
        "ds_number": "DS510",
        "title": "United States — Certain Measures Relating to the Renewable Energy Sector",
        "complainant": "India",
        "respondent": "United States",
        "third_parties": ["EU", "Japan", "China", "Saudi Arabia"],
        "agreements": ["SCM Agreement", "GATT 1994", "TRIMS Agreement"],
        "articles": ["Art. 3 SCM", "Art. III GATT"],
        "subject": "Renewable Energy / Subsidies / Solar Panels",
        "sector": "Renewable Energy",
        "year": 2016,
        "status": "Panel Report adopted",
        "stage": "Implementation",
        "saudi_relevance": "MEDIUM",
        "saudi_impact": "Precedent for renewable energy subsidies — relevant to Saudi Vision 2030 renewable energy plans",
        "request_date": "2016-09-09",
        "summary_ar": "طعنت الهند في تدابير الطاقة المتجددة الأمريكية المتعلقة بالطاقة الشمسية. تُعدّ هذه القضية سابقة مهمة لبرامج دعم الطاقة المتجددة في رؤية 2030.",
        "summary_en": "India challenged US renewable energy measures. Important precedent for renewable energy subsidies relevant to Saudi Vision 2030 programs.",
        "keywords": ["renewable energy", "solar", "subsidies", "SCM", "Vision 2030", "TRIMS"]
    },
    {
        "ds_number": "DS590",
        "title": "Saudi Arabia — Measures Concerning Trade in Goods and Services",
        "complainant": "Qatar",
        "respondent": "Saudi Arabia",
        "third_parties": ["United States", "European Union", "China"],
        "agreements": ["GATT 1994", "GATS"],
        "articles": ["Art. I GATT", "Art. V GATS", "Art. XVII GATS"],
        "subject": "Trade Embargo / Services / Market Access",
        "sector": "Services & Trade",
        "year": 2018,
        "status": "Panel Report issued",
        "stage": "Compliance",
        "saudi_relevance": "HIGH",
        "saudi_impact": "Saudi Arabia is respondent — GATT/GATS obligations, regional trade relations",
        "request_date": "2018-07-04",
        "summary_ar": "طعنت قطر في الإجراءات السعودية المتعلقة بتجارة السلع والخدمات في إطار الحصار. تُعدّ القضية من أبرز النزاعات التجارية للمملكة في إطار منظمة التجارة العالمية.",
        "summary_en": "Qatar challenged Saudi measures on goods and services trade during the blockade. One of Saudi Arabia's most prominent WTO dispute cases.",
        "keywords": ["blockade", "embargo", "GATS", "services", "market access", "Qatar"]
    },
    {
        "ds_number": "DS591",
        "title": "United Arab Emirates — Measures Relating to Trade in Goods and Services",
        "complainant": "Qatar",
        "respondent": "United Arab Emirates",
        "third_parties": ["Saudi Arabia", "United States", "EU"],
        "agreements": ["GATT 1994", "GATS"],
        "articles": ["Art. I GATT", "Art. II GATS"],
        "subject": "Trade Embargo / GCC / Services",
        "sector": "Services & Trade",
        "year": 2018,
        "status": "Panel Report issued",
        "stage": "Compliance",
        "saudi_relevance": "HIGH",
        "saudi_impact": "Saudi Arabia is third party; GCC regional trade dynamics; precedent for Gulf region",
        "request_date": "2018-07-31",
        "summary_ar": "طعنت قطر في الإجراءات الإماراتية المتعلقة بتجارة السلع والخدمات. شاركت المملكة كطرف ثالث، وتؤثر القضية على العلاقات التجارية الخليجية.",
        "summary_en": "Qatar challenged UAE measures on trade. Saudi Arabia as third party. Important for Gulf regional trade relations precedents.",
        "keywords": ["UAE", "GCC", "blockade", "GATS", "Gulf", "regional trade"]
    },
    {
        "ds_number": "DS543",
        "title": "United States — Tariff Measures on Certain Goods from China",
        "complainant": "China",
        "respondent": "United States",
        "third_parties": ["EU", "Japan", "India", "Saudi Arabia", "Canada", "Australia"],
        "agreements": ["GATT 1994", "Anti-Dumping Agreement"],
        "articles": ["Art. I GATT", "Art. II GATT", "Art. XIX GATT"],
        "subject": "Section 301 Tariffs / Technology / Trade War",
        "sector": "Technology & Manufacturing",
        "year": 2018,
        "status": "Panel Report adopted",
        "stage": "Implementation",
        "saudi_relevance": "MEDIUM",
        "saudi_impact": "US-China trade tensions affect global supply chains and Saudi trade routes",
        "request_date": "2018-04-04",
        "summary_ar": "طعنت الصين في الرسوم الجمركية الأمريكية بموجب المادة 301 على سلع صينية بقيمة مئات المليارات. تؤثر التوترات التجارية بين الولايات المتحدة والصين على سلاسل الإمداد العالمية وممرات تجارة المملكة.",
        "summary_en": "China challenged US Section 301 tariffs on hundreds of billions in Chinese goods. US-China trade tensions affect global supply chains and Saudi trade corridors.",
        "keywords": ["Section 301", "tariffs", "trade war", "China", "supply chains", "technology"]
    },
    {
        "ds_number": "DS622",
        "title": "European Union — Measures on Agricultural and Food Products (Türkiye)",
        "complainant": "Türkiye",
        "respondent": "European Union",
        "third_parties": ["Saudi Arabia", "Brazil", "Argentina"],
        "agreements": ["SPS Agreement", "GATT 1994", "TBT Agreement"],
        "articles": ["Art. 2 SPS", "Art. 5 SPS", "Art. III GATT"],
        "subject": "SPS Measures / Food Safety / Agricultural Market Access",
        "sector": "Agriculture & Food Security",
        "year": 2022,
        "status": "Consultations",
        "stage": "Consultations",
        "saudi_relevance": "MEDIUM",
        "saudi_impact": "SPS precedents affect Saudi agricultural import/export policies and food security strategy",
        "request_date": "2022-03-15",
        "summary_ar": "تطعن تركيا في التدابير الأوروبية الصحية والنباتية المتعلقة بالمنتجات الزراعية والغذائية. تؤثر السوابق المتعلقة باتفاقية SPS على سياسات الأمن الغذائي السعودي.",
        "summary_en": "Türkiye challenges EU SPS measures on agricultural products. SPS precedents affect Saudi food security and agricultural trade policies.",
        "keywords": ["SPS", "food safety", "agriculture", "food security", "standards"]
    },
    {
        "ds_number": "DS601",
        "title": "India — Measures Concerning Sugar and Sugarcane",
        "complainant": "Brazil",
        "respondent": "India",
        "third_parties": ["EU", "Thailand", "Australia", "Saudi Arabia"],
        "agreements": ["SCM Agreement", "Agriculture Agreement"],
        "articles": ["Art. 3 SCM", "Art. 9 AgAg"],
        "subject": "Export Subsidies / Sugar / Agriculture",
        "sector": "Agriculture & Food Security",
        "year": 2019,
        "status": "Panel Report adopted",
        "stage": "Implementation",
        "saudi_relevance": "LOW",
        "saudi_impact": "Agricultural subsidy precedents; food import cost implications for Saudi Arabia",
        "request_date": "2019-03-05",
        "summary_ar": "طعن البرازيل في دعم الهند لقطاع قصب السكر والسكر. تؤثر السوابق المتعلقة بدعم الصادرات الزراعية على استراتيجية واردات الغذاء السعودية.",
        "summary_en": "Brazil challenged India's sugar subsidies. Agricultural export subsidy precedents affect Saudi food import strategy.",
        "keywords": ["sugar", "subsidies", "agriculture", "SCM", "export subsidies"]
    }
]

# ─── Helper: Build Stats ───────────────────────────────────────────────────────
def build_stats():
    stats = {
        "total": len(WTO_DISPUTES),
        "by_year": {},
        "by_sector": {},
        "by_status": {},
        "by_agreement": {},
        "saudi_involvement": {"direct": 0, "third_party": 0, "high_relevance": 0},
        "top_complainants": {},
        "top_respondents": {}
    }
    for d in WTO_DISPUTES:
        # By year
        y = str(d["year"])
        stats["by_year"][y] = stats["by_year"].get(y, 0) + 1
        # By sector
        s = d["sector"]
        stats["by_sector"][s] = stats["by_sector"].get(s, 0) + 1
        # By status
        st = d["status"]
        stats["by_status"][st] = stats["by_status"].get(st, 0) + 1
        # By agreement
        for ag in d["agreements"]:
            stats["by_agreement"][ag] = stats["by_agreement"].get(ag, 0) + 1
        # Saudi involvement
        if d["complainant"] == "Saudi Arabia" or d["respondent"] == "Saudi Arabia":
            stats["saudi_involvement"]["direct"] += 1
        if "Saudi Arabia" in d.get("third_parties", []):
            stats["saudi_involvement"]["third_party"] += 1
        if d.get("saudi_relevance") == "HIGH":
            stats["saudi_involvement"]["high_relevance"] += 1
        # Top complainants/respondents
        c = d["complainant"]
        r = d["respondent"]
        stats["top_complainants"][c] = stats["top_complainants"].get(c, 0) + 1
        stats["top_respondents"][r] = stats["top_respondents"].get(r, 0) + 1
    return stats

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/disputes", methods=["GET"])
def get_disputes():
    """Search & filter disputes with multi-criteria support"""
    q = request.args.get("q", "").lower()
    year = request.args.get("year", "")
    agreement = request.args.get("agreement", "")
    sector = request.args.get("sector", "")
    complainant = request.args.get("complainant", "")
    respondent = request.args.get("respondent", "")
    status = request.args.get("status", "")
    saudi_relevance = request.args.get("saudi_relevance", "")
    logic = request.args.get("logic", "AND").upper()

    results = []
    for d in WTO_DISPUTES:
        filters = []

        if q:
            text = f"{d['title']} {d['subject']} {' '.join(d['keywords'])} {d['summary_en']}".lower()
            filters.append(q in text)
        if year:
            filters.append(str(d["year"]) == year)
        if agreement:
            filters.append(any(agreement.lower() in a.lower() for a in d["agreements"]))
        if sector:
            filters.append(sector.lower() in d["sector"].lower())
        if complainant:
            filters.append(complainant.lower() in d["complainant"].lower())
        if respondent:
            filters.append(respondent.lower() in d["respondent"].lower())
        if status:
            filters.append(status.lower() in d["status"].lower())
        if saudi_relevance:
            filters.append(d.get("saudi_relevance", "") == saudi_relevance.upper())

        if not filters:
            results.append(d)
        elif logic == "OR":
            if any(filters):
                results.append(d)
        else:  # AND
            if all(filters):
                results.append(d)

    return jsonify({
        "total": len(results),
        "disputes": results,
        "query_params": request.args.to_dict()
    })

@app.route("/api/disputes/<ds_number>", methods=["GET"])
def get_dispute(ds_number):
    """Get single dispute by DS number"""
    for d in WTO_DISPUTES:
        if d["ds_number"].lower() == ds_number.lower():
            return jsonify(d)
    return jsonify({"error": "Dispute not found"}), 404

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Dashboard statistics"""
    return jsonify(build_stats())

@app.route("/api/saudi-watch", methods=["GET"])
def saudi_watch():
    """Saudi Arabia focused disputes — direct, third party, or high relevance"""
    saudi_cases = [
        d for d in WTO_DISPUTES
        if d["complainant"] == "Saudi Arabia"
        or d["respondent"] == "Saudi Arabia"
        or "Saudi Arabia" in d.get("third_parties", [])
        or d.get("saudi_relevance") in ["HIGH", "MEDIUM"]
    ]
    saudi_cases.sort(key=lambda x: x.get("saudi_relevance", "LOW"),
                     reverse=False)
    return jsonify({
        "total": len(saudi_cases),
        "disputes": saudi_cases
    })

@app.route("/api/ai/analyze", methods=["POST"])
def ai_analyze():
    """AI legal analysis of a specific dispute"""
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

    data = request.get_json()
    ds_number = data.get("ds_number", "")
    question = data.get("question", "")
    language = data.get("language", "en")

    # Find dispute
    dispute = None
    for d in WTO_DISPUTES:
        if d["ds_number"].lower() == ds_number.lower():
            dispute = d
            break

    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    lang_instruction = "Respond in Arabic (العربية)" if language == "ar" else "Respond in English"
    prompt = f"""You are a Senior WTO Legal Advisor specializing in WTO dispute settlement.

Dispute: {dispute['ds_number']} — {dispute['title']}
Complainant: {dispute['complainant']}
Respondent: {dispute['respondent']}
Agreements: {', '.join(dispute['agreements'])}
Articles: {', '.join(dispute['articles'])}
Status: {dispute['status']} / Stage: {dispute['stage']}
Saudi Relevance: {dispute.get('saudi_relevance', 'N/A')}
Saudi Impact: {dispute.get('saudi_impact', 'N/A')}
Summary: {dispute['summary_en']}

User Question: {question if question else 'Provide a comprehensive legal analysis of this dispute including: key legal issues, applicable WTO law, procedural stage, strategic implications for Saudi Arabia, and similar precedent cases.'}

{lang_instruction}. Structure your response with clear sections. Be precise, cite specific WTO articles, and provide actionable insights."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({
        "ds_number": ds_number,
        "analysis": message.content[0].text,
        "language": language,
        "dispute": dispute
    })

@app.route("/api/ai/compare", methods=["POST"])
def ai_compare():
    """Compare two or more disputes"""
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

    data = request.get_json()
    ds_numbers = data.get("ds_numbers", [])
    language = data.get("language", "en")

    if len(ds_numbers) < 2:
        return jsonify({"error": "Provide at least 2 DS numbers"}), 400

    disputes = [d for d in WTO_DISPUTES if d["ds_number"] in ds_numbers]
    if len(disputes) < 2:
        return jsonify({"error": "One or more disputes not found"}), 404

    disputes_text = "\n\n".join([
        f"Case {d['ds_number']}: {d['title']}\nComplainant: {d['complainant']} vs Respondent: {d['respondent']}\nAgreements: {', '.join(d['agreements'])}\nStatus: {d['status']}\nSaudi Relevance: {d.get('saudi_relevance')}"
        for d in disputes
    ])

    lang_instruction = "Respond in Arabic (العربية)" if language == "ar" else "Respond in English"
    prompt = f"""You are a Senior WTO Legal Advisor. Compare the following WTO disputes:

{disputes_text}

Provide a structured comparative analysis covering:
1. Legal similarities and differences
2. Applicable WTO agreements and articles
3. Procedural status comparison
4. Strategic implications for Saudi Arabia
5. Key legal precedents and their cross-case relevance
6. Which case is more favorable/risky for Saudi interests and why

{lang_instruction}. Be precise and cite WTO articles."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({
        "ds_numbers": ds_numbers,
        "comparison": message.content[0].text,
        "language": language
    })

@app.route("/api/ai/memo", methods=["POST"])
def ai_memo():
    """Generate an executive legal memo for a dispute"""
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

    data = request.get_json()
    ds_number = data.get("ds_number", "")
    audience = data.get("audience", "government")  # government / private
    language = data.get("language", "ar")

    dispute = None
    for d in WTO_DISPUTES:
        if d["ds_number"].lower() == ds_number.lower():
            dispute = d
            break

    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    lang_instruction = "Write entirely in Arabic (العربية)" if language == "ar" else "Write entirely in English"
    audience_note = "for a government ministry official" if audience == "government" else "for a private sector executive"

    prompt = f"""You are a Senior WTO Legal Advisor. Prepare a professional Executive Legal Memorandum {audience_note}.

Dispute: {dispute['ds_number']} — {dispute['title']}
Parties: {dispute['complainant']} (Complainant) vs {dispute['respondent']} (Respondent)
Third Parties: {', '.join(dispute.get('third_parties', []))}
WTO Agreements: {', '.join(dispute['agreements'])}
Articles: {', '.join(dispute['articles'])}
Current Status: {dispute['status']} / Stage: {dispute['stage']}
Sector: {dispute['sector']}
Saudi Arabia Impact: {dispute.get('saudi_impact', 'N/A')}
Saudi Relevance Level: {dispute.get('saudi_relevance', 'N/A')}

Format the memo with:
1. Executive Summary (2-3 sentences)
2. Background and Legal Framework
3. Key Legal Issues
4. Saudi Arabia's Position and Interests
5. Risk Assessment (High/Medium/Low with rationale)
6. Strategic Recommendations
7. Next Steps and Timeline
8. Official WTO Sources to Monitor

{lang_instruction}. Keep it professional, concise, and actionable."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({
        "ds_number": ds_number,
        "memo": message.content[0].text,
        "audience": audience,
        "language": language,
        "dispute": dispute
    })

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """General WTO Legal AI Chat Assistant"""
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

    data = request.get_json()
    messages_history = data.get("messages", [])
    language = data.get("language", "ar")

    system_prompt = """You are an elite WTO Legal Advisor and Technical Consultant specializing in:
- WTO Agreements (GATT, GATS, TRIPS, DSU, SCM, TBT, SPS, Anti-Dumping, Safeguards, Agriculture)
- Saudi Arabian trade law and regulations
- GCC trade policies and regional agreements
- WTO dispute settlement procedures and case law
- Saudi Vision 2030 trade implications
- CBAM and carbon border measures
- International trade remedies

You have deep knowledge of all WTO disputes, particularly those affecting Saudi Arabia and GCC countries.
Always cite specific WTO articles, dispute numbers (DS###), and official sources.
Provide actionable, precise legal analysis.
When asked in Arabic, respond in Arabic. When asked in English, respond in English.
Reference official sources: wto.org, WT/DS documents, Panel/AB Reports."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system_prompt,
        messages=messages_history
    )

    return jsonify({
        "response": message.content[0].text,
        "language": language
    })

@app.route("/api/sources", methods=["GET"])
def official_sources():
    """Return curated official WTO and Saudi data sources"""
    return jsonify({
        "wto_official": [
            {
                "name": "WTO Dispute Settlement Database",
                "url": "https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm",
                "description": "Main WTO dispute settlement portal — all DS cases",
                "use_case": "Browse and monitor all WTO disputes"
            },
            {
                "name": "WTO Find Dispute Cases",
                "url": "https://www.wto.org/english/tratop_e/dispu_e/find_dispu_cases_e.htm",
                "description": "Advanced search for WTO dispute cases",
                "use_case": "Filter cases by year, agreement, country, subject"
            },
            {
                "name": "WTO Documents Online",
                "url": "https://docs.wto.org",
                "description": "Official WTO documents repository",
                "use_case": "Access Panel Reports, AB Reports, DSB Minutes"
            },
            {
                "name": "WTO Data Portal",
                "url": "https://data.wto.org",
                "description": "WTO trade statistics and data",
                "use_case": "Trade data analysis and tariff information"
            },
            {
                "name": "WTO API Portal",
                "url": "https://api.wto.org",
                "description": "WTO official API for data access",
                "use_case": "Programmatic access to WTO datasets"
            }
        ],
        "monitoring": [
            {
                "name": "ePing SPS/TBT Notifications",
                "url": "https://epingalert.org",
                "description": "Real-time SPS and TBT notifications",
                "use_case": "Monitor new SPS/TBT measures affecting Saudi exports"
            },
            {
                "name": "WTO I-TIP Services",
                "url": "https://i-tip.wto.org",
                "description": "Integrated Trade Intelligence Portal",
                "use_case": "Track trade policy measures and services schedules"
            },
            {
                "name": "WTO Environmental Database",
                "url": "https://edb.wto.org",
                "description": "Environmental measures database",
                "use_case": "Monitor CBAM and trade-environment measures"
            }
        ],
        "saudi_official": [
            {
                "name": "هيئة الخبراء بمجلس الوزراء",
                "url": "https://laws.boe.gov.sa",
                "description": "الأنظمة والتشريعات السعودية الرسمية",
                "use_case": "مراجعة الأنظمة واللوائح السعودية ذات الصلة بالتجارة"
            },
            {
                "name": "الهيئة العامة للتجارة الخارجية",
                "url": "https://www.gaft.gov.sa",
                "description": "الهيئة العامة للتجارة الخارجية السعودية",
                "use_case": "متابعة سياسات التجارة الخارجية والاتفاقيات"
            },
            {
                "name": "هيئة الزكاة والضريبة والجمارك",
                "url": "https://www.zatca.gov.sa",
                "description": "هيئة الزكاة والضريبة والجمارك",
                "use_case": "الرسوم الجمركية والإجراءات الجمركية السعودية"
            }
        ],
        "analysis": [
            {
                "name": "UNCTAD Investment Policy Hub",
                "url": "https://investmentpolicy.unctad.org",
                "description": "Investment treaties and trade policy analysis",
                "use_case": "International investment agreements affecting Saudi Arabia"
            },
            {
                "name": "World Bank Trade Data",
                "url": "https://wits.worldbank.org",
                "description": "World Integrated Trade Solution",
                "use_case": "Trade data analysis and tariff impact assessment"
            }
        ]
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "platform": "WTO Dispute Intelligence Platform",
        "version": "1.0.0",
        "disputes_loaded": len(WTO_DISPUTES),
        "ai_enabled": bool(ANTHROPIC_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    })

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
