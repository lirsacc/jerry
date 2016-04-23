"""
FB API docs for this:
https://developers.facebook.com/docs/messenger-platform/send-api-reference#request
"""
import requests

from jerry.config import load_conf



def set_the_welcome_message():
    """
    This should only be called by a human as it is the same for all new users.

    Example from the Documentation
    curl -X POST -H "Content-Type: application/json" -d '{
      "setting_type":"call_to_actions",
      "thread_state":"new_thread",
      "call_to_actions":[
        {
          "message":{
            "text":"Welcome to My Company!"
          }
        }
      ]
    }' "https://graph.facebook.com/v2.6/<PAGE_ID>/thread_settings?access_token=<PAGE_ACCESS_TOKEN>"


    :return:
    """
    cfg = load_conf()

    text = ("Hi, my name is Jerry! \n"
           "I am here to help you track your personal and business trips in "
            "one place. To get started type 'go to Munich Hbf'.\n"
            "Enjoy :)")
    print(text)

    data = {
        "setting_type": "call_to_actions",
        "thread_state": "new_thread",
        "call_to_actions": [
            {
                "message": {
                    "text": text
                }
            }
        ]
    }

    url = "https://graph.facebook.com/v2.6/{PAGE_ID}" \
          "/thread_settings?access_token={PAGE_ACCESS_TOKEN}".format(
        PAGE_ID=cfg["PAGE_ID"], PAGE_ACCESS_TOKEN=cfg["PAGE_ACCESS_TOKEN"]
    )

    r = requests.post(url, json=data)

    r.raise_for_status()
    print(r.text)
    return True





def get_first_name_of_user(fb_user_id):
    cfg = load_conf()
    url = "https://graph.facebook.com/v2.6/{USER_ID}?fields=first_name" \
          "&access_token={PAGE_ACCESS_TOKEN}".format(USER_ID=fb_user_id,
                                                     PAGE_ACCESS_TOKEN=
                                                     cfg["PAGE_ACCESS_TOKEN"])
    try:
        r = requests.get(url)
        first_name = r.json()["first_name"]
    except:
        first_name = ""
    return first_name




def test_getting_first_name():
    cfg = load_conf()
    fb_user_id = cfg["LORENZ_USER_ID"]
    assert(get_first_name_of_user(fb_user_id=fb_user_id) == "Lorenz")



if __name__ == '__main__':
    set_the_welcome_message()
    # test_getting_first_name()

