from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL")

def send_email(subject, body, to_email):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        app.logger.info(f"Email sent to {to_email} successfully.")
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")

def fetch_urls_from_site(base_url, max_depth=2):
    visited = set()
    to_visit = [(base_url, 0)]
    urls = []

    while to_visit:
        current_url, depth = to_visit.pop(0)
        if current_url in visited or depth > max_depth:
            continue

        try:
            response = requests.get(current_url, timeout=10)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            visited.add(current_url)
            urls.append(current_url)

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                if is_valid_url(full_url, base_url) and full_url not in visited:
                    to_visit.append((full_url, depth + 1))
        except Exception as e:
            logger.error(f"Error processing {current_url}: {e}")
    return list(set(urls))

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    base_parsed = urlparse(base_url)
    return parsed_url.netloc == base_parsed.netloc and parsed_url.scheme in ['http', 'https']

def check_url_status(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"url": url, "status": "online", "code": response.status_code}
        else:
            return {"url": url, "status": "offline", "code": response.status_code}
    except Exception as e:
        return {"url": url, "status": "offline", "error": str(e)}

@app.route('/monitor', methods=['GET'])
def monitor_website():
    base_url = request.args.get("base_url", "https://www.urbiaparques.com.br")
    max_depth = int(request.args.get("max_depth", 2))

    logger.info(f"Starting site scraping: {base_url}")
    urls = fetch_urls_from_site(base_url, max_depth)

    logger.info(f"Found URLs: {urls}")

    results = [check_url_status(url) for url in urls]
    offline_pages = [res for res in results if res["status"] == "offline"]

    if offline_pages:
        logger.warning(f"Offline pages: {offline_pages}")

        offline_pages_list = "\n".join([f"{page['url']} - {page.get('error', 'Code: ' + str(page['code']))}" for page in offline_pages])
        subject = "⚠️ Alert: Offline Pages Detected"
        body = f"The following pages are offline:\n\n{offline_pages_list}"

        send_email(subject, body, DEFAULT_EMAIL)

    return jsonify({
        "results": results,
        "offline_pages": offline_pages
    })

if __name__ == '__main__':
    app.run(debug=True)
