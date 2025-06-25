import streamlit as st
import tempfile
import os
from gtts import gTTS
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
from streamlit_mic_recorder import mic_recorder
import requests
try:
    from streamlit_lottie import st_lottie
except ImportError:
    st_lottie = None
    st.warning("streamlit-lottie is not installed. Run 'pip install streamlit-lottie' for animated icons.")
# from PIL import Image  # Not used

# --- Config Section ---
APP_NAME = "SpeakMosaic"
TAGLINE = "Your Multilingual Voice Assistant"
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"  # Example logo
SOCIAL_LINKS = "<a href='https://github.com/' target='_blank'>GitHub</a> | <a href='https://linkedin.com/' target='_blank'>LinkedIn</a>"
THEME_COLOR = "#6C63FF"

# --- Helper Functions ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def copy_to_clipboard(text):
    st.code(text, language=None)
    st.success("Copied to clipboard! (Select and copy manually)")

def show_onboarding():
    st.session_state['onboarded'] = True
    st.info("""
    **How to use SpeakMosaic:**
    1. Select or auto-detect your language (with flag!)
    2. Click the mic to record, or type text below
    3. Convert speech to text, or text to speech
    4. Download, copy, or share results
    5. Try advanced features in the main app!
    """)

# --- Custom CSS for a dark background and cleaner look ---
st.markdown(f"""
    <style>
        .main {{background-color: #fff;}}
        .block-container {{padding-top: 2rem; background-color: #fff;}}
        .stApp {{background-color: #fff;}}
        .stButton>button {{
            width: 100%;
            border-radius: 8px;
            font-size: 1.1rem;
            padding: 0.5em 0;
            background-color: {THEME_COLOR};
            color: white;
        }}
        .stTextArea textarea {{
            border-radius: 10px;
            min-height: 100px;
            font-size: 1.1rem;
            background-color: #fff;
            color: #222;
        }}
        .stAudio {{margin-top: 1em;}}
        .stDownloadButton {{margin-top: 0.5em;}}
        .stSelectbox {{margin-bottom: 1em; background-color: #fff; color: #222;}}
        .stCodeBlock {{background: #f8f9fa; border-radius: 8px; color: #222;}}
        .logo-img {{display: block; margin-left: auto; margin-right: auto; width: 60px;}}
        h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stCaption, .stText, .stSubheader, .stSidebar, .stSidebarContent, .stSidebar .sidebar-content, .stSidebar .sidebar-content *, .css-1v0mbdj, .css-1d391kg, .css-1offfwp, .css-1kyxreq, .css-1dp5vir, .css-1v3fvcr, .css-1c7y2kd, .css-1vzeuhh, .css-1vzeuhh *, .css-1c7y2kd * {{
            color: #222 !important;
        }}
        /* Sidebar background */
        section[data-testid="stSidebar"] {{
            background-color: #fff !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar: History, Theme, Onboarding ---
st.sidebar.image(LOGO_URL, width=60)
st.sidebar.title(f"🗂️ Menu")
if st.sidebar.button("How to Use?", help="Show onboarding guide"):
    show_onboarding()

# Font size adjuster
font_size = st.sidebar.slider("Font Size", 12, 32, 18)
st.markdown(f"<style>body, .stTextArea textarea, .stButton>button, .stSelectbox, .stCodeBlock {{font-size: {font_size}px !important;}}</style>", unsafe_allow_html=True)

# History (simple session state)
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'onboarded' not in st.session_state:
    st.session_state['onboarded'] = False
st.sidebar.markdown("---")
st.sidebar.subheader("🕑 Recent Activity")
for i, item in enumerate(reversed(st.session_state['history'][-5:])):
    st.sidebar.write(f"{item}")

# --- Page Setup ---
st.set_page_config(page_title=APP_NAME, layout="centered", page_icon=LOGO_URL)

# --- Welcome Section ---
st.image(LOGO_URL, width=80)
st.markdown(f"<h1 style='text-align:center; color:{THEME_COLOR};'>{APP_NAME}</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align:center; color:#444;'>{TAGLINE}</h3>", unsafe_allow_html=True)
if not st.session_state['onboarded']:
    show_onboarding()
st.markdown("---")

# --- Language Selection without Flags or Globe Symbols ---
LANGUAGES_DISPLAY = {name.title(): code for code, name in LANGUAGES.items()}
language_names = sorted(LANGUAGES_DISPLAY.keys())
col_lang, col_switch = st.columns([4, 1])
with col_lang:
    selected_language = st.selectbox(
        "🌐 Choose a language",
        language_names,  # Only show language names, no flags or globe
        index=language_names.index("English"),
        help="Select the language for recognition and speech."
    )
    lang_code = LANGUAGES_DISPLAY[selected_language]
with col_switch:
    if st.button("🔄 Swap", help="Quick switch to previous language"):
        if 'last_lang' in st.session_state:
            lang_code, st.session_state['last_lang'] = st.session_state['last_lang'], lang_code
    st.session_state['last_lang'] = lang_code

auto_detect = st.checkbox("Auto-detect language (for speech)", value=False, help="Let the app auto-detect spoken language.")

# --- Speak Now Section ---
st.subheader("🎤 Speak Now")
audio_bytes = mic_recorder(start_prompt="🎙️ Start Recording", stop_prompt="⏹️ Stop Recording", key="recorder")

text = ""
if audio_bytes:
    audio_data_bytes = None
    if isinstance(audio_bytes, dict) and 'audio' in audio_bytes and isinstance(audio_bytes['audio'], bytes):
        audio_data_bytes = audio_bytes['audio']
    elif isinstance(audio_bytes, bytes):
        audio_data_bytes = audio_bytes
    else:
        st.error("Unsupported audio format from mic_recorder. Please update the component or check your browser.")
    if audio_data_bytes:
        st.audio(audio_data_bytes, format="audio/wav")
        recognizer = sr.Recognizer()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data_bytes)
            tmp_path = tmp.name
        with st.spinner("Transcribing audio..."):
            try:
                with sr.AudioFile(tmp_path) as source:
                    audio_data = recognizer.record(source)
                    recog_lang = None
                    if auto_detect:
                        recog_lang = "en-US"  # Default fallback
                        text = recognizer.recognize_google(audio_data)  # type: ignore[attr-defined]  # Auto-detect
                    else:
                        recog_lang = lang_code
                        text = recognizer.recognize_google(audio_data, language=lang_code)  # type: ignore[attr-defined]
                    st.success("📝 Recognized Text:")
                    st.write(f"<div style='background:#e9ecef;padding:10px;border-radius:8px'>{text}</div>", unsafe_allow_html=True)
                    st.session_state['history'].append(f"🗣️ {text}")
                    if st.button("📋 Copy Text", help="Copy recognized text to clipboard"):
                        copy_to_clipboard(text)
            except Exception as e:
                st.error(f"❌ Could not recognize speech: {e}")
                text = ""
        os.remove(tmp_path)

st.markdown("---")

# --- Text to Voice Section ---
st.subheader("🗣️ Convert Text to Speech")
user_input = st.text_area("✍️ Enter text here to speak:", value=text, placeholder="Type or paste your text here...", help="Enter text to convert to speech.")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    speak_btn = st.button("🔊 Speak", use_container_width=True, help="Convert text to speech.")
with col2:
    clear_btn = st.button("🧹 Clear", use_container_width=True, help="Clear the text area.")
with col3:
    summarize_btn = st.button("📝 Summarize", use_container_width=True, help="Summarize the text (coming soon).")

if clear_btn:
    user_input = ""
    st.experimental_rerun()

if speak_btn:
    if user_input:
        translator = Translator()
        with st.spinner("Translating and generating speech..."):
            translated = translator.translate(user_input, dest=lang_code).text
            st.markdown(f"<div style='background:#23272F;padding:10px;border-radius:8px;color:#fff'>**Translated Text:** {translated}</div>", unsafe_allow_html=True)
            if st.button("📋 Copy Translation", help="Copy translated text to clipboard"):
                copy_to_clipboard(translated)
            try:
                tts = gTTS(translated, lang=lang_code)
                tts.save("output.mp3")
                st.audio("output.mp3", format="audio/mp3")
                with open("output.mp3", "rb") as f:
                    st.download_button("⬇️ Download Audio", f, file_name="speech.mp3")
                st.session_state['history'].append(f"🔊 {translated}")
            except Exception as e:
                st.error(f"TTS Error: {e}")
    else:
        st.warning("Please enter or record some text first.")

if summarize_btn:
    if user_input:
        st.info("(Summarization feature coming soon! Connect to an LLM API like OpenAI or HuggingFace for this.)")
    else:
        st.warning("Please enter or record some text first.")

# --- Recent Activity at Bottom ---
st.markdown("---")
st.subheader("🕑 Recent Activity")
for i, item in enumerate(reversed(st.session_state['history'][-5:])):
    st.write(f"{item}")

# --- Footer ---
st.markdown("---")
st.markdown(f"<div style='text-align:center;'>{SOCIAL_LINKS}</div>", unsafe_allow_html=True)
st.caption("Made with ❤️ using Streamlit | © 2025 TarunSailesh | Enhanced by AI")

