# app/routes/web.py
from flask import Blueprint, render_template, current_app
import logging

web_bp = Blueprint('web', __name__)
logger = logging.getLogger('EventosFeriados.web')

@web_bp.route('/')
def index():
    """Página inicial do sistema"""
    try:
        # Verificar status dos gerenciadores
        status = {
            'feriados': current_app.config['GERENCIADOR_FERIADOS'] is not None,
            'eventos': current_app.config['GERENCIADOR_EVENTOS'] is not None
        }
        
        # Por enquanto, retornar uma página simples
        # Posteriormente será substituída por uma interface moderna
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sistema de Feriados e Eventos</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
                .status {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #e8f4f8;
                    border-radius: 5px;
                }}
                .status-item {{
                    margin: 10px 0;
                }}
                .online {{
                    color: #28a745;
                    font-weight: bold;
                }}
                .offline {{
                    color: #dc3545;
                    font-weight: bold;
                }}
                .info {{
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-left: 4px solid #007bff;
                }}
                .endpoints {{
                    margin-top: 20px;
                }}
                code {{
                    background-color: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Sistema de Gerenciamento de Feriados e Eventos</h1>
                
                <div class="status">
                    <h2>Status dos Serviços</h2>
                    <div class="status-item">
                        Gerenciador de Feriados: 
                        <span class="{'online' if status['feriados'] else 'offline'}">
                            {'ONLINE' if status['feriados'] else 'OFFLINE'}
                        </span>
                    </div>
                    <div class="status-item">
                        Gerenciador de Eventos: 
                        <span class="{'online' if status['eventos'] else 'offline'}">
                            {'ONLINE' if status['eventos'] else 'OFFLINE'}
                        </span>
                    </div>
                </div>
                
                <div class="info">
                    <h3>Informações do Sistema</h3>
                    <p>Este sistema permite gerenciar feriados e eventos nos seguintes locais:</p>
                    <ul>
                        <li>Auditório Nobre</li>
                        <li>Átrio</li>
                        <li>Plenário</li>
                        <li>Creche</li>
                    </ul>
                    <p>A interface completa está em desenvolvimento.</p>
                </div>
                
                <div class="endpoints">
                    <h3>API Endpoints Disponíveis</h3>
                    <h4>Feriados:</h4>
                    <ul>
                        <li><code>GET /EventosFeriados/api/feriados</code> - Listar feriados</li>
                        <li><code>POST /EventosFeriados/api/feriados</code> - Adicionar feriado</li>
                        <li><code>GET /EventosFeriados/api/feriados/&lt;id&gt;</code> - Obter feriado</li>
                        <li><code>PUT /EventosFeriados/api/feriados/&lt;id&gt;</code> - Atualizar feriado</li>
                        <li><code>DELETE /EventosFeriados/api/feriados/&lt;id&gt;</code> - Remover feriado</li>
                    </ul>
                    
                    <h4>Eventos:</h4>
                    <ul>
                        <li><code>GET /EventosFeriados/api/eventos</code> - Listar eventos</li>
                        <li><code>POST /EventosFeriados/api/eventos</code> - Adicionar evento</li>
                        <li><code>GET /EventosFeriados/api/eventos/&lt;id&gt;</code> - Obter evento</li>
                        <li><code>PUT /EventosFeriados/api/eventos/&lt;id&gt;</code> - Atualizar evento</li>
                        <li><code>DELETE /EventosFeriados/api/eventos/&lt;id&gt;</code> - Remover evento</li>
                        <li><code>GET /EventosFeriados/api/eventos/locais</code> - Listar locais</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"Erro ao renderizar página inicial: {e}")
        return "Erro ao carregar página", 500

@web_bp.route('/feriados')
def feriados():
    """Página de gerenciamento de feriados (placeholder)"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gerenciamento de Feriados</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Gerenciamento de Feriados</h1>
        <p>Interface em desenvolvimento...</p>
        <a href="/EventosFeriados/">Voltar</a>
    </body>
    </html>
    """

@web_bp.route('/eventos')
def eventos():
    """Página de gerenciamento de eventos (placeholder)"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gerenciamento de Eventos</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Gerenciamento de Eventos</h1>
        <p>Interface em desenvolvimento...</p>
        <a href="/EventosFeriados/">Voltar</a>
    </body>
    </html>
    """