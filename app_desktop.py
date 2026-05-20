import webview
import threading
from app import app

def run_flask():
    """Função para rodar o Flask."""
    app.run(debug=False, port=5002)

if __name__ == '__main__':
    # Inicia o servidor Flask numa thread separada
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Cria uma janela nativa que aponta para o teu sistema Flask local
    webview.create_window(
        title="Belenenses - Gestão de Futebol Feminino",
        url="http://127.0.0.1:5002",
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False
    )
    webview.start()