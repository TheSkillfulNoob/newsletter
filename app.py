import streamlit as st
from datetime import date
from setup import configure_page, authenticate
from ui_input import handle_main_content, handle_fact_content, strip_html
from pdf_utils import (
    render_pdf_from_payload,
    generate_debug_page1,
    generate_debug_page2,
)
from streamlit_quill import st_quill
from google_utils import (
    load_history, 
    append_history,
    load_subscribers, 
    add_subscriber, 
    remove_subscriber
)

from mailing import send_newsletter  # your existing send_newsletter
from csv_utils import generate_appended_csv
import fitz

configure_page()
authenticate()

TEMPLATE_PATH = "Weekly-Newsletter-Template-v5.pdf"
week_no      = int(date.today().strftime("%V"))
ISSUE_TAG    = f"25w{week_no}"
OUTPUT_PDF   = f"{ISSUE_TAG}.pdf"

my_email = "theskillfulnoob2002@gmail.com"

# anchors and section_config as before…
anchors = {
    "title":        (12, 12, 588, 208),
    "events-prof":  (17, 244, 365, 418),
    # deprecated in v5 - "events-pers":  (17, 360, 365, 428), 
    "gratitude":    (17, 452, 320, 625), #original y2 is 528
    # deprecated in v5 - "productivity": (17, 533, 320, 623),
    "up_next":      (17, 655, 340, 805),
    "facts":        (335, 452, 585, 625),
    "img_rect":     (375, 220, 585, 430),
    "weekly":       (365, 732, 585, 805),
    "img_weekly":   (468, 640, 568, 740)
}
anchors = {k: fitz.Rect(*v) for k, v in anchors.items()}

section_config = {
    "title":        {"limit": 30,  "rich": False},
    "events-prof":  {"limit": 300, "rich": True},
    # "events-pers":  {"limit": 150, "rich": True}, # to deprecate
    "gratitude":    {"limit": 300, "rich": True},
    # "productivity": {"limit": 300, "rich": True}, # to deprecate
    "up_next":      {"limit": 300, "rich": True},
    "facts":        {"limit": 300, "rich": True},
    "weekly":       {"limit": 150, "rich": True},
}
sections = section_config.keys()

payload = {
    "img_rect":    "Test_image",
    "img_weekly":  "Test_image",
}

# --- split into tabs ---
tab_main, tab_graphs, tab_dl, tab_automail, tab_subs = st.tabs([
    "✏️ Main Content",
    "📊 Fact Graphs",
    "📥 Download",
    "✉️ Automail & History",
    "👥 Subscribers"
])

with tab_main:
    handle_main_content(sections, section_config, payload, week_no)

with tab_graphs:
    handle_fact_content(payload, week_no)

with tab_dl:
    st.markdown("### 🚀 Actions & Downloads")
    # Debug Page 1
    c1, c2 = st.columns([1,2])
    with c1:
        if st.button("🔎 Debug Page 1"):
            st.session_state.d1 = True
    with c2:
        if st.session_state.get("d1"):
            p1 = generate_debug_page1(TEMPLATE_PATH, anchors, payload)
            with open(p1,"rb") as f:
                st.download_button("⬇️ Download Page 1 Layout", f.read(), file_name="debug_page1.pdf")

    # Debug Page 2
    c3, c4 = st.columns([1,2])
    with c3:
        if st.button("🔎 Debug Page 2"):
            st.session_state.d2 = True
    with c4:
        if st.session_state.get("d2"):
            p2 = generate_debug_page2(payload)
            with open(p2,"rb") as f:
                st.download_button("⬇️ Download Page 2 Layout", f.read(), file_name="debug_page2.pdf")

    # Full Newsletter
    c5, c6 = st.columns([1,2])
    with c5:
        if st.button("📄 Generate Newsletter"):
            too_long = any(len(strip_html(payload[s]))>section_config[s]["limit"] for s in sections)
            if too_long:
                st.error("❌ One or more sections exceed limits.")
            else:
                st.session_state.pn = True
    with c6:
        if st.session_state.get("pn"):
            out = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
            if out:
                with open(out,"rb") as f:
                    st.download_button("⬇️ Download Newsletter", f.read(), file_name=OUTPUT_PDF)
                # CSV
                csv = generate_appended_csv(payload, week_tag=ISSUE_TAG)
                st.download_button("⬇️ Download Records CSV", data=csv,
                                   file_name="past-content.csv", mime="text/csv")

# ––– Tab 4: Automail & record history –––
with tab_automail:
    st.header("Send & Log Newsletter")

    # — Default subject from Main Content payload —
    week_no = int(date.today().strftime("%V"))
    default_title = payload.get("title", "").split(": ",1)[-1]  # after your Week tag
    default_subject = f"🌱 2025 W{week_no} Newsletter: {default_title}"
    subject = st.text_input("✉️ Email subject", value=default_subject)

    # — WYSIWYG editor for the inner “highlight” div —
    st.subheader("✏️ Highlight Box Content")
    inner_html = st_quill(
        key="mail_inner",
        html=True,
        placeholder="Enter your key message here…"
    )
    # Strip tags & enforce 500-char limit
    inner_text = strip_html(inner_html or "")
    st.caption(f"{len(inner_text)}/500 characters")
    if len(inner_text) > 500:
        st.error("❌ Too long! Please keep under 500 characters.")

    # — Assemble full HTML payload —
    wrapper_start = '''
    <html><body style="font-family:Arial,sans-serif;margin:0;padding:0;">
     <div style="background-color:#E0F7FA;padding:24px;"><div style="margin-top:20px;">
      <div style="background-color:#FFFACD;padding:16px;border-radius:8px;">
       <h2 style="color:#4CAF50;margin-top:0;">Your Weekly Digest ☀️</h2>
    '''
    wrapper_end = '''
      </div>
      <p style="font-style:italic;color:#3994cc;">
        Stay inspired and informed.<br>
        Feel free to <b>give me feedback</b> anytime—love to hear from you! ❤️<br>
        - Andrew
      </p>
     </div></div>
     <div style="background-color:#F0F0F0;padding:16px;font-size:0.9em;color:#555;text-align:center;">
       You received this because you’re subscribed to Andrew’s newsletter.<br>
       <a href="mailto:{your_email}">Unsubscribe</a> by emailing me.
     </div>
    </body></html>
    '''.format(your_email=my_email)

    html_content = wrapper_start + (inner_html or "") + wrapper_end

    # — Plain-text fallback —
    plain_body = st.text_area(
        "Plain-text email (fallback)", 
        value=f"Your Week {week_no} newsletter is attached.\nIf you can’t see HTML, please check the PDF."
    )

    # — Action buttons side by side —
    col_test, col_send = st.columns([1,1])
    with col_test:
        if st.button("📧 Test Send to Me"):
            if len(inner_text) <= 500:
                pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
                send_newsletter(
                    csv_path=None,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_content,
                    attachment_path=pdf_path,
                    debug_email=my_email
                )
                st.success("✅ Test email sent to you.")
            else:
                st.error("Fix your highlight box first!")

    with col_send:
        if st.button("📤 Send & Log"):
            if len(inner_text) <= 500:
                # 1️⃣ generate PDF
                pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
                # 2️⃣ send to real subscribers
                send_newsletter(
                    csv_path=None,       # swap in path to your live CSV
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_content,
                    attachment_path=pdf_path
                )
                st.success("✅ Newsletter sent to all subscribers.")
                # 3️⃣ record in history sheet
                week_tag = f"25w{week_no:02d}"
                append_history(week_tag, payload)
                st.success("✅ Logged to News-hist.")
            else:
                st.error("Fix your highlight box first!")

# ––– Tab 5: Subscriber management –––
with tab_subs:
    st.header("Manage Subscriber List")
    df_subs = load_subscribers()
    st.dataframe(df_subs)

    add_email = st.text_input("Add email", key="add_email")
    if st.button("➕ Add subscriber"):
        add_subscriber(add_email)

    drop_email = st.text_input("Remove email", key="drop_email")
    if st.button("➖ Remove subscriber"):
        remove_subscriber(drop_email)