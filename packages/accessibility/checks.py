from io import BytesIO
from pypdf import PdfReader
from packages.core.settings import policy


def validate_pdf(data: bytes, expected: int) -> None:
    pdf = PdfReader(BytesIO(data))
    cfg, dimensions = policy('print'), policy('page')
    if len(pdf.pages) != expected or not 4 <= expected <= cfg['max_pdf_pages']:
        raise ValueError('Unexpected PDF page count')
    tree = pdf.trailer['/Root']
    if cfg['require_language'] and tree.get('/Lang') is None:
        raise ValueError('PDF language metadata is missing')
    if cfg['require_tags'] and tree.get('/StructTreeRoot') is None:
        raise ValueError('Tagged PDF structure is missing')
    for index, page in enumerate(pdf.pages):
        box, tolerance = page.mediabox, dimensions['tolerance_pt']
        if (abs(float(box.width) - dimensions['width_pt']) > tolerance
                or abs(float(box.height) - dimensions['height_pt']) > tolerance):
            raise ValueError('Expected A4 PDF pages')
        if cfg['number_after_cover'] and index:
            if str(index + 1) not in (page.extract_text() or '').splitlines()[-3:]:
                raise ValueError(f'Page {index + 1} lacks a page number')
