from fastapi import FastAPI
from notion_client import Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback

app = FastAPI()
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENTS = ["patescool@gmail.com", "pauloyatowo@gmail.com", "brilla.co.ng@gmail.com"]

notion = Client(auth=NOTION_TOKEN)

@app.get("/")
def read_root():
    return {"message": "Brillá.ng Reminder Service is live ✨"}

@app.get("/send-reminder")
def send_reminder():
    try:
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        response = notion.databases.query(
            **{
                "database_id": DATABASE_ID,
                "filter": {
                    "property": "Scheduled Date",
                    "date": {
                        "equals": tomorrow.isoformat()
                    }
                }
            }
        )
        posts = response["results"]
    except Exception as e:
        error_trace = traceback.format_exc()
        print("❌ Notion API error:\n", error_trace)
        return {"status": "error", "message": "Failed to query Notion", "trace": error_trace}

    if posts:
        content = ""
        for post in posts:
            props = post["properties"]
            title = props["Campaign Title"]["title"][0]["plain_text"]
            scheduled = props["Scheduled Date"]["date"]["start"]
            fmt = props["Format"]["select"]["name"]
            platform = props["Platform"]["select"]["name"]
            audience = (
                props["Target Audience"]["rich_text"][0]["plain_text"]
                if props["Target Audience"]["rich_text"]
                else "TBD"
            )

            content += (
                f"🧼 <b>Campaign:</b> {title}<br>"
                f"📅 <b>Date:</b> {scheduled} | <b>Format:</b> {fmt} | <b>Platform:</b> {platform}<br>"
                f"🎯 <b>Audience:</b> {audience}<br>"
                f"✍️ <i>Make sure design and caption are ready today!</i><br><br>"
            )
    else:
        content = "✅ No posts scheduled for tomorrow. Rest easy or prep ahead!"

    # Prepare email
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = "🌟 Brillá.ng Content Reminder — What’s Up for Tomorrow?"
    msg.attach(MIMEText(content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
        return {"status": "success", "message": "Reminder email sent successfully."}
    except Exception as e:
        error_trace = traceback.format_exc()
        print("❌ Email sending error:\n", error_trace)
        return {"status": "error", "message": "Failed to send email", "trace": error_trace}
