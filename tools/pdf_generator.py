import os
from fpdf import FPDF

def generate_pdf(heading: str, content: str) -> str:
    """
    Creates a formatted PDF document with a title and body text.
    Saves it directly to the user's Desktop.
    """
    print(f"\n[📝 J.A.R.V.I.S. is compiling document: '{heading}.pdf'...]")
    
    try:
        # Initialize the PDF engine
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add the Heading (Arial, Bold, Size 16)
        pdf.set_font("Arial", 'B', 16)
        # Using encoding to handle special characters properly
        pdf.cell(200, 10, txt=heading.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        
        # Add a line break
        pdf.ln(10)
        
        # Add the Content (Arial, Regular, Size 12)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=content.encode('latin-1', 'replace').decode('latin-1'))
        
        # Determine save location (User's Desktop)
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        desktop_path = os.path.join(user_profile, 'Desktop')
        
        # Clean the heading to make it a valid filename
        safe_filename = "".join([c for c in heading if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_filename = safe_filename.replace(" ", "_") + ".pdf"
        
        file_path = os.path.join(desktop_path, safe_filename)
        
        # Save the file
        pdf.output(file_path)
        
        return f"Successfully generated the PDF '{safe_filename}' and saved it to your Desktop."
        
    except Exception as e:
        return f"Failed to generate the PDF document. Error: {str(e)}"

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating Document Compilation Protocol...")
    
    test_heading = "Project JARVIS Diagnostic Report"
    test_content = (
        "This is a test of the automated PDF generation subsystem.\n\n"
        "If you are reading this, Mr.Pranav, it means the Python FPDF library "
        "has successfully compiled this text array into a portable document format and "
        "routed it to your desktop."
    )
    
    response = generate_pdf(test_heading, test_content)
    print(f"\nResult: {response}")