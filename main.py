from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from datetime import datetime, timedelta
from notion_client import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENTS = ["patescool@gmail.com", "pauloyatowo@gmail.com", "brilla.co.ng@gmail.com"]

notion = Client(auth=NOTION_TOKEN)

def get_tomorrow_posts():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    response = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
            "filter": {
                "property": "Scheduled Date",
                "date": {"equals": tomorrow.isoformat()}
            }
        }
    )
    return response["results"]

@app.get("/send-reminder")
def send_reminder():
    posts = get_tomorrow_posts()
    if posts:
        content = ""
        for post in posts:
            props = post["properties"]
            title = props["Campaign Title"]["title"][0]["plain_text"]
            scheduled = props["Scheduled Date"]["date"]["start"]
            fmt = props["Format"]["select"]["name"]
            platform = props["Platform"]["select"]["name"]
            audience = props["Target Audience"]["rich_text"][0]["plain_text"] if props["Target Audience"]["rich_text"] else "TBD"

            content += (
                f"🧼 <b>Campaign:</b> {title}<br>"
                f"📅 <b>Date:</b> {scheduled} | <b>Format:</b> {fmt} | <b>Platform:</b> {platform}<br>"
                f"🎯 <b>Audience:</b> {audience}<br>"
                f"✍️ <i>Make sure design and caption are ready today!</i><br><br>"
            )
    else:
        content = "✅ No posts scheduled for tomorrow. Rest easy or prep ahead!"

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = "🌟 Brillá.ng Content Reminder — What’s Up for Tomorrow?"
    msg.attach(MIMEText(content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
        return JSONResponse(content={"message": "✅ Reminder sent."}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
