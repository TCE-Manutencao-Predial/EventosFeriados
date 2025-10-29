# app/routes/web.py
from flask import Blueprint, render_template, current_app
import logging
from ..utils.auth_decorators import require_auth

web_bp = Blueprint('web', __name__, 
                   template_folder='../templates',
                   static_folder='../static')
logger = logging.getLogger('EventosFeriados.web')

@web_bp.route('/')
@require_auth
def index():
    """Página inicial do sistema"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página inicial: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/feriados')
@require_auth
def feriados():
    """Página de gerenciamento de feriados"""
    try:
        return render_template('feriados.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de feriados: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/eventos')
@require_auth
def eventos():
    """Página de gerenciamento de eventos"""
    try:
        return render_template('eventos.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de eventos: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/calendario')
@require_auth
def calendario():
    """Página do calendário"""
    try:
        return render_template('calendario.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de calendário: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/historico')
@require_auth
def historico():
    """Página de histórico de alterações"""
    try:
        return render_template('historico.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de histórico: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/sincronizacao-clp')
@require_auth
def sincronizacao_clp():
    """Página de sincronização com CLP"""
    try:
        return render_template('sincronizacao_clp.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de sincronização CLP: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/sincronizacao-tce')
@require_auth
def sincronizacao_tce():
    """Página de sincronização com TCE"""
    try:
        return render_template('sincronizacao_tce.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de sincronização TCE: {e}")
        return "Erro ao carregar página", 500