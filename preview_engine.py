import fitz
from PIL import Image
import io


def render_pdf_preview(file_path):
    """
    渲染 PDF 第一页为图片
    """
    doc = fitz.open(file_path)

    if len(doc) == 0:
        doc.close()
        return None

    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img