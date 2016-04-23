"""
Example
curl -X POST -H "Content-Type: application/json" -d '{
  "recipient":{
    "id":"USER_ID"
  },
  "message":{
    "attachment":{
      "type":"template",
      "payload":{
        "template_type":"generic",
        "elements":[
          {
            "title":"Classic White T-Shirt",
            "image_url":"http://petersapparel.parseapp.com/img/item100-thumb.png",
            "subtitle":"Soft white cotton t-shirt is back in style",
            "buttons":[
              {
                "type":"web_url",
                "url":"https://petersapparel.parseapp.com/view_item?item_id=100",
                "title":"View Item"
              },
              {
                "type":"postback",
                "title":"Bookmark Item",
                "payload":"USER_DEFINED_PAYLOAD_FOR_ITEM100"
              }
            ]
          },
          {
            "title":"Classic Grey T-Shirt",
            "image_url":"http://petersapparel.parseapp.com/img/item101-thumb.png",
            "subtitle":"Soft gray cotton t-shirt is back in style",
            "buttons":[
              {
                "type":"web_url",
                "url":"https://petersapparel.parseapp.com/view_item?item_id=101",
                "title":"View Item"
              },
              {
                "type":"postback",
                "title":"Bookmark Item",
                "payload":"USER_DEFINED_PAYLOAD_FOR_ITEM101"
              }
            ]
          }
        ]
      }
    }
  }
}' "https://graph.facebook.com/v2.6/me/messages?access_token=<PAGE_ACCESS_TOKEN>"
"""

import datetime as dt
import random




def create_button(title, payload="", url="", button_type="postback"):
    """
    The button title will be stripped if it is longer than 20 chars.

    """

    assert button_type in ["postback", "web_url"]

    assert len(title) <= 20, "button title `{title}` is {x} chars to long. "\
                             "Max is 20 chars.".format(title=title,
                                                       x=len(title) - 20)

    if button_type == "postback":
        button = {
            "type": "postback",
            "title": title,
            "payload": payload,
        }
    else:
        button = {
            "type": "web_url",
            "title": title,
            "url": url,
        }
    return button


def create_element(title, subtitle="", image_url="", buttons=None):

    element = {
        "title": title,
        "subtitle": subtitle,
    }

    if buttons:
        element["buttons"] = buttons

    if image_url:
        element["image_url"] = image_url

    return element


def generate_generic_template(elements):
    attachment = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }
    return attachment


def travel_options(trip_start, trip_end, trip_dt, modals, distance=60):

    assert isinstance(trip_dt, dt.datetime)

    assert isinstance(modals, (list, tuple))
    for i in modals:
        assert i in ["train", "car_rental"]

    elements = []
    options_array = []

    # :%Y-%m-%d %H:%M
    distance = 0
    if trip_start.lower() == "munich":
        distance = 230
    elif trip_start.lower() == "stuttgart":
        distance = 160
    else:
        raise ValueError()

    if "train" in modals:
        option = {
            'modal': 'train',
            'distance': distance,
            'price': int(distance * 0.25),
            'from': trip_start + ' Hbf',
            'to': trip_end + ' Hbf',
            'duration': int(60 / 100 * distance),
        }
        options_array.append(option)

        buttons = [
            create_button("Book Train Ticket", payload="buy_train_ticket"),
            create_button("More Details", payload="train_details"),
        ]
        element = create_element(
            title="DB Train ({}€ - {}min)".format(option["price"], option["duration"]),
            subtitle="{date:%a, %d %b} with ICE 665{p2}"
                     " leaving from {start} at {date:%H:%M}"
                     " and arriving in {end} at {date:%H:%M}"
                     "".format(start=option["from"],
                               end=option["to"],
                               date=trip_dt,
                               p2=random.randint(1,9)),
            buttons=buttons
        )
        elements.append(element)

    if "car_rental" in modals:
        if trip_start.lower() == "munich":
            a, b = (" (Neuhausen)", " (Pragstr.)")
        elif trip_start.lower() == "stuttgart":
            a, b = (" (Pragstr.)", " (HBF)")
        else:
            a, b = ("", "")
        hertz_start_branch, hertz_end_branch = a,b

        option = {
            'modal': 'car_rental',
            'distance': distance,
            'price': int(distance * 0.33),
            'from':  'Hertz %s%s' % (trip_start, hertz_start_branch),
            'to': 'Hertz %s%s' % (trip_end, hertz_end_branch),
            'duration': int(0.8 * distance),
            'pickup_time': trip_dt - dt.timedelta(hours=2),
            'dropoff_time': trip_dt + dt.timedelta(minutes=distance, hours=1)
        }
        options_array.append(option)

        buttons = [
            create_button("Book car", payload="book_rental_car"),
            create_button("More Details", payload="rental_car_details"),
        ]

        element = create_element(
            title="Hertz car rental ({}€ - ca. {}min)".format(option["price"], option["duration"]),
            subtitle="On {date:%a, %d %b},"
                     " car pick up at {start} from {time1:%H:%M}."
                     " Dropoff at {end} until {time2:%H:%M}."
                     "".format(date=trip_dt,
                               time1=option["pickup_time"],
                               time2=option["dropoff_time"],
                               start=option["from"],
                               end=option["to"]),
            buttons=buttons
        )
        elements.append(element)

    return options_array, generate_generic_template(elements)


def travel_confirmation(modal):
    assert modal in ["car_rental", "train"]

    r_id = random.randint(10000, 99999)

    if modal == "car_rental":
        element = create_element(
            title="Your Hertz Reservation (Nr. %s)" % r_id,
            subtitle="Cancel it by typing "
                     "'cancel hertz {id}'".format(id=r_id),
            image_url="http://drive.google.com/uc?export=view&"
                      "id=0B-88jJpeaaJNLWdZVGF1S1hHZDg"
        )
    elif modal == "train":
        element = create_element(
            title="Your DB Ticket (Nr. %s)" % r_id,
            subtitle="Cancel it by typing "
                     "'cancel db {id}'".format(id=r_id),

            image_url="http://drive.google.com/uc?export=view&"
                      "id=0B-88jJpeaaJNUHpSaHQwTWpDWkk"
        )

    return generate_generic_template([element])


# def send_travel_options_to_lorenz():
#     from jerry.config import load_conf
#     from jerry.converse import send_message
#
#     cfg = load_conf()
#     fb_user_id = cfg["LORENZ_RECIPIENT_ID"]
#
#     _, payload = travel_options(
#         trip_start="Munich",
#         trip_end="Stuttgart",
#         trip_dt=dt.datetime(2016, 4, 28, 16),
#         modals=["car_rental", "train"]
#     )
#     send_message(fb_user_id, payload=payload)
#
# def send_travel_confirmation_to_lorenz(modal):
#     from jerry.config import load_conf
#     from jerry.converse import send_message
#     cfg = load_conf()
#     fb_user_id = cfg["LORENZ_RECIPIENT_ID"]
#     payload = travel_confirmation(modal)
#     send_message(fb_user_id, payload=payload)
#
# if __name__ == '__main__':
#     send_travel_options_to_lorenz()
#     send_travel_confirmation_to_lorenz("car_rental")
#     send_travel_confirmation_to_lorenz("train")