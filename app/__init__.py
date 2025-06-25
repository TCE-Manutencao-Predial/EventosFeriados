# app/__init__.py
from flask import Flask, render_template, jsonify, request
from .config import setup_logging, ROUTES_PREFIX
import logging

# Configurar logging
eventos_logger = setup_logging()

def create_app():
    """Cria e configura a aplicação Flask"""
    # IMPORTANTE: Configurar static_url_path com o prefixo
    app = Flask(__name__, static_url_path=f'{ROUTES_PREFIX}/static')
    app.config['SECRET_KEY'] = 'eventos_feriados_secret_key_2024'
    
    # Inicializa gerenciador de feriados
    try:
        from .utils.GerenciadorFeriados import GerenciadorFeriados
        app.config['GERENCIADOR_FERIADOS'] = GerenciadorFeriados.get_instance()
        eventos_logger.info("Gerenciador de feriados iniciado")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar gerenciador de feriados: {e}")
        app.config['GERENCIADOR_FERIADOS'] = None
    
    # Inicializa gerenciador de eventos
    try:
        from .utils.GerenciadorEventos import GerenciadorEventos
        app.config['GERENCIADOR_EVENTOS'] = GerenciadorEventos.get_instance()
        eventos_logger.info("Gerenciador de eventos iniciado")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar gerenciador de eventos: {e}")
        app.config['GERENCIADOR_EVENTOS'] = None
    
    # Handlers de erro
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'erro': 'Endpoint não encontrado'}), 404
        try:
            return render_template('erro_404.html'), 404
        except:
            return "Página não encontrada", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        eventos_logger.error(f"Erro interno: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'erro': 'Erro interno do servidor'}), 500
        try:
            return render_template('erro_500.html'), 500
        except:
            return "Erro interno do servidor", 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'erro': 'Requisição inválida'}), 400
        return "Requisição inválida", 400
    
    # Registrar blueprints com prefixo
    from .routes.api_feriados import api_feriados_bp
    from .routes.api_eventos import api_eventos_bp
    from .routes.web import web_bp
    
    # IMPORTANTE: Registrar com url_prefix
    app.register_blueprint(api_feriados_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(api_eventos_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(web_bp, url_prefix=ROUTES_PREFIX)
    
    # Rota de status da API
    @app.route(f'{ROUTES_PREFIX}/api/status')
    def api_status():
        return jsonify({
            'status': 'online',
            'versao': '1.0.0',
            'gerenciadores': {
                'feriados': app.config['GERENCIADOR_FERIADOS'] is not None,
                'eventos': app.config['GERENCIADOR_EVENTOS'] is not None
            }
        })
    
    # Log de rotas registradas para debug
    eventos_logger.info("Rotas registradas:")
    with app.app_context():
        for rule in app.url_map.iter_rules():
            eventos_logger.info(f"  {rule.endpoint}: {rule.rule}")
    
    return app