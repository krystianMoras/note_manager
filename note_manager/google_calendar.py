from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
import gcsa

import yaml

config = yaml.load(open("settings.yaml", "r"), Loader=yaml.FullLoader)


calendar_id = config["calendar_id"]

gc = GoogleCalendar(
    calendar_id,
    credentials_path="credentials.json",
    token_path="token.pickle",
)

gc.add_event(
    Event(
        summary="Test event",
        start=gcsa.utils.to_datetime("2021-01-01 00:00:00"),
        end=gcsa.utils.to_datetime("2021-01-01 01:00:00"),
    )
)
