# app/routes/api_public.py
"""
API Pública para consulta de feriados e eventos
Endpoints sem autenticação para uso externo
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

api_public_bp = Blueprint('api_public', __name__)
logger = logging.getLogger('EventosFeriados.api_public')

# ============================================================================
# FERIADOS - API PÚBLICA
# ============================================================================

@api_public_bp.route('/public/feriados', methods=['GET'])
def listar_feriados_publico():
    """
    Lista feriados (público - sem autenticação)
    
    Parâmetros Query String:
    - ano (int, opcional): Filtrar por ano específico
    - mes (int, opcional): Filtrar por mês específico (1-12)
    - ano_minimo (int, opcional): Filtrar feriados a partir de um ano
    - data_inicial (string, opcional): Filtrar a partir de data (formato: YYYY-MM-DD)
    - data_final (string, opcional): Filtrar até data (formato: YYYY-MM-DD)
    
    Retorna:
    {
        "sucesso": true,
        "total": 10,
        "feriados": [
            {
                "id": "uuid",
                "nome": "Confraternização Universal",
                "data": "2025-01-01",
                "tipo": "nacional",
                "dia_semana": "Quarta-feira"
            }
        ]
    }
    """
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        # Obter parâmetros de filtro
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        ano_minimo = request.args.get('ano_minimo', type=int)
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        
        # Listar feriados com filtros básicos
        feriados = gerenciador.listar_feriados(ano=ano, mes=mes, ano_minimo=ano_minimo)
        
        # Filtros adicionais por data
        if data_inicial or data_final:
            feriados_filtrados = []
            for feriado in feriados:
                data_feriado = datetime.strptime(feriado['data'], '%Y-%m-%d').date()
                
                # Filtro por data inicial
                if data_inicial:
                    try:
                        data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
                        if data_feriado < data_ini:
                            continue
                    except ValueError:
                        pass
                
                # Filtro por data final
                if data_final:
                    try:
                        data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
                        if data_feriado > data_fim:
                            continue
                    except ValueError:
                        pass
                
                feriados_filtrados.append(feriado)
            
            feriados = feriados_filtrados
        
        return jsonify({
            'sucesso': True,
            'total': len(feriados),
            'feriados': feriados
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar feriados (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


@api_public_bp.route('/public/feriados/<feriado_id>', methods=['GET'])
def obter_feriado_publico(feriado_id):
    """
    Obtém detalhes de um feriado específico (público - sem autenticação)
    
    Parâmetros:
    - feriado_id: ID do feriado
    
    Retorna:
    {
        "sucesso": true,
        "feriado": {
            "id": "uuid",
            "nome": "Natal",
            "data": "2025-12-25",
            "tipo": "nacional",
            "dia_semana": "Quinta-feira"
        }
    }
    """
    try:
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        feriado = gerenciador.obter_feriado(feriado_id)
        
        if not feriado:
            return jsonify({'erro': 'Feriado não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'feriado': feriado
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter feriado {feriado_id} (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


@api_public_bp.route('/public/feriados/verificar', methods=['GET'])
def verificar_feriado_publico():
    """
    Verifica se uma data é feriado (público - sem autenticação)
    
    Parâmetros Query String:
    - data (string, obrigatório): Data a verificar (formato: YYYY-MM-DD)
    
    Retorna:
    {
        "sucesso": true,
        "data": "2025-12-25",
        "eh_feriado": true,
        "feriado": {
            "id": "uuid",
            "nome": "Natal",
            "tipo": "nacional"
        }
    }
    """
    try:
        data_str = request.args.get('data')
        if not data_str:
            return jsonify({'erro': 'Parâmetro "data" é obrigatório'}), 400
        
        gerenciador = current_app.config['GERENCIADOR_FERIADOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        # Validar formato da data
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Data inválida. Use formato YYYY-MM-DD'}), 400
        
        # Verificar se é feriado
        feriado = gerenciador.obter_feriado_por_data(data)
        
        return jsonify({
            'sucesso': True,
            'data': data_str,
            'eh_feriado': feriado is not None,
            'feriado': feriado
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar feriado (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


# ============================================================================
# EVENTOS - API PÚBLICA
# ============================================================================

@api_public_bp.route('/public/eventos', methods=['GET'])
def listar_eventos_publico():
    """
    Lista eventos (público - sem autenticação)
    
    Parâmetros Query String:
    - ano (int, opcional): Filtrar por ano específico
    - mes (int, opcional): Filtrar por mês específico (1-12)
    - local (string, opcional): Filtrar por local ("Plenário" ou "Auditório")
    - ano_minimo (int, opcional): Filtrar eventos a partir de um ano
    - data_inicial (string, opcional): Filtrar a partir de data (formato: YYYY-MM-DD)
    - data_final (string, opcional): Filtrar até data (formato: YYYY-MM-DD)
    - ativos_apenas (bool, opcional): Se true, retorna apenas eventos não encerrados
    
    Retorna:
    {
        "sucesso": true,
        "total": 5,
        "eventos": [
            {
                "id": "uuid",
                "titulo": "Sessão Plenária",
                "data": "2025-11-15",
                "hora": "14:00",
                "local": "Plenário",
                "status": "ativo"
            }
        ]
    }
    """
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        # Obter parâmetros de filtro
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        local = request.args.get('local')
        ano_minimo = request.args.get('ano_minimo', type=int)
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        ativos_apenas = request.args.get('ativos_apenas', 'false').lower() == 'true'
        
        # Listar eventos com filtros básicos
        eventos = gerenciador.listar_eventos(
            ano=ano, 
            mes=mes, 
            local=local, 
            ano_minimo=ano_minimo
        )
        
        # Filtros adicionais
        eventos_filtrados = []
        for evento in eventos:
            # Filtrar eventos encerrados se solicitado
            if ativos_apenas and evento.get('encerrado'):
                continue
            
            data_evento = datetime.strptime(evento['data'], '%Y-%m-%d').date()
            
            # Filtro por data inicial
            if data_inicial:
                try:
                    data_ini = datetime.strptime(data_inicial, '%Y-%m-%d').date()
                    if data_evento < data_ini:
                        continue
                except ValueError:
                    pass
            
            # Filtro por data final
            if data_final:
                try:
                    data_fim = datetime.strptime(data_final, '%Y-%m-%d').date()
                    if data_evento > data_fim:
                        continue
                except ValueError:
                    pass
            
            eventos_filtrados.append(evento)
        
        return jsonify({
            'sucesso': True,
            'total': len(eventos_filtrados),
            'eventos': eventos_filtrados
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


@api_public_bp.route('/public/eventos/<evento_id>', methods=['GET'])
def obter_evento_publico(evento_id):
    """
    Obtém detalhes de um evento específico (público - sem autenticação)
    
    Parâmetros:
    - evento_id: ID do evento
    
    Retorna:
    {
        "sucesso": true,
        "evento": {
            "id": "uuid",
            "titulo": "Sessão Plenária",
            "data": "2025-11-15",
            "hora": "14:00",
            "local": "Plenário",
            "descricao": "...",
            "status": "ativo"
        }
    }
    """
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        evento = gerenciador.obter_evento(evento_id)
        
        if not evento:
            return jsonify({'erro': 'Evento não encontrado'}), 404
        
        return jsonify({
            'sucesso': True,
            'evento': evento
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter evento {evento_id} (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


@api_public_bp.route('/public/eventos/por-data', methods=['GET'])
def eventos_por_data_publico():
    """
    Lista eventos em uma data específica (público - sem autenticação)
    
    Parâmetros Query String:
    - data (string, obrigatório): Data a consultar (formato: YYYY-MM-DD)
    - local (string, opcional): Filtrar por local ("Plenário" ou "Auditório")
    
    Retorna:
    {
        "sucesso": true,
        "data": "2025-11-15",
        "total": 2,
        "eventos": [...]
    }
    """
    try:
        data_str = request.args.get('data')
        if not data_str:
            return jsonify({'erro': 'Parâmetro "data" é obrigatório'}), 400
        
        local = request.args.get('local')
        
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        # Validar formato da data
        try:
            datetime.strptime(data_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'erro': 'Data inválida. Use formato YYYY-MM-DD'}), 400
        
        # Buscar eventos da data
        eventos = gerenciador.obter_eventos_por_data(data_str, local=local)
        
        return jsonify({
            'sucesso': True,
            'data': data_str,
            'total': len(eventos),
            'eventos': eventos
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar eventos por data (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


@api_public_bp.route('/public/eventos/locais', methods=['GET'])
def listar_locais_publico():
    """
    Lista os locais de eventos disponíveis (público - sem autenticação)
    
    Retorna:
    {
        "sucesso": true,
        "locais": ["Plenário", "Auditório"]
    }
    """
    try:
        gerenciador = current_app.config['GERENCIADOR_EVENTOS']
        if not gerenciador:
            return jsonify({'erro': 'Serviço temporariamente indisponível'}), 503
        
        locais = gerenciador.obter_locais()
        
        return jsonify({
            'sucesso': True,
            'locais': locais
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar locais (público): {e}")
        return jsonify({'erro': 'Erro ao processar requisição'}), 500


# ============================================================================
# DOCUMENTAÇÃO E STATUS
# ============================================================================

@api_public_bp.route('/public/info', methods=['GET'])
def api_info():
    """
    Informações sobre a API pública
    
    Retorna:
    {
        "nome": "API Pública EventosFeriados TCE-GO",
        "versao": "1.0.0",
        "endpoints": {...}
    }
    """
    return jsonify({
        'nome': 'API Pública - Eventos e Feriados TCE-GO',
        'versao': '1.0.0',
        'descricao': 'API pública para consulta de feriados e eventos do Tribunal de Contas do Estado de Goiás',
        'autenticacao': 'Não requerida',
        'base_url': request.url_root.rstrip('/') + request.blueprint_url_prefix,
        'endpoints': {
            'feriados': {
                'GET /public/feriados': 'Lista todos os feriados (com filtros opcionais)',
                'GET /public/feriados/<id>': 'Obtém detalhes de um feriado específico',
                'GET /public/feriados/verificar?data=YYYY-MM-DD': 'Verifica se uma data é feriado'
            },
            'eventos': {
                'GET /public/eventos': 'Lista todos os eventos (com filtros opcionais)',
                'GET /public/eventos/<id>': 'Obtém detalhes de um evento específico',
                'GET /public/eventos/por-data?data=YYYY-MM-DD': 'Lista eventos em uma data específica',
                'GET /public/eventos/locais': 'Lista locais de eventos disponíveis'
            },
            'info': {
                'GET /public/info': 'Informações sobre esta API'
            }
        },
        'exemplos': {
            'listar_feriados_2025': '/public/feriados?ano=2025',
            'verificar_natal': '/public/feriados/verificar?data=2025-12-25',
            'eventos_plenario': '/public/eventos?local=Plenário&ativos_apenas=true',
            'eventos_novembro': '/public/eventos?ano=2025&mes=11'
        },
        'suporte': 'TI TCE-GO',
        'documentacao': request.url_root.rstrip('/') + '/EventosFeriados'
    })
