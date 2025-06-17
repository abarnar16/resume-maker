from fpdf import FPDF

def generate_resume_pdf(data, template_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"{data['name']} - {data['title']}", ln=True)

    pdf.cell(200, 10, txt="Experience:", ln=True)
    for job in data['experience']:
        pdf.cell(200, 10, txt=f"{job['role']} at {job['company']} ({job['years']})", ln=True)


    pdf.cell(200, 10, txt="Skills: " + ', '.join(data['skills']), ln=True)

    return pdf.output(dest='S').encode('latin1')  # Return PDF as bytes

