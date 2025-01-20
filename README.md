# FastAPI Website Monitoring Application
This is a FastAPI-based application designed to monitor the status of web pages by scraping URLs and checking their HTTP status. If any pages are offline (not responding with status 200), the application sends an email notification.

## Features

- Scrapes all internal links from a given base URL.
- Checks the HTTP status of each link.
- Sends email alerts if offline pages are detected.
- Configurable via a `.env` file for sensitive data.

---

## Requirements

- Python 3.8 or higher
- BeautifulSoup (bs4)
- Requests
- Python-dotenv
- Uvicorn (for running the server)

---

1. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

1. Install Dependencies
```bash
pip install -r requirements.txt
```


## Configuration
1. Create a .env File
Create a .env file in the project root with the following variables:
```bash
SMTP_SERVER=mail.smtp2go.com
SMTP_PORT=2525
SMTP_USER=your-email-user
SMTP_PASS=your-email-password
DEFAULT_EMAIL=your-notification-email@example.com
```

* SMTP_SERVER: The SMTP server address.
* SMTP_PORT: The SMTP server port.
* SMTP_USER: The SMTP username for authentication.
* SMTP_PASS: The SMTP password for authentication.
* DEFAULT_EMAIL: The email address to send notifications.


## Usage
1. Start the Application
Run the FastAPI application using Uvicorn:
```bash
python app.py
```

The server will start and be available at:
```bash
http://127.0.0.1:8000/
```
Interactive API Documentation Access the Swagger UI:
```bash
http://127.0.0.1:8000/docs
```

2. Test the Application
Use curl, Postman, or a web browser to test the /monitor endpoint.

Example with curl:
curl "http://127.0.0.1:5000/monitor?base_url=https://example.com&max_depth=2"

Query Parameters:
base_url: The starting URL for scraping (default: https://www.urbiaparques.com.br).
max_depth: The depth of the scraping process (default: 2).

3. Sample Response
If all pages are online:
```bash
{
    "results": [
        {"url": "https://example.com", "status": "online", "code": 200},
        {"url": "https://example.com/page", "status": "online", "code": 200}
    ],
    "offline_pages": []
}
```

If some pages are offline:
```bash
{
    "results": [
        {"url": "https://example.com", "status": "online", "code": 200},
        {"url": "https://example.com/error", "status": "offline", "code": 404}
    ],
    "offline_pages": [
        {"url": "https://example.com/error", "status": "offline", "code": 404}
    ]
}
```

4. Email Notifications
If offline pages are detected, an email notification will be sent to the address specified in the DEFAULT_EMAIL variable.


## Development
Run the Application in Debug Mode
```bash
uvicorn app:app --reload
```