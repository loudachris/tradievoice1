from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from reportlab.lib.utils import ImageReader
import base64
import io

# --- Loudachris Brand Colors ---
COLOR_PRIMARY = colors.HexColor("#E357AB") # Brilliant Rose
COLOR_SECONDARY = colors.HexColor("#8C87C9") # Tropical Indigo
COLOR_TEXT = colors.HexColor("#122933") # Dark Navy
COLOR_BG = colors.HexColor("#F5F5F5") # Platinum White

def generate_invoice(filename, quote_data, user_profile):
    """
    Generates a PDF invoice with Loudachris Branding.
    quote_data expects dict: {
        'customer_name': str,
        'items': [{'description', 'quantity', 'unit_price', 'total'}],
        'total_amount': float,
        'notes': str
    }
    """
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom Styles (simulating Filson Soft/Nunito with accessible standards)
    title_style = ParagraphStyle(
        'LoudachrisTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold', # Fallback as we don't have custom font files loaded
        fontSize=24,
        textColor=COLOR_PRIMARY,
        spaceAfter=20
    )
    
    normal_style = ParagraphStyle(
        'LoudachrisBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=COLOR_TEXT
    )

    # Logo / Header
    if user_profile.logo_base64:
        try:
            # Decode base64 image
            image_data = base64.b64decode(user_profile.logo_base64.split(',')[1])
            image_stream = io.BytesIO(image_data)
            img = ImageReader(image_stream)
            
            # Draw Image (manually drawing on canvas might be easier for positioning, 
            # but using Flowables keeps it simple for now or we use a Table for header)
            # Let's use a Table for the Header to align Logo Left and Text Right
            
            # Limited Image Flowable support in simpledoc, so let's stick to text for MVP stability
            # or try a simple Image flowable.
            from reportlab.platypus import Image
            logo = Image(image_stream, width=2*inch, height=1*inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error loading logo: {e}")
            story.append(Paragraph(user_profile.business_name, title_style))
    else:
        story.append(Paragraph(user_profile.business_name, title_style))

    story.append(Spacer(1, 12))
    
    # Business Details (ABN etc)
    if user_profile.abn:
        story.append(Paragraph(f"ABN: {user_profile.abn}", normal_style))
    
    invoice_title = "TAX INVOICE" if user_profile.gst_registered else "INVOICE"
    story.append(Paragraph(invoice_title, ParagraphStyle('InvoiceTitle', parent=styles['Heading2'], textColor=COLOR_SECONDARY)))
    story.append(Spacer(1, 12))
    story.append(Spacer(1, 12))
    
    # Customer Details
    story.append(Paragraph(f"To: {quote_data.get('customer_name', 'Valued Customer')}", normal_style))
    story.append(Spacer(1, 24))
    
    # Table Data
    data = [['Description', 'Qty', 'Unit Price', 'Total']]
    subtotal = 0.0
    
    for item in quote_data.get('items', []):
        row_total = item['total']
        subtotal += row_total
        data.append([
            item['description'],
            str(item['quantity']),
            f"${item['unit_price']:.2f}",
            f"${row_total:.2f}"
        ])
    
    # GST Logic
    if user_profile.gst_registered:
        gst_amount = subtotal * 0.10
        total_with_gst = subtotal + gst_amount
        
        data.append(['', '', 'Subtotal:', f"${subtotal:.2f}"])
        data.append(['', '', 'GST (10%):', f"${gst_amount:.2f}"])
        data.append(['', '', 'Grand Total:', f"${total_with_gst:.2f}"])
    else:
        # No GST
        data.append(['', '', 'Grand Total:', f"${subtotal:.2f}"])

    # Table Styling (Loudachris)
    table = Table(data, colWidths=[4*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        # Header Row
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Rows
        ('BACKGROUND', (0, 1), (-1, -1), COLOR_BG),
        ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        
        # Total Row
        ('BACKGROUND', (-2, -1), (-1, -1), COLOR_PRIMARY),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.white),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 24))
    
    # Notes
    if quote_data.get('notes'):
        story.append(Paragraph("Notes:", ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold')))
        story.append(Paragraph(quote_data['notes'], normal_style))
        
    doc.build(story)

if __name__ == "__main__":
    # Test Data
    sample_data = {
        "customer_name": "John Doe",
        "items": [
            {"description": "Install new lighting fixtures", "quantity": 5, "unit_price": 120.00, "total": 600.00},
            {"description": "Rewire living room", "quantity": 1, "unit_price": 500.00, "total": 500.00}
        ],
        "total_amount": 1100.00,
        "notes": "Work completed on time. Warranty valid for 12 months."
    }
    generate_invoice("test_invoice.pdf", sample_data)
    print("Generated test_invoice.pdf")
