import streamlit as st
from datetime import date
from setup import configure_page, authenticate
from ui_input import handle_main_content, handle_fact_content, strip_html
from pdf_utils import (
    render_pdf_from_payload,
    generate_debug_page1,
    generate_debug_page2,
)

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

TEMPLATE_PATH = "Weekly-Newsletter-Template-v4.pdf"
week_no      = int(date.today().strftime("%V"))
OUTPUT_PDF   = f"preview_week_{week_no}.pdf"
ISSUE_TAG    = f"25w{week_no}"
my_email = "theskillfulnoob2002@gmail.com"

# anchors and section_config as before…
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
    st.header("Send Newsletter & Log to History")
    # 1) regenerate PDF if not already
    subject = st.text_input("Email subject", key="mail_subject",
        value=f"Week {week_no}, {date.today().year} Newsletter")
    html_body = st.text_area("HTML body", height=200, key="mail_html",
        value=st.session_state.get("last_html", ""))  # or re-generate from payload
    plain_body = st.text_area("Plain-text body", height=100,
        value="Your newsletter is attached. Please view the PDF.")

    if st.button("📤 Send & Log"):
        # send
        pdf_path = render_pdf_from_payload(payload, TEMPLATE_PATH, OUTPUT_PDF, anchors)
        send_newsletter(
            csv_path=None,                    # production: path to subscribers csv
            subject=subject,
            plain_body=plain_body,
            html_body=html_body,
            attachment_path=pdf_path,
            debug_email = my_email
        )
        st.success("✅ Email sent.")
        # log
        week_tag = f"w{week_no:02d}{date.today().year%100}"
        append_history(week_tag, payload)
        st.success("✅ Logged to News-hist sheet.")

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