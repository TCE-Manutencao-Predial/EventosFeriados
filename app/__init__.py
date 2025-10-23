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
    
    # Inicializa integração CLP Plenário/Feriados
    try:
        from .utils.IntegracaoCLP import IntegracaoCLP
        if app.config['GERENCIADOR_FERIADOS'] and app.config['GERENCIADOR_EVENTOS']:
            app.config['INTEGRACAO_CLP'] = IntegracaoCLP(
                app.config['GERENCIADOR_FERIADOS'],
                app.config['GERENCIADOR_EVENTOS']
            )
            eventos_logger.info("Integração CLP Plenário iniciada")
        else:
            app.config['INTEGRACAO_CLP'] = None
            eventos_logger.warning("Integração CLP Plenário não iniciada - gerenciadores indisponíveis")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar integração CLP Plenário: {e}")
        app.config['INTEGRACAO_CLP'] = None
    
    # Inicializa integração CLP Auditório
    try:
        from .utils.IntegracaoCLPAuditorio import IntegracaoCLPAuditorio
        if app.config['GERENCIADOR_EVENTOS']:
            app.config['INTEGRACAO_CLP_AUDITORIO'] = IntegracaoCLPAuditorio(
                app.config['GERENCIADOR_EVENTOS']
            )
            eventos_logger.info("Integração CLP Auditório iniciada")
        else:
            app.config['INTEGRACAO_CLP_AUDITORIO'] = None
            eventos_logger.warning("Integração CLP Auditório não iniciada - gerenciador de eventos indisponível")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar integração CLP Auditório: {e}")
        app.config['INTEGRACAO_CLP_AUDITORIO'] = None
    
    # Inicializa agendador CLP
    try:
        from .utils.AgendadorCLP import AgendadorCLP
        agendador = AgendadorCLP.get_instance()
        if app.config['GERENCIADOR_FERIADOS'] and app.config['GERENCIADOR_EVENTOS']:
            agendador.inicializar_gerenciadores(
                app.config['GERENCIADOR_FERIADOS'],
                app.config['GERENCIADOR_EVENTOS']
            )
            agendador.iniciar()
            eventos_logger.info("Agendador CLP iniciado")
        else:
            eventos_logger.warning("Agendador CLP não iniciado - gerenciadores indisponíveis")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar agendador CLP: {e}")
    
    # Inicializa sistema de notificações de eventos
    try:
        from .utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
        gerenciador_notificacao = GerenciadorNotificacaoEventos.get_instance()
        gerenciador_notificacao.iniciar_scheduler_lembretes()
        eventos_logger.info("Sistema de notificações de eventos iniciado com scheduler ativo")
    except Exception as e:
        eventos_logger.error(f"Erro ao inicializar sistema de notificações de eventos: {e}")

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
    from .routes.api_clp import api_clp_bp
    from .routes.api_clp_auditorio import api_clp_auditorio_bp
    from .routes.api_tce import api_tce
    from .routes.web import web_bp
    
    # IMPORTANTE: Registrar com url_prefix
    app.register_blueprint(api_feriados_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(api_eventos_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(api_clp_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(api_clp_auditorio_bp, url_prefix=f'{ROUTES_PREFIX}/api')
    app.register_blueprint(api_tce, url_prefix=f'{ROUTES_PREFIX}/api/tce')
    app.register_blueprint(web_bp, url_prefix=ROUTES_PREFIX)
    
    # Rota de status da API
    @app.route(f'{ROUTES_PREFIX}/api/status')
    def api_status():
        try:
            from .utils.AgendadorCLP import AgendadorCLP
            agendador_status = AgendadorCLP.get_instance().status()
        except:
            agendador_status = {'executando': False}
        
        # Status do scheduler de notificações
        try:
            from .utils.GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
            ger_notif = GerenciadorNotificacaoEventos.get_instance()
            notificacoes_status = {
                'scheduler_ativo': ger_notif.running,
                'thread_viva': ger_notif.scheduler_thread.is_alive() if ger_notif.scheduler_thread else False,
                'sistema_inicializado': ger_notif.notificacao_eventos is not None
            }
        except Exception as e:
            eventos_logger.error(f"Erro ao obter status de notificações: {e}")
            notificacoes_status = {
                'scheduler_ativo': False,
                'thread_viva': False,
                'sistema_inicializado': False,
                'erro': str(e)
            }
            
        return jsonify({
            'status': 'online',
            'versao': '1.0.0',
            'gerenciadores': {
                'feriados': app.config['GERENCIADOR_FERIADOS'] is not None,
                'eventos': app.config['GERENCIADOR_EVENTOS'] is not None
            },
            'integracao_clp': {
                'plenario': app.config['INTEGRACAO_CLP'] is not None,
                'auditorio': app.config['INTEGRACAO_CLP_AUDITORIO'] is not None
            },
            'notificacoes_eventos': notificacoes_status,
            'sincronizacao_tce': {
                'habilitada': agendador_status.get('status_tce', {}).get('SYNC_ENABLED', False),
                'proximo_horario': agendador_status.get('proximo_horario_tce'),
                'agendador_ativo': agendador_status.get('executando', False)
            }
        })
    
    # Log de rotas registradas para debug
    eventos_logger.info("Rotas registradas:")
    with app.app_context():
        for rule in app.url_map.iter_rules():
            eventos_logger.info(f"  {rule.endpoint}: {rule.rule}")
    
    return app