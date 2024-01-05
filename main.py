# scrapes info from https://www.london-stadium.com/events/all.html once a day,
# filters for events happening within 24hrs
# sends notification of any events in the next 24hrs

import requests
from bs4 import BeautifulSoup
import smtplib
import os
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sender_email = os.getenv("SENDER_EMAIL")
sender_pwrd = os.getenv("SENDER_PWRD")
receiver_email = os.getenv("RECEIVER_EMAIL")

# scrape and format the data
res: requests.Response = requests.get("https://www.london-stadium.com/events/all.html")

res_html: bytes = res.content

parsed_html = BeautifulSoup(markup=res_html, features="html.parser")

event_elements = parsed_html.find_all(attrs={"class": "event-card"})

events_dict = dict()
for item in event_elements:
    # key is date and val is event name
    date_element = item.find("div", class_="event-card__date")["content"]
    event_name_element = item.find("div", class_="event-card__name").text

    # date from site is string like 2024-01-07T12:00:00+00:00
    # convert to datetime obj for comparisons and easier formatting later on
    date_element = datetime.fromisoformat(date_element)
    events_dict[date_element] = event_name_element


def filter_events(events_dict: dict, days_in_advance: int):
    today = datetime.now()
    tomorrow = today + timedelta(days=days_in_advance)

    events_dict = dict(sorted(events_dict.items()))
    filtered_events = dict()
    for date, event in events_dict.items():
        # make date tz aware
        if (
            today.replace(tzinfo=timezone.utc)
            <= date
            <= tomorrow.replace(tzinfo=timezone.utc)
        ):
            filtered_events[date] = event
        else:
            break
    return filtered_events


def format_date_for_printing(date: datetime):
    return date.strftime("%d %b %Y")


def construct_event_email(events: dict):
    # construct the message
    message = f"""
Uh oh! Looks like another fixture(s) at the London Stadium tomorrow :(

Parking might be a bit tough - good luck...

Event details:
    """
    for date, name in events.items():
        message += f"\n - {format_date_for_printing(date)}: {name}"

    message += "\n\nLots of love,\nBean x"

    return message


# Create the MIME object
message = MIMEMultipart()
message_body = construct_event_email(filter_events(events_dict, days_in_advance=1))
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = "Fixture(s) At London Stadium Tomorrow"

# Attach the text body to the email
message.attach(MIMEText(message_body, "plain"))
# send the data via mail
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_pwrd)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("Email sent successfully!")
except smtplib.SMTPAuthenticationError as e:
    print(f"Authentication failed. Check your credentials. Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
