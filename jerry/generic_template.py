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


def create_element(title, subtitle="", image_url="", buttons=[]):
    element = {
        "title": title,
        "image_url": image_url,
        "subtitle": subtitle,
        "buttons": buttons
    }
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


def travel_options(trip_start, trip_end, trip_time, modals, distance=60):

    assert isinstance(modals, (list, tuple))
    for i in modals:
        assert i in ["train", "car_rental", "bike"]

    elements = []
    options_array = []

    if "train" in modals:
        option = {
            'modal': 'train',
            'distance': distance,
            'price': int(distance * 1.8),
            'from': trip_start + ' Hbf',
            'to': trip_end + ' Hbf',
            'duration': int(distance) + ' mins'
        }
        options_array.append(option)

        buttons = [
            create_button("Book for %s" % option['price'], payload="buy_train_ticket"),
            create_button("More Journey Details", payload="train_details"),
        ]
        element = create_element(
            title="Use DB Train",
            subtitle="Train from {start} to {end} at {time}".format(
                start=trip_start, end=trip_end, time=trip_time),
            buttons=buttons
        )
        elements.append(element)

    if "car_rental" in modals:

        option = {
            'modal': 'car_rental',
            'distance': distance,
            'price': int(distance * 2.4),
            'from':  'Hertz, %s (Neuhausen)' % trip_start,
            'to': 'Hertz, %s (Pragstrasse)' % trip_end,
            'duration': int(1.2 * distance) + ' mins'
            'pickup_time': '9AM',
            'dropoff_time': '7PM'
        }
        options_array.append(option)

        buttons = [
            create_button("Book for xys€", payload="book_rental_car"),
            create_button("More Details", payload="rental_car_details"),
        ]

        element = create_element(
            title="Get a Car from Hertz",
            subtitle="Car pick up in {start} at {time}. Drop off in {end}"
                     " until {time2}".format(start=trip_start,
                                             end=trip_end,
                                             time=trip_time,
                                             time2="TODO"),
            buttons=buttons
        )
        elements.append(element)

    return options_array, generate_generic_template(elements)

#
# def send_travel_options_to_lorenz():
#     cfg = load_conf()
#     fb_user_id = cfg["LORENZ_RECIPIENT_ID"]
#     send_message(fb_user_id, payload=travel_options(
#         trip_start="München",
#         trip_end="Stuttgart",
#         trip_time="18:30",
#         options=["car_rental", "train"]
#     ))
#
# if __name__ == '__main__':
#     send_travel_options_to_lorenz()
