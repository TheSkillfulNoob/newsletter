import fitz
import html
import os
from pathlib import Path

def render_pdf_from_payload(payload, template_path, output_pdf, anchors, debug=False):
    template_path = Path(template_path)
    if not template_path.exists():
        return None
    doc = fitz.open(str(template_path))

    font_tag, font_name = None, None
    for fid, _, _, fname, tag, _ in doc[0].get_fonts():
        if "KaiseiTokumin" in fname:
            font_tag, font_name = tag, fname
            break
    if not font_tag:
        font_name = "Helvetica"

    def make_html(src, is_title=False):
        if not src:
            return ""
        if src.lstrip().startswith("<"):
            return src
        if is_title:
            return f'<h1 style="font-family:\'{font_name}\';margin:0">{html.escape(src)}</h1>'
        return f'<div style="font-family:\'{font_name}\';font-size:11pt;line-height:13pt">{html.escape(src)}</div>'

    page = doc[0]
    # First: insert HTML content only (skip image keys explicitly)
    for key in payload:
        if key in ["img_rect", "img_weekly"]:
            continue
        html_snip = make_html(payload.get(key, ""), is_title=(key == "title"))
        try:
            page.insert_htmlbox(anchors[key], html_snip, scale_low=0.5, overlay=True)
        except OverflowError:
            continue

    for img_key in ["img_rect", "img_weekly"]:
        if payload.get(img_key) and os.path.exists(payload[img_key]):
            page.insert_image(fitz.Rect(anchors[img_key]), filename=payload[img_key], keep_proportion=True, overlay=True)

    if debug:
        red, blue = (1, 0, 0), (0, 0, 1)
        for key, rect in anchors.items():
            page.draw_rect(rect, color=blue, width=0.5)
            page.draw_circle(fitz.Point(rect.x0, rect.y0), 4, color=red)

    doc.save(output_pdf, deflate=True, garbage=4)
    return output_pdf
