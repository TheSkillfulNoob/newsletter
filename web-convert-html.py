import streamlit as st
from streamlit_quill import st_quill
from streamlit.components.v1 import html as st_html
from datetime import date
import json
import html
import fitz  # PyMuPDF
import os
from pathlib import Path
import base64

st.set_page_config(page_title="Newsletter PDF Builder", layout="wide")
st.title("📬 Newsletter PDF Builder")

# ────────────────────────────── Setup
TEMPLATE_PATH = "Weekly-Newsletter-Template-v3.pdf"
week_no = int(date.today().strftime("%V"))
OUTPUT_PDF = f"preview_week_{week_no}.pdf"

anchors = {
    "title":        fitz.Rect(12,  12, 588, 208),
    "events":       fitz.Rect(15, 252, 365, 428),
    "gratitude":    fitz.Rect(15, 448, 275, 528),
    "productivity": fitz.Rect(15, 543, 275, 623),
    "up_next":      fitz.Rect(15, 665, 340, 805),
    "facts":        fitz.Rect(290, 465, 585, 625),
    "img_rect":     fitz.Rect(375, 220, 585, 430),
    "weekly":       fitz.Rect(359, 660, 464, 795),
}

sections = ["title", "events", "gratitude", "productivity", "up_next", "facts", "weekly"]
payload = {}

# ────────────────────────────── UI Input
image_file = st.sidebar.file_uploader("📷 Upload image for newsletter", type=["png", "jpg", "jpeg"])
image_path = None
if image_file:
    image_path = f"uploaded_image_{week_no}.png"
    with open(image_path, "wb") as f:
        f.write(image_file.getbuffer())

st.sidebar.markdown("---")
st.sidebar.markdown("You can copy the generated dictionary or preview PDF after filling in all sections.")

section_config = {
    "title":        {"limit": 30,  "rich": False, "bg": "#fffbe6"},
    "events":       {"limit": 400, "rich": True,  "bg": "#f0f8ff", "height": 200},
    "gratitude":    {"limit": 200, "rich": True,  "bg": "#f0fff0", "height": 100},
    "productivity": {"limit": 300, "rich": True,  "bg": "#f5f5dc", "height": 125},
    "up_next":      {"limit": 300, "rich": True,  "bg": "#e8f4fd", "height": 150},
    "facts":        {"limit": 300, "rich": True,  "bg": "#ffe4e1", "height": 150},
    "weekly":       {"limit": 150, "rich": True,  "bg": "#fef3e7", "height": 100},
}

for section in sections:
    cfg = section_config[section]

    with st.container():
        placeholder = f"Enter: {section}..." if cfg["rich"] else "Enter plain text..."
        if cfg["rich"]:
            st.subheader(section.capitalize())
            content = st_quill(key=f"editor_{section}", html=True, placeholder = placeholder, height = cfg["height"])
        else:
            content = st.text_input(f"{section.title()}", placeholder = placeholder, key=f"input_{section}")
        
        char_count = len(content) if content != placeholder else 0
        st.caption(f"{char_count}/{cfg['limit']} characters")

        if char_count > cfg["limit"]:
            st.error(f"Too long! Limit is {cfg['limit']} characters.")
        else:
            payload[section] = content or ""

payload["img_rect"] = image_path if image_path else "Test_image"

# ────────────────────────────── Generate Preview PDF
def render_pdf_from_payload(payload, template_path, output_pdf, anchors):
    template_path = Path(TEMPLATE_PATH)
    if not template_path.exists():
        st.error(f"Template not found: {template_path.resolve()}")
    else:
        doc = fitz.open(str(template_path))

    font_tag, font_name = None, None
    for fid, _, _, fname, tag, _ in doc[0].get_fonts():
        if "KaiseiTokumin" in fname:
            font_tag, font_name = tag, fname
            break
    if not font_tag:
        font_name = "Helvetica"

    def make_html(src, is_title=False):
        if not src:
            return ""
        if src.lstrip().startswith("<"):
            return src
        if is_title:
            return f'<h1 style="font-family:\'{font_name}\';margin:0">{html.escape(src)}</h1>'
        return f'<div style="font-family:\'{font_name}\';font-size:11pt;line-height:13pt">{html.escape(src)}</div>'

    page = doc[0]
    for key, rect in anchors.items():
        if key == "img_rect":
            continue
        html_snip = make_html(payload[key], is_title=(key == "title"))
        try:
            page.insert_htmlbox(rect, html_snip, scale_low=0.5, overlay=True)
        except OverflowError as e:
            st.warning(f"⚠️ Overflow in section '{key}': {e}")

    if payload["img_rect"] != "Test_image" and os.path.exists(payload["img_rect"]):
        page.insert_image(anchors["img_rect"], filename=payload["img_rect"], keep_proportion=True, overlay=True)

    doc.save(output_pdf, deflate=True, garbage=4)
    return output_pdf

# ────────────────────────────── Action Buttons
st.markdown("---")
col1, col2 = st.columns([1, 2])

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    user_pw = st.text_input("🔒 Enter password to unlock preview tools", type="password")
    if user_pw == st.secrets["auth"]["password"]:
        st.success("🔓 Access granted.")
        st.session_state.authenticated = True
    elif user_pw:
        st.error("❌ Incorrect password.")
    st.stop()
    
with col1:
    char_limit_exceeded = any(
    len(payload[sec]) > section_config[sec]["limit"]
    for sec in sections if sec in payload
    )

    if char_limit_exceeded:
        st.error("❌ One or more sections exceed character limits. Please revise before generating the PDF.")
    else:
        if st.button("📄 Generate PDF Preview"):
            pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
            st.success("PDF generated!")

with col2:
    st.download_button("⬇️ Download Payload JSON", data=json.dumps(payload, indent=2), file_name="newsletter_payload.json")

# ────────────────────────────── PDF Preview
if os.path.exists(OUTPUT_PDF):
    st.markdown("### 🔍 PDF Preview")
    with open(OUTPUT_PDF, "rb") as f:
        st.download_button("⬇️ Download PDF", f.read(), file_name=OUTPUT_PDF, mime="application/pdf")
    st.info("⚠️ Chrome and Edge block embedded PDF preview. Download the file and open locally!")