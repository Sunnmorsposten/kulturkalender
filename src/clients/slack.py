import os
from slack_bolt import App
# from dotenv import load_dotenv

# # Load environment variables from .env
# load_dotenv()

# Initialize your Slack app with token and signing secret
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)