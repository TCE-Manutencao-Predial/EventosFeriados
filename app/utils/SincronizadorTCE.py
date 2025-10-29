# app/utils/SincronizadorTCE.py
import requests
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .GerenciadorEventos import GerenciadorEventos
import urllib3

# Desabilitar avisos de SSL não verificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SincronizadorTCE:
    """
    Classe responsável por sincronizar eventos do Tribunal Pleno do TCE
    com o sistema local de eventos
    """
    
    _instance = None
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.SincronizadorTCE')
        self.gerenciador_eventos = GerenciadorEventos.get_instance()
        self.base_url = "https://catalogodeservicos.tce.go.gov.br/api/pauta/datas"
        self.prefixo_id_tce = "tce_tribunal_pleno"
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do sincronizador (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _obter_dados_json_tce(self, mes: int, ano: int) -> Optional[List[Dict]]:
        """
        Obtém os dados JSON da API do TCE para um mês/ano específico
        
        Args:
            mes: Mês (1-12)
            ano: Ano (ex: 2025)
            
        Returns:
            Lista de dicionários com dados dos eventos ou None em caso de erro
        """
        try:
            url = f"{self.base_url}/{mes:02d}/{ano}"
            self.logger.info(f"Consultando API do TCE: {url}")
            
            response = requests.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            # Parse do JSON
            dados = response.json()
            
            self.logger.info(f"Dados obtidos com sucesso da API do TCE para {mes:02d}/{ano} - {len(dados)} eventos")
            return dados
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout ao consultar API do TCE para {mes:02d}/{ano}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao consultar API do TCE para {mes:02d}/{ano}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao fazer parse do JSON da API do TCE: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao consultar API do TCE: {e}")
            return None
    
    def _processar_eventos_json(self, dados_json: List[Dict]) -> List[Dict]:
        """
        Processa os dados JSON e extrai eventos do Tribunal Pleno vespertinos
        Agrupa múltiplos eventos do mesmo dia em um único evento
        
        Args:
            dados_json: Lista de dicionários com dados da API
            
        Returns:
            Lista de dicionários com eventos filtrados e agrupados por dia
        """
        eventos_por_dia = {}  # Agrupa eventos por dia
        
        try:
            for evento_api in dados_json:
                dia = evento_api.get('dia')
                titulo = evento_api.get('titulo', '')
                
                if not dia or not titulo:
                    continue
                
                # Limpar quebras de linha do título
                titulo = titulo.replace('\n', ' ').strip()
                
                # Filtrar apenas eventos do Tribunal Pleno
                if not titulo.startswith('Tribunal Pleno:'):
                    continue
                
                # Extrair horário do título usando regex
                match_horario = re.search(r'às (\d{1,2}):(\d{2}) hora', titulo)
                if not match_horario:
                    continue
                
                hora = int(match_horario.group(1))
                minuto = int(match_horario.group(2))
                
                # Filtrar apenas eventos vespertinos (a partir das 12h)
                if hora < 12:
                    continue
                
                # Agrupar eventos por dia
                if dia not in eventos_por_dia:
                    eventos_por_dia[dia] = {
                        'dia': dia,
                        'eventos': [],
                        'horarios_originais': []
                    }
                
                eventos_por_dia[dia]['eventos'].append(titulo)
                eventos_por_dia[dia]['horarios_originais'].append(f"{hora:02d}:{minuto:02d}")
            
            # Converter para lista de eventos consolidados
            eventos_filtrados = []
            for dia, info in eventos_por_dia.items():
                # Criar título consolidado
                if len(info['eventos']) == 1:
                    titulo_consolidado = info['eventos'][0]
                    horarios_originais = info['horarios_originais'][0]
                else:
                    # Múltiplos eventos no mesmo dia
                    tipos_sessao = []
                    for evento in info['eventos']:
                        # Extrair tipo de sessão (Ordinária, Extraordinária, etc.)
                        if 'Ordinária' in evento:
                            if 'Ordinária' not in tipos_sessao:
                                tipos_sessao.append('Ordinária')
                        elif 'Extraordinária' in evento:
                            if 'Extraordinária' not in tipos_sessao:
                                tipos_sessao.append('Extraordinária')
                    
                    if len(tipos_sessao) == 1:
                        titulo_consolidado = f"Tribunal Pleno: {tipos_sessao[0]} (múltiplas sessões)"
                    else:
                        titulo_consolidado = f"Tribunal Pleno: {' e '.join(tipos_sessao)} (múltiplas sessões)"
                    
                    horarios_originais = ', '.join(info['horarios_originais'])
                
                eventos_filtrados.append({
                    'dia': dia,
                    'titulo': titulo_consolidado,
                    'hora_original': horarios_originais,
                    'quantidade_eventos': len(info['eventos']),
                    'eventos_detalhados': info['eventos']
                })
            
            self.logger.info(f"Filtrados {len(eventos_filtrados)} dias com eventos do Tribunal Pleno vespertinos")
            
            # Log detalhado dos eventos consolidados
            for evento in eventos_filtrados:
                if evento['quantidade_eventos'] > 1:
                    self.logger.info(f"Dia {evento['dia']}: {evento['quantidade_eventos']} eventos consolidados - {evento['hora_original']}")
                else:
                    self.logger.info(f"Dia {evento['dia']}: 1 evento - {evento['hora_original']}")
            
            return eventos_filtrados
            
        except Exception as e:
            self.logger.error(f"Erro ao processar eventos do JSON: {e}")
            return []
    
    def _gerar_id_evento_tce(self, dia: int, mes: int, ano: int) -> str:
        """
        Gera ID único para evento do TCE
        
        Args:
            dia: Dia do evento
            mes: Mês do evento
            ano: Ano do evento
            
        Returns:
            ID único para o evento
        """
        return f"{self.prefixo_id_tce}_{ano}{mes:02d}{dia:02d}"
    
    def _criar_evento_sistema(self, evento_tce: Dict, mes: int, ano: int) -> Optional[Dict]:
        """
        Cria um evento no sistema baseado nos dados do TCE
        
        Args:
            evento_tce: Dados do evento consolidado do TCE
            mes: Mês do evento
            ano: Ano do evento
            
        Returns:
            Evento criado ou None em caso de erro
        """
        try:
            # Preparar descrição detalhada
            if evento_tce['quantidade_eventos'] > 1:
                descricao = f"Evento sincronizado automaticamente da API do TCE - {evento_tce['quantidade_eventos']} sessões do Tribunal Pleno:\n"
                for i, evento_detalhe in enumerate(evento_tce['eventos_detalhados'], 1):
                    descricao += f"{i}. {evento_detalhe}\n"
            else:
                descricao = f"Evento sincronizado automaticamente da API do TCE - {evento_tce['titulo']}"
            
            dados_evento = {
                'nome': evento_tce['titulo'],
                'descricao': descricao,
                'local': 'Plenário',
                'dia': evento_tce['dia'],
                'mes': mes,
                'ano': ano,
                'hora_inicio': '13:00',  # Horário fixo para eventos vespertinos
                'hora_fim': '18:00',     # Horário fixo para eventos vespertinos
                'responsavel': 'Sistema - TCE',
                'participantes_estimados': 0,
                'fonte_tce': True,  # Marca para identificar eventos do TCE
                'hora_original_tce': evento_tce['hora_original'],
                'quantidade_eventos_tce': evento_tce['quantidade_eventos'],
                'eventos_detalhados_tce': evento_tce.get('eventos_detalhados', [])
            }
            
            # Gerar ID customizado para eventos do TCE (um por dia)
            evento_id = self._gerar_id_evento_tce(evento_tce['dia'], mes, ano)
            
            # Verificar se já existe um evento TCE para este dia
            evento_existente = self.gerenciador_eventos.obter_evento(evento_id)
            if evento_existente:
                # Verificar se houve mudanças nos eventos
                quantidade_atual = evento_existente.get('quantidade_eventos_tce', 1)
                eventos_atuais = evento_existente.get('eventos_detalhados_tce', [evento_existente['nome']])
                
                if (quantidade_atual != evento_tce['quantidade_eventos'] or 
                    set(eventos_atuais) != set(evento_tce['eventos_detalhados'])):
                    
                    # Atualizar evento existente com novas informações
                    self.logger.info(f"Atualizando evento TCE existente: {evento_tce['titulo']} - {evento_tce['dia']}/{mes}/{ano}")
                    
                    dados_atualizacao = {
                        'nome': evento_tce['titulo'],
                        'descricao': descricao,
                        'hora_original_tce': evento_tce['hora_original'],
                        'quantidade_eventos_tce': evento_tce['quantidade_eventos'],
                        'eventos_detalhados_tce': evento_tce['eventos_detalhados']
                    }
                    
                    evento_atualizado = self.gerenciador_eventos.atualizar_evento(evento_id, dados_atualizacao)
                    return evento_atualizado
                else:
                    self.logger.info(f"Evento TCE já existe e está atualizado: {evento_tce['titulo']} - {evento_tce['dia']}/{mes}/{ano}")
                    return evento_existente
            
            # Criar novo evento
            novo_evento = self.gerenciador_eventos.adicionar_evento(dados_evento)
            
            # Atualizar o ID para usar o padrão TCE e adicionar campos específicos
            for i, evento in enumerate(self.gerenciador_eventos.eventos):
                if evento['id'] == novo_evento['id']:
                    self.gerenciador_eventos.eventos[i]['id'] = evento_id
                    self.gerenciador_eventos.eventos[i]['fonte_tce'] = True
                    self.gerenciador_eventos.eventos[i]['hora_original_tce'] = evento_tce['hora_original']
                    self.gerenciador_eventos.eventos[i]['quantidade_eventos_tce'] = evento_tce['quantidade_eventos']
                    self.gerenciador_eventos.eventos[i]['eventos_detalhados_tce'] = evento_tce.get('eventos_detalhados', [])
                    break
            
            self.gerenciador_eventos._salvar_eventos()
            
            if evento_tce['quantidade_eventos'] > 1:
                self.logger.info(f"Evento TCE consolidado criado: {evento_tce['titulo']} - {evento_tce['dia']}/{mes}/{ano} ({evento_tce['quantidade_eventos']} sessões)")
            else:
                self.logger.info(f"Evento TCE criado: {evento_tce['titulo']} - {evento_tce['dia']}/{mes}/{ano}")
                
            return novo_evento
            
        except Exception as e:
            self.logger.error(f"Erro ao criar evento do TCE: {e}")
            return None
    
    def _remover_eventos_tce_obsoletos(self, mes: int, ano: int, eventos_atuais_tce: List[Dict]):
        """
        Remove eventos do TCE que não estão mais na API
        
        Args:
            mes: Mês de referência
            ano: Ano de referência
            eventos_atuais_tce: Lista de eventos atuais da API
        """
        try:
            # Obter todos os eventos do TCE para o mês/ano
            eventos_sistema = self.gerenciador_eventos.listar_eventos(ano=ano, mes=mes)
            eventos_tce_sistema = [e for e in eventos_sistema if e.get('fonte_tce', False)]
            
            # Criar set com IDs dos eventos atuais do TCE
            ids_eventos_atuais = set()
            for evento_tce in eventos_atuais_tce:
                evento_id = self._gerar_id_evento_tce(evento_tce['dia'], mes, ano)
                ids_eventos_atuais.add(evento_id)
            
            # Remover eventos que não estão mais na API
            eventos_removidos = 0
            for evento_sistema in eventos_tce_sistema:
                if evento_sistema['id'] not in ids_eventos_atuais:
                    if self.gerenciador_eventos.remover_evento(evento_sistema['id']):
                        eventos_removidos += 1
                        self.logger.info(f"Evento TCE removido: {evento_sistema['nome']} - {evento_sistema['dia']}/{evento_sistema['mes']}/{evento_sistema['ano']}")
            
            if eventos_removidos > 0:
                self.logger.info(f"Total de eventos TCE obsoletos removidos: {eventos_removidos}")
            
        except Exception as e:
            self.logger.error(f"Erro ao remover eventos TCE obsoletos: {e}")
    
    def sincronizar_mes(self, mes: int, ano: int) -> Dict:
        """
        Sincroniza eventos do TCE para um mês específico
        
        Args:
            mes: Mês (1-12)
            ano: Ano (ex: 2025)
            
        Returns:
            Dicionário com resultado da sincronização
        """
        resultado = {
            'sucesso': False,
            'mes': mes,
            'ano': ano,
            'eventos_criados': 0,
            'eventos_removidos': 0,
            'erro': None
        }
        
        try:
            self.logger.info(f"Iniciando sincronização TCE para {mes:02d}/{ano}")
            
            # Obter dados da API
            dados_json = self._obter_dados_json_tce(mes, ano)
            if not dados_json:
                resultado['erro'] = "Erro ao obter dados da API do TCE"
                return resultado
            
            # Processar eventos
            eventos_tce = self._processar_eventos_json(dados_json)
            
            # Remover eventos obsoletos antes de criar novos
            self._remover_eventos_tce_obsoletos(mes, ano, eventos_tce)
            
            # Criar/atualizar eventos
            eventos_criados = 0
            for evento_tce in eventos_tce:
                evento_criado = self._criar_evento_sistema(evento_tce, mes, ano)
                if evento_criado:
                    eventos_criados += 1
            
            resultado['sucesso'] = True
            resultado['eventos_criados'] = eventos_criados
            
            self.logger.info(f"Sincronização TCE concluída para {mes:02d}/{ano} - {eventos_criados} eventos processados")
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização TCE para {mes:02d}/{ano}: {e}")
            resultado['erro'] = str(e)
        
        return resultado
    
    def sincronizar_periodo_atual(self) -> Dict:
        """
        Sincroniza eventos do mês atual e próximo mês
        
        Returns:
            Dicionário com resultado da sincronização
        """
        resultado = {
            'sucesso': False,
            'sincronizacoes': [],
            'total_eventos_criados': 0,
            'erro': None
        }
        
        try:
            agora = datetime.now()
            
            # Sincronizar mês atual
            resultado_atual = self.sincronizar_mes(agora.month, agora.year)
            resultado['sincronizacoes'].append(resultado_atual)
            
            # Sincronizar próximo mês
            proximo_mes = agora + timedelta(days=32)
            proximo_mes = proximo_mes.replace(day=1)
            
            resultado_proximo = self.sincronizar_mes(proximo_mes.month, proximo_mes.year)
            resultado['sincronizacoes'].append(resultado_proximo)
            
            # Consolidar resultados
            resultado['sucesso'] = resultado_atual['sucesso'] and resultado_proximo['sucesso']
            resultado['total_eventos_criados'] = resultado_atual['eventos_criados'] + resultado_proximo['eventos_criados']
            
            if not resultado['sucesso']:
                erros = []
                if resultado_atual.get('erro'):
                    erros.append(f"Mês atual: {resultado_atual['erro']}")
                if resultado_proximo.get('erro'):
                    erros.append(f"Próximo mês: {resultado_proximo['erro']}")
                resultado['erro'] = "; ".join(erros)
            
            self.logger.info(f"Sincronização TCE período atual concluída - {resultado['total_eventos_criados']} eventos processados")
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização TCE período atual: {e}")
            resultado['erro'] = str(e)
        
        return resultado
