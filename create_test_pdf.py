from fpdf import FPDF
import os

def create_sample_pdf():
    # Make sure uploads directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Create PDF object
    pdf = FPDF()
    
    # Add a page
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", size=12)
    
    # Add content
    pdf.cell(200, 10, txt="SAMPLE COMPANY ANNUAL REPORT", ln=True, align='C')
    pdf.ln(10)
    
    # Business Overview
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="BUSINESS OVERVIEW", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="Sample Company Inc. is a technology company that develops cloud-based software solutions. Our main products include project management tools and data analytics platforms.")
    pdf.ln(5)
    
    # Competitive Advantages
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="COMPETITIVE ADVANTAGES", ln=True)
    pdf.set_font("Arial", size=12)
    advantages = [
        "- Proprietary technology",
        "- Strong brand recognition",
        "- Network effects",
        "- High switching costs"
    ]
    for adv in advantages:
        pdf.cell(200, 10, txt=adv, ln=True)
    pdf.ln(5)
    
    # Financial Highlights
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="FINANCIAL HIGHLIGHTS", ln=True)
    pdf.set_font("Arial", size=12)
    financials = [
        "- Revenue: $450 million (up 23%)",
        "- Gross Margin: 72%",
        "- Net Income: $65 million"
    ]
    for fin in financials:
        pdf.cell(200, 10, txt=fin, ln=True)
    pdf.ln(5)
    
    # Management Discussion
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="MANAGEMENT DISCUSSION", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="Our leadership team remains focused on long-term growth rather than short-term profits. The management team has extensive experience in the software industry.")
    pdf.ln(5)
    
    # Risks and Challenges
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="RISKS AND CHALLENGES", ln=True)
    pdf.set_font("Arial", size=12)
    risks = [
        "- Increasing competition",
        "- Rapid technological change",
        "- Cybersecurity threats"
    ]
    for risk in risks:
        pdf.cell(200, 10, txt=risk, ln=True)
    pdf.ln(5)
    
    # Outlook
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(200, 10, txt="OUTLOOK", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="We remain optimistic about our future growth prospects. The total addressable market for our solutions is expected to grow at 15% annually for the next five years.")
    
    # Save PDF to the uploads directory
    pdf_path = "uploads/sample_annual_report.pdf"
    pdf.output(pdf_path)
    print(f"Sample PDF created successfully at {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_sample_pdf()