# EventosFeriados.py
from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

app = create_app()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

def inicializar_sistema_notificacoes():
    """Inicializa o sistema de notificações de eventos"""
    try:
        from app.utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
        gerenciador = GerenciadorNotificacaoEventos.get_instance()
        gerenciador.iniciar_scheduler_lembretes()
        logging.getLogger('EventosFeriados').info("Sistema de notificações de eventos inicializado")
    except Exception as e:
        logging.getLogger('EventosFeriados').error(f"Erro ao inicializar sistema de notificações: {e}")

if __name__ == '__main__':
    # Inicializa o sistema de notificações
    inicializar_sistema_notificacoes()
    
    # from waitress import serve
    # serve(app, listen='127.0.0.1:5045')
    app.run(debug=True, port=5045)