# Jerry

> Multi modal reservation bot proof of concept

## Tech side

Datastore is rethinkdb and can be run through easily through docker.
Bot server is a simple Flask app running on Python 3.

Configuration is read from the environment by looking at all variables with the prefix `JERRY_`. Look at the `env.mock` file for examples.

You can then run the server with `python jerry/app.py`. To link it to Facebook messenger, follow the instructions from [there](https://developers.facebook.com/blog/post/2016/04/12/bots-for-messenger/) and create a page. Your server should be accessible from a public https connection, you can use `ngrok` while doing local development.
