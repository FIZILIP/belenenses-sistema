from app import app
import webview, threading, os

def run_flask():
    app.run(debug=False, port=5002, host="127.0.0.1")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    webview.create_window("GET CLUB", "http://127.0.0.1:5002", width=1400, height=900)
    webview.start()
    os._exit(0)
