# app/utils/SincronizadorCLP.py
import json
import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from threading import Lock
import os
import time
from ..config import CLP_CONFIG, DATA_DIR

class SincronizadorCLP:
    """
    Classe responsável pela sincronização de dados entre o sistema e CLPs externos
    Gerencia leitura, escrita, validação e controle de status
    """
    
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.SincronizadorCLP')
        self.config = CLP_CONFIG
        self.status_file = self.config['STATUS_FILE']
        self.backup_file = self.config['BACKUP_FILE']
        self.ultimo_status = self._carregar_status()
        self._sincronizacao_em_andamento = False
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do sincronizador (Singleton)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _carregar_status(self) -> Dict:
        """Carrega o status da última sincronização"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erro ao carregar status: {e}")
        
        return {
            'ultima_sincronizacao': None,
            'ultima_tentativa': None,
            'status': 'nunca_sincronizado',
            'erros': [],
            'dados_sincronizados': 0,
            'clp_disponivel': False,
            'versao_dados': 0
        }
    
    def _salvar_status(self, status: Dict) -> bool:
        """Salva o status atual da sincronização"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar status: {e}")
            return False
    
    def _fazer_backup_dados(self, dados: Dict) -> bool:
        """Faz backup dos dados antes da sincronização"""
        try:
            backup = {
                'timestamp': datetime.now().isoformat(),
                'dados': dados,
                'versao': self.ultimo_status.get('versao_dados', 0) + 1
            }
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao fazer backup: {e}")
            return False
    
    def verificar_conectividade_clp(self) -> Tuple[bool, str]:
        """Verifica se o CLP está acessível"""
        if not self.config['API_BASE_URL']:
            return False, "URL da API não configurada"
        
        try:
            # Testa lendo uma tag simples (N33:0)
            url_teste = f"{self.config['API_BASE_URL']}/tag_read/{self.config['CLP_IP']}/N33%253A0"
            auth = HTTPBasicAuth(self.config['AUTH_USER'], self.config['AUTH_PASS'])
            
            response = requests.get(
                url_teste, 
                auth=auth,
                timeout=self.config['TIMEOUT']
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'valor' in data:
                    return True, "CLP conectado e responsivo"
                else:
                    return False, "CLP respondeu mas formato inesperado"
            elif response.status_code == 401:
                return False, "Erro de autenticação (credenciais inválidas)"
            elif response.status_code == 403:
                return False, "Acesso negado (sem permissão)"
            else:
                return False, f"CLP respondeu com status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout na conexão com CLP"
        except requests.exceptions.ConnectionError:
            return False, "Erro de conexão com CLP"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    def ler_dados_clp(self) -> Tuple[bool, Dict]:
        """Lê os dados atuais do CLP para comparação"""
        try:
            if not self.config['API_BASE_URL']:
                return False, {"erro": "URL da API não configurada"}
            
            auth = HTTPBasicAuth(self.config['AUTH_USER'], self.config['AUTH_PASS'])
            dados_clp = {
                'feriados': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Ler todas as tags de feriados (N33:0-19 para dias e N34:0-19 para meses)
            for i in range(self.config['MAX_FERIADOS']):
                try:
                    # Ler dia (N33:i)
                    url_dia = f"{self.config['API_BASE_URL']}/tag_read/{self.config['CLP_IP']}/N33%253A{i}"
                    response_dia = requests.get(url_dia, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    # Ler mês (N34:i)
                    url_mes = f"{self.config['API_BASE_URL']}/tag_read/{self.config['CLP_IP']}/N34%253A{i}"
                    response_mes = requests.get(url_mes, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    if response_dia.status_code == 200 and response_mes.status_code == 200:
                        data_dia = response_dia.json()
                        data_mes = response_mes.json()
                        
                        dia = data_dia.get('valor', 0)
                        mes = data_mes.get('valor', 0)
                        
                        # Se dia e mês são válidos (não zero), adicionar como feriado
                        if dia > 0 and mes > 0 and dia <= 31 and mes <= 12:
                            dados_clp['feriados'].append({
                                'slot': i,
                                'dia': dia,
                                'mes': mes
                            })
                    elif response_dia.status_code == 401 or response_mes.status_code == 401:
                        return False, {"erro": "Erro de autenticação ao ler dados"}
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao ler slot {i}: {e}")
                    continue
            
            self.logger.info(f"Lidos {len(dados_clp['feriados'])} feriados do CLP")
            return True, dados_clp
                
        except Exception as e:
            erro = f"Erro ao ler dados do CLP: {str(e)}"
            self.logger.error(erro)
            return False, {"erro": erro}
    
    def _preparar_dados_para_clp(self, gerenciador_feriados, gerenciador_eventos) -> Dict:
        """Prepara os dados para envio ao CLP com filtros otimizados"""
        agora = datetime.now()
        ano_atual = agora.year
        data_atual = agora.date()
        uma_semana_atras = data_atual - timedelta(days=7)
        
        dados_clp = {
            'ano': ano_atual,
            'feriados': [],
            'timestamp': agora.isoformat()
        }
        
        try:
            # Obter todos os feriados do ano atual
            todos_feriados = gerenciador_feriados.listar_feriados(ano=ano_atual)
            
            feriados_filtrados = []
            
            for feriado in todos_feriados:
                try:
                    data_feriado = date(ano_atual, feriado['mes'], feriado['dia'])
                    
                    # Incluir feriados da última semana (para documentação)
                    if uma_semana_atras <= data_feriado <= data_atual:
                        feriados_filtrados.append((feriado, data_feriado, 'passado'))
                    
                    # Incluir feriados futuros até o fim do ano
                    elif data_feriado > data_atual:
                        feriados_filtrados.append((feriado, data_feriado, 'futuro'))
                        
                except ValueError:
                    # Data inválida (ex: 29/02 em ano não bissexto)
                    self.logger.warning(f"Data inválida ignorada: {feriado['dia']}/{feriado['mes']}/{ano_atual}")
                    continue
            
            # Ordenar por data (passados primeiro, depois futuros)
            feriados_filtrados.sort(key=lambda x: (x[2] == 'futuro', x[1]))
            
            # Limitar a 10 feriados para não ocupar desnecessariamente o CLP
            max_feriados = min(len(feriados_filtrados), 10)
            
            for i, (feriado, data_feriado, categoria) in enumerate(feriados_filtrados[:max_feriados]):
                dados_clp['feriados'].append({
                    'slot': i,
                    'dia': feriado['dia'],
                    'mes': feriado['mes'],
                    'nome': feriado['nome'][:30],  # Para log/debug
                    'tipo': feriado['tipo'],
                    'categoria': categoria,  # 'passado' ou 'futuro'
                    'data': data_feriado.strftime('%Y-%m-%d')
                })
            
            passados = len([f for f in dados_clp['feriados'] if f['categoria'] == 'passado'])
            futuros = len([f for f in dados_clp['feriados'] if f['categoria'] == 'futuro'])
            
            self.logger.info(f"Dados preparados: {len(dados_clp['feriados'])} feriados "
                           f"({passados} passados, {futuros} futuros) - "
                           f"limitado a 10/{self.config['MAX_FERIADOS']} slots")
            
            if len(feriados_filtrados) > 10:
                self.logger.info(f"Filtrados {len(feriados_filtrados)} feriados relevantes, "
                               f"enviando apenas os 10 mais próximos/recentes para otimizar o CLP")
            
            return dados_clp
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dados: {e}")
            raise
    
    def _escrever_dados_sequencial(self, dados: Dict) -> Tuple[bool, List[str]]:
        """Escreve dados no CLP de forma sequencial usando a API do TCE"""
        erros = []
        sucesso = True
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            auth = HTTPBasicAuth(self.config['AUTH_USER'], self.config['AUTH_PASS'])
            
            # Primeiro: Limpar apenas os primeiros 10 slots (otimização)
            slots_a_limpar = min(10, self.config['MAX_FERIADOS'])
            self.logger.info(f"Limpando {slots_a_limpar} slots de feriados no CLP...")
            
            for i in range(slots_a_limpar):
                try:
                    # Limpar dia (N33:i)
                    url_dia = f"{self.config['API_BASE_URL']}/tag_write/{self.config['CLP_IP']}/N33%253A{i}/0"
                    response_dia = requests.get(url_dia, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    # Limpar mês (N34:i)
                    url_mes = f"{self.config['API_BASE_URL']}/tag_write/{self.config['CLP_IP']}/N34%253A{i}/0"
                    response_mes = requests.get(url_mes, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    if response_dia.status_code == 401 or response_mes.status_code == 401:
                        return False, ["Erro de autenticação ao escrever dados"]
                    elif response_dia.status_code != 200 or response_mes.status_code != 200:
                        erro = f"Erro ao limpar slot {i}: dia={response_dia.status_code}, mês={response_mes.status_code}"
                        erros.append(erro)
                        self.logger.warning(erro)
                    else:
                        # Verificar se retornou {"sucesso":true}
                        try:
                            data_dia = response_dia.json()
                            data_mes = response_mes.json()
                            if not (data_dia.get('sucesso') and data_mes.get('sucesso')):
                                erro = f"Falha na limpeza do slot {i}: respostas inválidas"
                                erros.append(erro)
                        except:
                            erro = f"Erro ao verificar resposta da limpeza do slot {i}"
                            erros.append(erro)
                    
                    # Pequena pausa entre escritas
                    time.sleep(0.1)
                    
                except Exception as e:
                    erro = f"Erro ao limpar slot {i}: {str(e)}"
                    erros.append(erro)
                    sucesso = False
            
            # Segundo: Escrever feriados nos slots correspondentes
            self.logger.info(f"Escrevendo {len(dados['feriados'])} feriados no CLP...")
            feriados_escritos = 0
            
            for feriado in dados['feriados']:
                slot = feriado['slot']
                dia = feriado['dia']
                mes = feriado['mes']
                
                try:
                    # Escrever dia (N33:slot)
                    url_dia = f"{self.config['API_BASE_URL']}/tag_write/{self.config['CLP_IP']}/N33%253A{slot}/{dia}"
                    response_dia = requests.get(url_dia, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    # Escrever mês (N34:slot)
                    url_mes = f"{self.config['API_BASE_URL']}/tag_write/{self.config['CLP_IP']}/N34%253A{slot}/{mes}"
                    response_mes = requests.get(url_mes, auth=auth, timeout=self.config['TIMEOUT'])
                    
                    if response_dia.status_code == 401 or response_mes.status_code == 401:
                        erro = f"Erro de autenticação ao escrever feriado {feriado['nome']}"
                        erros.append(erro)
                        sucesso = False
                    elif response_dia.status_code == 200 and response_mes.status_code == 200:
                        # Verificar se ambas as escritas retornaram {"sucesso":true}
                        try:
                            data_dia = response_dia.json()
                            data_mes = response_mes.json()
                            
                            if data_dia.get('sucesso') and data_mes.get('sucesso'):
                                feriados_escritos += 1
                                self.logger.debug(f"Feriado {feriado['nome']} escrito no slot {slot}: {dia:02d}/{mes:02d}")
                            else:
                                erro = f"Falha ao escrever feriado {feriado['nome']} no slot {slot}: sucesso=false"
                                erros.append(erro)
                                sucesso = False
                        except:
                            erro = f"Resposta inválida ao escrever feriado {feriado['nome']} no slot {slot}"
                            erros.append(erro)
                            sucesso = False
                    else:
                        erro = f"Erro HTTP ao escrever feriado {feriado['nome']} no slot {slot}: dia={response_dia.status_code}, mês={response_mes.status_code}"
                        erros.append(erro)
                        sucesso = False
                    
                    # Pequena pausa entre escritas
                    time.sleep(0.2)
                    
                except Exception as e:
                    erro = f"Erro ao escrever feriado {feriado['nome']} no slot {slot}: {str(e)}"
                    erros.append(erro)
                    sucesso = False
            
            self.logger.info(f"Processo de escrita concluído: {feriados_escritos}/{len(dados['feriados'])} feriados escritos com sucesso")
            
            if len(erros) == 0:
                sucesso = True
            
            return sucesso, erros
            
        except Exception as e:
            erro = f"Erro geral na escrita sequencial: {str(e)}"
            self.logger.error(erro)
            return False, [erro]
    
    def _verificar_integridade_dados(self, dados_enviados: Dict) -> Tuple[bool, List[str]]:
        """Verifica se os dados foram escritos corretamente no CLP"""
        try:
            sucesso_leitura, dados_clp = self.ler_dados_clp()
            if not sucesso_leitura:
                return False, ["Não foi possível ler dados do CLP para verificação"]
            
            erros_integridade = []
            
            # Verificar feriados
            feriados_enviados = len(dados_enviados['feriados'])
            feriados_clp = len(dados_clp.get('feriados', []))
            
            if feriados_enviados != feriados_clp:
                erros_integridade.append(f"Quantidade de feriados: enviados {feriados_enviados}, no CLP {feriados_clp}")
            else:
                # Verificar cada feriado individualmente
                for feriado_enviado in dados_enviados['feriados']:
                    slot = feriado_enviado['slot']
                    dia_enviado = feriado_enviado['dia']
                    mes_enviado = feriado_enviado['mes']
                    
                    # Procurar o feriado correspondente no CLP
                    feriado_encontrado = False
                    for feriado_clp in dados_clp['feriados']:
                        if (feriado_clp['slot'] == slot and 
                            feriado_clp['dia'] == dia_enviado and 
                            feriado_clp['mes'] == mes_enviado):
                            feriado_encontrado = True
                            break
                    
                    if not feriado_encontrado:
                        erros_integridade.append(f"Feriado {dia_enviado:02d}/{mes_enviado:02d} não encontrado no slot {slot} do CLP")
            
            sucesso = len(erros_integridade) == 0
            
            if sucesso:
                self.logger.info(f"Verificação de integridade passou: {feriados_clp} feriados confirmados no CLP")
            else:
                self.logger.error(f"Verificação de integridade falhou: {len(erros_integridade)} problemas encontrados")
            
            return sucesso, erros_integridade
            
        except Exception as e:
            erro = f"Erro ao verificar integridade: {str(e)}"
            self.logger.error(erro)
            return False, [erro]
    
    def sincronizar_manual(self, gerenciador_feriados, gerenciador_eventos) -> Dict:
        """Executa sincronização manual com CLP"""
        if self._sincronizacao_em_andamento:
            return {
                'sucesso': False,
                'erro': 'Sincronização já em andamento',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            self._sincronizacao_em_andamento = True
            self.logger.info("Iniciando sincronização manual com CLP")
            
            # Verificar conectividade
            conectado, msg_conectividade = self.verificar_conectividade_clp()
            if not conectado:
                return {
                    'sucesso': False,
                    'erro': f'CLP não acessível: {msg_conectividade}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Preparar dados
            dados = self._preparar_dados_para_clp(gerenciador_feriados, gerenciador_eventos)
            
            # Fazer backup
            self._fazer_backup_dados(dados)
            
            # Escrever dados
            sucesso_escrita, erros_escrita = self._escrever_dados_sequencial(dados)
            
            # Verificar integridade
            sucesso_verificacao, erros_verificacao = self._verificar_integridade_dados(dados)
            
            # Atualizar status
            sucesso_total = sucesso_escrita and sucesso_verificacao
            novo_status = self.ultimo_status.copy()
            novo_status.update({
                'ultima_tentativa': datetime.now().isoformat(),
                'clp_disponivel': conectado,
                'erros': erros_escrita + erros_verificacao
            })
            
            if sucesso_total:
                novo_status.update({
                    'ultima_sincronizacao': datetime.now().isoformat(),
                    'status': 'sincronizado',
                    'dados_sincronizados': len(dados['feriados']),
                    'feriados_sincronizados': len(dados['feriados']),
                    'versao_dados': novo_status.get('versao_dados', 0) + 1
                })
                self.logger.info("Sincronização manual concluída com sucesso")
            else:
                novo_status['status'] = 'erro_sincronizacao'
                self.logger.error("Sincronização manual falhou")
            
            self.ultimo_status = novo_status
            self._salvar_status(novo_status)
            
            return {
                'sucesso': sucesso_total,
                'dados_sincronizados': len(dados['feriados']),
                'feriados': len(dados['feriados']),
                'slots_utilizados': f"{len(dados['feriados'])}/{self.config['MAX_FERIADOS']}",
                'erros': erros_escrita + erros_verificacao,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            erro = f"Erro na sincronização manual: {str(e)}"
            self.logger.error(erro)
            return {
                'sucesso': False,
                'erro': erro,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self._sincronizacao_em_andamento = False
    
    def obter_status_sincronizacao(self) -> Dict:
        """Retorna o status atual da sincronização"""
        conectado, msg_conectividade = self.verificar_conectividade_clp()
        
        status = self.ultimo_status.copy()
        status.update({
            'clp_online': conectado,
            'msg_conectividade': msg_conectividade,
            'sincronizacao_em_andamento': self._sincronizacao_em_andamento,
            'horarios_sincronizacao': self.config['SYNC_TIMES'],
            'sync_automatica_habilitada': self.config['SYNC_ENABLED']
        })
        
        return status
    
    def deve_sincronizar_automaticamente(self) -> bool:
        """Verifica se deve executar sincronização automática baseado no horário"""
        if not self.config['SYNC_ENABLED']:
            return False
        
        agora = datetime.now()
        hora_atual = agora.strftime('%H:%M')
        
        # Verificar se é um dos horários de sincronização
        for horario in self.config['SYNC_TIMES']:
            if hora_atual == horario:
                # Verificar se já sincronizou hoje neste horário
                ultima_sync = self.ultimo_status.get('ultima_sincronizacao')
                if ultima_sync:
                    data_ultima_sync = datetime.fromisoformat(ultima_sync).date()
                    if data_ultima_sync == agora.date():
                        # Já sincronizou hoje, verificar se foi neste horário
                        hora_ultima_sync = datetime.fromisoformat(ultima_sync).strftime('%H:%M')
                        if hora_ultima_sync == horario:
                            return False  # Já sincronizou neste horário hoje
                
                return True
        
        return False
