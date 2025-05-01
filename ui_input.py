import streamlit as st
from streamlit_quill import st_quill

def handle_inputs(sections, section_config, payload):
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
