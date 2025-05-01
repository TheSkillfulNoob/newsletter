import streamlit as st
from streamlit_quill import st_quill
from datetime import date

def handle_inputs(sections, section_config, payload, week_no):
    # Sidebar image uploads
    image_path, image_path_weekly = None, None

    image_file = st.sidebar.file_uploader("📷 Upload: Week Summary", type=["png", "jpg", "jpeg"])
    if image_file:
        image_path = f"uploaded_image_{week_no}.png"
        with open(image_path, "wb") as f:
            f.write(image_file.getbuffer())
        st.sidebar.image(image_path, width=200)

    image_file_weekly = st.sidebar.file_uploader("📷 Upload: Weekly Cover", type=["png", "jpg", "jpeg"], key="weekly_image")
    if image_file_weekly:
        image_path_weekly = f"uploaded_image_weekly_{week_no}.png"
        with open(image_path_weekly, "wb") as f:
            f.write(image_file_weekly.getbuffer())
        st.sidebar.image(image_path_weekly, width=200)

    st.sidebar.markdown("---")
    st.sidebar.markdown("You can copy the generated dictionary or preview PDF after filling in all sections.")

    # Text inputs
    for section in sections:
        cfg = section_config[section]
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

    return image_path or "Test_image", image_path_weekly or "Test_image"
