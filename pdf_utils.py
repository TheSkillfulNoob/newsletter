import fitz
import html
import os
from pathlib import Path
import streamlit as st
from datetime import date

image_grid_rects = [
    fitz.Rect(40, 50, 260, 270),
    fitz.Rect(310, 50, 550, 270),
    fitz.Rect(40, 315, 260, 535),
    fitz.Rect(310, 315, 550, 535),
    fitz.Rect(40, 580, 260, 800),
    fitz.Rect(310, 580, 550, 800),
]

def render_pdf_from_payload(payload, template_path, output_pdf, anchors):
    template_path = Path(template_path)
    if not template_path.exists() or not template_path.name.endswith(".pdf"):
        st.error("❌ Template must be a valid .pdf file.")
        return None

    template_doc = fitz.open(str(template_path))
    template_page = template_doc[0]
    doc = fitz.open()

    page1 = doc.new_page(width=template_page.rect.width, height=template_page.rect.height)
    page1.show_pdf_page(page1.rect, template_doc, 0)
    st.write("✅ page1 parent:", page1.parent is not None and page1.parent.is_pdf)

    insert_main_content(page1, payload, anchors, template_page)

    page2 = None
    if payload.get("fact_images"):
        page2 = doc.new_page(width=595, height=842)
        insert_fact_images(page2, payload)

    doc.save(output_pdf, deflate=True, garbage=4)
    return output_pdf

def insert_main_content(page, payload, anchors, font_source_page):
    font_tag, font_name = None, None
    for fid, _, _, fname, tag, _ in font_source_page.get_fonts():
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

    text_keys = [k for k in anchors if not k.startswith("img") and k in payload and isinstance(payload[k], str)]
    for key in text_keys:
        html_snip = make_html(payload[key], is_title=(key == "title"))
        try:
            page.insert_htmlbox(anchors[key], html_snip, scale_low=0.5, overlay=True)
        except OverflowError:
            continue

    for img_key in ["img_rect", "img_weekly"]:
        if payload.get(img_key) and os.path.exists(payload[img_key]):
            page.insert_image(anchors[img_key], filename=payload[img_key], keep_proportion=True, overlay=True)

def insert_fact_images(page, payload):
    st.write("✅ page2 parent:", page.parent is not None and page.parent.is_pdf)
    week_no = int(date.today().strftime("%V"))
    heading = f"Week {week_no}: Selected Graphs / Charts"
    page.insert_textbox(fitz.Rect(40, 15, 550, 40), heading, fontsize=14, align=1, color=(0, 0, 0))
    for i, item in enumerate(payload["fact_images"][:6]):
        rect = image_grid_rects[i]
        if os.path.exists(item["img"]):
            page.insert_image(rect, filename=item["img"], keep_proportion=True, overlay=True)
        caption = item.get("caption", "")
        if caption.strip():
            caption_rect = fitz.Rect(rect.x0, rect.y1 + 4, rect.x1, rect.y1 + 28)
            page.insert_textbox(caption_rect, caption, fontsize=10, color=(0, 0, 0))

def generate_debug_page1(template_path, anchors, payload, output_path="debug_page1.pdf"):
    doc = fitz.open(template_path)
    page = doc[0]
    shape = page.new_shape()
    for key, rect in anchors.items():
        shape.draw_rect(rect)
        shape.draw_circle(fitz.Point(rect.x0, rect.y0), 4)
        page.insert_textbox(fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1),
                            f"{key}: {payload.get(key, '')[:40]}", fontsize=8)
    shape.finish(color=(0, 0, 1), width=0.5)
    shape.commit()
    doc.save(output_path, deflate=True)
    return output_path

def generate_debug_page2(payload, output_path="debug_page2.pdf", width=595, height=842):
    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    shape = page.new_shape()
    for i, rect in enumerate(image_grid_rects):
        shape.draw_rect(rect)
        shape.draw_circle(fitz.Point(rect.x0, rect.y0), 4)
        if i < len(payload.get("fact_images", [])):
            caption = payload["fact_images"][i].get("caption", "")
            page.insert_textbox(fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1),
                                caption[:40], fontsize=8)
    shape.finish(color=(0, 1, 0), width=0.5)
    shape.commit()
    doc.save(output_path, deflate=True)
    return output_path
