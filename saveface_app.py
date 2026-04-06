import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from xml.etree import ElementTree as ET
import anthropic
import json
import re

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
# Write favicon inline so it works on Streamlit Cloud without a separate file
import os, pathlib
_favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#1a1714"/>
  <rect x="8" y="8" width="48" height="48" rx="4" fill="none" stroke="#C4A484" stroke-width="0.8" opacity="0.5"/>
  <text x="32" y="50"
        text-anchor="middle"
        font-family="Georgia, serif"
        font-size="36"
        font-weight="300"
        font-style="italic"
        fill="#C4A484"
        letter-spacing="-2">SF</text>
</svg>"""
_favicon_path = pathlib.Path("favicon.svg")
if not _favicon_path.exists():
    _favicon_path.write_text(_favicon_svg)

st.set_page_config(
    page_title="SaveFace.io",
    page_icon="favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# FONT AWESOME
# ──────────────────────────────────────────────
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────
# CUSTOM CSS  — premium editorial aesthetic
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Jost:wght@300;400;500;600&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Cormorant Garamond', serif;
    background-color: #1a1714;
    color: #F0EAE0;
    font-size: 1.05rem;
}

/* Full dark background across every Streamlit layer */
.stApp, .stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
section[data-testid="stMain"] {
    background-color: #1a1714 !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 1200px !important; }

/* ── Hero — now blends into page, defined by gold accent ── */
.hero {
    background: #221E1A;
    border: 1px solid rgba(196,164,132,0.2);
    border-radius: 24px;
    padding: 3.5rem 3rem 3rem;
    color: #F0EAE0;
    margin-bottom: 2.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(196,164,132,0.18) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #C4A484;
    margin-bottom: 0.8rem;
}
.hero h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 4rem;
    font-weight: 300;
    line-height: 1.05;
    color: #F0EAE0;
    margin: 0 0 1rem 0;
    letter-spacing: -0.02em;
}
.hero h1 em { font-style: italic; color: #C4A484; }
.hero p {
    font-size: 0.95rem;
    font-weight: 300;
    opacity: 0.65;
    margin: 0;
    max-width: 480px;
    line-height: 1.7;
}
.hero-badges { display: flex; gap: 0.6rem; margin-top: 1.8rem; flex-wrap: wrap; }
.hero-badge {
    background: rgba(196,164,132,0.1);
    border: 1px solid rgba(196,164,132,0.25);
    border-radius: 30px;
    padding: 5px 14px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: rgba(240,234,224,0.7);
}

/* ── Cards ── */
.card {
    background: #221E1A;
    border-radius: 18px;
    padding: 1.8rem;
    border: 1px solid rgba(196,164,132,0.15);
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

/* ── Ingredient Cards ── */
.ing-card { border-radius: 14px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
.ing-card-red   { background: #2A1E1E; border: 1px solid #4A2828; }
.ing-card-green { background: #1A2620; border: 1px solid #2A4035; }

.ing-name {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: #F0EAE0;
    margin-bottom: 0.3rem;
    line-height: 1.2;
}
.ing-status-red   { font-size: 0.7rem; font-weight: 600; color: #E08080; letter-spacing: 0.1em; text-transform: uppercase; }
.ing-status-green { font-size: 0.7rem; font-weight: 600; color: #6EC98F; letter-spacing: 0.1em; text-transform: uppercase; }
.ing-reason { font-size: 0.85rem; color: #B0A898; line-height: 1.65; margin: 0.5rem 0 0.7rem; font-weight: 300; }

/* ── Tags ── */
.condition-tag {
    display: inline-block;
    background: rgba(196,164,132,0.12);
    color: #C4A484;
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.68rem;
    font-weight: 600;
    margin: 2px 3px 2px 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.ai-tag {
    display: inline-block;
    background: rgba(100,120,220,0.15);
    color: #8FA0E8;
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.68rem;
    font-weight: 600;
    margin: 2px 3px 2px 0;
}

/* ── PubMed citations ── */
.cite-block { background: #141210; border-radius: 10px; padding: 0.9rem 1.1rem; margin-top: 0.8rem; border: 1px solid rgba(196,164,132,0.1); }
.cite-label { font-size: 0.63rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: #6B5B4E; margin-bottom: 0.5rem; }
.pubmed-link { display: block; color: #8BADD4; font-size: 0.82rem; text-decoration: none; padding: 5px 0; line-height: 1.5; border-bottom: 1px solid rgba(255,255,255,0.05); }
.pubmed-link:last-child { border-bottom: none; }
.pubmed-pmid { font-size: 0.7rem; font-weight: 600; color: #6B5B4E; margin-right: 6px; }

/* ── Section headers ── */
.section-header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.7rem;
    font-weight: 400;
    color: #F0EAE0;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid rgba(196,164,132,0.2);
}

/* ── Summary bar ── */
.summary-bar {
    background: #141210;
    border: 1px solid rgba(196,164,132,0.15);
    border-radius: 16px;
    padding: 1.4rem 2rem;
    display: flex;
    gap: 2.5rem;
    align-items: center;
    margin-top: 2rem;
    flex-wrap: wrap;
}
.summary-num { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; font-weight: 600; color: #F0EAE0; line-height: 1; }
.summary-desc { font-size: 0.65rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: #6B5B4E; margin-top: 4px; }
.summary-divider { width: 1px; height: 36px; background: rgba(196,164,132,0.15); }

/* ── Streamlit widget overrides ── */
.stButton > button {
    background: #C4A484 !important;
    color: #1a1714 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 10px !important;
    border: 1px solid rgba(196,164,132,0.25) !important;
    background: #221E1A !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1rem !important;
    color: #F0EAE0 !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: #6B5B4E !important; }
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #C4A484 !important;
    box-shadow: 0 0 0 3px rgba(196,164,132,0.15) !important;
}

/* Multiselect + radio */
.stMultiSelect > div { border-radius: 10px !important; border: 1px solid rgba(196,164,132,0.25) !important; background: #221E1A !important; }
[data-testid="stMultiSelect"] span { color: #F0EAE0 !important; }
.stRadio label { color: #B0A898 !important; }
label, .stMarkdown p, .stMarkdown h5,
[data-testid="stWidgetLabel"], .stRadio label,
[data-baseweb="select"] *, [data-baseweb="tag"] * {
    color: #B0A898 !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1rem !important;
}

/* Color picker label */
.stColorPicker label { color: #B0A898 !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #141210 !important; border-right: 1px solid rgba(196,164,132,0.1) !important; }
section[data-testid="stSidebar"] * { color: #B0A898 !important; }

/* Alerts */
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Dermatology-grade ingredient analysis</div>
    <h1>Save<em>Face</em></h1>
    <p>Enter any skincare product and we cross-reference every ingredient against published clinical evidence — for your specific skin conditions.</p>
    <div class="hero-badges">
        <span class="hero-badge"><i class="fa-solid fa-flask-vial"></i> PubMed-cited</span>
        <span class="hero-badge"><i class="fa-solid fa-microchip"></i> AI-assisted</span>
        <span class="hero-badge"><i class="fa-solid fa-stethoscope"></i> 5 conditions</span>
        <span class="hero-badge"><i class="fa-solid fa-droplet"></i> INCIdecoder linked</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# KNOWLEDGE BASE  (your original lists, expanded)
# ──────────────────────────────────────────────
RED_FLAGS = {
    "eczema": [
        "fragrance","lanolin","alcohol denat","essential oils","menthol",
        "camphor","sodium lauryl sulfate","sls","sodium laureth sulfate",
        "sles","propylene glycol","formaldehyde","methylisothiazolinone",
        "benzalkonium chloride","neomycin","bacitracin",
    ],
    "acne": [
        "coconut oil","isopropyl myristate","shea butter","lanolin",
        "lauric acid","mineral oil","algae extract","carrageenan",
        "acetylated lanolin","isopropyl palmitate","myristyl myristate",
        "sodium lauryl sulfate","wheat germ oil","soybean oil",
    ],
    "rosacea": [
        "alcohol denat","menthol","witch hazel","fragrance","camphor",
        "peppermint oil","eucalyptus oil","sodium lauryl sulfate",
        "lactic acid","glycolic acid","retinol","benzoyl peroxide",
        "clove oil","cinnamon","tea tree oil",
    ],
    "seborrheic dermatitis": [
        "fragrance","alcohol denat","essential oils",
        "sodium lauryl sulfate","lanolin","propylene glycol",
        "methylchloroisothiazolinone","methylisothiazolinone",
    ],
    "contact dermatitis": [
        "fragrance","nickel","cobalt","chromate","formaldehyde",
        "methylisothiazolinone","methylchloroisothiazolinone",
        "parabens","lanolin","propylene glycol","benzalkonium chloride",
        "neomycin","bacitracin","colophonium","balsam of peru",
    ],
}

GREEN_FLAGS = {
    "eczema":               ["ceramides","colloidal oatmeal","glycerin","petrolatum","shea butter","panthenol","allantoin"],
    "acne":                 ["salicylic acid","benzoyl peroxide","niacinamide","adapalene","azelaic acid","tea tree oil","zinc"],
    "rosacea":              ["niacinamide","azelaic acid","green tea extract","centella asiatica","allantoin","zinc"],
    "seborrheic dermatitis":["ketoconazole","zinc pyrithione","selenium sulfide","ciclopirox","coal tar","salicylic acid"],
    "contact dermatitis":   ["ceramides","petrolatum","colloidal oatmeal","panthenol","allantoin"],
}

INGREDIENT_INFO = {
    "fragrance":                    "A broad term covering hundreds of chemicals; a top trigger for allergic contact dermatitis and sensitization.",
    "lanolin":                      "Derived from sheep wool; highly comedogenic and a recognized contact allergen.",
    "alcohol denat":                "Denaturated alcohol strips the skin barrier and can exacerbate dryness and rosacea flushing.",
    "essential oils":               "Highly volatile compounds; frequent sensitizers in fragrance-allergic individuals.",
    "menthol":                      "Stimulates cold receptors; can worsen rosacea vascular reactivity and eczema inflammation.",
    "camphor":                      "Penetrating irritant that can inflame compromised or sensitive skin.",
    "sodium lauryl sulfate":        "Strong anionic surfactant that disrupts the epidermal barrier; major eczema irritant.",
    "coconut oil":                  "Rich in comedogenic lauric acid; clogs follicles in acne-prone skin.",
    "isopropyl myristate":          "Lipophilic emollient that penetrates follicles and promotes comedone formation.",
    "shea butter":                  "Excellent emollient for dry skin but rated 0–2 on the comedogenicity scale — high-risk for acne.",
    "lauric acid":                  "A C12 fatty acid shown to stimulate P. acnes and provoke inflammatory acne.",
    "mineral oil":                  "Occlusive petrolatum derivative; can trap sebum and worsen comedonal acne.",
    "witch hazel":                  "High tannin and alcohol content can dry and irritate rosacea-prone skin.",
    "peppermint oil":               "Contains menthol and other terpenoids; potent contact sensitizer.",
    "sodium laureth sulfate":       "Milder than SLS but still a barrier disruptor at high concentrations.",
    "propylene glycol":             "Humectant and penetration enhancer; causes contact dermatitis in sensitive individuals.",
    "formaldehyde":                 "Preservative and known human carcinogen; strong sensitizer for contact dermatitis.",
    "methylisothiazolinone":        "Preservative biocide declared 'Allergen of the Year 2013' by the ACDS.",
    "benzalkonium chloride":        "Quaternary ammonium compound; irritant and sensitizer in atopic individuals.",
    "ceramides":                    "Physiologic skin lipids that restore and maintain the epidermal barrier — cornerstone of eczema therapy.",
    "colloidal oatmeal":            "FDA-recognized skin protectant; anti-inflammatory and antipruritic in eczema.",
    "glycerin":                     "Hygroscopic humectant that pulls moisture into the stratum corneum.",
    "niacinamide":                  "Reduces sebum, strengthens barrier, and inhibits inflammatory cytokine release.",
    "azelaic acid":                 "Dual-action: reduces P. acnes + inhibits inflammatory mediators relevant to rosacea.",
    "salicylic acid":               "Beta-hydroxy acid that dissolves comedones and has keratolytic + anti-inflammatory properties.",
    "benzoyl peroxide":             "Bactericidal against P. acnes; reduces antibiotic resistance when used in combination.",
    "ketoconazole":                 "Azole antifungal; targets Malassezia species implicated in seborrheic dermatitis.",
    "zinc pyrithione":              "Antifungal and antibacterial; effective against Malassezia in dandruff and sebderm.",
    "selenium sulfide":             "Antifungal mechanism through cytostatic effect on Malassezia.",
    "petrolatum":                   "Inert occlusive that creates a physical barrier; gold standard for compromised skin.",
    "panthenol":                    "Pro-vitamin B5; improves wound healing and skin hydration.",
    "allantoin":                    "Keratolytic and anti-irritant; promotes cell proliferation and wound repair.",
    "tea tree oil":                 "Has antimicrobial properties for acne but is a recognized contact sensitizer at high concentrations.",
    "green tea extract":            "Rich in EGCG; anti-inflammatory and antioxidant properties beneficial in rosacea.",
    "centella asiatica":            "Triterpenoids promote collagen synthesis and reduce inflammation in sensitive skin.",
}

# ──────────────────────────────────────────────
# PUBMED HELPERS
# ──────────────────────────────────────────────
PUBMED_API_KEY = "2e0d3c7237cd76559a733da596d501b11508"

# Clinical terminology map — ensures PubMed searches use the correct medical terms
CONDITION_MESH = {
    "eczema":                "atopic dermatitis",
    "acne":                  "acne vulgaris",
    "rosacea":               "rosacea",
    "seborrheic dermatitis": "seborrheic dermatitis",
    "contact dermatitis":    "allergic contact dermatitis",
}

# Pre-defined high-quality queries for known irritant pairs
# Format: (ingredient, condition) -> PubMed query string
KNOWN_QUERIES = {
    ("fragrance", "contact dermatitis"):    '"fragrance"[tiab] AND "contact dermatitis"[tiab] AND "allergen"[tiab]',
    ("fragrance", "eczema"):                '"fragrance"[tiab] AND "atopic dermatitis"[tiab]',
    ("fragrance", "rosacea"):               '"fragrance"[tiab] AND "rosacea"[tiab] AND "irritant"[tiab]',
    ("sodium lauryl sulfate", "eczema"):    '"sodium lauryl sulfate"[tiab] AND "skin barrier"[tiab] AND "atopic dermatitis"[tiab]',
    ("sodium lauryl sulfate", "contact dermatitis"): '"sodium lauryl sulfate"[tiab] AND "irritant contact dermatitis"[tiab]',
    ("lanolin", "contact dermatitis"):      '"lanolin"[tiab] AND "contact allergy"[tiab]',
    ("lanolin", "acne"):                    '"lanolin"[tiab] AND "comedogenic"[tiab]',
    ("coconut oil", "acne"):                '"coconut oil"[tiab] AND "comedogenic"[tiab]',
    ("isopropyl myristate", "acne"):        '"isopropyl myristate"[tiab] AND "comedogenicity"[tiab]',
    ("alcohol denat", "rosacea"):           '"alcohol"[tiab] AND "rosacea"[tiab] AND "skin irritation"[tiab]',
    ("alcohol denat", "eczema"):            '"alcohol"[tiab] AND "atopic dermatitis"[tiab] AND "skin barrier"[tiab]',
    ("methylisothiazolinone", "contact dermatitis"): '"methylisothiazolinone"[tiab] AND "contact allergy"[tiab]',
    ("methylisothiazolinone", "eczema"):    '"methylisothiazolinone"[tiab] AND "sensitization"[tiab]',
    ("propylene glycol", "contact dermatitis"): '"propylene glycol"[tiab] AND "contact dermatitis"[tiab]',
    ("menthol", "rosacea"):                 '"menthol"[tiab] AND "skin irritation"[tiab]',
    ("formaldehyde", "contact dermatitis"): '"formaldehyde"[tiab] AND "contact allergy"[tiab] AND "skin"[tiab]',
    ("parabens", "contact dermatitis"):     '"parabens"[tiab] AND "contact allergy"[tiab]',
    ("lauric acid", "acne"):                '"lauric acid"[tiab] AND "acne"[tiab]',
    ("mineral oil", "acne"):                '"mineral oil"[tiab] AND "comedogenic"[tiab]',
    ("neomycin", "contact dermatitis"):     '"neomycin"[tiab] AND "contact allergy"[tiab] AND "sensitization"[tiab]',
    ("benzalkonium chloride", "contact dermatitis"): '"benzalkonium chloride"[tiab] AND "skin irritation"[tiab]',
    ("witch hazel", "rosacea"):             '"witch hazel"[tiab] AND "skin irritation"[tiab]',
    ("shea butter", "acne"):                '"shea butter"[tiab] AND "comedogenic"[tiab]',
    ("essential oils", "contact dermatitis"): '"essential oil"[tiab] AND "contact dermatitis"[tiab] AND "allergen"[tiab]',
    ("essential oils", "eczema"):           '"essential oil"[tiab] AND "atopic dermatitis"[tiab] AND "irritant"[tiab]',
}

def _build_query(ingredient: str, condition: str) -> str:
    """Build a precise, clinically-targeted PubMed query."""
    key = (ingredient.lower(), condition.lower())
    if key in KNOWN_QUERIES:
        return KNOWN_QUERIES[key]
    # Build a structured query using MeSH/clinical terminology
    mesh_condition = CONDITION_MESH.get(condition, condition)
    # Use field-tagged terms to ensure the ingredient AND condition co-occur
    mc = mesh_condition
    return (
        f'"{ingredient}"[tiab] AND ("{mc}"[tiab] OR "{mc}"[MeSH Terms]) '
        f'AND ("irritant"[tiab] OR "sensitizer"[tiab] OR "allergen"[tiab] '
        f'OR "comedogenic"[tiab] OR "skin reaction"[tiab] OR "adverse"[tiab])'
    )

def _search_pubmed_ids(query: str, max_results: int = 5) -> list[str]:
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmax": max_results,
                  "retmode": "json", "api_key": PUBMED_API_KEY}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()["esearchresult"]["idlist"]
    except Exception:
        return []

def _fetch_articles(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {"db": "pubmed", "id": ",".join(pmids),
                  "retmode": "xml", "api_key": PUBMED_API_KEY}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        articles = []
        for pmid, art in zip(pmids, root.findall(".//PubmedArticle")):
            title   = art.findtext(".//ArticleTitle", "No title available")
            abstract = art.findtext(".//AbstractText", "")
            year    = art.findtext(".//PubDate/Year", "")
            journal = art.findtext(".//Journal/ISOAbbreviation", "")
            articles.append({
                "pmid": pmid, "title": title, "abstract": abstract,
                "year": year, "journal": journal,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        return articles
    except Exception:
        return []

def _ai_filter_articles(articles: list[dict], ingredient: str, condition: str) -> list[dict]:
    """Use Claude to verify each article is genuinely about this ingredient-condition relationship."""
    if not articles:
        return []
    summaries = [
        {"pmid": a["pmid"], "title": a["title"], "abstract": a["abstract"][:400]}
        for a in articles
    ]
    prompt = f"""You are a dermatology research assistant. I need to find PubMed articles that specifically study or report on "{ingredient}" as an irritant, allergen, or problematic ingredient for "{condition}".

Here are candidate articles (title + abstract excerpt):
{json.dumps(summaries, indent=2)}

Return ONLY a JSON array of the PMIDs that are genuinely relevant — i.e. the article actually discusses "{ingredient}" in the context of "{condition}", skin irritation, contact allergy, comedogenicity, or adverse skin reactions. Exclude anything only tangentially related.

Respond with ONLY a JSON array of strings, e.g. ["12345678", "87654321"]. No explanation, no markdown."""
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        valid_pmids = set(json.loads(raw))
        return [a for a in articles if a["pmid"] in valid_pmids]
    except Exception:
        return articles  # fallback: return unfiltered if AI call fails

def get_citations(ingredient: str, condition: str) -> list[dict]:
    """Fetch 2-3 PubMed articles that genuinely document ingredient as irritant for condition."""
    query = _build_query(ingredient, condition)
    pmids = _search_pubmed_ids(query, max_results=6)  # fetch more, filter down

    # Fallback if precise query returns nothing
    if not pmids:
        mesh_condition = CONDITION_MESH.get(condition, condition)
        pmids = _search_pubmed_ids(
            f'"{ingredient}"[tiab] AND "{mesh_condition}"[tiab]',
            max_results=6
        )
    if not pmids:
        return []

    articles  = _fetch_articles(pmids)
    filtered  = _ai_filter_articles(articles, ingredient, condition)
    return filtered[:3]  # return max 3 verified articles

# ──────────────────────────────────────────────
# INCIDECODER SCRAPER  (fuzzy search → best match)
# ──────────────────────────────────────────────
def _search_incidecoder(query: str) -> list[dict]:
    """Search INCIdecoder and return list of {name, url} matches."""
    try:
        url = "https://incidecoder.com/search"
        r = requests.get(url, params={"query": query},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        results = []
        for a in soup.select("a.klavika-font, a[href*='/products/']"):
            href = a.get("href", "")
            if "/products/" in href:
                name = a.get_text(strip=True)
                if name:
                    results.append({
                        "name": name,
                        "url": "https://incidecoder.com" + href if href.startswith("/") else href
                    })
        return results[:8]
    except Exception:
        return []

def search_incidecoder_suggestions(query: str) -> list[str]:
    """Return up to 8 product name suggestions from INCIdecoder for autocomplete."""
    if not query or len(query) < 3:
        return []
    try:
        r = requests.get(
            "https://incidecoder.com/search",
            params={"query": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        soup = BeautifulSoup(r.content, "html.parser")
        names = []
        for a in soup.select("a[href*='/products/']"):
            name = a.get_text(strip=True)
            if name and name not in names:
                names.append(name)
        return names[:8]
    except Exception:
        return []

def _pick_best_match(query: str, candidates: list[dict]) -> dict | None:
    """Use Claude to pick the most likely product match from search results."""
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    names = [c["name"] for c in candidates]
    numbered = ", ".join(f"{i+1}. {n}" for i, n in enumerate(names))
    prompt = (
        'A user searched for: ' + query + '\n'
        'These products were found on INCIdecoder:\n'
        + numbered
        + '\n\nRespond with ONLY the number of the best matching product. Just a single integer.'
    )
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        idx = int(response.content[0].text.strip()) - 1
        return candidates[idx] if 0 <= idx < len(candidates) else candidates[0]
    except Exception:
        return candidates[0]

def _scrape_ingredients(product_url: str) -> list[str] | None:
    """Scrape ingredient list from a product page URL."""
    try:
        r = requests.get(product_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        div = soup.find("div", id="ingredlist-short") or soup.find("div", id="ingredlist")
        if div:
            links = div.find_all("a", class_="ingred-link")
            return [l.get_text(strip=True).lower() for l in links if l.get_text(strip=True)]
    except Exception:
        pass
    return None

def fetch_ingredients_incidecoder(product_name: str) -> tuple[list[str] | None, str | None]:
    """
    Fuzzy-search INCIdecoder for product_name, pick best match, return
    (ingredients, matched_product_name).
    """
    candidates = _search_incidecoder(product_name)
    if not candidates:
        # Last resort: try direct slug
        slug = re.sub(r"[^a-z0-9\-]", "", product_name.lower().strip().replace(" ", "-"))
        ingredients = _scrape_ingredients(f"https://incidecoder.com/products/{slug}")
        return (ingredients, product_name if ingredients else None)

    best = _pick_best_match(product_name, candidates)
    if not best:
        return (None, None)

    ingredients = _scrape_ingredients(best["url"])
    return (ingredients, best["name"])

# ──────────────────────────────────────────────
# AI-POWERED INGREDIENT CLASSIFIER  (Claude API)
# ──────────────────────────────────────────────
def ai_classify_ingredients(ingredients: list[str], conditions: list[str]) -> dict:
    """
    For ingredients NOT in our knowledge base, ask Claude to classify them.
    Returns dict: {ingredient: {status, reason, conditions_flagged}}
    """
    # Only send unknowns to save tokens
    known = set(INGREDIENT_INFO.keys()) | {i for flags in RED_FLAGS.values() for i in flags} \
                                        | {i for flags in GREEN_FLAGS.values() for i in flags}
    unknowns = [i for i in ingredients if i.lower() not in known]
    if not unknowns:
        return {}

    cond_str = ", ".join(conditions)
    prompt = f"""You are a dermatology expert. Classify each ingredient below for its safety profile relative to these skin conditions: {cond_str}.

Ingredients to classify:
{json.dumps(unknowns)}

Respond ONLY with a valid JSON object (no markdown, no explanation) in this exact schema:
{{
  "ingredient_name": {{
    "status": "irritant" | "beneficial" | "neutral",
    "conditions_flagged": ["list of conditions it is problematic for, if any"],
    "reason": "One concise clinical sentence explaining why."
  }}
}}

If an ingredient is generally safe, set status to "neutral" and conditions_flagged to [].
"""
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        return {}

# ──────────────────────────────────────────────
# CORE ANALYSIS FUNCTION
# ──────────────────────────────────────────────
def analyze(ingredients: list[str], conditions: list[str]) -> dict:
    red, green, neutral, unknown_results = [], [], [], []

    # Build merged flag sets for selected conditions
    all_red   = {i for c in conditions for i in RED_FLAGS.get(c, [])}
    all_green = {i for c in conditions for i in GREEN_FLAGS.get(c, [])}

    for ing in ingredients:
        ing_lower = ing.lower().strip()
        if not ing_lower:
            continue
        conds_flagged_red   = [c for c in conditions if ing_lower in [x.lower() for x in RED_FLAGS.get(c, [])]]
        conds_flagged_green = [c for c in conditions if ing_lower in [x.lower() for x in GREEN_FLAGS.get(c, [])]]

        if conds_flagged_red:
            red.append({
                "name": ing,
                "conditions": conds_flagged_red,
                "reason": INGREDIENT_INFO.get(ing_lower, "Known irritant for the selected skin condition(s)."),
            })
        elif conds_flagged_green:
            green.append({
                "name": ing,
                "conditions": conds_flagged_green,
                "reason": INGREDIENT_INFO.get(ing_lower, "Clinically beneficial for the selected skin condition(s)."),
            })

    # AI classification for unknowns
    ai_results = ai_classify_ingredients(ingredients, conditions)
    for ing, data in ai_results.items():
        if data.get("status") == "irritant":
            red.append({
                "name": ing,
                "conditions": data.get("conditions_flagged", []),
                "reason": data.get("reason", ""),
                "ai": True,
            })
        elif data.get("status") == "beneficial":
            green.append({
                "name": ing,
                "conditions": data.get("conditions_flagged", []),
                "reason": data.get("reason", ""),
                "ai": True,
            })

    return {"red": red, "green": green, "total": len(ingredients)}

# ──────────────────────────────────────────────
# UI LAYOUT
# ──────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("##### Skin Conditions")
    conditions_display = {c.title(): c for c in RED_FLAGS.keys()}
    selected_display = st.multiselect(
        "Which conditions to screen for?",
        options=list(conditions_display.keys()),
        default=[],
        placeholder="Choose condition(s)...",
        label_visibility="collapsed",
    )
    conditions = [conditions_display[d] for d in selected_display]

    st.markdown("##### Product Input")
    input_mode = st.radio("How would you like to enter the product?",
                          ["Search by product name", "Paste ingredient list"],
                          horizontal=True, label_visibility="collapsed")

    product_name = ""
    manual_list  = ""

    if input_mode == "Search by product name":
        # Autocomplete via selectbox when suggestions exist, plain input otherwise
        raw_query = st.text_input(
            "Product name",
            placeholder="e.g. CeraVe Moisturizing Cream",
            label_visibility="collapsed",
            key="product_search_input",
        )
        if raw_query and len(raw_query) >= 3:
            with st.spinner(""):
                suggestions = search_incidecoder_suggestions(raw_query)
            if suggestions:
                # Prepend the raw query so user can keep what they typed
                options = [raw_query] + [s for s in suggestions if s.lower() != raw_query.lower()]
                chosen = st.selectbox(
                    "Suggestions",
                    options=options,
                    label_visibility="collapsed",
                    key="product_suggestion",
                )
                product_name = chosen
            else:
                product_name = raw_query
        else:
            product_name = raw_query

        st.caption("Select a suggestion or press Analyze to search.")
        # Enter key triggers run via form
        run_on_enter = st.session_state.get("product_search_input", "") != "" and                        st.session_state.get("_last_query", "") != st.session_state.get("product_search_input", "")
    else:
        manual_list = st.text_area(
            "Paste ingredient list",
            height=160,
            placeholder="Water, Glycerin, Niacinamide, Fragrance, ...",
            label_visibility="collapsed",
        )
        run_on_enter = False

    st.markdown("")
    run = st.button("Analyze Ingredients") or (
        input_mode == "Search by product name" and
        product_name.strip() and
        st.session_state.get("_submitted_query") != product_name
    )
    if run and product_name:
        st.session_state["_submitted_query"] = product_name

with right:
    if run:
        if not conditions:
            st.warning("Please select at least one skin condition.")
            st.stop()

        ingredients = []

        if input_mode == "Search by product name":
            if not product_name.strip():
                st.warning("Please enter a product name.")
                st.stop()
            with st.spinner(f"Searching INCIdecoder for *{product_name}*…"):
                ingredients, matched_name = fetch_ingredients_incidecoder(product_name)
            if not ingredients:
                st.error("Could not find that product. Try a shorter name or paste ingredients manually.")
                st.stop()
            if matched_name and matched_name.lower() != product_name.lower():
                st.info(f"Matched to: **{matched_name}**")
            st.success(f"Found **{len(ingredients)} ingredients**")
        else:
            if not manual_list.strip():
                st.warning("Please paste an ingredient list.")
                st.stop()
            ingredients = [i.strip() for i in manual_list.split(",") if i.strip()]
            st.success(f"Loaded **{len(ingredients)} ingredients**")


        with st.spinner("Running AI + database analysis…"):
            results = analyze(ingredients, conditions)

        # ── RED FLAGS ─────────────────────────────
        st.markdown('<div class="section-header">Clinically Concerning Ingredients</div>', unsafe_allow_html=True)
        if results["red"]:
            for item in results["red"]:
                ai_tag = '<span class="ai-tag">AI</span>' if item.get("ai") else ""
                cond_tags = " ".join(f'<span class="condition-tag">{c}</span>' for c in item["conditions"])
                st.markdown(f"""
<div class="ing-card ing-card-red">
  <div class="ing-status-red">Irritant</div>
  <div class="ing-name">{item['name'].title()}</div>
  <div class="ing-reason">{item['reason']}</div>
  {cond_tags} {ai_tag}
</div>""", unsafe_allow_html=True)
                with st.spinner(f"Fetching PubMed citations for {item['name']}…"):
                    cond_label = item["conditions"][0] if item["conditions"] else conditions[0]
                    citations  = get_citations(item["name"], cond_label)
                if citations:
                    links_html = "".join(
                        f'<a class="pubmed-link" href="{c['url']}" target="_blank">' +
                        f'<span class="pubmed-pmid">PMID {c['pmid']}</span>{c['title']}' +
                        (f' ({c['year']} · {c['journal']})' if c['year'] else '') + '</a>'
                        for c in citations
                    )
                    st.markdown(f'<div class="cite-block"><div class="cite-label">Supporting Literature</div>{links_html}</div>', unsafe_allow_html=True)
                st.markdown("")
        else:
            st.success("No red-flag ingredients detected for the selected conditions.")

        # ── GREEN FLAGS ───────────────────────────
        st.markdown('<div class="section-header">Clinically Beneficial Ingredients</div>', unsafe_allow_html=True)
        if results["green"]:
            for item in results["green"]:
                cond_tags = " ".join(f'<span class="condition-tag">{c}</span>' for c in item["conditions"])
                st.markdown(f"""
<div class="ing-card ing-card-green">
  <div class="ing-status-green">Beneficial</div>
  <div class="ing-name">{item['name'].title()}</div>
  <div class="ing-reason">{item['reason']}</div>
  {cond_tags}
</div>""", unsafe_allow_html=True)
        else:
            st.info("No known beneficial ingredients found for the selected conditions.")

        # ── SUMMARY BAR ───────────────────────────
        r, g, t = len(results["red"]), len(results["green"]), results["total"]
        st.markdown(f'''
<div class="summary-bar">
  <div class="summary-stat"><div class="summary-num">{t}</div><div class="summary-desc">Ingredients scanned</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-num" style="color:#E88080;">{r}</div><div class="summary-desc">Concerning</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-num" style="color:#6EC98F;">{g}</div><div class="summary-desc">Beneficial</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-num" style="color:#9E9189;">{t - r - g}</div><div class="summary-desc">Neutral</div></div>
</div>''', unsafe_allow_html=True)
        st.markdown("")

        # ── FULL INGREDIENT LIST (colour-coded) ───
        red_names   = {item["name"].lower() for item in results["red"]}
        green_names = {item["name"].lower() for item in results["green"]}
        pills = []
        for ing in ingredients:
            ing_l = ing.lower().strip()
            if ing_l in red_names:
                style = "background:rgba(224,128,128,0.15);border:1px solid rgba(224,128,128,0.35);color:#E08080;"
            elif ing_l in green_names:
                style = "background:rgba(110,201,143,0.15);border:1px solid rgba(110,201,143,0.35);color:#6EC98F;"
            else:
                style = "background:rgba(196,164,132,0.08);border:1px solid rgba(196,164,132,0.18);color:#9E9189;"
            pills.append(
                f'<span style="display:inline-block;{style}border-radius:20px;padding:3px 12px;' +
                f'font-size:0.82rem;margin:3px 3px 3px 0;font-family:Cormorant Garamond,serif;line-height:1.8;">' +
                f'{ing.title()}</span>'
            )
        pills_html = " ".join(pills)
        with st.expander(f"Full ingredient list — {len(ingredients)} ingredients"):
            st.markdown(
                '<p style="font-size:0.72rem;color:#6B5B4E;letter-spacing:0.1em;text-transform:uppercase;' +
                'margin-bottom:0.8rem;">Red = concerning · Green = beneficial · Grey = neutral</p>' +
                pills_html,
                unsafe_allow_html=True
            )

        st.caption("SaveFace.io does not replace medical advice. Always consult a board-certified dermatologist.")
    else:
        st.markdown("<p style=\"color:#6B5B4E;font-size:1.1rem;margin-top:2rem;\">Results will appear here once you analyze a product.</p>", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────
with st.sidebar:
    st.markdown("### SaveFace")
    st.markdown("**Conditions covered:**")
    for c in RED_FLAGS:
        st.markdown(f"- {c.title()}")
    st.markdown("---")
    st.markdown("Built by **Laila Al Rawi** 💡")
    st.markdown("💌 info@saveface.io")
