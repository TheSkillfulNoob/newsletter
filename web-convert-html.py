import streamlit as st
from streamlit_quill import st_quill
from datetime import date
import json
import html
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="WYSIWYG Newsletter Builder", layout="wide")
st.title("📬 Newsletter Builder & PDF Generator")

# ────────────────────────────── Setup
TEMPLATE_PATH = "Weekly Newsletter Template v3.pdf"
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

for section in sections:
    with st.expander(f"✏️ {section}", expanded=section in ["title", "events"]):
        content = st_quill(key=f"editor_{section}", html=True, placeholder=f"Enter HTML for {section}...")
        payload[section] = content or ""

payload["img_rect"] = image_path if image_path else "Test_image"

# ────────────────────────────── Generate Preview PDF
def render_pdf_from_payload(payload, template_path, output_pdf, anchors):
    doc = fitz.open(template_path)

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

with col1:
    if st.button("📄 Generate PDF Preview"):
        pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
        st.success("PDF generated!")

with col2:
    st.download_button("⬇️ Download Payload JSON", data=json.dumps(payload, indent=2), file_name="newsletter_payload.json")

# ────────────────────────────── PDF Preview
if os.path.exists(OUTPUT_PDF):
    st.markdown("### 🔍 PDF Preview")
    with open(OUTPUT_PDF, "rb") as f:
        st.download_button("⬇️ Download PDF", f, file_name=OUTPUT_PDF, mime="application/pdf")
        st.pdf(f)