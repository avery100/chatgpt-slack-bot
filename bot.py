import slack
import os
import time
import traceback
from werkzeug.wsgi import ClosingIterator
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, g, Response
from slackeventsapi import SlackEventAdapter
from playwright.sync_api import sync_playwright


# https://stackoverflow.com/a/51027874/15223881
# This code helps with Slack's 3 second timeout - it sends a response right away, then does the rest of the work
class AfterThisResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extensioe
        app.after_this_response = self

        # install middleware
        app.wsgi_app = AfterThisResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        try:
            for fn in self.callbacks:
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
        finally:
            self.callbacks = []

class AfterThisResponseMiddleware:
    def __init__(self, application, after_this_response_ext):
        self.application = application
        self.after_this_response_ext = after_this_response_ext

    def __call__(self, environ, start_response):
        iterator = self.application(environ, start_response)
        try:
            return ClosingIterator(iterator, [self.after_this_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize a Flask app to host the events adapter
# app = Flask(__name__)
app = Flask("after_response")
AfterThisResponse(app)

slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], "/slack/events", app)

# Start playwright
PLAY = sync_playwright().start()
BROWSER = PLAY.chromium.launch_persistent_context(
    user_data_dir="/tmp/playwright",
    headless=False,
)
PAGE = BROWSER.new_page()

def get_input_box():
    """Get the child textarea of `PromptTextarea__TextareaWrapper`"""
    return PAGE.query_selector("textarea")

def is_logged_in():
    # See if we have a textarea with data-id="root"
    return get_input_box() is not None

def is_loading_response() -> bool:
    """See if the send button is disabled, if it is, we're not loading"""
    return not PAGE.query_selector("textarea ~ button").is_enabled()

def send_message(message):
    # Send the message
    box = get_input_box()
    box.click()
    box.fill(message)
    box.press("Enter")

def get_last_message():
    """Get the latest message"""
    while is_loading_response():
        #time.sleep(0.25)
        time.sleep(1)
    page_elements = PAGE.query_selector_all("div[class*='request-:']")
    last_element = page_elements.pop()
    return last_element.inner_text()

def regenerate_response():
    """Clicks on the Try again button.
    Returns None if there is no button"""
    try_again_button = PAGE.query_selector("button:has-text('Try again')")
    if try_again_button is not None:
        try_again_button.click()
    return try_again_button

def get_reset_button():
    """Returns the reset thread button (it is an a tag not a button)"""
    return PAGE.query_selector("a:has-text('Reset thread')")

def start_browser():
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        print("Please log in to OpenAI Chat")
        print("Press enter when you're done")
        input()
    else:
        print("Logged in")

# Initialize a Slack Web API client
slack_web_client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = slack_web_client.api_call("auth.test")['user_id']

# Create an event listener for "message" events
@slack_event_adapter.on("message")
def handle_message(payload):
    @app.after_this_response
    def after_response():
    
        event = payload.get("event", {})
    
        # print("\n \nReceived from Slack: \n")
        # print(payload)
        # print("\n ")
        
        event_id = event.get("event_ts")
        channel_id = event.get("channel")
        user_id = event.get("user")
        text = event.get("text")

        # print("\n ")
        # print("user_id: ", user_id)
        # print("BOT_ID: ", BOT_ID)
        # print("\n \n")

        # print("event_id: ", event_id)

        # Ignore messages from the bot itself
        if user_id != None and BOT_ID != user_id:
            
            # print("SENDING MESSAGE! \n \n")
            send_message(text) 
            response = get_last_message()
            # print("Response from chatGPT: ", response)

            # Send a reply echoing the message
            slack_web_client.chat_postMessage(channel=channel_id, text=response)

# Create an endpoint for the Slack slash command /regenerate
@app.route("/regenerate", methods=["POST"])
def regenerate():
    
    @app.after_this_response
    def after_response():
        regenerate_response()
        response = get_last_message()

        # Send a reply echoing the message
        slack_web_client.chat_postMessage(
            channel="chatgpt-test", text=response)

    return Response(status=200)

# Start the Flask server on default port 5000
if __name__ == "__main__":
    start_browser()
    app.run(threaded=False)



