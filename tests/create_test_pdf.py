from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def create_test_pdf(output_path: str = "test_document.pdf"):
    """Create a test PDF with entities and relationships."""
    c = canvas.Canvas(output_path, pagesize=letter)
    textobject = c.beginText()
    textobject.setTextOrigin(inch, 10*inch)
    textobject.setFont("Times-Roman", 12)

    content = """
John Doe works at TechCorp Inc. since 2020.
Alice Smith joined TechCorp in 2021.
Project Phoenix is a key initiative at TechCorp.
The project started on 2023-01-15.
John and Alice work together on Project Phoenix.
Cognitive Computing is a related concept.
"""
    
    for line in content.strip().split('\n'):
        textobject.textLine(line)
        
    c.drawText(textobject)
    c.save()
    print(f"Created test PDF: {output_path}")

if __name__ == "__main__":
    create_test_pdf() 