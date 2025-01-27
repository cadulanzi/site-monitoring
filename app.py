import datetime
import json
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import logging
from fastapi_utils.tasks import repeat_every
import boto3
from botocore.exceptions import NoCredentialsError

# Load environment variables
load_dotenv()

# Initialize FastAPI and Logger
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Email sender function
def send_email(subject: str, body: str, to_email: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# URL validation function
def is_valid_url(url: str, base_url: str) -> bool:
    parsed_url = urlparse(url)
    base_parsed = urlparse(base_url)
    return parsed_url.netloc == base_parsed.netloc and parsed_url.scheme in ["http", "https"]

# Web scraping function
def fetch_urls_from_site(base_url: str, max_depth: int = 2) -> list:
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

            soup = BeautifulSoup(response.content, "html.parser")
            visited.add(current_url)
            urls.append(current_url)

            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(base_url, href)
                if is_valid_url(full_url, base_url) and full_url not in visited:
                    to_visit.append((full_url, depth + 1))
        except Exception as e:
            logger.error(f"Error processing {current_url}: {e}")
    return list(set(urls))

# URL status checker function
def check_url_status(url: str) -> dict:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"url": url, "status": "online", "code": response.status_code}
        else:
            return {"url": url, "status": "offline", "code": response.status_code}
    except Exception as e:
        return {"url": url, "status": "offline", "error": str(e)}

# Pydantic model for the response
class MonitorResponse(BaseModel):
    results: list
    offline_pages: list
    
def send_to_bucket(bucket_name, s3_file_name, results):
    s3 = boto3.client('s3')
    bucket_name = os.getenv("S3_BUCKET_NAME")
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_file_name,
            Body=json.dumps(results),
            ContentType='application/json'
        )
        logger.info(f"Results stored in S3 bucket {bucket_name} as {s3_file_name}")
    except NoCredentialsError:
        logger.error("Credentials not available for S3")

@app.get("/monitor", response_model=MonitorResponse)
def monitor_website(
    base_url: str = Query("https://www.urbiaparques.com.br", description="Base URL to scrape"),
    max_depth: int = Query(2, description="Maximum scraping depth"),
):
    logger.info(f"Starting site scraping: {base_url}")
    urls = fetch_urls_from_site(base_url, max_depth)

    logger.info(f"Found URLs: {urls}")

    results = [check_url_status(url) for url in urls]
    
    hour = datetime.datetime.now().strftime("%H")
    day = datetime.datetime.now().strftime("%d")
    year = datetime.datetime.now().strftime("%Y")
    month = datetime.datetime.now().strftime("%m")
    send_to_bucket(S3_BUCKET_NAME, f"{base_url}/{year}/{month}/{day}/{hour}.json", results)
    
    offline_pages = [res for res in results if res["status"] == "offline"]

    if offline_pages:
        logger.warning(f"Offline pages: {offline_pages}")
        offline_pages_list = "\n".join(
            [f"{page['url']} - {page.get('error', 'Code: ' + str(page['code']))}" for page in offline_pages]
        )
        subject = "⚠️ Alert: Offline Pages Detected"
        body = f"The following pages are offline:\n\n{offline_pages_list}"
        send_email(subject, body, DEFAULT_EMAIL)

    return JSONResponse(content={"results": results, "offline_pages": offline_pages})

@app.on_event("startup")
@repeat_every(seconds=60)
def scheduled_monitoring():
    base_url = "https://www.urbiaparques.com.br"
    max_depth = 2
    logger.info(f"Starting scheduled site scraping: {base_url}")
    urls = fetch_urls_from_site(base_url, max_depth)

    logger.info(f"Found URLs: {urls}")

    results = [check_url_status(url) for url in urls]
    
    hour = datetime.datetime.now().strftime("%H")
    day = datetime.datetime.now().strftime("%d")
    year = datetime.datetime.now().strftime("%Y")
    month = datetime.datetime.now().strftime("%m")
    send_to_bucket(S3_BUCKET_NAME, f"urbiaparques/{year}/{month}/{day}/{hour}.json", results)

    offline_pages = [res for res in results if res["status"] == "offline"]

    if offline_pages:
        logger.warning(f"Offline pages: {offline_pages}")
        offline_pages_list = "\n".join(
            [f"{page['url']} - {page.get('error', 'Code: ' + str(page['code']))}" for page in offline_pages]
        )
        subject = "⚠️ Alert: Offline Pages Detected"
        body = f"The following pages are offline:\n\n{offline_pages_list}"
        send_email(subject, body, DEFAULT_EMAIL)
