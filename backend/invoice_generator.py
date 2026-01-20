from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# --- Loudachris Brand Colors ---
COLOR_PRIMARY = colors.HexColor("#E357AB") # Brilliant Rose
COLOR_SECONDARY = colors.HexColor("#8C87C9") # Tropical Indigo
COLOR_TEXT = colors.HexColor("#122933") # Dark Navy
COLOR_BG = colors.HexColor("#F5F5F5") # Platinum White

def generate_invoice(filename, quote_data):
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
    # (Assuming text logic for now as we don't have an image asset, but would normally place logo top-left)
    story.append(Paragraph("TradieVoice Pro", title_style))
    story.append(Spacer(1, 12))
    
    # Customer Details
    story.append(Paragraph(f"To: {quote_data.get('customer_name', 'Valued Customer')}", normal_style))
    story.append(Spacer(1, 24))
    
    # Table Data
    data = [['Description', 'Qty', 'Unit Price', 'Total']]
    for item in quote_data.get('items', []):
        data.append([
            item['description'],
            str(item['quantity']),
            f"${item['unit_price']:.2f}",
            f"${item['total']:.2f}"
        ])
    
    # Add Total Row
    data.append(['', '', 'Grand Total:', f"${quote_data.get('total_amount', 0):.2f}"])

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
