# app/utils/IntegracaoCLP.py
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging
from .SincronizadorCLP import SincronizadorCLP

class IntegracaoCLP:
    """
    Classe para integração com CLPs (Controladores Lógicos Programáveis)
    Fornece interface simplificada para consulta de feriados e eventos
    """
    
    def __init__(self, gerenciador_feriados, gerenciador_eventos):
        self.logger = logging.getLogger('EventosFeriados.IntegracaoCLP')
        self.gerenciador_feriados = gerenciador_feriados
        self.gerenciador_eventos = gerenciador_eventos
        self.sincronizador = SincronizadorCLP.get_instance()
    
    def obter_status_sincronizacao(self) -> Dict:
        """Obtém status completo da sincronização com CLP"""
        return self.sincronizador.obter_status_sincronizacao()
    
    def sincronizar_dados(self) -> Dict:
        """Executa sincronização manual com CLP"""
        return self.sincronizador.sincronizar_manual(
            self.gerenciador_feriados,
            self.gerenciador_eventos
        )
    
    def verificar_conectividade(self) -> Dict:
        """Verifica conectividade com CLP"""
        conectado, mensagem = self.sincronizador.verificar_conectividade_clp()
        return {
            'conectado': conectado,
            'mensagem': mensagem,
            'timestamp': datetime.now().isoformat()
        }
    
    def ler_dados_do_clp(self) -> Dict:
        """Lê dados atuais do CLP"""
        sucesso, dados = self.sincronizador.ler_dados_clp()
        return {
            'sucesso': sucesso,
            'dados': dados,
            'timestamp': datetime.now().isoformat()
        }
    
    def obter_status_data(self, dia: int, mes: int, ano: int) -> Dict:
        """
        Obtém status completo de uma data específica
        Retorna informações sobre feriado e eventos do dia
        """
        try:
            # Verificar se é feriado
            feriado = self.gerenciador_feriados.verificar_feriado(dia, mes, ano)
            
            # Obter eventos do dia
            eventos = self.gerenciador_eventos.obter_eventos_por_data(dia, mes, ano)
            
            # Preparar resposta otimizada para CLP
            status = {
                'data': f'{dia:02d}/{mes:02d}/{ano}',
                'timestamp': int(datetime(ano, mes, dia).timestamp()),
                'e_feriado': feriado is not None,
                'feriado': None,
                'total_eventos': len(eventos),
                'eventos_por_local': {},
                'proximos_eventos': []
            }
            
            if feriado:
                status['feriado'] = {
                    'nome': feriado['nome'],
                    'tipo': feriado['tipo']
                }
            
            # Organizar eventos por local
            for local in self.gerenciador_eventos.LOCAIS_VALIDOS:
                eventos_local = [e for e in eventos if e['local'] == local]
                if eventos_local:
                    status['eventos_por_local'][local] = [{
                        'nome': e['nome'],
                        'inicio': e['hora_inicio'],
                        'fim': e['hora_fim']
                    } for e in eventos_local]
            
            # Adicionar próximos eventos (até 3)
            for evento in eventos[:3]:
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
        Obtém calendário resumido do mês para CLPs
        Inclui apenas dias com feriados ou eventos
        """
        try:
            # Obter feriados do mês
            feriados = self.gerenciador_feriados.listar_feriados(ano=ano, mes=mes)
            
            # Obter eventos do mês
            eventos = self.gerenciador_eventos.listar_eventos(ano=ano, mes=mes)
            
            # Criar estrutura de calendário
            calendario = {
                'mes': mes,
                'ano': ano,
                'dias_especiais': {},
                'total_feriados': len(feriados),
                'total_eventos': len(eventos)
            }
            
            # Adicionar feriados
            for feriado in feriados:
                dia = feriado['dia']
                if dia not in calendario['dias_especiais']:
                    calendario['dias_especiais'][dia] = {
                        'feriado': False,
                        'eventos': 0
                    }
                calendario['dias_especiais'][dia]['feriado'] = True
            
            # Adicionar contagem de eventos
            for evento in eventos:
                dia = evento['dia']
                if dia not in calendario['dias_especiais']:
                    calendario['dias_especiais'][dia] = {
                        'feriado': False,
                        'eventos': 0
                    }
                calendario['dias_especiais'][dia]['eventos'] += 1
            
            return calendario
            
        except Exception as e:
            self.logger.error(f"Erro ao obter calendário resumido: {e}")
            raise
    
    def obter_proximo_evento(self, local: Optional[str] = None) -> Optional[Dict]:
        """
        Obtém o próximo evento a ocorrer (geral ou por local)
        Útil para CLPs que precisam se preparar para eventos
        """
        try:
            agora = datetime.now()
            hoje = agora.date()
            hora_atual = agora.time()
            
            # Obter eventos futuros
            eventos_futuros = []
            
            # Verificar próximos 365 dias
            for dias in range(365):
                data_verificar = hoje + timedelta(days=dias)
                eventos_dia = self.gerenciador_eventos.obter_eventos_por_data(
                    data_verificar.day, 
                    data_verificar.month, 
                    data_verificar.year
                )
                
                for evento in eventos_dia:
                    # Se é hoje, verificar se o horário ainda não passou
                    if dias == 0:
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
            
            # Preparar resposta simplificada
            return {
                'nome': proximo['nome'],
                'local': proximo['local'],
                'data': f"{proximo['dia']:02d}/{proximo['mes']:02d}/{proximo['ano']}",
                'inicio': proximo['hora_inicio'],
                'fim': proximo['hora_fim'],
                'timestamp': proximo['timestamp'],
                'em_dias': dias,
                'descricao': proximo.get('descricao', '')
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter próximo evento: {e}")
            return None
    
    def verificar_local_disponivel(self, local: str, dia: int, mes: int, ano: int,
                                  hora_inicio: str, hora_fim: str) -> Dict:
        """
        Verifica se um local está disponível em determinado horário
        Útil para CLPs que controlam acesso aos locais
        """
        try:
            if local not in self.gerenciador_eventos.LOCAIS_VALIDOS:
                return {
                    'disponivel': False,
                    'motivo': 'Local inválido',
                    'locais_validos': self.gerenciador_eventos.LOCAIS_VALIDOS
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
        """
        Exporta dados em formato otimizado para CLPs
        formato: 'compacto' ou 'completo'
        """
        try:
            agora = datetime.now()
            
            if formato == 'compacto':
                # Formato compacto: apenas próximos 30 dias
                dados = {
                    'versao': '1.0',
                    'timestamp': int(agora.timestamp()),
                    'proximos_30_dias': []
                }
                
                for dias in range(30):
                    data = agora.date() + timedelta(days=dias)
                    status = self.obter_status_data(data.day, data.month, data.year)
                    
                    if status['e_feriado'] or status['total_eventos'] > 0:
                        dados['proximos_30_dias'].append({
                            'd': data.day,
                            'm': data.month,
                            'f': 1 if status['e_feriado'] else 0,
                            'e': status['total_eventos']
                        })
                
            else:  # completo
                # Formato completo: mais detalhado
                dados = {
                    'versao': '1.0',
                    'timestamp': int(agora.timestamp()),
                    'ano_atual': agora.year,
                    'mes_atual': agora.month,
                    'dia_atual': agora.day,
                    'locais': self.gerenciador_eventos.LOCAIS_VALIDOS,
                    'calendario': {}
                }
                
                # Incluir 3 meses de dados
                for offset_mes in range(3):
                    mes = (agora.month + offset_mes - 1) % 12 + 1
                    ano = agora.year + ((agora.month + offset_mes - 1) // 12)
                    
                    calendario_mes = self.obter_calendario_resumido(mes, ano)
                    dados['calendario'][f'{ano}-{mes:02d}'] = calendario_mes
            
            return dados
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar dados para CLP: {e}")
            raise
        
    def limpar_todos_dados_clp(self) -> Dict:
        """Limpa todos os dados do CLP (feriados e eventos)"""
        sucesso, erros = self.sincronizador.limpar_todos_dados_clp()
        return {
            'sucesso': sucesso,
            'erros': erros,
            'timestamp': datetime.now().isoformat()
        }