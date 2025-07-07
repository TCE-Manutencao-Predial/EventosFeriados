# app/routes/web.py
from flask import Blueprint, render_template, current_app
import logging

web_bp = Blueprint('web', __name__, 
                   template_folder='../templates',
                   static_folder='../static')
logger = logging.getLogger('EventosFeriados.web')

@web_bp.route('/')
def index():
    """Página inicial do sistema"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página inicial: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/feriados')
def feriados():
    """Página de gerenciamento de feriados"""
    try:
        return render_template('feriados.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de feriados: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/eventos')
def eventos():
    """Página de gerenciamento de eventos"""
    try:
        return render_template('eventos.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de eventos: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/calendario')
def calendario():
    """Página do calendário"""
    try:
        return render_template('calendario.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de calendário: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/sincronizacao-clp')
def sincronizacao_clp():
    """Página de sincronização com CLP"""
    try:
        return render_template('sincronizacao_clp.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de sincronização CLP: {e}")
        return "Erro ao carregar página", 500