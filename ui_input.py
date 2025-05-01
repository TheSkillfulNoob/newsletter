import streamlit as st
from streamlit_quill import st_quill
from datetime import date
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self):
        return ''.join(self.text_parts)

def strip_html(html_str):
    parser = HTMLTextExtractor()
    parser.feed(html_str or "")
    return parser.get_text()

def handle_main_content(sections, section_config, payload, week_no):
    # — sidebar image uploads (page-1 images) —
    image_file = st.sidebar.file_uploader("📷 Week Summary Image", type=["png","jpg","jpeg"])
    if image_file:
        path = f"uploaded_image_{week_no}.png"
        with open(path,"wb") as f: f.write(image_file.getbuffer())
        st.sidebar.image(path, width=200)
        payload["img_rect"] = path

    image_file_weekly = st.sidebar.file_uploader("📷 Weekly Cover Image", type=["png","jpg","jpeg"])
    if image_file_weekly:
        path = f"uploaded_image_weekly_{week_no}.png"
        with open(path,"wb") as f: f.write(image_file_weekly.getbuffer())
        st.sidebar.image(path, width=200)
        payload["img_weekly"] = path

    st.sidebar.markdown("---")
    st.sidebar.markdown("Fill in your newsletter text sections:")

    for section in sections:
        st.markdown("#### ✏️ " + section.capitalize())
        cfg = section_config[section]
        placeholder = f"Enter {section}…" if cfg["rich"] else ""
        if cfg["rich"]:
            html_src = st_quill(key=f"editor_{section}", html=True, placeholder=placeholder)
            visible = strip_html(html_src)
            payload[section] = html_src or ""
        else:
            visible = st.text_input(section.title(), key=f"input_{section}")
            payload[section] = visible or ""
        st.caption(f"{len(visible)} / {cfg['limit']} chars")

def handle_fact_content(payload, week_no):
    st.markdown("### 📊 Fun Facts & Analysis Images <br>")
    uploaded = st.file_uploader("Upload up to 6 images", type=["png","jpg","jpeg"], accept_multiple_files=True)
    payload["fact_images"] = []
    for i,file in enumerate(uploaded[:6]):
        path = f"fact_img_{week_no}_{i+1}.png"
        with open(path,"wb") as f: f.write(file.getbuffer())
        st.image(path, width=200)
        caption = st.text_input(f"Insight {i+1}", key=f"cap_{i}")
        payload["fact_images"].append({"img":path, "caption":caption[:100]})