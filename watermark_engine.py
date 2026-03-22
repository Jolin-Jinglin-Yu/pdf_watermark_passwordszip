import io
import os
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


# 注册中文字体（内置中文字体，适合简体中文）
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _create_watermark_pdf(page_width, page_height, text, opacity=0.3, rotation=-45, font_size=36):
    """
    生成单页水印 PDF（二进制）
    """
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # 半透明灰色
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=opacity))

    # 关键：使用支持中文的字体
    c.setFont("STSong-Light", font_size)

    # 页面中心旋转
    c.saveState()
    c.translate(page_width / 2, page_height / 2)
    c.rotate(rotation)

    # 居中画文字
    text_width = pdfmetrics.stringWidth(text, "STSong-Light", font_size)
    c.drawString(-text_width / 2, 0, text)

    c.restoreState()
    c.save()
    packet.seek(0)
    return packet.read()


def add_watermark_to_pdf(
    input_path,
    output_path,
    watermark_text,
    opacity=0.3,
    rotation=-45,
    font_size=36,
):
    """
    给 PDF 每一页叠加文字水印，并保存到 output_path
    """
    src_doc = fitz.open(input_path)
    out_doc = fitz.open()

    for page in src_doc:
        rect = page.rect
        page_width = rect.width
        page_height = rect.height

        # 原页复制到新文档
        new_page = out_doc.new_page(width=page_width, height=page_height)
        new_page.show_pdf_page(rect, src_doc, page.number)

        # 生成同尺寸水印页
        wm_pdf_bytes = _create_watermark_pdf(
            page_width=page_width,
            page_height=page_height,
            text=watermark_text,
            opacity=opacity,
            rotation=rotation,
            font_size=font_size,
        )

        wm_doc = fitz.open(stream=wm_pdf_bytes, filetype="pdf")
        new_page.show_pdf_page(rect, wm_doc, 0, overlay=True)
        wm_doc.close()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_doc.save(output_path)
    out_doc.close()
    src_doc.close()

    return output_path