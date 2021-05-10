from bs4 import BeautifulSoup
from functools import cache
from dataclasses import dataclass
import requests
import re
import datetime

from .errors import ConflictError
from .user import User


class LancasterSportsCentre:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.user = User.from_session(self.login())

    @cache
    def login(self):
        session = requests.Session()
        login_page = session.get(
            "https://lancaster.legendonlineservices.co.uk/enterprise/account/login"
        )
        token = re.search(
            r"name=\"__RequestVerificationToken\" type=\"hidden\" value=\"(.*?)\"",
            login_page.text,
        )

        if token is None:
            raise ConnectionError(
                "The Lancaster Sports Centre website seems to be down."
            )

        token = token.group(1)

        login_confirmation = session.post(
            "https://lancaster.legendonlineservices.co.uk/enterprise/account/login",
            data={
                "login.Email": self.username,
                "login.Password": self.password,
                "login.RedirectURL": "",
                "__RequestVerificationToken": token,
            },
            allow_redirects=False,
        )

        if login_confirmation.status_code == 302:
            return session
        else:
            raise ValueError("Login failed.")

    def checkout(self):
        session = self.login()
        resp = session.get(
            "https://lancaster.legendonlineservices.co.uk/enterprise/Basket/Pay",
            allow_redirects=False,
        )
        if resp.status_code == 302:
            session.get(
                "https://lancaster.legendonlineservices.co.uk/enterprise/basket/paymentconfirmed"
            )

        return resp.status_code == 302

    def bookings(self):
        with self.login() as s:
            bookings_page = s.get(
                "https://lancaster.legendonlineservices.co.uk/enterprise/BookingsCentre/MyBookings"
            )
            bookings_parsed = re.findall(
                r"<h5 class='TextMembers'>(.*?)<\/h5><p> \((.+?)\)<br \/>Location: (.*?)<br \/>Date: (.*?) <",
                bookings_page.text,
            )
            return [Booking.from_tuple(data) for data in bookings_parsed]

    def get_slots(self, category, activity):
        s = self.login()

        club_data = {
            "club": 1,
            "X-Requested-With": "XMLHttpRequest",
        }
        s.post(
            "https://lancaster.legendonlineservices.co.uk/enterprise/bookingscentre/behaviours",
            data=club_data,
        )
        category_data = {
            "behaviours": category,
            "bookingType": 0,
            "X-Requested-With": "XMLHttpRequest",
        }
        s.post(
            "https://lancaster.legendonlineservices.co.uk/enterprise/bookingscentre/activities",
            data=category_data,
        )
        activity_data = {
            "activity": activity,
            "X-Requested-With": "XMLHttpRequest",
        }
        s.post(
            "https://lancaster.legendonlineservices.co.uk/enterprise/bookingscentre/activitySelect",
            data=activity_data,
        )
        timetable = s.get(
            "https://lancaster.legendonlineservices.co.uk/enterprise/bookingscentre/TimeTable"
        )

        soup = BeautifulSoup(timetable.text, "lxml")
        slots = soup.select("tr:not(.titleRow)")
        slots = [
            GymSlot.from_timetable_row(s, gym=self)
            for s in slots
            if s.select("td")[-1].text == "[ Add to Basket ]"
        ]
        return sorted(slots)

    def get_gym_slots(self, *, after=0, before=24):
        slots = self.get_slots(701, 729)
        after = int(after) + (after - int(after)) / 0.60
        before = int(before) + (before - int(before)) / 0.60
        slots = [
            s
            for s in slots
            if s.start_date.hour + (s.start_date.minute / 60) >= after
            and s.end_date.hour + (s.end_date.minute / 60) <= before
        ]
        return slots

    def __repr__(self):
        return f"LancasterSportsCentre(username={self.username!r})"


@dataclass(frozen=True, order=True)
class Booking:
    start_date: datetime.datetime
    end_date: datetime.datetime
    name: str
    location: str
    status: str

    @classmethod
    def from_tuple(cls, data):
        name, status, location, date_str = data

        start_date_str = date_str.split(" - ")[0]
        end_date_str = (
            " ".join(start_date_str.split(" ")[:3])
            + " "
            + date_str.split("-")[1].strip()
        )

        start_date = datetime.datetime.strptime(start_date_str, "%d %B %Y %H:%M")
        end_date = datetime.datetime.strptime(end_date_str, "%d %B %Y %H:%M")

        return cls(start_date, end_date, name, location, status)


@dataclass(frozen=True, order=True)
class GymSlot:
    start_date: datetime.datetime
    end_date: datetime.datetime
    location: str
    spaces: int
    id: int
    gym: LancasterSportsCentre

    @classmethod
    def from_timetable_row(cls, row, gym):
        cells = row.find_all("td")
        location, day, date, time_slot, spaces, *other, basket = [
            s for s in row.find_all("td")
        ]
        start_time, end_time = time_slot.text.split(" - ")
        spaces = int(spaces.text.split()[0])
        start_date = datetime.datetime.strptime(
            date.text + " " + start_time, "%d/%m/%Y %H:%M"
        )
        end_date = datetime.datetime.strptime(
            date.text + " " + end_time, "%d/%m/%Y %H:%M"
        )
        _id = int(basket.select_one("a")["onclick"][11:-1])

        return cls(start_date, end_date, location, spaces, _id, gym)

    def add_to_basket(self):
        s = self.gym.login()
        resp = s.get(
            "https://lancaster.legendonlineservices.co.uk/enterprise/BookingsCentre/AddBooking",
            params={"booking": self.id},
        ).json()

        if not resp["Success"]:
            if resp["Message"].startswith("You already have a booking"):
                raise ConflictError(resp["Message"])
            else:
                raise Exception(resp["Message"])

        return True
