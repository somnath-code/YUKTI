from io import BytesIO
from pypdf import PdfReader
from adapters.pdf_renderer.weasy import WeasyRenderer


def test_language_and_tag_tree(catalog):
    data, _ = WeasyRenderer().render('Accessibility check', '2026-11-15', catalog['articles'][:1])
    root = PdfReader(BytesIO(data)).trailer['/Root']
    assert root['/Lang'] == 'en-GB' and root.get('/StructTreeRoot')
