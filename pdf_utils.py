import fitz
import html
import os
from pathlib import Path
import streamlit as st

image_grid_rects = [
    fitz.Rect(40, 40, 280, 230),
    fitz.Rect(310, 40, 550, 230),
    fitz.Rect(40, 250, 280, 440),
    fitz.Rect(310, 250, 550, 440),
    fitz.Rect(40, 460, 280, 650),
    fitz.Rect(310, 460, 550, 650),
]

def render_pdf_from_payload(payload, template_path, output_pdf, anchors, debug=False):
    template_path = Path(template_path)
    if not template_path.exists():
        st.error("❌ Template file does not exist.")
        return None
    if not template_path.name.endswith(".pdf"):
        st.error("❌ Template file must be a .pdf document.")
        return None

    # Open original template and clone into new doc
    original = fitz.open(str(template_path))
    new_doc = fitz.open()
    new_doc.insert_pdf(original, from_page=0, to_page=0)
    page1 = new_doc[0]

    # Detect font
    font_tag, font_name = None, None
    for fid, _, _, fname, tag, _ in page1.get_fonts():
        if "KaiseiTokumin" in fname:
            font_tag, font_name = tag, fname
            break
    if not font_tag:
        font_name = "Helvetica"

    def make_html(src, is_title=False):
        if not src:
            return ""
        if isinstance(src, str) and src.lstrip().startswith("<"):
            return src
        if is_title:
            return f'<h1 style="font-family:\'{font_name}\';margin:0">{html.escape(str(src))}</h1>'
        return f'<div style="font-family:\'{font_name}\';font-size:11pt;line-height:13pt">{html.escape(str(src))}</div>'

    # Insert HTML text boxes
    text_keys = [k for k in anchors if not k.startswith("img") and k in payload and isinstance(payload[k], str)]
    for key in text_keys:
        html_snip = make_html(payload[key], is_title=(key == "title"))
        try:
            page1.insert_htmlbox(anchors[key], html_snip, scale_low=0.5, overlay=True)
        except OverflowError:
            continue

    # Insert first page images
    for img_key in ["img_rect", "img_weekly"]:
        if payload.get(img_key) and os.path.exists(payload[img_key]):
            page1.insert_image(anchors[img_key], filename=payload[img_key], keep_proportion=True, overlay=True)
        else:
            st.warning(f"⚠️ Image file for '{img_key}' not found or not uploaded.")

    # ───────── Add second page with image grid
    if payload.get("fact_images"):
        new_doc.new_page()
        page2 = new_doc[-1]

        for i, item in enumerate(payload["fact_images"][:6]):
            rect = image_grid_rects[i]
            if os.path.exists(item["img"]):
                page2.insert_image(rect, filename=item["img"], keep_proportion=True, overlay=True)
            caption = item.get("caption", "")
            if caption.strip():
                caption_rect = fitz.Rect(rect.x0, rect.y1 + 4, rect.x1, rect.y1 + 28)
                page2.insert_textbox(caption_rect, caption, fontsize=10, color=(0, 0, 0))

        if debug:
            red, blue = (1, 0, 0), (0, 0, 1)
            for key, rect in anchors.items():
                page1.draw_rect(rect, color=blue, width=0.5)
                page1.draw_circle(fitz.Point(rect.x0, rect.y0), 4, color=red)
            for rect in image_grid_rects:
                page2.draw_rect(rect, color=blue, width=0.5)
                page2.draw_circle(fitz.Point(rect.x0, rect.y0), 4, color=red)

    new_doc.save(output_pdf, deflate=True, garbage=4)
    return output_pdf