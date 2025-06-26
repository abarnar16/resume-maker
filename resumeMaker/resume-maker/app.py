import os
import json
import time
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from openai import OpenAI
from your_pdf_generator import generate_resume_pdf
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")

openAIkey = os.environ.get("OPENAI_API_KEY")
if not openAIkey:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=openAIkey)


def scrape_linkedin_text(url):
    options = Options()
    # Comment out or remove headless mode to open real browser window
    # options.headless = True

    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        print("Please log in to LinkedIn in the opened browser window, then come back here and press Enter...")
        input()  # Wait for manual login
        time.sleep(3)  # Wait a moment after login

        body = driver.find_element("tag name", "body")
        text = body.text
    finally:
        driver.quit()
    return text


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_linkedin_url', methods=['POST'])
def process_linkedin_url():
    linkedin_url = request.form.get('linkedin_url', '').strip()
    if not linkedin_url:
        return "LinkedIn URL is required.", 400

    try:
        profile_text = scrape_linkedin_text(linkedin_url)
    except Exception as e:
        app.logger.error(f"Error scraping LinkedIn URL: {e}")
        return "Failed to scrape LinkedIn profile. Make sure the URL is public and correct.", 500

    prompt = f"""
Extract the following JSON from the LinkedIn profile text below:
- name
- title
- experience: list of roles with company, role, and years
- skills: list

Text:
{profile_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract structured resume data as JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        result_text = response.choices[0].message.content
        app.logger.info(f"OpenAI output: {result_text}")

        resume_info = json.loads(result_text)
        session['resume_data'] = resume_info
    except json.JSONDecodeError:
        app.logger.error("Failed to parse JSON from OpenAI response")
        return "Failed to parse data from LinkedIn profile text", 500
    except Exception as e:
        app.logger.error(f"OpenAI API error: {e}")
        return "Failed to process LinkedIn profile text", 500

    return redirect('/choose_template')


@app.route('/choose_template')
def choose_template():
    if 'resume_data' not in session:
        return redirect('/')
    return render_template('choose_template.html')


@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    template_id = request.form.get('template_id')
    if not template_id:
        return "Template ID is required.", 400

    data = session.get('resume_data')
    if not data:
        return redirect('/')

    try:
        pdf_bytes = generate_resume_pdf(data, template_id)
    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        return "Failed to generate resume PDF", 500

    return send_file(
        BytesIO(pdf_bytes),
        download_name='resume.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )


if __name__ == '__main__':
    app.run(debug=True)
