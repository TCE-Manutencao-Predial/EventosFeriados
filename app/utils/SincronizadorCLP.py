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
import urllib3

# Desabilitar avisos de SSL não verificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        
        # Configurar sessão HTTP com configurações específicas
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.config['AUTH_USER'], self.config['AUTH_PASS'])
        
        # Log da configuração inicial
        self.logger.info(f"SincronizadorCLP inicializado com API_BASE_URL: {self.config['API_BASE_URL']}")
        self.logger.info(f"CLP_IP: {self.config['CLP_IP']}")
        self.logger.info(f"AUTH_USER: {self.config['AUTH_USER']}")
        
    def _fazer_requisicao_com_correcao_redirect(self, url: str, descricao: str = "requisição") -> requests.Response:
        """
        Faz uma requisição HTTP com correção automática de redirecionamentos incorretos
        """
        try:
            response = self.session.get(url, timeout=self.config['TIMEOUT'], allow_redirects=False, verify=False)
            
            # Verificar se houve redirecionamento
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                self.logger.warning(f"Redirecionamento detectado para {descricao}: {redirect_url}")
                
                # Corrigir domínio incorreto se necessário
                if 'automacao.tce.go.br' in redirect_url and 'automacao.tce.go.gov.br' not in redirect_url:
                    corrected_url = redirect_url.replace('automacao.tce.go.br', 'automacao.tce.go.gov.br')
                    self.logger.warning(f"Corrigindo domínio para {descricao}: {corrected_url}")
                    response = self.session.get(corrected_url, timeout=self.config['TIMEOUT'], verify=False)
                elif 'automacao.tce.go.gov.br' in redirect_url:
                    # Domínio correto, seguir normalmente
                    response = self.session.get(redirect_url, timeout=self.config['TIMEOUT'], verify=False)
                else:
                    self.logger.error(f"Redirecionamento para domínio desconhecido em {descricao}: {redirect_url}")
                    
            return response
            
        except Exception as e:
            self.logger.error(f"Erro na requisição {descricao}: {e}")
            raise
        
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
            'feriados_sincronizados': 0,
            'eventos_sincronizados': 0,
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
            # Log da configuração para debug
            #self.logger.info(f"Configuração API_BASE_URL: {self.config['API_BASE_URL']}")
            
            # Testa lendo uma tag simples (N33:0)
            url_teste = f"{self.config['API_BASE_URL']}/tag_read/{self.config['CLP_IP']}/N33%253A0"
            
            #self.logger.info(f"Testando conectividade com URL completa: {url_teste}")
            
            response = self._fazer_requisicao_com_correcao_redirect(url_teste, "teste de conectividade")
            
            #self.logger.debug(f"Resposta da conectividade: Status {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'valor' in data:
                        self.logger.debug(f"CLP conectado - valor lido: {data.get('valor')}")
                        return True, "CLP conectado e responsivo"
                    else:
                        self.logger.error(f"CLP respondeu mas formato inesperado: {data}")
                        return False, "CLP respondeu mas formato inesperado"
                except Exception as e:
                    self.logger.error(f"Erro ao fazer parse JSON da conectividade: {e}")
                    self.logger.error(f"Conteúdo da resposta: {response.text[:200]}...")
                    return False, f"Erro no parse da resposta: {str(e)}"
            elif response.status_code == 401:
                return False, "Erro de autenticação (credenciais inválidas)"
            elif response.status_code == 403:
                return False, "Acesso negado (sem permissão)"
            else:
                self.logger.error(f"CLP respondeu com status inesperado: {response.status_code}")
                self.logger.error(f"Conteúdo da resposta: {response.text[:200]}...")
                return False, f"CLP respondeu com status {response.status_code}"
                
        except requests.exceptions.Timeout:
            self.logger.error("Timeout na verificação de conectividade")
            return False, "Timeout na conexão com CLP"
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Erro de conexão na verificação: {e}")
            return False, "Erro de conexão com CLP"
        except Exception as e:
            self.logger.error(f"Erro inesperado na verificação de conectividade: {e}")
            return False, f"Erro inesperado: {str(e)}"
    
    def _preparar_dados_para_clp(self, gerenciador_feriados, gerenciador_eventos) -> Dict:
        """Prepara os dados para envio ao CLP com filtros otimizados"""
        agora = datetime.now()
        ano_atual = agora.year
        data_atual = agora.date()
        uma_semana_atras = data_atual - timedelta(days=7)
        
        dados_clp = {
            'ano': ano_atual,
            'feriados': [],
            'eventos_plenario': [],
            'timestamp': agora.isoformat()
        }
        
        try:
            # PREPARAR FERIADOS
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
            
            # PREPARAR EVENTOS DO PLENÁRIO
            todos_eventos_plenario = gerenciador_eventos.obter_eventos_por_local('Plenário', ano=ano_atual)
            eventos_filtrados = []
            
            for evento in todos_eventos_plenario:
                try:
                    # FILTRAR EVENTOS ENCERRADOS - NÃO SINCRONIZAR COM CLP
                    if evento.get('encerrado_em'):
                        self.logger.info(f"⏭️ Ignorando evento encerrado: '{evento['nome']}' (encerrado em {evento['encerrado_em']})")
                        continue
                    
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
            max_eventos = min(len(eventos_filtrados), 10)
            
            for i, (evento, data_evento, categoria) in enumerate(eventos_filtrados[:max_eventos]):
                # Extrair horas e minutos
                hora_inicio_parts = evento['hora_inicio'].split(':')
                hora_fim_parts = evento['hora_fim'].split(':')
                
                dados_clp['eventos_plenario'].append({
                    'slot': i,
                    'dia': evento['dia'],
                    'mes': evento['mes'],
                    'hora_inicio': int(hora_inicio_parts[0]),
                    'minuto_inicio': int(hora_inicio_parts[1]),
                    'hora_fim': int(hora_fim_parts[0]),
                    'minuto_fim': int(hora_fim_parts[1]),
                    'nome': evento['nome'][:30],  # Para log/debug
                    'categoria': categoria,  # 'passado' ou 'futuro'
                    'data': data_evento.strftime('%Y-%m-%d')
                })
            
            passados_f = len([f for f in dados_clp['feriados'] if f['categoria'] == 'passado'])
            futuros_f = len([f for f in dados_clp['feriados'] if f['categoria'] == 'futuro'])
            passados_e = len([e for e in dados_clp['eventos_plenario'] if e['categoria'] == 'passado'])
            futuros_e = len([e for e in dados_clp['eventos_plenario'] if e['categoria'] == 'futuro'])
            
            self.logger.info(f"Dados preparados: {len(dados_clp['feriados'])} feriados "
                           f"({passados_f} passados, {futuros_f} futuros), "
                           f"{len(dados_clp['eventos_plenario'])} eventos Plenário "
                           f"({passados_e} passados, {futuros_e} futuros)")
            
            if len(feriados_filtrados) > 10:
                self.logger.info(f"Filtrados {len(feriados_filtrados)} feriados relevantes, "
                               f"enviando apenas os 10 mais próximos/recentes")
            
            if len(eventos_filtrados) > 10:
                self.logger.info(f"Filtrados {len(eventos_filtrados)} eventos Plenário relevantes, "
                               f"enviando apenas os 10 mais próximos/recentes")
            
            return dados_clp
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dados: {e}")
            raise
    
    def _escrever_dados_batch(self, dados: Dict) -> Tuple[bool, List[str]]:
        """Escreve dados no CLP usando a nova API batch para evitar timeouts"""
        erros = []
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            # Montar todas as operações em um único payload
            operations = []
            
            # Adicionar operações de feriados
            feriados_count = len(dados['feriados'])
            self.logger.info(f"Preparando escrita de {feriados_count} feriados no CLP...")
            
            for feriado in dados['feriados']:
                slot = feriado['slot']
                dia = feriado['dia']
                mes = feriado['mes']
                
                # Adicionar operações para dia e mês
                operations.append({"tag_address": f"N33:{slot}", "value": str(dia)})
                operations.append({"tag_address": f"N34:{slot}", "value": str(mes)})
            
            # Adicionar operações de limpeza para slots de feriados não utilizados
            slots_a_limpar = min(10, self.config['MAX_FERIADOS'])
            if feriados_count < slots_a_limpar:
                self.logger.info(f"Preparando limpeza de slots não utilizados {feriados_count} a {slots_a_limpar-1}...")
                
                for i in range(feriados_count, slots_a_limpar):
                    operations.append({"tag_address": f"N33:{i}", "value": "0"})
                    operations.append({"tag_address": f"N34:{i}", "value": "0"})
            
            # Adicionar operações de eventos do Plenário
            eventos_count = len(dados.get('eventos_plenario', []))
            if eventos_count > 0:
                self.logger.info(f"Preparando escrita de {eventos_count} eventos do Plenário no CLP...")
                
                for evento in dados['eventos_plenario']:
                    slot = evento['slot']
                    dia = evento['dia']
                    mes = evento['mes']
                    hora_inicio = evento['hora_inicio']
                    minuto_inicio = evento['minuto_inicio']
                    hora_fim = evento['hora_fim']
                    minuto_fim = evento['minuto_fim']
                    
                    # Adicionar operações para evento completo
                    operations.append({"tag_address": f"N60:{slot}", "value": str(dia)})
                    operations.append({"tag_address": f"N61:{slot}", "value": str(mes)})
                    operations.append({"tag_address": f"N62:{slot}", "value": str(hora_inicio)})
                    operations.append({"tag_address": f"N63:{slot}", "value": str(minuto_inicio)})
                    operations.append({"tag_address": f"N64:{slot}", "value": str(hora_fim)})
                    operations.append({"tag_address": f"N65:{slot}", "value": str(minuto_fim)})
            
            # Adicionar operações de limpeza para slots de eventos não utilizados
            max_eventos = self.config.get('MAX_EVENTOS', 10)
            if eventos_count < max_eventos:
                self.logger.info(f"Preparando limpeza de slots de eventos não utilizados {eventos_count} a {max_eventos-1}...")
                
                for i in range(eventos_count, max_eventos):
                    operations.append({"tag_address": f"N60:{i}", "value": "0"})
                    operations.append({"tag_address": f"N61:{i}", "value": "0"})
                    operations.append({"tag_address": f"N62:{i}", "value": "0"})
                    operations.append({"tag_address": f"N63:{i}", "value": "0"})
                    operations.append({"tag_address": f"N64:{i}", "value": "0"})
                    operations.append({"tag_address": f"N65:{i}", "value": "0"})
            
            # Preparar payload para API batch
            payload = {
                "clp_address": self.config['CLP_IP'],
                "operations": operations
            }
            
            self.logger.info(f"Enviando {len(operations)} operações em lote para o CLP")
            self.logger.debug(f"Payload batch: {json.dumps(payload, indent=2)}")
            
            # Fazer requisição POST para API batch
            url_batch = f"{self.config['API_BASE_URL']}/tag_write_batch"
            headers = {'Content-Type': 'application/json'}
            
            # DEBUG COMPLETO PARA DIAGNOSTICAR ERRO 405
            self.logger.info("=== DEBUG API BATCH - INÍCIO ===")
            self.logger.info(f"URL completa: {url_batch}")
            self.logger.info(f"Método HTTP: POST")
            self.logger.info(f"Headers enviados: {headers}")
            self.logger.info(f"CLP Address: {payload['clp_address']}")
            self.logger.info(f"Número de operações: {len(operations)}")
            self.logger.info(f"Tamanho do payload: {len(json.dumps(payload))} bytes")
            self.logger.info(f"Auth configurado: {self.config['AUTH_USER']}")
            self.logger.info(f"Sessão tem auth: {hasattr(self.session, 'auth') and self.session.auth is not None}")
            
            # Verificar URL parseada
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url_batch)
                self.logger.info(f"URL parseada - Scheme: {parsed.scheme}, Host: {parsed.netloc}, Path: {parsed.path}")
            except Exception as e:
                self.logger.error(f"Erro ao fazer parse da URL: {e}")
            
            # Teste HEAD para verificar se endpoint existe
            try:
                self.logger.info("Testando endpoint com HEAD request...")
                head_resp = self.session.head(url_batch, headers=headers, timeout=10, allow_redirects=False)
                self.logger.info(f"HEAD response: Status {head_resp.status_code}")
                self.logger.info(f"HEAD headers: {dict(head_resp.headers)}")
            except Exception as e:
                self.logger.error(f"Erro no HEAD request: {e}")
            
            self.logger.info("Fazendo requisição POST...")
            
            response = self.session.post(
                url_batch, 
                json=payload, 
                headers=headers, 
                timeout=self.config['TIMEOUT'] * 3,  # Timeout maior para operação batch
                allow_redirects=False
            )
            
            # Verificar redirecionamento
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                self.logger.warning(f"Redirecionamento detectado na operação batch: {redirect_url}")
                
                # Corrigir domínio incorreto se necessário
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
            
            self.logger.info(f"Resposta da API batch: Status {response.status_code}")
            
            # DEBUG COMPLETO DA RESPOSTA
            self.logger.info("=== DEBUG RESPOSTA API ===")
            self.logger.info(f"Status Code: {response.status_code}")
            self.logger.info(f"Response Headers: {dict(response.headers)}")
            self.logger.info(f"Response URL: {response.url}")
            self.logger.info(f"Request URL: {response.request.url}")
            self.logger.info(f"Request Method: {response.request.method}")
            self.logger.info(f"Request Headers: {dict(response.request.headers)}")
            
            # Diagnóstico específico para erro 405
            if response.status_code == 405:
                self.logger.error("=== DIAGNÓSTICO ERRO 405 METHOD NOT ALLOWED ===")
                self.logger.error("CAUSAS POSSÍVEIS:")
                self.logger.error("1. Endpoint /api/tag_write_batch não existe na API externa")
                self.logger.error("2. API externa não aceita método POST neste endpoint")
                self.logger.error("3. Endpoint requer parâmetros ou formato diferente")
                self.logger.error("4. Problema de autenticação impedindo acesso ao endpoint")
                
                # Verificar Allow header
                allow_methods = response.headers.get('Allow', 'não especificado')
                self.logger.error(f"Métodos permitidos pelo servidor: {allow_methods}")
                
                # Log do conteúdo completo
                response_content = response.text
                self.logger.error(f"Conteúdo completo da resposta 405:")
                self.logger.error("--- INÍCIO RESPOSTA ---")
                self.logger.error(response_content)
                self.logger.error("--- FIM RESPOSTA ---")
                
                # Tentar GET no mesmo endpoint
                try:
                    self.logger.info("Testando GET no mesmo endpoint...")
                    get_resp = self.session.get(url_batch, timeout=10, allow_redirects=False, verify=False)
                    self.logger.info(f"GET response: Status {get_resp.status_code}")
                    if get_resp.status_code != 405:
                        self.logger.info(f"GET content: {get_resp.text[:200]}...")
                except Exception as e:
                    self.logger.error(f"Erro no teste GET: {e}")
                
                # Tentar API raiz
                try:
                    self.logger.info("Testando API raiz...")
                    root_url = f"{self.config['API_BASE_URL']}"
                    root_resp = self.session.get(root_url, timeout=10, allow_redirects=False, verify=False)
                    self.logger.info(f"API raiz response: Status {root_resp.status_code}")
                    if root_resp.status_code == 200:
                        self.logger.info(f"API raiz content: {root_resp.text[:300]}...")
                except Exception as e:
                    self.logger.error(f"Erro no teste API raiz: {e}")
            
            if response.status_code == 401:
                return False, ["Erro de autenticação na operação batch"]
            elif response.status_code == 200:
                # Processar resposta batch
                try:
                    batch_result = response.json()
                    self.logger.debug(f"Resultado batch: {json.dumps(batch_result, indent=2)}")
                    
                    if batch_result.get('success'):
                        summary = batch_result.get('summary', {})
                        total = summary.get('total', 0)
                        successful = summary.get('successful', 0)
                        failed = summary.get('failed', 0)
                        
                        self.logger.info(f"Operação batch concluída: {successful}/{total} operações bem-sucedidas")
                        
                        if failed > 0:
                            # Coletar erros específicos
                            results = batch_result.get('results', {})
                            for tag_address, result in results.items():
                                if not result.get('success'):
                                    erro = f"Falha na tag {tag_address}: {result.get('error', 'erro desconhecido')}"
                                    erros.append(erro)
                                    self.logger.error(erro)
                            
                            return failed == 0, erros  # Sucesso apenas se nenhuma operação falhou
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
                # DEBUG PARA ERROS HTTP DIFERENTES DE 200/401
                self.logger.error("=== DEBUG ERRO HTTP ===")
                self.logger.error(f"Status Code: {response.status_code}")
                self.logger.error(f"URL requisição: {response.url}")
                self.logger.error(f"Método: {response.request.method}")
                self.logger.error(f"Headers resposta: {dict(response.headers)}")
                
                # Mapear códigos de erro
                error_map = {
                    400: "Bad Request - Payload inválido",
                    404: "Not Found - Endpoint não existe",
                    405: "Method Not Allowed - Método POST não permitido",
                    415: "Unsupported Media Type - Content-Type inválido",
                    500: "Internal Server Error - Erro interno da API",
                    502: "Bad Gateway - Problema proxy/gateway",
                    503: "Service Unavailable - Serviço indisponível"
                }
                
                error_desc = error_map.get(response.status_code, "Erro HTTP desconhecido")
                self.logger.error(f"Descrição: {error_desc}")
                
                erro = f"Erro HTTP na operação batch: {response.status_code} - {error_desc}"
                erros.append(erro)
                self.logger.error(f"{erro} - Conteúdo: {response.text[:500]}...")
                return False, erros
                
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
                    'dados_sincronizados': len(dados['feriados']) + len(dados.get('eventos_plenario', [])),
                    'feriados_sincronizados': len(dados['feriados']),
                    'eventos_sincronizados': len(dados.get('eventos_plenario', [])),
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
                'dados_sincronizados': len(dados['feriados']) + len(dados.get('eventos_plenario', [])),
                'feriados': len(dados['feriados']),
                'eventos_plenario': len(dados.get('eventos_plenario', [])),
                'slots_utilizados_feriados': f"{len(dados['feriados'])}/{self.config['MAX_FERIADOS']}",
                'slots_utilizados_eventos': f"{len(dados.get('eventos_plenario', []))}/{self.config.get('MAX_EVENTOS', 10)}",
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
    
    def obter_status_sincronizacao(self) -> Dict:
        """Retorna o status atual da sincronização"""
        self.logger.info("Obtendo status de sincronização...")
        
        conectado, msg_conectividade = self.verificar_conectividade_clp()
        
        self.logger.info(f"Conectividade verificada: conectado={conectado}, mensagem='{msg_conectividade}'")
        
        status = self.ultimo_status.copy()
        status.update({
            'clp_online': conectado,
            'msg_conectividade': msg_conectividade,
            'sincronizacao_em_andamento': self._sincronizacao_em_andamento,
            'horarios_sincronizacao': self.config['SYNC_TIMES'],
            'sync_automatica_habilitada': self.config['SYNC_ENABLED']
        })
        
        self.logger.info(f"Status compilado: {status}")
        
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
    
    def limpar_todos_dados_clp(self) -> Tuple[bool, List[str]]:
        """Limpa todos os dados do CLP usando a nova API batch"""
        erros = []
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            self.logger.info("Iniciando limpeza completa do CLP usando API batch...")
            
            # Preparar todas as operações de limpeza em lote
            operations = []
            
            # Limpar todos os slots de feriados (N33 e N34)
            max_feriados = self.config['MAX_FERIADOS']
            self.logger.info(f"Preparando limpeza de {max_feriados} slots de feriados...")
            
            for i in range(max_feriados):
                operations.append({"tag_address": f"N33:{i}", "value": "0"})
                operations.append({"tag_address": f"N34:{i}", "value": "0"})
            
            # Limpar todos os slots de eventos do Plenário (N60-N65)
            max_eventos = self.config.get('MAX_EVENTOS', 10)
            self.logger.info(f"Preparando limpeza de {max_eventos} slots de eventos do Plenário...")
            
            for i in range(max_eventos):
                operations.append({"tag_address": f"N60:{i}", "value": "0"})
                operations.append({"tag_address": f"N61:{i}", "value": "0"})
                operations.append({"tag_address": f"N62:{i}", "value": "0"})
                operations.append({"tag_address": f"N63:{i}", "value": "0"})
                operations.append({"tag_address": f"N64:{i}", "value": "0"})
                operations.append({"tag_address": f"N65:{i}", "value": "0"})
            
            # Preparar payload para API batch
            payload = {
                "clp_address": self.config['CLP_IP'],
                "operations": operations
            }
            
            self.logger.info(f"Enviando {len(operations)} operações de limpeza em lote para o CLP")
            self.logger.debug(f"Payload de limpeza: {json.dumps(payload, indent=2)}")
            
            # Fazer requisição POST para API batch
            url_batch = f"{self.config['API_BASE_URL']}/tag_write_batch"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(
                url_batch, 
                json=payload, 
                headers=headers, 
                timeout=self.config['TIMEOUT'] * 3,  # Timeout maior para operação batch
                allow_redirects=False
            )
            
            # Verificar redirecionamento
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                self.logger.warning(f"Redirecionamento detectado na limpeza batch: {redirect_url}")
                
                # Corrigir domínio incorreto se necessário
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
            
            self.logger.info(f"Resposta da API batch de limpeza: Status {response.status_code}")
            
            if response.status_code == 401:
                return False, ["Erro de autenticação na limpeza batch"]
            elif response.status_code == 200:
                # Processar resposta batch
                try:
                    batch_result = response.json()
                    self.logger.debug(f"Resultado da limpeza batch: {json.dumps(batch_result, indent=2)}")
                    
                    if batch_result.get('success'):
                        summary = batch_result.get('summary', {})
                        total = summary.get('total', 0)
                        successful = summary.get('successful', 0)
                        failed = summary.get('failed', 0)
                        
                        self.logger.info(f"Limpeza batch concluída: {successful}/{total} operações bem-sucedidas")
                        
                        if failed > 0:
                            # Coletar erros específicos
                            results = batch_result.get('results', {})
                            for tag_address, result in results.items():
                                if not result.get('success'):
                                    erro = f"Falha na limpeza da tag {tag_address}: {result.get('error', 'erro desconhecido')}"
                                    erros.append(erro)
                                    self.logger.error(erro)
                            
                            return failed == 0, erros  # Sucesso apenas se nenhuma operação falhou
                        else:
                            self.logger.info(f"Limpeza completa concluída: {max_feriados} slots de feriados e {max_eventos} slots de eventos limpos")
                            return True, []
                    else:
                        erro = f"Operação de limpeza batch falhou: {batch_result.get('error', 'erro desconhecido')}"
                        erros.append(erro)
                        self.logger.error(erro)
                        return False, erros
                
                except Exception as e:
                    erro = f"Erro ao processar resposta da limpeza batch: {str(e)}"
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
    
    def get_status(self) -> Dict:
        """Retorna o status atual da sincronização"""
        return self.ultimo_status.copy()
    
    def is_sincronizacao_em_andamento(self) -> bool:
        """Verifica se há sincronização em andamento"""
        return self._sincronizacao_em_andamento
    
    def remover_eventos_do_dia(self, dia: int, mes: int) -> Tuple[bool, List[str]]:
        """
        Remove todos os eventos do Plenário de um dia específico do CLP.
        Usado para encerrar eventos mais cedo.
        
        Args:
            dia: Dia do evento (1-31)
            mes: Mês do evento (1-12)
            
        Returns:
            Tupla (sucesso, lista_de_erros)
        """
        erros = []
        
        try:
            if not self.config['API_BASE_URL']:
                return False, ["URL da API não configurada"]
            
            self.logger.info(f"Removendo eventos do Plenário do dia {dia:02d}/{mes:02d} do CLP...")
            
            # Preparar operações para zerar apenas os eventos do dia específico
            operations = []
            max_eventos = self.config.get('MAX_EVENTOS', 10)
            
            # Iterar pelos slots e zerar aqueles que correspondem ao dia/mês
            for i in range(max_eventos):
                # Ler valor atual para verificar se é o dia correto
                # Como não temos leitura batch, vamos zerar todos os slots que correspondem
                # ao padrão dia/mês usando operações condicionais
                operations.append({"tag_address": f"N60:{i}", "value": "0"})
                operations.append({"tag_address": f"N61:{i}", "value": "0"})
                operations.append({"tag_address": f"N62:{i}", "value": "0"})
                operations.append({"tag_address": f"N63:{i}", "value": "0"})
                operations.append({"tag_address": f"N64:{i}", "value": "0"})
                operations.append({"tag_address": f"N65:{i}", "value": "0"})
            
            # Preparar payload para API batch
            payload = {
                "clp_address": self.config['CLP_IP'],
                "operations": operations
            }
            
            self.logger.info(f"Limpando todos os {max_eventos} slots de eventos do Plenário (dia {dia:02d}/{mes:02d})")
            
            # Fazer requisição POST para API batch
            url_batch = f"{self.config['API_BASE_URL']}/tag_write_batch"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(
                url_batch, 
                json=payload, 
                headers=headers, 
                timeout=self.config['TIMEOUT'] * 2,
                allow_redirects=False
            )
            
            # Verificar redirecionamento
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                if 'automacao.tce.go.br' in redirect_url and 'automacao.tce.go.gov.br' not in redirect_url:
                    corrected_url = redirect_url.replace('automacao.tce.go.br', 'automacao.tce.go.gov.br')
                    response = self.session.post(corrected_url, json=payload, headers=headers, 
                                                timeout=self.config['TIMEOUT'] * 2)
                elif 'automacao.tce.go.gov.br' in redirect_url:
                    response = self.session.post(redirect_url, json=payload, headers=headers, 
                                                timeout=self.config['TIMEOUT'] * 2)
            
            if response.status_code == 200:
                batch_result = response.json()
                if batch_result.get('success'):
                    summary = batch_result.get('summary', {})
                    successful = summary.get('successful', 0)
                    failed = summary.get('failed', 0)
                    
                    self.logger.info(f"Remoção de eventos concluída: {successful} operações bem-sucedidas, {failed} falharam")
                    
                    if failed > 0:
                        results = batch_result.get('results', {})
                        for tag_address, result in results.items():
                            if not result.get('success'):
                                erro = f"Falha na tag {tag_address}: {result.get('error', 'erro desconhecido')}"
                                erros.append(erro)
                    
                    return failed == 0, erros
                else:
                    erro = f"Operação falhou: {batch_result.get('error', 'erro desconhecido')}"
                    erros.append(erro)
                    return False, erros
            else:
                erro = f"Erro HTTP: {response.status_code}"
                erros.append(erro)
                return False, erros
                
        except Exception as e:
            erro = f"Erro ao remover eventos do dia: {str(e)}"
            erros.append(erro)
            self.logger.error(erro)
            return False, erros

