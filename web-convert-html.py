import streamlit as st
import json
from streamlit_quill import st_quill
import fitz
from datetime import date
import html

st.set_page_config(page_title="Newsletter HTML Builder", layout="wide")
st.title("📝 Newsletter HTML Generator")

# Define section names
sections = [
    "title", "events", "gratitude", "productivity", "up_next", "facts", "weekly"
]

# Initialize the payload dictionary
payload = {}

st.sidebar.header("🧭 Instructions")
st.sidebar.markdown("""
- Use the editor below to input content for each section.
- Style text using **HTML tags** or **rich text controls**.
- Only one image will be used (at `img_rect`).
""")

image_upload = st.sidebar.file_uploader("📷 Upload one image for `img_rect`", type=["png", "jpg", "jpeg"])

st.markdown("---")

for section in sections:
    with st.expander(f"✏️ Edit Section: {section}", expanded=section in ["title", "events"]):
        default = "<p>Your HTML content here</p>" if section != "title" else "Your newsletter title"
        quill_html = st_quill(key=f"editor_{section}", html=True, placeholder="Enter your content here...")
        payload[section] = quill_html or ""

# Image name stub
payload["img_rect"] = image_upload.name if image_upload else "Test_image"

st.markdown("---")
st.subheader("📦 Preview Payload Dictionary")
st.code(json.dumps(payload, indent=4), language="json")

# Optionally: Live preview using iframe/markdown
if st.checkbox("🔍 Show HTML Preview (limited)"):
    for k in sections:
        st.markdown(f"### {k.title()} Preview")
        st.components.v1.html(payload[k], height=300, scrolling=True)

# Download the payload dictionary as a JSON file
st.download_button(
    label="💾 Download Payload JSON",
    data=json.dumps(payload, indent=2),
    file_name="newsletter_payload.json",
    mime="application/json"
)

def render_pdf_from_payload(payload, template_path="Weekly Newsletter Template v3.pdf", image_path=None):
    week_no = int(date.today().strftime("%V"))
    OUTPUT = f"preview_{week_no}.pdf"

    doc = fitz.open(template_path)

    # font detection
    font_tag, font_name = None, None
    for fid, _, _, fname, tag, _ in doc[0].get_fonts():
        if "KaiseiTokumin" in fname:
            font_tag, font_name = tag, fname
            break
    assert font_tag, "Kaisei Tokumin not found!"

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

    def make_html(src, is_title=False):
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
            print(f"⚠️ Overflow in {key}: {e}")

    if image_path:
        page.insert_image(anchors["img_rect"], filename=image_path, keep_proportion=True, overlay=True)

    doc.save(OUTPUT, deflate=True, garbage=4)
    return OUTPUT

if st.button("📄 Generate Preview PDF"):
    pdf_path = render_pdf_from_payload(payload, template_path="Weekly Newsletter Template v3.pdf",
                                       image_path=image_upload.name if image_upload else None)
    with open(pdf_path, "rb") as f:
        st.download_button("⬇️ Download PDF", data=f, file_name=pdf_path, mime="application/pdf")
        st.pdf(f)