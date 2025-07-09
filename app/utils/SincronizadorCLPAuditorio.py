# app/utils/SincronizadorCLPAuditorio.py
import json
import os
import logging
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
from threading import Lock
from requests.auth import HTTPBasicAuth
from ..config import CLP_AUDITORIO_CONFIG

class SincronizadorCLPAuditorio:
    """
    Classe responsável pela sincronização de dados entre o sistema e o CLP do Auditório
    Gerencia especificamente eventos do Auditório Nobre e Foyer do Auditório
    """
    
    _instance = None
    _lock = Lock()
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.SincronizadorCLPAuditorio')
        self.config = CLP_AUDITORIO_CONFIG
        self.status_file = self.config['STATUS_FILE']
        self.backup_file = self.config['BACKUP_FILE']
        self.ultimo_status = self._carregar_status()
        self._sincronizacao_em_andamento = False
        
        # Configurar sessão HTTP com configurações específicas
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.config['AUTH_USER'], self.config['AUTH_PASS'])
        
        # Log da configuração inicial
        self.logger.info(f"SincronizadorCLPAuditorio inicializado com API_BASE_URL: {self.config['API_BASE_URL']}")
        self.logger.info(f"CLP_IP: {self.config['CLP_IP']}")
        self.logger.info(f"Locais gerenciados: {self.config['LOCAIS_GERENCIADOS']}")
        
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
            'clp_disponivel': False,
            'eventos_auditorio_sincronizados': 0,
            'status': 'nunca_sincronizado',
            'erros': [],
            'versao_dados': 0
        }
    
    def _salvar_status(self, status: Dict) -> bool:
        """Salva o status atual da sincronização"""
        try:
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            
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
            
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao fazer backup: {e}")
            return False
    
    def _fazer_requisicao_com_correcao_redirect(self, url: str, descricao: str = "requisição") -> requests.Response:
        """
        Faz uma requisição HTTP com correção automática de redirecionamentos incorretos
        """
        try:
            response = self.session.get(url, timeout=self.config['TIMEOUT'], allow_redirects=False)
            
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                self.logger.debug(f"Redirecionamento detectado em {descricao}: {redirect_url}")
                
                # Corrigir domínio incorreto se necessário
                if 'automacao.tce.go.br' in redirect_url and 'automacao.tce.go.gov.br' not in redirect_url:
                    corrected_url = redirect_url.replace('automacao.tce.go.br', 'automacao.tce.go.gov.br')
                    self.logger.debug(f"Corrigindo domínio em {descricao}: {corrected_url}")
                    response = self.session.get(corrected_url, timeout=self.config['TIMEOUT'])
                elif 'automacao.tce.go.gov.br' in redirect_url:
                    response = self.session.get(redirect_url, timeout=self.config['TIMEOUT'])
                else:
                    self.logger.error(f"Redirecionamento para domínio desconhecido em {descricao}: {redirect_url}")
                    raise requests.exceptions.RequestException(f"Redirecionamento inválido: {redirect_url}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erro em {descricao}: {e}")
            raise
    
    def verificar_conectividade_clp(self) -> Tuple[bool, str]:
        """Verifica se o CLP está acessível"""
        if not self.config['API_BASE_URL']:
            return False, "URL da API não configurada"
        
        try:
            # Testa lendo uma tag simples (N91:0)
            url_teste = f"{self.config['API_BASE_URL']}/tag_read/{self.config['CLP_IP']}/N91%253A0"
            
            response = self._fazer_requisicao_com_correcao_redirect(url_teste, "teste de conectividade")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'valor' in data:
                        self.logger.debug(f"CLP Auditório conectado - valor lido: {data.get('valor')}")
                        return True, "CLP Auditório conectado e responsivo"
                    else:
                        self.logger.error(f"CLP Auditório respondeu mas formato inesperado: {data}")
                        return False, "CLP Auditório respondeu mas formato inesperado"
                except Exception as e:
                    self.logger.error(f"Erro ao fazer parse JSON da conectividade: {e}")
                    return False, f"Erro no parse da resposta: {str(e)}"
            elif response.status_code == 401:
                return False, "Erro de autenticação (credenciais inválidas)"
            elif response.status_code == 403:
                return False, "Acesso negado (sem permissão)"
            else:
                self.logger.error(f"CLP Auditório respondeu com status inesperado: {response.status_code}")
                return False, f"CLP Auditório respondeu com status {response.status_code}"
                
        except requests.exceptions.Timeout:
            self.logger.error("Timeout na verificação de conectividade")
            return False, "Timeout na conexão com CLP Auditório"
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Erro de conexão na verificação: {e}")
            return False, "Erro de conexão com CLP Auditório"
        except Exception as e:
            self.logger.error(f"Erro inesperado na verificação de conectividade: {e}")
            return False, f"Erro inesperado: {str(e)}"
    
    def _preparar_dados_para_clp(self, gerenciador_eventos) -> Dict:
        """Prepara os dados para envio ao CLP Auditório com filtros otimizados"""
        agora = datetime.now()
        ano_atual = agora.year
        data_atual = agora.date()
        uma_semana_atras = data_atual - timedelta(days=7)
        
        dados_clp = {
            'ano': ano_atual,
            'eventos_auditorio': [],
            'timestamp': agora.isoformat()
        }
        
        try:
            # PREPARAR EVENTOS DOS LOCAIS DO AUDITÓRIO
            eventos_filtrados = []
            
            for local in self.config['LOCAIS_GERENCIADOS']:
                eventos_local = gerenciador_eventos.obter_eventos_por_local(local, ano=ano_atual)
                
                for evento in eventos_local:
                    try:
                        data_evento = date(evento['ano'], evento['mes'], evento['dia'])
                        
                        # Incluir eventos da última semana (para documentação)
                        if uma_semana_atras <= data_evento <= data_atual:
                            eventos_filtrados.append((evento, data_evento, 'passado'))
                        
                        # Incluir eventos futuros até o fim do ano
                        elif data_evento > data_atual:
                            eventos_filtrados.append((evento, data_evento, 'futuro'))
                            
                    except ValueError:
                        self.logger.warning(f"Data inválida ignorada: {evento['dia']}/{evento['mes']}/{evento['ano']}")
                        continue
            
            # Ordenar por data e hora (passados primeiro, depois futuros)
            eventos_filtrados.sort(key=lambda x: (x[2] == 'futuro', x[1], x[0]['hora_inicio']))
            
            # Limitar a 10 eventos para não ocupar desnecessariamente o CLP
            max_eventos = min(len(eventos_filtrados), self.config['MAX_EVENTOS'])
            
            for i, (evento, data_evento, categoria) in enumerate(eventos_filtrados[:max_eventos]):
                # Extrair horas e minutos
                hora_inicio_parts = evento['hora_inicio'].split(':')
                hora_fim_parts = evento['hora_fim'].split(':')
                
                dados_clp['eventos_auditorio'].append({
                    'slot': i,
                    'dia': evento['dia'],
                    'mes': evento['mes'],
                    'hora_inicio': int(hora_inicio_parts[0]),
                    'minuto_inicio': int(hora_inicio_parts[1]),
                    'hora_fim': int(hora_fim_parts[0]),
                    'minuto_fim': int(hora_fim_parts[1]),
                    'nome': evento['nome'][:30],  # Para log/debug
                    'local': evento['local'],
                    'categoria': categoria,  # 'passado' ou 'futuro'
                    'data': data_evento.strftime('%Y-%m-%d')
                })
            
            passados_e = len([e for e in dados_clp['eventos_auditorio'] if e['categoria'] == 'passado'])
            futuros_e = len([e for e in dados_clp['eventos_auditorio'] if e['categoria'] == 'futuro'])
            
            self.logger.info(f"Dados preparados para CLP Auditório: {len(dados_clp['eventos_auditorio'])} eventos "
                           f"({passados_e} passados, {futuros_e} futuros)")
            
            if len(eventos_filtrados) > self.config['MAX_EVENTOS']:
                self.logger.info(f"Filtrados {len(eventos_filtrados)} eventos Auditório relevantes, "
                               f"enviando apenas os {self.config['MAX_EVENTOS']} mais próximos/recentes")
            
            return dados_clp
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dados: {e}")
            raise
    
    def _escrever_dados_batch(self, dados: Dict) -> Tuple[bool, List[str]]:
        """Escreve dados no CLP usando API batch"""
        erros = []
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            # Preparar operações batch
            operations = []
            
            # Escrever eventos do Auditório
            eventos = dados.get('eventos_auditorio', [])
            eventos_count = len(eventos)
            
            self.logger.info(f"Preparando escrita de {eventos_count} eventos do Auditório...")
            
            for evento in eventos:
                slot = evento['slot']
                operations.extend([
                    {"tag_address": f"N91:{slot}", "value": str(evento['dia'])},
                    {"tag_address": f"N92:{slot}", "value": str(evento['mes'])},
                    {"tag_address": f"N93:{slot}", "value": str(evento['hora_inicio'])},
                    {"tag_address": f"N94:{slot}", "value": str(evento['minuto_inicio'])},
                    {"tag_address": f"N95:{slot}", "value": str(evento['hora_fim'])},
                    {"tag_address": f"N96:{slot}", "value": str(evento['minuto_fim'])}
                ])
            
            # Limpar slots não utilizados
            max_eventos = self.config['MAX_EVENTOS']
            if eventos_count < max_eventos:
                self.logger.info(f"Preparando limpeza de slots de eventos não utilizados {eventos_count} a {max_eventos-1}...")
                
                for i in range(eventos_count, max_eventos):
                    operations.extend([
                        {"tag_address": f"N91:{i}", "value": "0"},
                        {"tag_address": f"N92:{i}", "value": "0"},
                        {"tag_address": f"N93:{i}", "value": "0"},
                        {"tag_address": f"N94:{i}", "value": "0"},
                        {"tag_address": f"N95:{i}", "value": "0"},
                        {"tag_address": f"N96:{i}", "value": "0"}
                    ])
            
            # Fazer requisição batch se houver operações
            if operations:
                payload = {
                    "clp_address": self.config['CLP_IP'],
                    "operations": operations
                }
                
                self.logger.info(f"Enviando {len(operations)} operações em lote para o CLP Auditório")
                
                url_batch = f"{self.config['API_BASE_URL']}/tag_write_batch"
                headers = {'Content-Type': 'application/json'}
                
                response = self.session.post(
                    url_batch, 
                    json=payload, 
                    headers=headers, 
                    timeout=self.config['TIMEOUT'] * 3,
                    allow_redirects=False
                )
                
                # Verificar redirecionamento
                if response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('Location', '')
                    self.logger.warning(f"Redirecionamento detectado na operação batch: {redirect_url}")
                    
                    if 'automacao.tce.go.br' in redirect_url and 'automacao.tce.go.gov.br' not in redirect_url:
                        corrected_url = redirect_url.replace('automacao.tce.go.br', 'automacao.tce.go.gov.br')
                        self.logger.warning(f"Corrigindo domínio na operação batch: {corrected_url}")
                        response = self.session.post(
                            corrected_url, 
                            json=payload, 
                            headers=headers, 
                            timeout=self.config['TIMEOUT'] * 3
                        )
                    elif 'automacao.tce.go.gov.br' in redirect_url:
                        response = self.session.post(
                            redirect_url, 
                            json=payload, 
                            headers=headers, 
                            timeout=self.config['TIMEOUT'] * 3
                        )
                    else:
                        self.logger.error(f"Redirecionamento para domínio desconhecido: {redirect_url}")
                        return False, [f"Redirecionamento inválido: {redirect_url}"]
                
                if response.status_code == 401:
                    return False, ["Erro de autenticação na operação batch"]
                elif response.status_code == 200:
                    try:
                        batch_result = response.json()
                        
                        if batch_result.get('success'):
                            summary = batch_result.get('summary', {})
                            successful = summary.get('successful', 0)
                            failed = summary.get('failed', 0)
                            
                            self.logger.info(f"Operação batch CLP Auditório concluída: {successful}/{len(operations)} operações bem-sucedidas")
                            
                            if failed > 0:
                                results = batch_result.get('results', {})
                                for tag_address, result in results.items():
                                    if not result.get('success'):
                                        erro = f"Falha na tag {tag_address}: {result.get('error', 'erro desconhecido')}"
                                        erros.append(erro)
                                        self.logger.error(erro)
                                
                                return failed == 0, erros
                            else:
                                return True, []
                        else:
                            erro = f"Operação batch falhou: {batch_result.get('error', 'erro desconhecido')}"
                            erros.append(erro)
                            self.logger.error(erro)
                            return False, erros
                    
                    except Exception as e:
                        erro = f"Erro ao processar resposta batch: {str(e)}"
                        erros.append(erro)
                        self.logger.error(f"{erro} - Conteúdo: {response.text[:500]}...")
                        return False, erros
                else:
                    erro = f"Erro HTTP na operação batch: {response.status_code}"
                    erros.append(erro)
                    self.logger.error(f"{erro} - Conteúdo: {response.text[:500]}...")
                    return False, erros
            else:
                self.logger.info("Nenhuma operação necessária para o CLP Auditório")
                return True, []
                
        except requests.exceptions.Timeout:
            erro = "Timeout na operação batch"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
        except requests.exceptions.ConnectionError as e:
            erro = f"Erro de conexão na operação batch: {str(e)}"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
        except Exception as e:
            erro = f"Erro geral na operação batch: {str(e)}"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
    
    def sincronizar_manual(self, gerenciador_eventos) -> Dict:
        """Executa sincronização manual com CLP Auditório"""
        if self._sincronizacao_em_andamento:
            return {
                'sucesso': False,
                'erro': 'Sincronização já em andamento',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            self._sincronizacao_em_andamento = True
            self.logger.info("Iniciando sincronização manual com CLP Auditório")
            
            # Verificar conectividade
            conectado, msg_conectividade = self.verificar_conectividade_clp()
            if not conectado:
                return {
                    'sucesso': False,
                    'erro': f'CLP Auditório não acessível: {msg_conectividade}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Preparar dados
            dados = self._preparar_dados_para_clp(gerenciador_eventos)
            
            # Fazer backup
            self._fazer_backup_dados(dados)
            
            # Escrever dados usando API batch
            sucesso_escrita, erros_escrita = self._escrever_dados_batch(dados)
            
            # Atualizar status
            sucesso_total = sucesso_escrita
            novo_status = self.ultimo_status.copy()
            novo_status.update({
                'ultima_tentativa': datetime.now().isoformat(),
                'clp_disponivel': conectado,
                'erros': erros_escrita
            })
            
            if sucesso_total:
                novo_status.update({
                    'ultima_sincronizacao': datetime.now().isoformat(),
                    'status': 'sincronizado',
                    'eventos_auditorio_sincronizados': len(dados.get('eventos_auditorio', [])),
                    'versao_dados': novo_status.get('versao_dados', 0) + 1
                })
                self.logger.info("Sincronização manual CLP Auditório concluída com sucesso")
            else:
                novo_status['status'] = 'erro_sincronizacao'
                self.logger.error("Sincronização manual CLP Auditório falhou")
            
            self.ultimo_status = novo_status
            self._salvar_status(novo_status)
            
            return {
                'sucesso': sucesso_total,
                'dados_sincronizados': len(dados.get('eventos_auditorio', [])),
                'eventos_auditorio': len(dados.get('eventos_auditorio', [])),
                'slots_utilizados_eventos': f"{len(dados.get('eventos_auditorio', []))}/{self.config['MAX_EVENTOS']}",
                'erros': erros_escrita,
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
    
    def limpar_todos_dados_clp(self) -> Tuple[bool, List[str]]:
        """Limpa todos os dados do CLP Auditório usando a nova API batch"""
        erros = []
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            self.logger.info("Iniciando limpeza completa do CLP Auditório usando API batch...")
            
            # Preparar todas as operações de limpeza em lote
            operations = []
            
            # Limpar todos os slots de eventos do Auditório (N91-N96)
            max_eventos = self.config['MAX_EVENTOS']
            self.logger.info(f"Preparando limpeza de {max_eventos} slots de eventos do Auditório...")
            
            for i in range(max_eventos):
                operations.extend([
                    {"tag_address": f"N91:{i}", "value": "0"},
                    {"tag_address": f"N92:{i}", "value": "0"},
                    {"tag_address": f"N93:{i}", "value": "0"},
                    {"tag_address": f"N94:{i}", "value": "0"},
                    {"tag_address": f"N95:{i}", "value": "0"},
                    {"tag_address": f"N96:{i}", "value": "0"}
                ])
            
            # Preparar payload para API batch
            payload = {
                "clp_address": self.config['CLP_IP'],
                "operations": operations
            }
            
            self.logger.info(f"Enviando {len(operations)} operações de limpeza em lote para o CLP Auditório")
            
            # Fazer requisição POST para API batch
            url_batch = f"{self.config['API_BASE_URL']}/tag_write_batch"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(
                url_batch, 
                json=payload, 
                headers=headers, 
                timeout=self.config['TIMEOUT'] * 3,
                allow_redirects=False
            )
            
            # Verificar redirecionamento
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                self.logger.warning(f"Redirecionamento detectado na limpeza batch: {redirect_url}")
                
                if 'automacao.tce.go.br' in redirect_url and 'automacao.tce.go.gov.br' not in redirect_url:
                    corrected_url = redirect_url.replace('automacao.tce.go.br', 'automacao.tce.go.gov.br')
                    self.logger.warning(f"Corrigindo domínio na limpeza batch: {corrected_url}")
                    response = self.session.post(
                        corrected_url, 
                        json=payload, 
                        headers=headers, 
                        timeout=self.config['TIMEOUT'] * 3
                    )
                elif 'automacao.tce.go.gov.br' in redirect_url:
                    response = self.session.post(
                        redirect_url, 
                        json=payload, 
                        headers=headers, 
                        timeout=self.config['TIMEOUT'] * 3
                    )
                else:
                    self.logger.error(f"Redirecionamento para domínio desconhecido: {redirect_url}")
                    return False, [f"Redirecionamento inválido: {redirect_url}"]
            
            if response.status_code == 401:
                return False, ["Erro de autenticação na limpeza batch"]
            elif response.status_code == 200:
                try:
                    batch_result = response.json()
                    
                    if batch_result.get('success'):
                        summary = batch_result.get('summary', {})
                        total = summary.get('total', 0)
                        successful = summary.get('successful', 0)
                        failed = summary.get('failed', 0)
                        
                        self.logger.info(f"Limpeza batch CLP Auditório concluída: {successful}/{total} operações bem-sucedidas")
                        
                        if failed > 0:
                            results = batch_result.get('results', {})
                            for tag_address, result in results.items():
                                if not result.get('success'):
                                    erro = f"Falha na limpeza da tag {tag_address}: {result.get('error', 'erro desconhecido')}"
                                    erros.append(erro)
                                    self.logger.error(erro)
                            
                            return failed == 0, erros
                        else:
                            self.logger.info(f"Limpeza completa CLP Auditório concluída: {max_eventos} slots de eventos limpos")
                            return True, []
                    else:
                        erro = f"Operação de limpeza batch falhou: {batch_result.get('error', 'erro desconhecido')}"
                        erros.append(erro)
                        self.logger.error(erro)
                        return False, erros
                
                except Exception as e:
                    erro = f"Erro ao processar resposta de limpeza batch: {str(e)}"
                    erros.append(erro)
                    self.logger.error(f"{erro} - Conteúdo: {response.text[:500]}...")
                    return False, erros
            else:
                erro = f"Erro HTTP na limpeza batch: {response.status_code}"
                erros.append(erro)
                self.logger.error(f"{erro} - Conteúdo: {response.text[:500]}...")
                return False, erros
                
        except requests.exceptions.Timeout:
            erro = "Timeout na limpeza batch"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
        except requests.exceptions.ConnectionError as e:
            erro = f"Erro de conexão na limpeza batch: {str(e)}"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
        except Exception as e:
            erro = f"Erro geral na limpeza batch: {str(e)}"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros
    
    def obter_status_sincronizacao(self) -> Dict:
        """Obtém status completo da sincronização com CLP Auditório"""
        conectado, msg_conectividade = self.verificar_conectividade_clp()
        
        status = self.ultimo_status.copy()
        
        # Normalizar o campo de eventos sincronizados para compatibilidade com o frontend
        eventos_sincronizados = status.get('eventos_auditorio_sincronizados', 0)
        
        status.update({
            'clp_online': conectado,
            'msg_conectividade': msg_conectividade,
            'sync_automatica_habilitada': self.config['SYNC_ENABLED'],
            'horarios_sincronizacao': self.config['SYNC_TIMES'],
            'max_eventos': self.config['MAX_EVENTOS'],
            'locais_gerenciados': self.config['LOCAIS_GERENCIADOS'],
            'clp_ip': self.config['CLP_IP'],
            'eventos_sincronizados': eventos_sincronizados  # Campo normalizado para o frontend
        })
        
        return status
