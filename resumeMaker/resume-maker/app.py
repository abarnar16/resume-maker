from flask import Flask, render_template, request, redirect, send_file
from io import BytesIO
import os
from openai import OpenAI
from your_pdf_generator import generate_resume_pdf  # your PDF function

app = Flask(__name__)

# Initialize OpenAI client with your API key
client = OpenAI(api_key=openAIkey)

resume_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    linkedin_text = request.form['linkedin_text']

    prompt = f"""
Extract the following JSON from the LinkedIn profile text below:
- name
- title
- experience: list of roles with company, role, and years
- skills: list

Text:
{linkedin_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4" if available
            messages=[
                {"role": "system", "content": "Extract structured resume data as JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        result_text = response.choices[0].message.content
        print("GPT Output:", result_text)
        resume_data['info'] = eval(result_text)  # Be careful using eval in production!
    except Exception as e:
        print("OpenAI API error:", e)
        return "Failed to process LinkedIn text", 500

    return redirect('/choose_template')

@app.route('/choose_template')
def choose_template():
    return render_template('choose_template.html')

@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    template_id = request.form['template_id']
    data = resume_data.get('info')
    pdf_bytes = generate_resume_pdf(data, template_id)
    return send_file(BytesIO(pdf_bytes),
                     download_name='resume.pdf',
                     as_attachment=True,
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
