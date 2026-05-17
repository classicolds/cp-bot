"""
Keep-alive Flask server for UptimeRobot / Replit hosting.
Runs in a background thread so it never blocks the Telegram bot.
"""

import threading
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive", 200


def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def keep_alive():
    """Start the Flask server in a daemon thread."""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
