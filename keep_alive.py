"""
🏓 Мини веб-сервер для пингов от UptimeRobot.
Без него Render усыпит бота через 15 минут.
UptimeRobot пингует каждые 5 минут → бот не спит.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        pass  # Не засоряем логи

def keep_alive(port=8080):
    """Запускает веб-сервер в отдельном потоке."""
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🏓 Keep-alive сервер запущен на порту {port}")
