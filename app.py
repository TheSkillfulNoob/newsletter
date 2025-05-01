import streamlit as st
from datetime import date
from setup import configure_page, authenticate
from ui_input import handle_inputs
from pdf_utils import (
    render_pdf_from_payload,
    generate_debug_page1,
    generate_debug_page2,
)
from csv_utils import generate_appended_csv
import fitz
configure_page()
authenticate()

TEMPLATE_PATH = "Weekly-Newsletter-Template-v4.pdf"
week_no = int(date.today().strftime("%V"))
OUTPUT_PDF = f"preview_week_{week_no}.pdf"
ISSUE_TAG = f"25w{week_no}"

anchors = {
    "title":        (12, 12, 588, 208),
    "events-prof":  (17, 254, 365, 358),
    "events-pers":  (17, 360, 365, 428),
    "gratitude":    (17, 445, 320, 528),
    "productivity": (17, 533, 320, 623),
    "up_next":      (17, 655, 340, 805),
    "facts":        (335, 460, 585, 625),
    "img_rect":     (375, 220, 585, 430),
    "weekly":       (365, 732, 585, 805),
    "img_weekly":   (468, 640, 568, 740)
}
anchors = {k: fitz.Rect(*v) for k, v in anchors.items()}

section_config = {
    "title":        {"limit": 30,  "rich": False},
    "events-prof":  {"limit": 250, "rich": True},
    "events-pers":  {"limit": 150, "rich": True},
    "gratitude":    {"limit": 200, "rich": True},
    "productivity": {"limit": 300, "rich": True},
    "up_next":      {"limit": 300, "rich": True},
    "facts":        {"limit": 300, "rich": True},
    "weekly":       {"limit": 150, "rich": True},
}

sections = list(section_config.keys())
payload = {}

payload["img_rect"] = "Test_image"
payload["img_weekly"] = "Test_image"
handle_inputs(sections, section_config, payload, week_no)

# (1) Debug Page 1
col1, col2 = st.columns([1, 2])
with col1:
    if st.button("📤 Debug Page 1"):
        st.session_state.debug1_ready = True
with col2:
    if st.session_state.get("debug1_ready"):
        debug_path1 = generate_debug_page1(TEMPLATE_PATH, anchors, payload)
        with open(debug_path1, "rb") as f:
            st.download_button("⬇️ Download Page 1 Layout", f.read(), file_name="debug_page1.pdf")

# (2) Debug Page 2
col3, col4 = st.columns([1, 2])
with col3:
    if st.button("📤 Debug Page 2"):
        st.session_state.debug2_ready = True
with col4:
    if st.session_state.get("debug2_ready"):
        debug_path2 = generate_debug_page2(payload)
        with open(debug_path2, "rb") as f:
            st.download_button("⬇️ Download Page 2 Layout", f.read(), file_name="debug_page2.pdf")

# (3) Generate Full Newsletter
col5, col6 = st.columns([1, 2])
with col5:
    if st.button("📄 Preview Newsletter"):
        if any(len(payload[s]) > section_config[s]["limit"] for s in sections if s in payload):
            st.error("❌ Section exceeds character limits.")
        else:
            st.session_state.preview_ready = True
with col6:
    if st.session_state.get("preview_ready"):
        preview_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
        if preview_path:
            st.success("✅ PDF Ready")
            with open(preview_path, "rb") as f:
                st.download_button("⬇️ Download Newsletter", f.read(), file_name=OUTPUT_PDF)

csv = generate_appended_csv(payload, week_tag=ISSUE_TAG)
st.download_button("⬇️ Download Updated past-content.csv", data=csv, file_name="past-content.csv", mime="text/csv")
