from io import BytesIO
from pypdf import PdfReader
from adapters.pdf_renderer.weasy import WeasyRenderer


def test_a4_contents_and_optional_corrections(catalog):
    article = catalog['articles'][3]
    pdf, pages = WeasyRenderer().render('Test A4', '2026-11-15', [article], corrections=['Updated title in the source record.'])
    assert pages == 5
    document = PdfReader(BytesIO(pdf))
    assert 'Corrections' in document.pages[1].extract_text()
    assert 'Updated title' in document.pages[-1].extract_text()
    links = {str(item.get_object().get('/Dest')) for item in document.pages[1]['/Annots']}
    assert links == {'article-3', 'references', 'corrections'}
