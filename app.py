import streamlit as st
from datetime import date
from setup import configure_page, authenticate
from ui_input import handle_inputs
from pdf_utils import render_pdf_from_payload
from csv_utils import generate_appended_csv

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

handle_inputs(sections, section_config, payload)

payload["img_rect"] = "Test_image"
payload["img_weekly"] = "Test_image"

show_debug = st.checkbox("🧪 Show debug layout boundaries (circles + boxes)")
if st.button("📄 Generate PDF Preview"):
    if any(len(payload[s]) > section_config[s]["limit"] for s in sections if s in payload):
        st.error("❌ Section exceeds character limits.")
    else:
        path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors, debug=show_debug)
        if path:
            st.success("✅ PDF generated!")
            with open(path, "rb") as f:
                st.download_button("⬇️ Download PDF", f.read(), file_name=OUTPUT_PDF, mime="application/pdf")

csv = generate_appended_csv(payload, week_tag=ISSUE_TAG)
st.download_button("⬇️ Download Updated past-content.csv", data=csv, file_name="past-content.csv", mime="text/csv")
