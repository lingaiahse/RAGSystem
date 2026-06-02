"""
Generate a small one-page PDF for testing.
Requires `reportlab` installed: `pip install reportlab`.

If reportlab is not available, this script will write a text placeholder with a .pdf extension.
"""
import os
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


def generate(path: str):
    if REPORTLAB_AVAILABLE:
        c = canvas.Canvas(path, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(72, 720, "Sample HR Policy")
        c.drawString(72, 700, "This is a generated test PDF for RAG ingestion.")
        c.drawString(72, 680, "Department: HR | Location: US | Role Level: L2")
        c.showPage()
        c.save()
        print(f"Generated PDF at {path}")
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("Sample HR Policy\nThis is a fallback placeholder PDF (text) for testing.\nReplace with a real PDF for proper ingestion.")
        print(f"Wrote placeholder file at {path} (install reportlab for a real PDF)")


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', 'backend', 'test_data', 'sample_policy_generated.pdf')
    out = os.path.normpath(out)
    generate(out)
