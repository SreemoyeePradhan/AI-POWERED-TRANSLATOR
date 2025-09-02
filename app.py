import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from speech_utils import text_to_speech, extract_text_from_txt, extract_text_from_docx, extract_text_from_pdf

# Load environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Add GEMINI_API_KEY=your_key to .env")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

# Languages
LANGUAGES = {
    "Auto Detect": "auto",
    "English": "en",
    "Hindi": "hi",
    "Bengali": "bn",          # Added Bengali
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
}

st.set_page_config(page_title="🌐 Translator", layout="wide")
st.title("🌐 Translator — Gemini")
st.write("Translate text or documents using Google Gemini.")

# Sidebar
st.sidebar.header("Settings")
model_choice = st.sidebar.selectbox("Gemini model", [GEMINI_MODEL])
enable_tts = st.sidebar.checkbox("Enable Text-to-Speech", value=True)

# Target language
target_lang_name = st.selectbox("Target language", list(LANGUAGES.keys()), index=0)
target_code = LANGUAGES[target_lang_name]

# History storage
if "history" not in st.session_state:
    st.session_state.history = []

# Helper functions
def add_to_history(original, translated, src_lang, tgt_lang):
    st.session_state.history.append({
        "source": original,
        "translated": translated,
        "source_lang": src_lang,
        "target_lang": tgt_lang
    })

def extract_text_from_response(response):
    return getattr(response, "text", None) or getattr(response, "output_text", None) or str(response)

def clear_text():
    st.session_state.text_input = ""

# --- Text Translation ---
st.subheader("Text Translation")
text_input = st.text_area("Enter text", height=150, key="text_input")
cols = st.columns([1, 1])

with cols[0]:
    if st.button("Translate"):
        if not text_input.strip():
            st.warning("Enter some text to translate.")
        else:
            with st.spinner("Detecting source language..."):
                detect_prompt = f"Detect the language of the following text. Reply with language name and code only:\n{text_input}"
                model = genai.GenerativeModel(GEMINI_MODEL)
                detected_response = model.generate_content(contents=detect_prompt)
                detected = extract_text_from_response(detected_response).strip()
                src_lang_name = detected.split()[0] if detected else "Unknown"
                src_code = detected.split()[-1] if detected else "auto"
                st.info(f"Detected language: {src_lang_name} ({src_code})")

            with st.spinner("Translating text..."):
                trans_prompt = f"Translate the following text from {src_lang_name} to {target_lang_name}:\n{text_input}"
                translated_response = model.generate_content(contents=trans_prompt)
                translated = extract_text_from_response(translated_response).strip()
                st.success("Translated Text:")
                st.write(translated)
                add_to_history(text_input, translated, src_lang_name, target_lang_name)

                if enable_tts and target_code != "auto":
                    audio_file = text_to_speech(translated, lang_code=target_code)
                    st.audio(audio_file, format="audio/mp3")

with cols[1]:
    st.button("Clear Text", on_click=clear_text)

# --- Document Translation ---
st.markdown("---")
st.subheader("Document Translation")
uploaded_file = st.file_uploader("Upload .txt, .docx, or .pdf", type=["txt", "docx", "pdf"])
if uploaded_file:
    try:
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext == "txt":
            doc_text = extract_text_from_txt(uploaded_file)
        elif ext == "docx":
            doc_text = extract_text_from_docx(uploaded_file)
        elif ext == "pdf":
            doc_text = extract_text_from_pdf(uploaded_file)
        else:
            doc_text = ""

        if doc_text:
            with st.spinner("Detecting source language..."):
                detect_prompt = f"Detect the language of the following text. Reply with language name and code only:\n{doc_text[:500]}"
                model = genai.GenerativeModel(GEMINI_MODEL)
                detected_response = model.generate_content(contents=detect_prompt)
                detected = extract_text_from_response(detected_response).strip()
                src_lang_name = detected.split()[0] if detected else "Unknown"
                src_code = detected.split()[-1] if detected else "auto"
                st.info(f"Detected language: {src_lang_name} ({src_code})")

            with st.spinner("Translating document..."):
                trans_prompt = f"Translate the following text from {src_lang_name} to {target_lang_name}:\n{doc_text[:2000]}"
                translated_response = model.generate_content(contents=trans_prompt)
                translated = extract_text_from_response(translated_response).strip()
                st.success("Translated Document Text:")
                st.text_area("Translation", value=translated, height=300)
                add_to_history(doc_text[:2000], translated, src_lang_name, target_lang_name)

                if enable_tts and target_code != "auto":
                    audio_file = text_to_speech(translated, lang_code=target_code)
                    st.audio(audio_file, format="audio/mp3")
    except Exception as e:
        st.error(f"Document translation failed: {e}")

# --- History Panel ---
st.markdown("---")
st.subheader("Translation History")
if st.session_state.history:
    for i, item in enumerate(reversed(st.session_state.history[-10:])):
        st.markdown(f"**#{i+1} | {item['source_lang']} → {item['target_lang']}**")
        st.write(item["source"])
        st.write("➡️")
        st.write(item["translated"])
else:
    st.write("No translations yet.")
