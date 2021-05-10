# Lancaster Sports Centre

A simple wrapper for the Lancaster Sports Centre API, allowing you to book sessions.

## Installation

```
pip install lusportscentre
```

## Usage

```
from lusportscentre import LancasterSportsCentre

sports_centre = LancasterSportsCentre("username", "password")

# get user info
print(sports_centre.user)

# get all available gym slots after 16:30
slots = sports_centre.get_gym_slots(after=16.30)

# book a slot
slot = slots[0]
slot.add_to_basket()
sports_centre.checkout()

# view all your current bookings
for booking in sports_centre.bookings():
    print(booking)
```
