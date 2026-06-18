from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


pdf = canvas.Canvas("test.pdf", pagesize=A4)

pdf.drawString(
    100,
    750,
    "Hello Billing Engine!"
)

pdf.save()

print("PDF created successfully")