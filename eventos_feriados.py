# eventos_feriados.py
from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

app = create_app()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, port=5045)