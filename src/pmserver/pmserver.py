import json
from flask import Flask, request, jsonify, render_template
from threading import Thread
import logging

class PMServer:
    def __init__(self, config, event_queue, host="0.0.0.0", port=8080):
        self.app = Flask(__name__)
        self.app.logger.disabled = True

        # Disable Werkzeug (Flask development server) access logs
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # Also disable Flask's logger if needed
        self.app.logger.setLevel(logging.ERROR)

        # Enable template auto-reload
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.jinja_env.auto_reload = True
        self.queue = event_queue
        self.host = host
        self.port = port
        self.config = config
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/<page>")
        def render_page(page):
            try:
                return render_template(f"{page}.html")
            except Exception:
                return "Page not found", 404

        @self.app.route("/event", methods=["POST"])
        def event():
            data = request.get_json()
            print(f"Received event {data}")
            if not data:
                return jsonify({"error": "Missing 'action'"}), 400
            if type(data) == str:
                try:
                    data = json.loads(data.strip())
                except:
                    msg = f"ERROR: problem converting '{data}' to json"
                    print(msg)
                    return jsonify({"status": "error", "msg": msg})
            self.queue.put(data)
            return jsonify({"status": "queued", "action": data})

    def start(self):
        def run():
            self.app.run(host=self.host, port=self.port, threaded=True)
        Thread(target=run, daemon=True).start()

