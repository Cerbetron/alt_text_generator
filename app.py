import streamlit as st
import io
import requests
from datetime import datetime
from utils.pdf_utils import extract_images_from_pdf
from utils.preprocess import preprocess_image
from utils.alt_text_generator import generate_alt_text
from utils.helpers import label_output, ensure_dir_exists, image_to_base64

st.set_page_config(page_title=" PDF Alt-Text Generator", layout="wide")

st.markdown(
    """
    <style>
    html, body, .main, .block-container {
        background-color: #0e0e0e !important;
        color: #ffffff !important;
    }
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stNumberInput input {
        background-color: #1c1c1c !important;
        color: #00ffcc !important;
        border: 1px solid #00bfff;
        border-radius: 8px;
    }

    .stSelectbox div[data-baseweb="select"] {
        width: 100%;
        background: linear-gradient(145deg, #00ffdd, #0078ff);
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 6px 14px;
    }

    .stButton>button, .stDownloadButton button {
        background: linear-gradient(145deg, #00ffdd, #0078ff);
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 10px;
        padding: 6px 14px;
    }

    .stSidebar {
        background-color: #121212 !important;
    }
    .result-card {
        background-color: #1c1c1c;
        border: 1px solid #00bfff;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 16px;
    }
    .result-card img {
        width: 100%;
        border-radius: 6px;
    }
    .alt-text {
        margin-top: 8px;
        color: #00ffcc;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/pdf.png", width=80)
    st.title(" Alt-Text Generator")
    selected_model = st.radio("Vision Model", ["OpenAI", "Groq"])
    openai_key = st.text_input("OpenAI API Key", type="password")
    groq_key = st.text_input("Groq API Key", type="password")
    language = st.selectbox(
        "Alt-Text Language",
        ["English", "Dutch", "Spanish", "French", "German"],
        index=0,
    )
    alt_lines = st.number_input(
        " Number of Alt-Text Lines",
        min_value=1,
        max_value=5,
        value=2,
        step=1,
        help="Defines how many lines the generated alt-text should be."
    )
    

with st.expander("🔍 Test OpenAI API Key"):
    test_key = st.text_input("Test Key", type="password")
    if st.button("Check OpenAI Key"):
        try:
            r = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {test_key}"})
            if r.status_code == 200:
                st.success("✅ API key is valid.")
            else:
                st.error(f"❌ Invalid (status code: {r.status_code})")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# Main
st.title(" PDF Image Alt-Text Generator")
uploaded_file = st.file_uploader("📤 Upload PDF", type=["pdf"])

if uploaded_file:
    with st.status("⏳ Extracting and analyzing images..."):
        pdf_bytes = uploaded_file.read()
        images_by_page = extract_images_from_pdf(io.BytesIO(pdf_bytes))

        total_images = sum(len(imgs) for imgs in images_by_page.values())
        progress = st.progress(0)

        output_lines = []
        flagged = []
        logos = 0
        processed = 0

        for page_num, images in images_by_page.items():
            with st.expander(f"Page {page_num}"):
                for idx, image in enumerate(images):
                    processed += 1
                    cleaned_img, is_logo, was_flagged, reason = preprocess_image(image)

                    alt_text = generate_alt_text(
                        cleaned_img,
                        selected_model,
                        openai_key,
                        groq_key,
                        is_logo=is_logo,
                        alt_line_count=alt_lines,
                        language=language,
                    )

                    label = label_output(page_num, idx + 1, alt_text)
                    if was_flagged:
                        label += f"\n(Note: ⚠️ {reason})"
                        flagged.append(f"Page {page_num} - Image {idx + 1}: {reason}")
                    if is_logo:
                        logos += 1

                    output_lines.append(label)

                    card_html = f"""
                    <div class='result-card'>
                        <img src='data:image/png;base64,{image_to_base64(cleaned_img)}' />
                        <p class='alt-text'>{alt_text}</p>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    progress.progress(processed / total_images)

        progress.empty()

        if flagged:
            st.markdown("### ⚠️ Flagged Images")
            for msg in flagged:
                st.warning(msg)

        # Prepare output
        alt_text_final = "\n\n".join(output_lines)
        ensure_dir_exists("outputs/generated_texts")
        pdf_name = uploaded_file.name.rsplit(".", 1)[0]
        output_filename = f"{pdf_name}_alt_text.txt"
        output_path = f"outputs/generated_texts/{output_filename}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(alt_text_final)

    metrics = st.columns(3)
    metrics[0].metric("Images", total_images)
    metrics[1].metric("Logos", logos)
    metrics[2].metric("Flagged", len(flagged))

    if st.download_button(
        label="📥 Download Alt-Text File",
        data=alt_text_final,
        file_name=output_filename,
        mime="text/plain",
    ):
        st.success("✅ Downloaded!")

else:
    st.warning(" Please upload a PDF to begin.")
