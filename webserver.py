from flask import Flask, jsonify
from threading import Thread
import os

# Create a Flask app
app = Flask(__name__)


@app.route('/')
def home():
    return "Welcome to the bot server!"


@app.route('/status')
def status():
    return jsonify({"status": "Bot is running!"})


def run_flask():
    app.run(host='0.0.0.0', port=8000)


def start_webserver():
    # Run the Flask app in a separate thread
    webserver_thread = Thread(target=run_flask)
    webserver_thread.daemon = True
    webserver_thread.start()


if __name__ == "__main__":
    start_webserver()
    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Web server stopped.")
