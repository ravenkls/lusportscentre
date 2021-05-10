from dataclasses import dataclass
from bs4 import BeautifulSoup
import re


@dataclass(frozen=True)
class User:
    name: str
    email: str
    mobile: str
    membership: str
    membership_number: str
    membership_status: str
    member_status: str

    @classmethod
    def from_session(cls, session):
        resp = session.get(
            "https://lancaster.legendonlineservices.co.uk/enterprise/Account/CSC"
        )
        soup = BeautifulSoup(resp.text, "lxml")
        account_details = soup.find_all("div", class_="passportDetail")

        details = []
        for detail_str in map(lambda a: a.decode_contents(), account_details):
            info = re.findall(r"<h4>.+:<\/h4>\r\n\s*(.*)", detail_str)[0].strip()
            info_processed = re.sub("<[^<]+?>", "", info)
            details.append(info_processed)

        return cls(*details)
