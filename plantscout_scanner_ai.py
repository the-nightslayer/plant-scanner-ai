import streamlit as st
import base64
import os
import json
from datetime import datetime
from groq import Groq
from io import BytesIO
from PIL import Image

# Configuration and Constants
HISTORY_FILE = "plant_history.json"
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

# Initialize Groq Client
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
if not GROQ_API_KEY:
    st.error("Please set GROQ_API_KEY in .streamlit/secrets.toml or as an environment variable.")
    st.stop()
client = Groq(api_key=GROQ_API_KEY)

# Page Config
st.set_page_config(
    page_title="LeafLens AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    """Injects premium aesthetics using CSS and forces Streamlit's white bars to disappear."""
    st.markdown("""
    <style>
    /* Gradient Background that looks premium and natural */
    .stApp, .stApp > header {
        background: linear-gradient(135deg, #dcedc8 0%, #a5d6a7 50%, #81c784 100%) !important;
        background-attachment: fixed !important;
        color: #1b5e20;
    }

    /* Completely nuke all possible Streamlit default headers, toolbars, and white decoration lines */
    header, 
    [data-testid="stHeader"], 
    .stAppHeader, 
    [data-testid="stToolbar"],
    .stToolbar,
    div[data-testid="stDecoration"] {
        display: none !important;
        height: 0px !important;
        visibility: hidden !important;
        background: transparent !important;
        opacity: 0 !important;
    }

    /* Zero out all top spacing so there's absolutely no white margin */
    #root > div:nth-child(1) {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Reduce top padding from the main container */
    .block-container {
        padding-top: 1rem !important;
        margin-top: 0 !important;
        padding-bottom: 2rem !important;
    }

    /* Main Typography */
    h1, h2, h3, p {
        color: #1b5e20 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Glassmorphism Design for Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.15);
    }
    
    .glass-card h3 {
        margin-top: 0;
        border-bottom: 2px solid #66bb6a;
        padding-bottom: 10px;
        margin-bottom: 15px;
        color: #2e7d32 !important;
    }

    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 20px;
        padding: 25px;
        border: 2px dashed #4caf50;
        transition: border-color 0.3s ease;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #1b5e20;
    }
    
    /* Uploaded Image Radius */
    img {
        border-radius: 15px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    /* Beautiful Button */
    .stButton > button {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%) !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 12px 25px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.4) !important;
        width: 100%;
        margin-top: 15px;
    }
    .stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(27, 94, 32, 0.6) !important;
    }

    /* Sidebar aesthetics */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.7) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    /* Expander style inside Sidebar */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.5);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.8);
    }

    /* -------------------------------------------------------------------------- */
    /* ANIMATIONS */
    /* -------------------------------------------------------------------------- */
    
    /* Falling Leaves Animation */
    @keyframes fall {
        0% { transform: translateY(-10vh) translateX(-20px) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) translateX(50px) rotate(360deg); opacity: 0; }
    }
    @keyframes fall-reverse {
        0% { transform: translateY(-10vh) translateX(20px) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) translateX(-50px) rotate(-360deg); opacity: 0; }
    }
    .leaf-container {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; z-index: 0; overflow: hidden;
    }
    .leaf {
        position: absolute;
        top: -10%;
        font-size: 28px;
        opacity: 0; /* start hidden until animation overrides */
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));
    }

    /* Water Spray Animation */
    @keyframes water-burst {
        0% { transform: translate(0, 0) scale(0.5); opacity: 1; filter: drop-shadow(0 0 5px rgba(64,196,255,0.8)); }
        70% { opacity: 1; }
        100% { transform: translate(var(--tx), var(--ty)) scale(1.5) rotate(var(--rot)); opacity: 0; filter: drop-shadow(0 0 20px rgba(64,196,255,0)); }
    }
    .water-droplet {
        position: absolute;
        bottom: 20px; /* position relative to button */
        left: 50%;
        margin-left: -15px; 
        animation: water-burst 1.5s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        pointer-events: none;
        z-index: 9999;
    }
    </style>
    """, unsafe_allow_html=True)

    # Inject leaves globally
    st.markdown("""
    <div class="leaf-container">
        <div class="leaf" style="left: 10%; animation: fall 12s linear infinite; animation-delay: 0s;">🍃</div>
        <div class="leaf" style="left: 25%; animation: fall-reverse 15s linear infinite; animation-delay: 2s;">🌿</div>
        <div class="leaf" style="left: 45%; animation: fall 14s linear infinite; animation-delay: 5s;">🌱</div>
        <div class="leaf" style="left: 65%; animation: fall-reverse 11s linear infinite; animation-delay: 1s;">🍃</div>
        <div class="leaf" style="left: 85%; animation: fall 16s linear infinite; animation-delay: 3s;">🌿</div>
        <div class="leaf" style="left: 95%; animation: fall-reverse 13s linear infinite; animation-delay: 6s;">🌱</div>
        <div class="leaf" style="left: 5%; animation: fall 10s linear infinite; animation-delay: 7s;">🍃</div>
        <div class="leaf" style="left: 55%; animation: fall-reverse 18s linear infinite; animation-delay: 4s;">🌿</div>
    </div>
    """, unsafe_allow_html=True)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_history(plant_data):
    history = load_history()
    history.insert(0, plant_data)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def encode_image(image_bytes):
    """
    Optimizes and downscales the image to prevent API payload limits.
    Returns base64 string.
    """
    img = Image.open(BytesIO(image_bytes))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
        
    # Max dimensions for Groq vision reasoning
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_plant(base64_image):
    prompt = """
    Analyze this plant image and provide a JSON response EXACTLY with these keys. Do not return any markdown codeblocks or text outside the JSON. Return valid JSON only:
    {
        "name": "Common name of the plant",
        "health_status": "Is it healthy? If not, what is wrong? Provide specific details.",
        "maintenance": "How to maintain it (water, light, soil).",
        "garden_suitability": "Is it good for a typical garden or indoors? Why?",
        "bee_impact": "How does it impact bees and pollinators?"
    }
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        if content.startswith("```json"):
            content = content.replace("```json", "", 1).replace("```", "")
        return json.loads(content)
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None

def main():
    inject_custom_css()
    
    # Beautiful Header
    st.markdown("<h1 style='text-align: center; font-size: 3.5em; padding-top: 10px;'>🌿 LeafLens AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.3em; margin-bottom: 40px;'>Upload a photo of your plant to instantly uncover its secrets and health status.</p>", unsafe_allow_html=True)

    # Sidebar for History
    st.sidebar.markdown("<h2>📚 Botanical Journal</h2>", unsafe_allow_html=True)
    search_query = st.sidebar.text_input("Search history...", "")
    history = load_history()
    
    filtered_history = [
        item for item in history 
        if 'name' in item and search_query.lower() in item['name'].lower()
    ]

    for item in filtered_history:
        if 'name' in item:
            with st.sidebar.expander(f"🍃 {item.get('name', 'Unknown')} ({item.get('date', '')})"):
                st.write(f"**Health:** {item.get('health_status', 'N/A')}")
                st.write(f"**Bees:** {item.get('bee_impact', 'N/A')}")

    # Main Layout
    col1, padding, col2 = st.columns([1.2, 0.1, 1.7])

    with col1:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 15px; margin-bottom: 25px;'>
            <h3 style='border-bottom: none; margin-bottom: 0px;'>📸 Capture & Discover</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Session state for managing the uploaded file to replace the widget UX
        if 'plant_image_bytes' not in st.session_state:
            st.session_state.plant_image_bytes = None
            st.session_state.plant_image_name = ""
            
        if st.session_state.plant_image_bytes is None:
            uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "webp"])
            if uploaded_file is not None:
                st.session_state.plant_image_bytes = uploaded_file.getvalue()
                st.session_state.plant_image_name = uploaded_file.name
                st.rerun() # Refresh to hide uploader and show image
        else:
            # Display image in place of the uploader
            st.image(st.session_state.plant_image_bytes, caption=st.session_state.plant_image_name, use_container_width=True)
            
            # Action Buttons
            if st.button("✨ Identify & Analyze Plant"):
                with st.spinner("🌿 Consulting the botanical AI..."):
                    base64_img = encode_image(st.session_state.plant_image_bytes)
                    result = analyze_plant(base64_img)
                    
                    if result:
                        result['date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_to_history(result)
                        st.session_state['last_result'] = result
                        
                        # Spray water effect immediately after analyzing
                        st.markdown("""
                            <div style="position: relative; width: 100%; height: 0; display: flex; justify-content: center;">
                                <div class="water-droplet" style="--tx: -120px; --ty: -180px; --rot: -45deg; font-size: 35px;">💦</div>
                                <div class="water-droplet" style="--tx: 120px; --ty: -160px; --rot: 45deg; font-size: 30px;">💧</div>
                                <div class="water-droplet" style="--tx: 0px; --ty: -220px; --rot: 0deg; font-size: 40px;">💦</div>
                                <div class="water-droplet" style="--tx: -70px; --ty: -140px; --rot: -20deg; font-size: 25px;">💧</div>
                                <div class="water-droplet" style="--tx: 70px; --ty: -150px; --rot: 20deg; font-size: 28px;">💦</div>
                                <div class="water-droplet" style="--tx: -40px; --ty: -200px; --rot: -10deg; font-size: 32px;">💧</div>
                                <div class="water-droplet" style="--tx: 40px; --ty: -210px; --rot: 10deg; font-size: 38px;">💦</div>
                                <div class="water-droplet" style="--tx: -160px; --ty: -100px; --rot: -60deg; font-size: 24px;">💧</div>
                                <div class="water-droplet" style="--tx: 160px; --ty: -110px; --rot: 60deg; font-size: 26px;">💦</div>
                            </div>
                        """, unsafe_allow_html=True)
            
            # Button to clear the image and bring the uploader back
            if st.button("🔄 Choose Different Photo"):
                st.session_state.plant_image_bytes = None
                st.session_state.plant_image_name = ""
                if 'last_result' in st.session_state:
                    del st.session_state['last_result']
                st.rerun()

    with col2:
        if 'last_result' in st.session_state:
            res = st.session_state['last_result']
            st.markdown(f"<h2 style='margin-top: 0;'>🌿 Analysis: {res.get('name', 'Unknown Plant')}</h2>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="glass-card">
                <h3>🩺 Health & Maintenance</h3>
                <p><strong>Status:</strong> {res.get('health_status', 'N/A')}</p>
                <p><strong>Care Routine:</strong> {res.get('maintenance', 'N/A')}</p>
            </div>
            
            <div class="glass-card">
                <h3>🏡 Garden Suitability</h3>
                <p>{res.get('garden_suitability', 'N/A')}</p>
            </div>
            
            <div class="glass-card">
                <h3>🐝 Environmental Impact</h3>
                <p>{res.get('bee_impact', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 60px 20px;">
                <h3 style="border: none; margin-bottom: 20px; font-size: 1.8em;">Awaiting a Plant...</h3>
                <p style="font-size: 1.2em; color: #388e3c;">Upload a photo on the left, and I will reveal everything about its health, care instructions, and impact on our environment!</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
