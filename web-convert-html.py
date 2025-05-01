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
import pandas as pd

st.set_page_config(page_title="Newsletter PDF Builder", layout="wide")
st.title("📬 Newsletter PDF Builder")

# ────────────────────────────── Setup
TEMPLATE_PATH = "Weekly-Newsletter-Template-v4.pdf"
week_no = int(date.today().strftime("%V"))
OUTPUT_PDF = f"preview_week_{week_no}.pdf"
ISSUE_TAG = f"25w{week_no}"

anchors = {   
    "title":        fitz.Rect(12,  12, 588, 208),
    "events-prof":  fitz.Rect(17, 254, 365, 358), #Split new
    "events-pers":  fitz.Rect(17, 360, 365, 428), #Split new
    "gratitude":    fitz.Rect(17, 445, 320, 528), #y0 decreased to accommodate bullet
    "productivity": fitz.Rect(17, 533, 320, 623), #y0 decreased to accommodate bullet
    "up_next":      fitz.Rect(17, 655, 340, 805),
    "facts":        fitz.Rect(335, 460, 585, 625),
    "img_rect":     fitz.Rect(375, 220, 585, 430),
    "weekly": 		fitz.Rect(365, 732, 585, 805),
    "img_weekly": 	fitz.Rect(468, 640, 568, 740) #New image
}

sections = ["title", "events-prof", "events-pers", "gratitude", "productivity", "up_next", "facts", "weekly"]
payload = {}

# ────────────────────────────── Password Gate
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    
if not st.session_state.authenticated:
    user_pw = st.text_input("🔒 Enter password to unlock preview tools", type="password")
    if user_pw == st.secrets["auth"]["password"]:
        st.success("🔓 Access granted.")
        st.session_state.authenticated = True
        st.rerun()  # 🔁 Force rerun so new UI appears
    elif user_pw:
        st.error("❌ Incorrect password.")
    st.stop()

# ────────────────────────────── UI Input
image_file = st.sidebar.file_uploader("📷 Upload: Week Summary", type=["png", "jpg", "jpeg"])
image_path = None
if image_file:
    image_path = f"uploaded_image_{week_no}.png"
    with open(image_path, "wb") as f:
        f.write(image_file.getbuffer())
    st.sidebar.image(image_path, width=200)

image_file_weekly = st.sidebar.file_uploader("📷 Upload: Weekly Cover", type=["png", "jpg", "jpeg"], key="weekly_image")
image_path_weekly = None
if image_file_weekly:
    image_path_weekly = f"uploaded_image_weekly_{week_no}.png"
    with open(image_path_weekly, "wb") as f:
        f.write(image_file_weekly.getbuffer())
    st.sidebar.image(image_path_weekly, width=200)

st.sidebar.markdown("---")
st.sidebar.markdown("You can copy the generated dictionary or preview PDF after filling in all sections.")

section_config = {
    "title":        {"limit": 30,  "rich": False, "bg": "#fffbe6"},
    "events-prof":  {"limit": 250, "rich": True,  "bg": "#f0f8ff"},
    "events-pers":  {"limit": 150, "rich": True,  "bg": "#f0f8ff"},
    "gratitude":    {"limit": 200, "rich": True,  "bg": "#f0fff0"},
    "productivity": {"limit": 300, "rich": True,  "bg": "#f5f5dc"},
    "up_next":      {"limit": 300, "rich": True,  "bg": "#e8f4fd"},
    "facts":        {"limit": 300, "rich": True,  "bg": "#ffe4e1"},
    "weekly":       {"limit": 150, "rich": True,  "bg": "#fef3e7"},
}

for section in sections:
    cfg = section_config[section]
    with st.container():
        #st_html(f"""
        #    <div style="background-color:{cfg['bg']}; padding:16px; border-radius:10px; margin-bottom:10px">
        #        <h5 style='margin-top:0; text-transform:capitalize;'>✏️ {section}</h5>
        #    </div>
        #""", height=100)

        placeholder = f"Enter: {section}..." if cfg["rich"] else "Enter plain text..."
        if cfg["rich"]:
            st.subheader("✏️ " + section.capitalize())
            content = st_quill(key=f"editor_{section}", html=True, placeholder=placeholder)
        else:
            content = st.text_input(f"{section.title()}", placeholder=placeholder, key=f"input_{section}")

        char_count = len(content) if content else 0
        st.caption(f"{char_count}/{cfg['limit']} characters")

        if char_count > cfg["limit"]:
            st.error(f"Too long! Limit is {cfg['limit']} characters.")
        else:
            payload[section] = content or ""

payload["img_rect"] = image_path if image_path else "Test_image"
payload["img_weekly"] = image_path_weekly if image_path_weekly else "Test_image"

# ────────────────────────────── Generate Preview PDF
def render_pdf_from_payload(payload, template_path, output_pdf, anchors, debug=False):
    template_path = Path(template_path)
    if not template_path.exists():
        st.error(f"Template not found: {template_path.resolve()}")
        return None
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
    if payload.get("img_weekly") != "Test_image" and os.path.exists(payload["img_weekly"]):
        page.insert_image(anchors["img_weekly"], filename=payload["img_weekly"], keep_proportion=True, overlay=True)

    if debug:
        red = (1, 0, 0)
        blue = (0, 0, 1)
        page = doc[0]
        shape = page.new_shape()
        
        for key, rect in anchors.items():
            # Draw anchor box
            page.draw_rect(rect, color=blue, width=0.5)
            # Draw top-left point
            point = fitz.Point(rect.x0, rect.y0)
            page.draw_circle(point, 4, color=red)
        
        shape.commit()
    doc.save(output_pdf, deflate=True, garbage=4)
    return output_pdf

# ────────────────────────────── Save to CSV
def append_payload_to_csv(payload, week_tag, csv_path="past-content.csv"):
    # Define all expected columns
    columns = ["week", "title", "events-prof", "events-pers", "gratitude",
               "productivity", "up_next", "facts", "weekly"]

    # Create a row with defaults
    row = {col: "" for col in columns}
    row["week"] = week_tag

    # Copy over values from payload
    for key in payload:
        if key in row:
            row[key] = payload[key]

    df = pd.DataFrame([row])

    # Append to CSV
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode="a", header=False, index=False)
        st.success(f"✅ Append Payload ({week_tag}) to CSV!")
    else:
        df.to_csv(csv_path, mode="w", header=True, index=False)
        
# ────────────────────────────── Action Buttons
st.markdown("---")
show_debug = st.checkbox("🧪 Show debug layout boundaries (circles + boxes)")
col1, col2 = st.columns([1, 2])

with col1:
    char_limit_exceeded = any(
        len(payload[sec]) > section_config[sec]["limit"]
        for sec in sections if sec in payload
    )

    if char_limit_exceeded:
        st.error("❌ One or more sections exceed character limits. Please revise before generating the PDF.")
    else:
        if st.button("📄 Generate PDF Preview"):
            pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors, debug=show_debug)
            if pdf_path:
                st.success("✅ PDF generated!")
                append_payload_to_csv(payload, ISSUE_TAG)
with col2:
    if st.button("⬇️ Append Payload to CSV"):
        week_tag = f"25w{date.today().isocalendar().week}"
        append_payload_to_csv(payload, week_tag = week_tag)
        

# ────────────────────────────── PDF Preview
if os.path.exists(OUTPUT_PDF):
    st.markdown("### 🔍 PDF Preview")
    with open(OUTPUT_PDF, "rb") as f:
        st.download_button("⬇️ Download PDF", f.read(), file_name=OUTPUT_PDF, mime="application/pdf")
    st.info("⚠️ Chrome and Edge block embedded PDF preview. Download the file and open locally!")
    