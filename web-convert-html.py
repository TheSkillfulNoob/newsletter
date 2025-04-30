import streamlit as st
import json

st.set_page_config(page_title="Newsletter HTML Builder", layout="wide")
st.title("📝 WYSIWYG Newsletter HTML Generator")

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
        html_input = st.text_area(f"HTML for `{section}`", value=default, height=200)
        payload[section] = html_input

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
