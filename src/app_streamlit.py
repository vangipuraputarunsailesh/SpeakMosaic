# SpeakMosaic: Multilingual Voice Assistant Web App
# This app lets users convert speech to text, text to speech, and translate between languages.
# It uses Streamlit for the UI, Google APIs for speech/translation, and supports live mic recording with st_audiorec.

import streamlit as st
import tempfile
import os
from gtts import gTTS
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
import requests
import time
from st_audiorec import st_audiorec  # For live audio recording
from google.cloud import texttospeech

# --- Visitor Counter (for demo/analytics) ---
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0
st.session_state['counter'] += 1

# --- App Configuration ---
APP_NAME = "SpeakMosaic"
TAGLINE = " Multilingual Voice Assistant"
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"  # Example logo
SOCIAL_LINKS = "<a href='https://github.com/' target='_blank'>GitHub</a> | <a href='https://linkedin.com/' target='_blank'>LinkedIn</a>"
THEME_COLOR = "#6C63FF"

# --- Helper Functions ---
def copy_to_clipboard(text):
    st.code(text, language=None)
    st.success("Copied to clipboard! (Select and copy manually)")

# --- Professional CSS Styling ---
st.markdown('''
    <link href="https://fonts.googleapis.com/css?family=Inter:400,700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4 { font-weight: 700; }
        .main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;}
        .block-container {background: rgba(255,255,255,0.97); border-radius: 20px; padding: 2rem; margin: 1rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1);}
        .header-container {text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #6C63FF, #8B5CF6); border-radius: 15px; margin-bottom: 2rem; color: white;}
        .section-card {box-shadow:0 4px 24px rgba(0,0,0,0.08); border-radius:18px; padding:2rem; margin-bottom:2.5rem; background:white;}
        .stButton > button {background: linear-gradient(135deg, #6C63FF, #8B5CF6); color: white; border: none; border-radius: 10px; padding: 0.75rem 2rem; font-weight: 600; transition: background 0.3s, transform 0.2s; box-shadow: 0 4px 15px rgba(108,99,255,0.3);}
        .stButton > button:hover {transform: scale(1.04); box-shadow: 0 6px 20px rgba(108,99,255,0.4);}
        .stTextArea textarea {border-radius: 10px; border: 2px solid #e1e5e9; padding: 1rem; font-size: 1rem; transition: border-color 0.3s ease;}
        .stTextArea textarea:focus {border-color: #6C63FF; box-shadow: 0 0 0 3px rgba(108,99,255,0.1);}
        .stSelectbox {border-radius: 10px;}
        .info-box {background: linear-gradient(135deg, #E3F2FD, #BBDEFB); border-left: 4px solid #2196F3; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
        .success-box {background: linear-gradient(135deg, #E8F5E8, #C8E6C9); border-left: 4px solid #4CAF50; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
        .feature-card {background: white; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid #e1e5e9;}
        .darkmode-toggle {position: fixed; top: 1.5rem; right: 2.5rem; z-index: 999;}
        @media (max-width: 768px) {.block-container {margin: 0.5rem; padding: 1rem;}}
    </style>
''', unsafe_allow_html=True)

# --- Sidebar: Professional Navigation ---
st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <img src="{LOGO_URL}" width="60" style="border-radius: 50%;">
        <h3 style="color: {THEME_COLOR}; margin: 1rem 0;">{APP_NAME}</h3>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
font_size = st.sidebar.slider("📏 Font Size", 12, 32, 18)
st.markdown(f"<style>body, .stTextArea textarea, .stButton>button, .stSelectbox {{font-size: {font_size}px !important;}}</style>", unsafe_allow_html=True)
if 'history' not in st.session_state:
    st.session_state['history'] = []
st.sidebar.markdown("### 📋 Recent Activity")
for i, item in enumerate(reversed(st.session_state['history'][-5:])):
    st.sidebar.markdown(f"• {item}")

# --- Main Page Setup ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon=LOGO_URL)

# Dark mode toggle
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False
with st.sidebar:
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
    dark_mode_toggle = st.checkbox("🌙 Dark Mode", value=st.session_state['dark_mode'])
    st.session_state['dark_mode'] = dark_mode_toggle
if st.session_state['dark_mode']:
    st.markdown('''<style>body, .block-container, .section-card {background: #23272f !important; color: #f3f3f3 !important;} .stTextArea textarea, .stSelectbox, .stButton > button {background: #23272f !important; color: #f3f3f3 !important;}</style>''', unsafe_allow_html=True)

# --- Main Page Setup ---
st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" width="80" style="border-radius: 50%; margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 3rem; font-weight: 700;">{APP_NAME}</h1>
        <h3 style="margin: 0.5rem 0; opacity: 0.9;">{TAGLINE}</h3>
        <p style="margin: 0; opacity: 0.8;">Transform your voice into text and text into voice across multiple languages</p>
    </div>
""", unsafe_allow_html=True)

# --- Language Selection ---
st.markdown("""
    <div class="section-container">
        <h2 style="color: #333; margin-bottom: 1rem;">🌐 Language Settings</h2>
        <p style="color: #666; margin-bottom: 1rem;">Choose your preferred language for both voice recognition and text-to-speech conversion</p>
    </div>
""", unsafe_allow_html=True)
LANGUAGES_DISPLAY = {name.title(): code for code, name in LANGUAGES.items()}
language_names = sorted(LANGUAGES_DISPLAY.keys())
col_lang, col_switch, col_auto = st.columns([3, 1, 2])
with col_lang:
    selected_language = st.selectbox(
        "**Select Language**",
        language_names,
        index=language_names.index("English"),
        help="Choose the language for recognition and speech synthesis"
    )
    lang_code = LANGUAGES_DISPLAY[selected_language]
with col_switch:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Swap", help="Quick switch to previous language"):
        if 'last_lang' in st.session_state:
            lang_code, st.session_state['last_lang'] = st.session_state['last_lang'], lang_code
    st.session_state['last_lang'] = lang_code
with col_auto:
    st.markdown("<br>", unsafe_allow_html=True)
    auto_detect = st.checkbox("Auto-detect speech language", value=False, help="Let the app automatically detect the language you're speaking")
st.session_state['selected_language'] = selected_language
st.session_state['lang_code'] = lang_code

# --- TEXT TO VOICE SECTION ---
st.markdown('''<div class="section-card">''', unsafe_allow_html=True)
st.markdown("""
    <div class="section-container">
        <h2 style="color: #333; margin-bottom: 1rem;">🔊 Text to Voice Conversion <span title='Convert your text to speech in any language.' style='cursor:help;'>ℹ️</span></h2>
        <div class="info-box">
            <strong>How it works:</strong> Type or paste your text below, select your target language, and click "Convert to Speech" to hear it spoken aloud. The app will automatically translate your text if needed.
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Voice Gender Selection ---
st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h4 style="margin-bottom: 0.5rem; color: #333;">🗣️ Voice Gender</h4>
        <p style="margin-bottom: 0.5rem; color: #666;">Choose the gender of the voice for speech synthesis:</p>
    </div>
""", unsafe_allow_html=True)
voice_gender = st.radio(
    "",
    ("👩 Female", "👨 Male"),
    index=0,
    horizontal=True,
    help="Select the gender of the voice for speech synthesis"
)
if "Female" in voice_gender:
    gender_enum = texttospeech.SsmlVoiceGender.FEMALE
else:
    gender_enum = texttospeech.SsmlVoiceGender.MALE

# --- TEXT TO VOICE STATE MANAGEMENT ---
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

# --- TEXT TO VOICE BUTTONS (CLEAR LOGIC FIRST) ---
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    speak_btn = st.button("🎵 Convert to Speech", use_container_width=True, help="Convert your text to speech in the selected language")
with col2:
    clear_btn = st.button("🧹 Clear", use_container_width=True, help="Clear the text area")
with col3:
    copy_btn = st.button("📋 Copy", use_container_width=True, help="Copy the text to clipboard")
with col4:
    summarize_btn = st.button("📝 Summarize", use_container_width=True, help="Summarize the text (coming soon)")

if clear_btn:
    st.session_state['user_input'] = ""
    st.rerun()

user_input = st.text_area(
    "**Enter your text here:**",
    value=st.session_state['user_input'],
    key="user_input",
    placeholder="Type or paste the text you want to convert to speech...",
    help="Enter any text you want to hear spoken aloud",
    height=150
)
# --- Live Character Count ---
user_input_str = user_input if user_input is not None else ""
st.markdown(f"<small style='color:#888;'>{len(user_input_str)} characters</small>", unsafe_allow_html=True)

if copy_btn and st.session_state['user_input']:
    copy_to_clipboard(st.session_state['user_input'])

if speak_btn:
    if st.session_state['user_input']:
        try:
            translator = Translator()
            with st.spinner("🔄 Translating and generating speech..."):
                translated = translator.translate(st.session_state['user_input'], dest=st.session_state['lang_code']).text
                st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ Translation Complete!</strong><br>
                        <strong>Original:</strong> {st.session_state['user_input']}<br>
                        <strong>Translated:</strong> {translated}
                    </div>
                """, unsafe_allow_html=True)
                if st.button("📋 Copy Translation", help="Copy translated text to clipboard"):
                    copy_to_clipboard(translated)
                try:
                    # --- Google Cloud TTS Integration ---
                    client = texttospeech.TextToSpeechClient()
                    synthesis_input = texttospeech.SynthesisInput(text=translated)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code=st.session_state['lang_code'],
                        ssml_gender=gender_enum
                    )
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3
                    )
                    response = client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    with open("output.mp3", "wb") as out:
                        out.write(response.audio_content)
                    st.markdown("### 🎧 Listen to Your Text")
                    st.audio("output.mp3", format="audio/mp3")
                    with open("output.mp3", "rb") as f:
                        st.download_button(
                            "⬇️ Download Audio File",
                            f,
                            file_name=f"speech_{st.session_state['lang_code']}.mp3",
                            help="Download the generated audio file"
                        )
                    st.session_state['history'].append(f"🔊 Generated speech: {translated[:50]}...")
                except Exception as e:
                    st.error(f"❌ Speech generation failed: {e}")
        except Exception as e:
            st.error(f"❌ Translation failed: {e}")
    else:
        st.warning("⚠️ Please enter some text first!")

if summarize_btn:
    if st.session_state['user_input']:
        st.info("📝 Summarization feature coming soon! This will use AI to create concise summaries of your text.")
    else:
        st.warning("⚠️ Please enter some text first!")
st.markdown('''</div>''', unsafe_allow_html=True)

# --- VOICE TO TEXT SECTION ---
st.markdown("""
    <div class="section-container">
        <h2 style="color: #333; margin-bottom: 1rem;">🎤 Voice to Text Conversion</h2>
        <div class="info-box">
            <strong>How it works:</strong> Click the microphone button below, speak clearly, and the app will convert your speech to text. You can speak in any language and it will be translated to your selected language.
        </div>
    </div>
""", unsafe_allow_html=True)

# --- VOICE TO TEXT STATE MANAGEMENT ---
if 'recognized_text' not in st.session_state:
    st.session_state['recognized_text'] = ""

SUPPORTED_LANGS = [
    'af', 'ar', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'gu', 'he', 'hi', 'hr', 'hu', 'id', 'it', 'ja', 'jw', 'km', 'kn', 'ko', 'la', 'lv', 'ml', 'mr', 'my', 'ne', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-cn', 'zh-tw'
]
if lang_code not in SUPPORTED_LANGS:
    st.markdown("""
        <div style="background: #FFF3CD; border-left: 4px solid #FFC107; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            ⚠️ <strong>Language Support Notice:</strong> The selected language may have limited support for speech recognition. Results may vary.
        </div>
    """, unsafe_allow_html=True)

st.markdown("### 🎙️ Start Recording")
wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    st.markdown("### 🎧 Your Recording")
    st.audio(wav_audio_data, format='audio/wav')
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(wav_audio_data)
        tmp_path = tmp.name
    with st.spinner("🔄 Processing your speech..."):
        try:
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
                if auto_detect:
                    recognized = recognizer.recognize_google(audio_data)
                else:
                    recognized = recognizer.recognize_google(audio_data, language=lang_code)
                st.session_state['recognized_text'] = recognized
                st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ Speech Recognized Successfully!</strong><br>
                        <strong>Original:</strong> {recognized}
                    </div>
                """, unsafe_allow_html=True)
                # Always translate to the selected language if it's different from recognition language
                if auto_detect or lang_code != "en":
                    translator = Translator()
                    translated_text = translator.translate(recognized, dest=lang_code).text
                    st.markdown(f"""
                        <div class="success-box">
                            <strong>🌐 Translation:</strong> {translated_text}
                        </div>
                    """, unsafe_allow_html=True)
                    st.session_state['recognized_text'] = translated_text
                st.session_state['history'].append(f"🗣️ Recognized: {recognized[:50]}...")
        except Exception as e:
            st.error(f"❌ Could not recognize speech: {e}")
        finally:
            os.remove(tmp_path)

# --- Recognized Text Editing and Transfer ---
st.session_state['recognized_text'] = st.text_area(
    "**Edit recognized text (optional):**",
    value=st.session_state['recognized_text'],
    key="edit_recognized_text",
    placeholder="Recognized text will appear here after recording. You can edit it if needed.",
    height=100
)
if st.button("✏️ Use for Text-to-Speech", key="use_for_tts"):
    st.session_state['user_input'] = st.session_state['recognized_text']
    st.experimental_rerun()

# --- Recent Activity Section ---
st.markdown("""
    <div class="section-container">
        <h2 style="color: #333; margin-bottom: 1rem;">📋 Recent Activity</h2>
    </div>
""", unsafe_allow_html=True)
# Add Clear History button
clear_history_btn = st.button("🧹 Clear History", help="Clear all recent activity from this session.")
if clear_history_btn:
    st.session_state['history'] = []
    st.rerun()
if st.session_state['history']:
    for i, item in enumerate(reversed(st.session_state['history'][-10:])):
        st.markdown(f"• {item}")
else:
    st.info("No recent activity. Start by converting some text or recording your voice!")

# --- Professional Footer ---
st.markdown("---")
st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px;">
        <p style="margin: 0; color: #666;">
            {SOCIAL_LINKS} | Made with ❤️ using Streamlit | © 2025 TarunSailesh | Enhanced by AI
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #888;">
            Visitor #{st.session_state['counter']} | Powered by Google Speech Recognition & Translation APIs
        </p>
    </div>
""", unsafe_allow_html=True)

# Set Google Cloud credentials (update the path as needed for your local machine)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\tarun\Downloads\speakmosaic-tts-sa.json"
st.write("File exists:", os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]))
