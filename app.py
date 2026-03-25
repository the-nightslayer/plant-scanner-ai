import streamlit as st
import base64
import json
import os
import hashlib
from datetime import datetime
from groq import Groq
from PIL import Image
import io

# ============================================
# GROQ API KEY
# Set in Streamlit Secrets (`.streamlit/secrets.toml`) or env var `GROQ_API_KEY`.
# ============================================
GROQ_API_KEY = None
try:
    # Streamlit secrets are available when running inside Streamlit.
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")  # type: ignore[attr-defined]
except Exception:
    GROQ_API_KEY = None

if not GROQ_API_KEY:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Fallback: load from local `.env` file (so you don't have to paste the key manually)
# Supports either:
#   - GROQ_API_KEY="...."
#   - raw value on the first non-empty line (common in simple one-line .env files)
if not GROQ_API_KEY:
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
                        GROQ_API_KEY = v.strip().strip("'").strip('"')
                        break
                else:
                    # If the .env is just the raw key value
                    GROQ_API_KEY = ln.strip().strip("'").strip('"')
                    break
    except Exception:
        GROQ_API_KEY = None

if not GROQ_API_KEY:
    st.warning(
        "Missing `GROQ_API_KEY`. The app UI will still load, but plant analysis is disabled until you set it in "
        "Streamlit secrets (`.streamlit/secrets.toml`) or the `GROQ_API_KEY` environment variable."
    )
    client = None
else:
    # Initialize Groq client
    client = Groq(api_key=GROQ_API_KEY)

# Page configuration
st.set_page_config(
    page_title="Plant Scanner AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #2d5a27;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5a8f53;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background: linear-gradient(135deg, #f0f9f0 0%, #e8f5e8 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid #2d5a27;
        margin: 1rem 0;
    }
    .bee-badge {
        background: #fef3c7;
        color: #92400e;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        display: inline-block;
        font-weight: 600;
    }
    .garden-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        display: inline-block;
        font-weight: 600;
    }
    .history-item {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background-color: #2d5a27;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1e3d1a;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for history
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []

if 'show_history' not in st.session_state:
    st.session_state.show_history = False

if 'last_uploaded_hash' not in st.session_state:
    st.session_state.last_uploaded_hash = None

if 'latest_result' not in st.session_state:
    st.session_state.latest_result = None


def encode_image_to_base64(image_file):
    """Convert uploaded image to base64 string."""
    return base64.standard_b64encode(image_file.getvalue()).decode("utf-8")


def analyze_plant(image_base64, image_type="image/jpeg"):
    """Analyze the plant image using Groq's vision model."""
    if client is None:
        st.error("Groq API key not configured. Set `GROQ_API_KEY` to enable analysis.")
        return None
    
    prompt = """You are an expert botanist and garden specialist. Analyze this plant image and provide detailed information in the following JSON format:

{
    "plant_name": "Common name of the plant",
    "scientific_name": "Scientific/Latin name",
    "plant_type": "Type (flower, shrub, tree, herb, vegetable, etc.)",
    "bee_friendly": {
        "is_good_for_bees": true/false,
        "bee_rating": "Excellent/Good/Moderate/Poor",
        "explanation": "Why this plant is good or bad for bees"
    },
    "garden_suitability": {
        "is_good_for_garden": true/false,
        "garden_rating": "Excellent/Good/Moderate/Poor",
        "benefits": ["list of garden benefits"],
        "considerations": ["any concerns or considerations"]
    },
    "maintenance": {
        "difficulty": "Easy/Moderate/Difficult",
        "watering": "Watering requirements and frequency",
        "sunlight": "Sunlight requirements",
        "soil": "Preferred soil type",
        "pruning": "Pruning advice",
        "fertilizing": "Fertilizing recommendations",
        "seasonal_care": "Season-specific care tips",
        "common_problems": ["Common issues and how to prevent them"],
        "tips": ["Additional maintenance tips"]
    },
    "interesting_facts": ["2-3 interesting facts about this plant"]
}

Be thorough and helpful. If you cannot identify the plant with certainty, provide your best assessment and note any uncertainty."""

    try:
        response = client.chat.completions.create(
            # Use Groq's current supported vision model.
            # (Older `llama-*-vision-preview` models may get decommissioned.)
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_completion_tokens=2000,
            # Ask for strict JSON output (more reliable than trying to extract braces).
            response_format={"type": "json_object"},
        )
        
        response_text = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # First try strict parse (JSON mode usually returns a pure JSON object).
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: find JSON bounds in case the model returned extra text.
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        
        # If JSON parsing fails, return a structured response
        return {
            "plant_name": "Unknown Plant",
            "scientific_name": "Not identified",
            "plant_type": "Unknown",
            "raw_response": response_text,
            "bee_friendly": {"is_good_for_bees": None, "bee_rating": "Unknown", "explanation": "Could not parse response"},
            "garden_suitability": {"is_good_for_garden": None, "garden_rating": "Unknown", "benefits": [], "considerations": []},
            "maintenance": {
                "difficulty": "Unknown",
                "watering": "Not specified",
                "sunlight": "Not specified",
                "soil": "Not specified",
                "pruning": "Not specified",
                "fertilizing": "Not specified",
                "seasonal_care": "Not specified",
                "common_problems": [],
                "tips": [],
            },
            "interesting_facts": []
        }
        
    except Exception as e:
        st.error(f"Error analyzing plant: {str(e)}")
        return None


def save_to_history(image_data, result):
    """Save scan result to history."""
    history_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image": image_data,
        "result": result
    }
    st.session_state.scan_history.insert(0, history_entry)
    # Keep only last 20 entries
    st.session_state.scan_history = st.session_state.scan_history[:20]


def display_result(result):
    """Display the analysis result in a simple, user-focused format."""
    if not result:
        return
    
    # Plant Name Header
    st.markdown(f"## 🌱 {result.get('plant_name', 'Unknown Plant')}")
    st.markdown(f"*{result.get('scientific_name', 'Scientific name not available')}*")
    st.markdown(f"**Type:** {result.get('plant_type', 'Unknown')}")
    
    st.divider()
    
    # Bee Friendly Section
    bee_info = result.get('bee_friendly', {})
    st.markdown("### 🐝 Is it good for bees?")
    if bee_info.get('is_good_for_bees'):
        st.success(f"**Yes** ({bee_info.get('bee_rating', 'Unknown')})")
    elif bee_info.get('is_good_for_bees') is False:
        st.warning(f"**Not really** ({bee_info.get('bee_rating', 'Unknown')})")
    else:
        st.info(f"**Unknown** ({bee_info.get('bee_rating', 'Unknown')})")
    st.write(bee_info.get('explanation', 'No information available'))
    
    # Maintenance Section
    st.markdown("### 🛠️ How to maintain it")
    maintenance = result.get('maintenance', {})

    st.markdown(f"**💪 Difficulty:** {maintenance.get('difficulty', 'Unknown')}")
    st.markdown(f"**💧 Watering:** {maintenance.get('watering', 'Not specified')}")
    st.markdown(f"**☀️ Sunlight:** {maintenance.get('sunlight', 'Not specified')}")
    st.markdown(f"**🌍 Soil:** {maintenance.get('soil', 'Not specified')}")
    st.markdown(f"**✂️ Pruning:** {maintenance.get('pruning', 'Not specified')}")
    st.markdown(f"**🧪 Fertilizing:** {maintenance.get('fertilizing', 'Not specified')}")
    st.markdown(f"**🗓️ Seasonal Care:** {maintenance.get('seasonal_care', 'Not specified')}")

    problems = maintenance.get('common_problems', [])
    if problems:
        st.markdown("**⚠️ Common Problems:**")
        for problem in problems:
            st.markdown(f"- {problem}")

    tips = maintenance.get('tips', [])
    if tips:
        st.markdown("**💡 Tips:**")
        for tip in tips:
            st.markdown(f"- {tip}")


def display_history():
    """Display the scan history."""
    st.markdown("## 📜 Scan History")
    
    if not st.session_state.scan_history:
        st.info("No scans yet! Upload a plant image to get started.")
        return
    
    for i, entry in enumerate(st.session_state.scan_history):
        with st.expander(f"🌿 {entry['result'].get('plant_name', 'Unknown')} - {entry['timestamp']}", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display thumbnail
                try:
                    image_bytes = base64.b64decode(entry['image'])
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, width=160)
                except:
                    st.write("Image not available")
            
            with col2:
                result = entry['result']
                st.markdown(f"**Scientific Name:** {result.get('scientific_name', 'Unknown')}")
                
                bee_info = result.get('bee_friendly', {})
                garden_info = result.get('garden_suitability', {})
                
                st.markdown(f"**🐝 Bee Rating:** {bee_info.get('bee_rating', 'Unknown')}")
                st.markdown(f"**🏡 Garden Rating:** {garden_info.get('garden_rating', 'Unknown')}")
                
                maintenance = result.get('maintenance', {})
                st.markdown(f"**Care Difficulty:** {maintenance.get('difficulty', 'Unknown')}")
            
            if st.button(f"View Full Details", key=f"view_{i}"):
                st.session_state.selected_history = i
                st.session_state.show_history = False
                st.rerun()


# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🌿 Plant Scanner AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Powered by Groq AI - Identify plants, check bee friendliness, and get care tips!</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🌱 Navigation")
        
        if st.button("🔍 New Scan", use_container_width=True):
            st.session_state.show_history = False
            st.session_state.latest_result = None
            st.session_state.last_uploaded_hash = None
            if 'selected_history' in st.session_state:
                del st.session_state.selected_history
            st.rerun()
        
        if st.button("📜 View History", use_container_width=True):
            st.session_state.show_history = True
            st.rerun()
        
        st.divider()
        
        st.markdown("### 📊 Stats")
        st.metric("Total Scans", len(st.session_state.scan_history))
        
        bee_friendly_count = sum(1 for entry in st.session_state.scan_history 
                                  if entry['result'].get('bee_friendly', {}).get('is_good_for_bees'))
        st.metric("Bee-Friendly Plants Found", bee_friendly_count)
        
        st.divider()
        
        st.markdown("### ℹ️ About")
        st.markdown("""
        This app uses AI to:
        - 🌱 Identify plants from photos
        - 🐝 Check if they're good for bees
        - 🏡 Evaluate garden suitability
        - 🛠️ Provide care instructions
        """)
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.scan_history = []
            st.success("History cleared!")
            st.rerun()
    
    # Main Content
    if st.session_state.show_history:
        display_history()
    elif 'selected_history' in st.session_state:
        # Show selected history item
        entry = st.session_state.scan_history[st.session_state.selected_history]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            try:
                image_bytes = base64.b64decode(entry['image'])
                image = Image.open(io.BytesIO(image_bytes))
                st.image(image, caption="Scanned Plant", width=240)
            except:
                st.write("Image not available")
        
        with col2:
            st.markdown(f"**Scanned on:** {entry['timestamp']}")
        
        display_result(entry['result'])
        
        if st.button("← Back to Scanner"):
            del st.session_state.selected_history
            st.rerun()
    else:
        # Scanner View
        st.markdown("### 📸 Upload a Plant Image")

        uploaded_file = st.file_uploader(
            "Upload a plant photo",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=False,
            label_visibility="collapsed",
            help="Click the white upload area to add a plant photo"
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            # Preview
            try:
                image = Image.open(io.BytesIO(file_bytes))
                st.image(image, caption="Uploaded Plant", width=240)
            except Exception:
                st.write("Uploaded image preview not available.")

            # Auto-scan as soon as a new image is uploaded
            if st.session_state.last_uploaded_hash != file_hash:
                st.session_state.latest_result = None

                # Get image type for the data URL
                if uploaded_file.type and '/' in uploaded_file.type:
                    ext = uploaded_file.type.split('/')[-1]
                    image_type = f"image/{ext}"
                else:
                    image_type = "image/jpeg"

                with st.spinner("🌿 Analyzing plant... This may take a moment..."):
                    image_base64 = encode_image_to_base64(uploaded_file)
                    result = analyze_plant(image_base64, image_type)
                    if result:
                        save_to_history(image_base64, result)
                        st.session_state.last_uploaded_hash = file_hash
                        st.session_state.latest_result = result
                        st.success("✅ Scan complete!")
                    else:
                        st.session_state.latest_result = None

            if st.session_state.latest_result is not None:
                st.divider()
                st.markdown("### 🧾 Scan Result")
                display_result(st.session_state.latest_result)
        else:
            st.markdown("""
            ### 📋 Tips for Best Results
            - 📸 Take a clear, well-lit photo
            - 🎯 Focus on the plant's leaves and flowers
            - 🔍 Get close enough to see details
            - 🌤️ Natural lighting works best
            - 📐 Include the whole plant if possible
            """)


if __name__ == "__main__":
    main()
