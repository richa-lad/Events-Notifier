# scrapes info from https://www.london-stadium.com/events/all.html once a day,
# filters for events happening within 24hrs
# sends notification of any events in the next 24hrs

import requests
from bs4 import BeautifulSoup

res: requests.Response = requests.get("https://www.london-stadium.com/events/all.html")

res_html: bytes = res.content

parsed_html = BeautifulSoup(markup=res_html, features="html.parser")

event_elements = parsed_html.find_all(attrs={"class": "event-card"})

events_dict = dict()
for item in event_elements:
    # key is date and val is event name
    date_element = item.find("div", class_="event-card__date")["content"]
    event_name_element = item.find("div", class_="event-card__name").text
    events_dict[date_element] = event_name_element

print(events_dict)
