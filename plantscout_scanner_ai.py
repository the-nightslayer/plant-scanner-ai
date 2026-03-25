import streamlit as st
import base64
import json
import os
import re
import hashlib
import io
from groq import Groq
from datetime import datetime
from PIL import Image

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Plant Scanner AI",
    page_icon="🌿",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --moss: #2d4a1e;
  --fern: #4a7c3f;
  --sage: #8faa7b;
  --mint: #c8ddb8;
  --cream: #f7f4ed;
  --parchment: #ede8db;
  --bark: #5c4a32;
  --honey: #d4a843;
  --rust: #c05a2e;
  --ink: #1a1a14;
  --mist: #e8f0e0;
  --sky: #e8f4fd;
  --sky-border: #b8d8f0;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background-color: var(--cream) !important;
  color: var(--ink) !important;
}

.block-container { max-width: 600px !important; padding-top: 0 !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* ── App Header ── */
.app-header {
  background: var(--moss);
  border-radius: 0 0 20px 20px;
  padding: 22px 24px 18px;
  margin: -1rem -1rem 1.5rem -1rem;
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  overflow: hidden;
}
.app-header::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 160px; height: 160px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
}
.logo-mark {
  background: var(--honey);
  border-radius: 12px;
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.header-title {
  font-family: 'Playfair Display', serif !important;
  font-size: 24px;
  font-weight: 900;
  color: #f7f4ed;
  line-height: 1;
  margin: 0;
}
.header-sub {
  font-family: 'DM Mono', monospace !important;
  font-size: 11px;
  color: var(--sage);
  letter-spacing: 0.5px;
  margin: 3px 0 0 0;
  font-weight: 300;
}

/* ── Intro card ── */
.intro-card {
  background: var(--parchment);
  border-radius: 16px;
  padding: 16px 18px;
  border: 1px solid var(--mint);
  display: flex;
  gap: 12px;
  margin-bottom: 0.75rem;
}
.intro-icon { font-size: 24px; flex-shrink: 0; }
.intro-card h4 {
  font-family: 'Playfair Display', serif !important;
  font-size: 14px;
  font-weight: 700;
  color: var(--moss);
  margin: 0 0 4px 0;
}
.intro-card p {
  font-size: 12px;
  color: var(--bark);
  line-height: 1.5;
  font-weight: 300;
  margin: 0;
}

/* ── Section label ── */
.section-label {
  font-family: 'DM Mono', monospace !important;
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--bark);
  font-weight: 500;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--mint);
  padding-bottom: 6px;
}

/* ── Result header ── */
.result-header-native {
  background: linear-gradient(135deg, var(--moss), var(--fern));
  border-radius: 20px 20px 0 0;
  padding: 24px 22px;
  color: white;
}
.result-header-invasive {
  background: linear-gradient(135deg, #7a2020, var(--rust));
  border-radius: 20px 20px 0 0;
  padding: 24px 22px;
  color: white;
}
.result-badge {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 2px;
  text-transform: uppercase;
  background: rgba(255,255,255,0.2);
  color: white;
  padding: 4px 12px;
  border-radius: 100px;
  display: inline-block;
  margin-bottom: 12px;
}
.result-name {
  font-family: 'Playfair Display', serif !important;
  font-size: 28px;
  font-weight: 900;
  color: white;
  line-height: 1;
  margin-bottom: 10px;
}
.result-impact {
  font-size: 13px;
  color: rgba(255,255,255,0.85);
  line-height: 1.5;
  font-weight: 300;
}

/* ── Info cards ── */
.bee-card {
  background: #fffbf0;
  border: 1px solid #f5e4a0;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  gap: 14px;
  margin-bottom: 1rem;
}
.bee-icon-box {
  width: 44px; height: 44px;
  background: var(--honey);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.card-label {
  font-family: 'DM Mono', monospace !important;
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 6px;
  font-weight: 500;
}
.bee-card .card-label { color: #8a6d1a; }
.card-text { font-size: 13px; line-height: 1.5; font-weight: 300; margin: 0; }
.bee-card .card-text { color: #5a4a1a; }

/* ── Garden card ── */
.garden-card-good { background: #f0faf0; border: 1px solid #b8ddb8; border-radius: 16px; padding: 16px; display: flex; gap: 14px; margin-bottom: 1rem; }
.garden-card-caution { background: #fffbf0; border: 1px solid #f5d080; border-radius: 16px; padding: 16px; display: flex; gap: 14px; margin-bottom: 1rem; }
.garden-card-remove { background: #fdf1ee; border: 1px solid #f0ccc0; border-radius: 16px; padding: 16px; display: flex; gap: 14px; margin-bottom: 1rem; }

.garden-icon-box { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.garden-card-good .garden-icon-box { background: #b8ddb8; }
.garden-card-caution .garden-icon-box { background: #f5d080; }
.garden-card-remove .garden-icon-box { background: #f0ccc0; }

.garden-card-good .card-label { color: var(--moss); }
.garden-card-caution .card-label { color: #7a5a10; }
.garden-card-remove .card-label { color: var(--rust); }

.garden-verdict {
  font-family: 'Playfair Display', serif !important;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 5px;
}
.garden-card-good .garden-verdict { color: var(--moss); }
.garden-card-caution .garden-verdict { color: #7a5a10; }
.garden-card-remove .garden-verdict { color: var(--rust); }

.garden-summary { font-size: 12px; line-height: 1.55; font-weight: 300; margin: 0; }
.garden-card-good .garden-summary { color: #2a4a2a; }
.garden-card-caution .garden-summary { color: #5a4a10; }
.garden-card-remove .garden-summary { color: #5a2a1a; }

/* ── Stars ── */
.stars { font-size: 16px; margin-bottom: 6px; letter-spacing: 2px; }

/* ── Care grid ── */
.care-card {
  background: var(--sky);
  border: 1px solid var(--sky-border);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 1rem;
}
.care-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.care-stat {
  background: white;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid var(--sky-border);
}
.care-stat-label {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #5a7a9a;
  font-weight: 500;
  margin-bottom: 4px;
}
.care-stat-value { font-size: 13px; font-weight: 500; color: var(--ink); }
.difficulty-easy { background: #d0f0d0; color: var(--moss); border-radius: 100px; padding: 3px 10px; font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; display: inline-block; }
.difficulty-moderate { background: #fef0c0; color: #7a5a10; border-radius: 100px; padding: 3px 10px; font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; display: inline-block; }
.difficulty-challenging { background: #fde0d0; color: var(--rust); border-radius: 100px; padding: 3px 10px; font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; display: inline-block; }

.care-tips-label {
  font-family: 'DM Mono', monospace !important;
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #5a7a9a;
  font-weight: 500;
  margin-bottom: 8px;
}
.care-tip {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 12px;
  color: #2a4a6a;
  line-height: 1.45;
  font-weight: 300;
  padding: 7px 0;
  border-bottom: 1px solid var(--sky-border);
}
.care-tip:last-child { border-bottom: none; }
.tip-dot { color: #5a9aaa; font-size: 16px; line-height: 1; margin-top: -1px; }

/* ── Plant replacement items ── */
.plant-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--mist);
  border-radius: 14px;
  border: 1px solid var(--mint);
  margin-bottom: 8px;
}
.plant-num {
  width: 26px; height: 26px;
  background: var(--fern);
  color: white;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}
.plant-name {
  font-family: 'Playfair Display', serif !important;
  font-size: 15px;
  font-weight: 700;
  color: var(--moss);
  line-height: 1;
  margin-bottom: 3px;
}
.plant-benefit { font-size: 11px; color: var(--bark); font-weight: 300; line-height: 1.3; }
.bee-tag {
  margin-left: auto;
  background: var(--honey);
  color: white;
  font-size: 9px;
  font-family: 'DM Mono', monospace;
  padding: 3px 8px;
  border-radius: 100px;
  flex-shrink: 0;
  font-weight: 500;
  white-space: nowrap;
}

/* ── History item ── */
.history-item {
  background: white;
  border-radius: 16px;
  padding: 14px;
  display: flex;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--mint);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.history-item-name {
  font-family: 'Playfair Display', serif !important;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
}
.history-native { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--fern); font-weight: 500; text-transform: uppercase; }
.history-invasive { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--rust); font-weight: 500; text-transform: uppercase; }
.history-time { font-size: 11px; color: #aaa; font-weight: 300; margin-top: 2px; }

/* ── Streamlit widget overrides ── */
.stButton button {
  background: linear-gradient(135deg, var(--fern), var(--moss)) !important;
  color: white !important;
  border: none !important;
  border-radius: 14px !important;
  font-family: 'Playfair Display', serif !important;
  font-style: italic !important;
  font-size: 16px !important;
  padding: 14px 0 !important;
  width: 100%;
  transition: all 0.2s !important;
}
.stButton button:hover { opacity: 0.9 !important; }
div[data-testid="stFileUploader"] {
  border: 2px dashed var(--mint) !important;
  border-radius: 20px !important;
  background: var(--mist) !important;
  padding: 12px !important;
}

/* When we've uploaded an image, we replace the uploader area with a preview. */
.upload-preview {
  border: 2px dashed var(--mint) !important;
  border-radius: 20px !important;
  background: var(--mist) !important;
  padding: 14px !important;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-preview-img {
  width: 100%;
  height: 100%;
  max-height: 420px;
  object-fit: contain;
  border-radius: 12px;
  display: block;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_scan" not in st.session_state:
    st.session_state.selected_scan = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_uploaded_hash" not in st.session_state:
    st.session_state.last_uploaded_hash = None
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_mime" not in st.session_state:
    st.session_state.uploaded_mime = "image/jpeg"
if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0


def load_groq_api_key() -> str | None:
    # 1) Streamlit secrets (when configured)
    try:
        key = st.secrets.get("GROQ_API_KEY")  # type: ignore[attr-defined]
        if key:
            return str(key)
    except Exception:
        pass

    # 2) Environment variable
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    # 3) Local `.env` (useful for local development)
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f.readlines()]
            for ln in lines:
                if not ln or ln.startswith("#"):
                    continue
                if "=" in ln:
                    k, v = ln.split("=", 1)
                    if k.strip() == "GROQ_API_KEY":
                        return v.strip().strip("'").strip('"')
                else:
                    # If `.env` is just the raw token value
                    return ln.strip().strip("'").strip('"')
    except Exception:
        return None

    return None


GROQ_API_KEY = load_groq_api_key()


# ── Groq client ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


# ── Helpers ───────────────────────────────────────────────────────────────────
def stars_html(rating: int) -> str:
    n = max(1, min(5, int(rating or 3)))
    filled = "★" * n
    empty = "☆" * (5 - n)
    return f'<div class="stars" style="color:#d4a843">{filled}<span style="color:#ddd">{empty}</span></div>'


def difficulty_html(d: str) -> str:
    d = (d or "Moderate").strip()
    cls = {
        "easy": "difficulty-easy",
        "challenging": "difficulty-challenging",
    }.get(d.lower(), "difficulty-moderate")
    return f'<span class="{cls}">{d}</span>'


def garden_class(verdict: str) -> str:
    v = (verdict or "").lower()
    if "remove" in v:
        return "remove"
    if "caution" in v:
        return "caution"
    return "good"


GARDEN_ICON = {"good": "🌸", "caution": "⚠️", "remove": "🚫"}


def time_ago(ts: datetime) -> str:
    diff = (datetime.now() - ts).total_seconds()
    if diff < 60:
        return "Just now"
    if diff < 3600:
        return f"{int(diff/60)}m ago"
    if diff < 86400:
        return f"{int(diff/3600)}h ago"
    return f"{int(diff/86400)}d ago"


# This prompt matches the UI renderer in this file.
PROMPT = """Identify this plant and return ONLY valid JSON (no markdown, no extra text) with these keys:
{
  "commonName": "Plant name",
  "isNative": true or false,
  "isInvasive": true or false,
  "impact": "1-2 sentence ecological impact",
  "beeSupport": "1-2 sentence description of how this plant affects local bees",
  "gardenRating": number 1-5 where 5 is excellent for home gardens,
  "gardenVerdict": exactly one of: "Good for your garden" or "Caution advised" or "Remove from garden",
  "gardenSummary": "2-3 sentences on suitability for home gardens covering spread, aesthetics, neighbour impact",
  "care": {
    "sunlight": "Full sun or Partial shade or Full shade",
    "watering": "e.g. Weekly, Drought tolerant, Keep moist",
    "soil": "e.g. Well-drained loamy, Sandy dry, Rich moist",
    "difficulty": exactly one of: "Easy" or "Moderate" or "Challenging",
    "tips": ["tip 1", "tip 2", "tip 3"]
  },
  "nativeReplacements": [
    {"name": "Plant name", "benefit": "Brief ecological benefit"},
    {"name": "Plant name", "benefit": "Brief ecological benefit"},
    {"name": "Plant name", "benefit": "Brief ecological benefit"}
  ]
}"""


def analyse_plant(client: Groq, image_bytes: bytes, mime: str) -> dict:
    b64 = base64.b64encode(image_bytes).decode()
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        temperature=0.2,
        max_completion_tokens=1500,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or ""
    # Fallback for cases where the model returns code fences anyway
    clean = re.sub(r"```json\n?|\n?```", "", raw).strip()
    return json.loads(clean)


def render_result(data: dict):
    gc = garden_class(data.get("gardenVerdict", ""))
    header_cls = "result-header-invasive" if data.get("isInvasive") else "result-header-native"
    badge = "⚠ Invasive Species" if data.get("isInvasive") else "✓ Native Plant"

    st.markdown(
        f"""
<div class="{header_cls}">
  <div class="result-badge">{badge}</div>
  <div class="result-name">{data.get("commonName","Unknown")}</div>
  <p class="result-impact">{data.get("impact","")}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">🐝 Bee Friendliness</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="bee-card">
  <div class="bee-icon-box">🐝</div>
  <div>
    <div class="card-label">Bee Impact</div>
    <p class="card-text">{data.get("beeSupport","")}</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">🌱 Care & Maintenance</div>', unsafe_allow_html=True)
    care = data.get("care", {})
    tips = care.get("tips", []) or []
    tips_html = "".join(
        f'<div class="care-tip"><span class="tip-dot">•</span><span>{t}</span></div>'
        for t in tips
    )
    st.markdown(
        f"""
<div class="care-card">
  <div class="care-grid">
    <div class="care-stat">
      <div class="care-stat-label">☀️ Sunlight</div>
      <div class="care-stat-value">{care.get("sunlight","—")}</div>
    </div>
    <div class="care-stat">
      <div class="care-stat-label">💧 Watering</div>
      <div class="care-stat-value">{care.get("watering","—")}</div>
    </div>
    <div class="care-stat">
      <div class="care-stat-label">🪱 Soil</div>
      <div class="care-stat-value">{care.get("soil","—")}</div>
    </div>
    <div class="care-stat">
      <div class="care-stat-label">📊 Difficulty</div>
      {difficulty_html(care.get("difficulty","Moderate"))}
    </div>
  </div>
  <div class="care-tips-label">Tips</div>
  {tips_html}
</div>
""",
        unsafe_allow_html=True,
    )

    # Optional: keep the garden verdict card for extra usefulness.
    st.markdown('<div class="section-label">🏡 Garden Suitability</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="garden-card-{gc}">
  <div class="garden-icon-box">{GARDEN_ICON[gc]}</div>
  <div style="flex:1">
    <div class="card-label">Garden Assessment</div>
    {stars_html(data.get("gardenRating", 3))}
    <div class="garden-verdict">{data.get("gardenVerdict","")}</div>
    <p class="garden-summary">{data.get("gardenSummary","")}</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    replacements = data.get("nativeReplacements", [])
    if replacements:
        st.markdown('<div class="section-label">🌿 Plant These Instead</div>', unsafe_allow_html=True)
        for i, plant in enumerate(replacements, 1):
            st.markdown(
                f"""
<div class="plant-item">
  <div class="plant-num">{i}</div>
  <div style="flex:1">
    <div class="plant-name">{plant.get("name","")}</div>
    <div class="plant-benefit">{plant.get("benefit","")}</div>
  </div>
  <div class="bee-tag">🐝 Bee Safe</div>
</div>
""",
                unsafe_allow_html=True,
            )


# ── App header ────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
  <div class="logo-mark">🌿</div>
  <div>
    <p class="header-title">Plant Scanner AI</p>
    <p class="header-sub">Identify plants · See bee impact · Get care tips</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_scanner, tab_history = st.tabs(["📷  Scanner", "📊  History"])

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER TAB
# ═══════════════════════════════════════════════════════════════════════════════
with tab_scanner:
    st.markdown(
        """
<div class="intro-card">
  <div class="intro-icon">🐝</div>
  <div>
    <h4>Identify & Replant for Bees</h4>
    <p>Click the white upload area to add a plant photo. The app will scan it automatically and show plant info, bee impact, and care tips.</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not GROQ_API_KEY:
        st.warning("⚠ Groq API key is not configured. Set it in `.env` as `GROQ_API_KEY=...`.")

    # Use a placeholder so the upload zone can be replaced immediately by the preview image.
    upload_slot = st.empty()

    if st.session_state.uploaded_image_bytes is None:
        with upload_slot.container():
            uploaded = st.file_uploader(
                "Upload a plant photo",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
                key=f"plant_uploader_{st.session_state.uploader_version}",
            )

        # If a file was uploaded, scan it and then replace the upload zone with the image.
        if uploaded is not None:
            st.session_state.uploaded_image_bytes = uploaded.getvalue()
            st.session_state.uploaded_mime = uploaded.type or "image/jpeg"

            file_hash = hashlib.sha256(st.session_state.uploaded_image_bytes).hexdigest()
            st.session_state.last_result = None

            # Auto-scan only when the uploaded image changes
            if GROQ_API_KEY and st.session_state.last_uploaded_hash != file_hash:
                st.session_state.last_uploaded_hash = file_hash
                with st.spinner("🌿 Scanning plant..."):
                    try:
                        client = get_client(GROQ_API_KEY)
                        result = analyse_plant(
                            client,
                            st.session_state.uploaded_image_bytes,
                            st.session_state.uploaded_mime,
                        )
                        st.session_state.history.insert(
                            0,
                            {
                                **result,
                                "timestamp": datetime.now(),
                                "image_bytes": st.session_state.uploaded_image_bytes,
                                "mime": st.session_state.uploaded_mime,
                            },
                        )
                        st.session_state.last_result = result
                    except json.JSONDecodeError:
                        st.error("Could not parse plant data. Try a clearer photo.")
                    except Exception as e:
                        st.error(f"Scan failed: {e}")

            # Replace uploader zone with the preview image (same slot).
            upload_slot.empty()
            b64 = base64.b64encode(st.session_state.uploaded_image_bytes).decode("utf-8")
            st.markdown(
                f"""
<div class='upload-preview'>
  <img class='upload-preview-img' src="data:{st.session_state.uploaded_mime};base64,{b64}" alt="Uploaded plant"/>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        # Already uploaded: show preview in the same slot.
        with upload_slot.container():
            b64 = base64.b64encode(st.session_state.uploaded_image_bytes).decode("utf-8")
            st.markdown(
                f"""
<div class='upload-preview'>
  <img class='upload-preview-img' src="data:{st.session_state.uploaded_mime};base64,{b64}" alt="Uploaded plant"/>
</div>
""",
                unsafe_allow_html=True,
            )

        if st.button("Upload another photo"):
            st.session_state.uploaded_image_bytes = None
            st.session_state.last_uploaded_hash = None
            st.session_state.last_result = None
            st.session_state.uploader_version += 1
            st.rerun()

    if st.session_state.last_result is not None and st.session_state.uploaded_image_bytes is not None:
        render_result(st.session_state.last_result)


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY TAB
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    history = st.session_state.history

    if st.session_state.selected_scan is not None:
        scan = st.session_state.selected_scan

        if st.button("← Back to History"):
            st.session_state.selected_scan = None
            st.rerun()

        try:
            st.image(scan["image_bytes"], width=320)
        except Exception:
            pass
        render_result(scan)

    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"""
<h2 style="font-family:'Playfair Display',serif;font-size:24px;
            font-weight:900;color:var(--moss);margin:0 0 4px 0">
  My Scans
</h2>
""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
<p style="font-family:'DM Mono',monospace;font-size:11px;
           color:var(--sage);font-weight:300;margin-top:8px;text-align:right">
  {len(history)} plants
</p>
""",
                unsafe_allow_html=True,
            )

        if not history:
            st.markdown(
                """
<div style="text-align:center;padding:48px 20px;background:var(--mist);
             border-radius:20px;border:2px dashed var(--mint)">
  <div style="font-size:48px;margin-bottom:12px;opacity:0.4">🌾</div>
  <h3 style="font-family:'Playfair Display',serif;color:var(--moss);
              font-style:italic;margin-bottom:6px">No scans yet</h3>
  <p style="font-family:'DM Mono',monospace;font-size:12px;
              color:var(--sage);font-weight:300">
    scan your first plant to see it here
  </p>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            for i, scan in enumerate(history):
                status_cls = "history-invasive" if scan.get("isInvasive") else "history-native"
                status_text = "⚠ Invasive" if scan.get("isInvasive") else "✓ Native"
                ago = time_ago(scan["timestamp"])

                col_img, col_info, col_btn = st.columns([1, 4, 1])
                with col_img:
                    try:
                        st.image(scan["image_bytes"], width=56)
                    except Exception:
                        pass

                with col_info:
                    st.markdown(
                        f"""
<div class="history-item-name">{scan.get("commonName","Unknown")}</div>
<div class="{status_cls}">{status_text}</div>
<div class="history-time">{ago}</div>
""",
                        unsafe_allow_html=True,
                    )

                with col_btn:
                    if st.button("›", key=f"hist_{i}"):
                        st.session_state.selected_scan = scan
                        st.rerun()

                st.markdown(
                    "<hr style='border:none;border-top:1px solid var(--mint);margin:6px 0'>",
                    unsafe_allow_html=True,
                )

