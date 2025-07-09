# app/utils/IntegracaoCLPAuditorio.py
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from .SincronizadorCLPAuditorio import SincronizadorCLPAuditorio

class IntegracaoCLPAuditorio:
    """
    Classe para integração com CLP do Auditório (Controlador Lógico Programável)
    Fornece interface simplificada para consulta e sincronização de eventos do Auditório
    Gerencia especificamente eventos do Auditório Nobre e Foyer do Auditório
    """
    
    def __init__(self, gerenciador_eventos):
        self.logger = logging.getLogger('EventosFeriados.IntegracaoCLPAuditorio')
        self.gerenciador_eventos = gerenciador_eventos
        self.sincronizador = SincronizadorCLPAuditorio.get_instance()
    
    def obter_status_sincronizacao(self) -> Dict:
        """Obtém status completo da sincronização com CLP Auditório"""
        return self.sincronizador.obter_status_sincronizacao()
    
    def sincronizar_dados(self) -> Dict:
        """Executa sincronização manual com CLP Auditório"""
        return self.sincronizador.sincronizar_manual(self.gerenciador_eventos)
    
    def verificar_conectividade(self) -> Dict:
        """Verifica conectividade com CLP Auditório"""
        conectado, mensagem = self.sincronizador.verificar_conectividade_clp()
        return {
            'conectado': conectado,
            'mensagem': mensagem,
            'timestamp': datetime.now().isoformat()
        }
    
    def obter_status_data(self, dia: int, mes: int, ano: int) -> Dict:
        """
        Obtém status completo de uma data específica para os locais do Auditório
        Retorna informações sobre eventos do dia no Auditório Nobre e Foyer
        """
        try:
            # Obter eventos do dia para os locais do Auditório
            eventos_auditorio = []
            
            for local in self.sincronizador.config['LOCAIS_GERENCIADOS']:
                eventos_local = self.gerenciador_eventos.obter_eventos_por_data(dia, mes, ano)
                eventos_local = [e for e in eventos_local if e['local'] == local]
                eventos_auditorio.extend(eventos_local)
            
            # Preparar resposta otimizada para CLP
            status = {
                'data': f'{dia:02d}/{mes:02d}/{ano}',
                'timestamp': int(datetime(ano, mes, dia).timestamp()),
                'total_eventos_auditorio': len(eventos_auditorio),
                'eventos_por_local': {},
                'proximos_eventos': []
            }
            
            # Organizar eventos por local
            for local in self.sincronizador.config['LOCAIS_GERENCIADOS']:
                eventos_local = [e for e in eventos_auditorio if e['local'] == local]
                if eventos_local:
                    status['eventos_por_local'][local] = [{
                        'nome': e['nome'],
                        'inicio': e['hora_inicio'],
                        'fim': e['hora_fim']
                    } for e in eventos_local]
            
            # Adicionar próximos eventos (até 3)
            for evento in eventos_auditorio[:3]:
                status['proximos_eventos'].append({
                    'nome': evento['nome'],
                    'local': evento['local'],
                    'inicio': evento['hora_inicio'],
                    'fim': evento['hora_fim']
                })
            
            return status
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status da data: {e}")
            raise
    
    def obter_calendario_resumido(self, mes: int, ano: int) -> Dict:
        """
        Obtém calendário resumido do mês para CLPs do Auditório
        Inclui apenas dias com eventos do Auditório
        """
        try:
            # Obter eventos do mês para os locais do Auditório
            eventos_auditorio = []
            
            for local in self.sincronizador.config['LOCAIS_GERENCIADOS']:
                eventos_local = self.gerenciador_eventos.listar_eventos(ano=ano, mes=mes, local=local)
                eventos_auditorio.extend(eventos_local)
            
            # Criar estrutura de calendário
            calendario = {
                'mes': mes,
                'ano': ano,
                'dias_especiais': {},
                'total_eventos_auditorio': len(eventos_auditorio),
                'locais_gerenciados': self.sincronizador.config['LOCAIS_GERENCIADOS']
            }
            
            # Adicionar contagem de eventos por dia
            for evento in eventos_auditorio:
                dia = evento['dia']
                if dia not in calendario['dias_especiais']:
                    calendario['dias_especiais'][dia] = {
                        'eventos_auditorio': 0,
                        'por_local': {}
                    }
                
                calendario['dias_especiais'][dia]['eventos_auditorio'] += 1
                
                # Contar por local
                local = evento['local']
                if local not in calendario['dias_especiais'][dia]['por_local']:
                    calendario['dias_especiais'][dia]['por_local'][local] = 0
                calendario['dias_especiais'][dia]['por_local'][local] += 1
            
            return calendario
            
        except Exception as e:
            self.logger.error(f"Erro ao obter calendário resumido: {e}")
            raise
    
    def obter_proximo_evento(self, local: Optional[str] = None) -> Optional[Dict]:
        """
        Obtém o próximo evento dos locais do Auditório
        Se local for especificado, filtra apenas por esse local
        """
        try:
            agora = datetime.now()
            data_atual = agora.date()
            hora_atual = agora.time()
            
            eventos_futuros = []
            
            # Verificar próximos 30 dias
            for dias_adicionais in range(30):
                data_verificar = data_atual + timedelta(days=dias_adicionais)
                
                # Obter eventos do dia
                eventos_dia = self.gerenciador_eventos.obter_eventos_por_data(
                    data_verificar.day, data_verificar.month, data_verificar.year
                )
                
                # Filtrar apenas eventos dos locais do Auditório
                eventos_dia = [e for e in eventos_dia if e['local'] in self.sincronizador.config['LOCAIS_GERENCIADOS']]
                
                for evento in eventos_dia:
                    # Se for hoje, verificar se ainda não passou
                    if data_verificar == data_atual:
                        hora_evento = datetime.strptime(evento['hora_inicio'], '%H:%M').time()
                        if hora_evento <= hora_atual:
                            continue
                    
                    # Filtrar por local se especificado
                    if local and evento['local'] != local:
                        continue
                    
                    # Adicionar timestamp para ordenação
                    evento['timestamp'] = int(datetime(
                        evento['ano'], 
                        evento['mes'], 
                        evento['dia'],
                        int(evento['hora_inicio'].split(':')[0]),
                        int(evento['hora_inicio'].split(':')[1])
                    ).timestamp())
                    
                    eventos_futuros.append(evento)
                
                # Se encontrou eventos, não precisa verificar mais dias
                if eventos_futuros:
                    break
            
            if not eventos_futuros:
                return None
            
            # Ordenar por timestamp e pegar o primeiro
            eventos_futuros.sort(key=lambda x: x['timestamp'])
            proximo = eventos_futuros[0]
            
            # Remover timestamp antes de retornar
            del proximo['timestamp']
            
            return proximo
            
        except Exception as e:
            self.logger.error(f"Erro ao obter próximo evento: {e}")
            return None
    
    def verificar_local_disponivel(self, local: str, dia: int, mes: int, ano: int,
                                  hora_inicio: str, hora_fim: str) -> Dict:
        """
        Verifica se um local do Auditório está disponível em determinado horário
        Útil para CLPs que controlam acesso aos locais
        """
        try:
            # Verificar se o local é gerenciado pelo CLP Auditório
            if local not in self.sincronizador.config['LOCAIS_GERENCIADOS']:
                return {
                    'disponivel': True,  # Local não é gerenciado por este CLP
                    'motivo': f'Local {local} não é gerenciado pelo CLP Auditório',
                    'locais_gerenciados': self.sincronizador.config['LOCAIS_GERENCIADOS']
                }
            
            # Verificar se há eventos conflitantes
            conflito = self.gerenciador_eventos._validar_conflito_horario(
                local, dia, mes, ano, hora_inicio, hora_fim
            )
            
            if conflito:
                # Buscar o evento conflitante para informar
                eventos_dia = self.gerenciador_eventos.obter_eventos_por_data(dia, mes, ano)
                eventos_local = [e for e in eventos_dia if e['local'] == local]
                
                return {
                    'disponivel': False,
                    'motivo': 'Conflito de horário',
                    'eventos_conflitantes': [{
                        'nome': e['nome'],
                        'inicio': e['hora_inicio'],
                        'fim': e['hora_fim']
                    } for e in eventos_local]
                }
            
            return {
                'disponivel': True,
                'motivo': None,
                'eventos_conflitantes': []
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar disponibilidade: {e}")
            return {
                'disponivel': False,
                'motivo': f'Erro ao verificar: {str(e)}',
                'eventos_conflitantes': []
            }
    
    def exportar_dados_clp(self, formato: str = 'compacto') -> Dict:
        """Exporta dados em formato otimizado para CLPs do Auditório"""
        try:
            agora = datetime.now()
            
            if formato == 'compacto':
                # Formato compacto: apenas próximos 7 dias
                dados = {
                    'versao': '1.0',
                    'timestamp': int(agora.timestamp()),
                    'dados': []
                }
                
                for i in range(7):
                    data = agora.date() + timedelta(days=i)
                    status = self.obter_status_data(data.day, data.month, data.year)
                    
                    if status['total_eventos_auditorio'] > 0:
                        dados['dados'].append({
                            'd': data.day,
                            'm': data.month,
                            'e': status['total_eventos_auditorio']
                        })
                
            else:  # completo
                # Formato completo: mais detalhado
                dados = {
                    'versao': '1.0',
                    'timestamp': int(agora.timestamp()),
                    'ano_atual': agora.year,
                    'mes_atual': agora.month,
                    'dia_atual': agora.day,
                    'locais_gerenciados': self.sincronizador.config['LOCAIS_GERENCIADOS'],
                    'calendario': {}
                }
                
                # Incluir 3 meses de dados
                for offset_mes in range(3):
                    mes = (agora.month + offset_mes - 1) % 12 + 1
                    ano = agora.year + ((agora.month + offset_mes - 1) // 12)
                    
                    calendario_mes = self.obter_calendario_resumido(mes, ano)
                    chave_mes = f"{ano}-{mes:02d}"
                    dados['calendario'][chave_mes] = calendario_mes
            
            return dados
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar dados: {e}")
            raise
    
    def limpar_todos_dados_clp(self) -> Dict:
        """Limpa todos os dados do CLP Auditório (eventos)"""
        sucesso, erros = self.sincronizador.limpar_todos_dados_clp()
        return {
            'sucesso': sucesso,
            'erros': erros,
            'timestamp': datetime.now().isoformat()
        }
