# app/utils/GerenciadorEventos.py
import json
import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from ..config import DATA_DIR

class GerenciadorEventos:
    _instance = None
    
    # Locais disponíveis para eventos
    LOCAIS_VALIDOS = ['Auditório Nobre', 'Átrio', 'Plenário', 'Creche', 'Foyer do Auditório', 'Mini-Auditório', 'Sala de Conferências']
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.GerenciadorEventos')
        self.logger.info(f"🚀 Inicializando GerenciadorEventos...")
        self.logger.info(f"📁 DATA_DIR configurado: {DATA_DIR}")
        
        self.arquivo_eventos = os.path.join(DATA_DIR, 'eventos.json')
        self.logger.info(f"📄 Arquivo de eventos: {self.arquivo_eventos}")
        
        self.eventos = []
        self._carregar_eventos()
        
        self.logger.info(f"✅ GerenciadorEventos inicializado com {len(self.eventos)} eventos")
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do gerenciador (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _carregar_eventos(self):
        """Carrega os eventos do arquivo JSON"""
        self.logger.info(f"Iniciando carregamento de eventos do arquivo: {self.arquivo_eventos}")
        
        # Verificar se o diretório existe
        dir_eventos = os.path.dirname(self.arquivo_eventos)
        if not os.path.exists(dir_eventos):
            self.logger.warning(f"Diretório não existe: {dir_eventos}")
            try:
                os.makedirs(dir_eventos, exist_ok=True)
                self.logger.info(f"Diretório criado: {dir_eventos}")
            except Exception as e:
                self.logger.error(f"Erro ao criar diretório {dir_eventos}: {e}")
        
        if os.path.exists(self.arquivo_eventos):
            try:
                # Verificar tamanho do arquivo
                tamanho_arquivo = os.path.getsize(self.arquivo_eventos)
                self.logger.info(f"Arquivo existe. Tamanho: {tamanho_arquivo} bytes")
                
                with open(self.arquivo_eventos, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    if len(conteudo) > 0:
                        self.logger.info(f"Conteúdo do arquivo (primeiros 100 chars): {conteudo[:100]}")
                    else:
                        self.logger.warning("Arquivo está vazio")
                    
                    # Voltar ao início do arquivo
                    f.seek(0)
                    self.eventos = json.load(f)
                    
                self.logger.info(f"✅ Carregados {len(self.eventos)} eventos do arquivo {self.arquivo_eventos}")
                
                if len(self.eventos) > 0:
                    self.logger.info(f"Primeiro evento: {self.eventos[0].get('nome', 'N/A')} - {self.eventos[0].get('dia', 'N/A')}/{self.eventos[0].get('mes', 'N/A')}/{self.eventos[0].get('ano', 'N/A')}")
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Erro de JSON ao carregar eventos: {e}")
                self.eventos = []
            except Exception as e:
                self.logger.error(f"Erro ao carregar eventos: {e}")
                self.eventos = []
        else:
            self.logger.warning(f"Arquivo de eventos não existe: {self.arquivo_eventos}")
            self.eventos = []
            self.logger.info("Criando arquivo de eventos vazio...")
            self._salvar_eventos()
    
    def _salvar_eventos(self):
        """Salva os eventos no arquivo JSON"""
        try:
            self.logger.info(f"Iniciando salvamento de {len(self.eventos)} eventos em: {self.arquivo_eventos}")
            
            # Verificar se o diretório existe
            dir_eventos = os.path.dirname(self.arquivo_eventos)
            if not os.path.exists(dir_eventos):
                self.logger.warning(f"Diretório não existe, criando: {dir_eventos}")
                os.makedirs(dir_eventos, exist_ok=True)
            
            with open(self.arquivo_eventos, 'w', encoding='utf-8') as f:
                json.dump(self.eventos, f, ensure_ascii=False, indent=2)
                
            # Verificar se o arquivo foi salvo corretamente
            if os.path.exists(self.arquivo_eventos):
                tamanho = os.path.getsize(self.arquivo_eventos)
                self.logger.info(f"✅ Eventos salvos com sucesso. Arquivo: {tamanho} bytes")
            else:
                self.logger.error("❌ Arquivo não foi criado após salvamento")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar eventos: {e}")
            return False
    
    def _validar_conflito_horario(self, local: str, dia: int, mes: int, ano: int, 
                                  hora_inicio: str, hora_fim: str, evento_id: Optional[str] = None) -> bool:
        """Verifica se há conflito de horário no local especificado"""
        # Converter horários para comparação
        inicio_novo = datetime.strptime(hora_inicio, '%H:%M').time()
        fim_novo = datetime.strptime(hora_fim, '%H:%M').time()
        
        for evento in self.eventos:
            # Pular o próprio evento em caso de atualização
            if evento_id and evento['id'] == evento_id:
                continue
                
            # Verificar apenas eventos no mesmo local e data
            if (evento['local'] == local and 
                evento['dia'] == dia and 
                evento['mes'] == mes and 
                evento['ano'] == ano):
                
                inicio_existente = datetime.strptime(evento['hora_inicio'], '%H:%M').time()
                fim_existente = datetime.strptime(evento['hora_fim'], '%H:%M').time()
                
                # Verificar sobreposição de horários
                if not (fim_novo <= inicio_existente or inicio_novo >= fim_existente):
                    return True
        
        return False
    
    def listar_eventos(self, ano: Optional[int] = None, mes: Optional[int] = None, 
                      local: Optional[str] = None, ano_minimo: Optional[int] = None) -> List[Dict]:
        """Lista todos os eventos ou filtra por ano/mês/local"""
        eventos_filtrados = self.eventos
        
        # Filtrar eventos muito antigos (mais de 7 dias) apenas se não houver filtro de mês específico
        if not mes and not ano:
            data_limite = datetime.now() - timedelta(days=7)
            
            eventos_filtrados = [e for e in eventos_filtrados 
                               if datetime(e['ano'], e['mes'], e['dia']) >= data_limite]
        
        if ano:
            eventos_filtrados = [e for e in eventos_filtrados if e['ano'] == ano]
        elif ano_minimo:
            eventos_filtrados = [e for e in eventos_filtrados if e['ano'] >= ano_minimo]
        
        if mes:
            eventos_filtrados = [e for e in eventos_filtrados if e['mes'] == mes]
        
        if local:
            eventos_filtrados = [e for e in eventos_filtrados if e['local'] == local]
        
        # Ordenar por data e hora
        eventos_filtrados.sort(key=lambda x: (x['ano'], x['mes'], x['dia'], x['hora_inicio']))
        
        return eventos_filtrados
    
    def obter_evento(self, evento_id: str) -> Optional[Dict]:
        """Obtém um evento específico pelo ID"""
        for evento in self.eventos:
            if evento['id'] == evento_id:
                return evento
        return None
    
    def adicionar_evento(self, dados: Dict) -> Dict:
        """Adiciona um novo evento"""
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['nome', 'local', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")
            
            # Validar local
            if dados['local'] not in self.LOCAIS_VALIDOS:
                raise ValueError(f"Local inválido. Locais válidos: {', '.join(self.LOCAIS_VALIDOS)}")
            
            # Validar data
            try:
                data_teste = date(dados['ano'], dados['mes'], dados['dia'])
            except ValueError:
                raise ValueError("Data inválida")
            
            # Validar horários
            try:
                hora_inicio = datetime.strptime(dados['hora_inicio'], '%H:%M')
                hora_fim = datetime.strptime(dados['hora_fim'], '%H:%M')
                
                if hora_inicio >= hora_fim:
                    raise ValueError("Hora de início deve ser anterior à hora de término")
                    
            except ValueError as e:
                if "time data" in str(e):
                    raise ValueError("Formato de horário inválido. Use HH:MM")
                raise
            
            # Verificar conflito de horário
            if self._validar_conflito_horario(dados['local'], dados['dia'], dados['mes'], 
                                            dados['ano'], dados['hora_inicio'], dados['hora_fim']):
                raise ValueError(f"Conflito de horário no {dados['local']} para esta data e horário")
            
            # Criar novo evento
            novo_evento = {
                'id': f"{dados['ano']}{dados['mes']:02d}{dados['dia']:02d}_{dados['local'].lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
                'nome': dados['nome'],
                'descricao': dados.get('descricao', ''),
                'local': dados['local'],
                'dia': dados['dia'],
                'mes': dados['mes'],
                'ano': dados['ano'],
                'hora_inicio': dados['hora_inicio'],
                'hora_fim': dados['hora_fim'],
                'responsavel': dados.get('responsavel', ''),
                'participantes_estimados': dados.get('participantes_estimados', 0),
                'criado_em': datetime.now().isoformat(),
                'atualizado_em': datetime.now().isoformat()
            }
            
            self.eventos.append(novo_evento)
            self._salvar_eventos()
            
            # Registrar no histórico
            try:
                from .GerenciadorHistorico import GerenciadorHistorico
                historico = GerenciadorHistorico.get_instance()
                historico.registrar_alteracao(
                    tipo_entidade='evento',
                    entidade_id=novo_evento['id'],
                    operacao='criar',
                    dados_novos=novo_evento
                )
            except Exception as e_hist:
                self.logger.warning(f"Falha ao registrar no histórico: {e_hist}")
            
            # Integração com sistema de notificações em background
            try:
                import threading
                from .GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
                
                def enviar_notificacao_background():
                    """Envia notificação em thread separada para não bloquear a interface"""
                    try:
                        gerenciador_notificacao = GerenciadorNotificacaoEventos.get_instance()
                        gerenciador_notificacao.notificar_evento_criado(novo_evento)
                        self.logger.info(f"Notificação de evento enviada em background: {novo_evento['nome']}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao enviar notificação de evento em background: {e}")
                
                # Executar notificação em thread separada (não bloqueante)
                thread_notificacao = threading.Thread(
                    target=enviar_notificacao_background,
                    daemon=True,  # Thread será encerrada quando a aplicação principal terminar
                    name=f"NotificacaoEvento_{novo_evento['id']}"
                )
                thread_notificacao.start()
                self.logger.debug(f"Thread de notificação iniciada para evento: {novo_evento['nome']}")
                
            except Exception as e:
                self.logger.warning(f"Erro ao iniciar thread de notificação: {e}")
            
            self.logger.info(f"Evento adicionado: {novo_evento['nome']} no {novo_evento['local']}")
            return novo_evento
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar evento: {e}")
            raise
    
    def atualizar_evento(self, evento_id: str, dados: Dict) -> Optional[Dict]:
        """Atualiza um evento existente"""
        try:
            for i, evento in enumerate(self.eventos):
                if evento['id'] == evento_id:
                    # Snapshot antes das mudanças para notificação
                    evento_antes = evento.copy()
                    # Validar local se fornecido
                    if 'local' in dados and dados['local'] not in self.LOCAIS_VALIDOS:
                        raise ValueError(f"Local inválido. Locais válidos: {', '.join(self.LOCAIS_VALIDOS)}")
                    
                    # Validar data se fornecida
                    if any(k in dados for k in ['dia', 'mes', 'ano']):
                        dia = dados.get('dia', evento['dia'])
                        mes = dados.get('mes', evento['mes'])
                        ano = dados.get('ano', evento['ano'])
                        try:
                            date(ano, mes, dia)
                        except ValueError:
                            raise ValueError("Data inválida")
                    
                    # Validar horários se fornecidos
                    hora_inicio = dados.get('hora_inicio', evento['hora_inicio'])
                    hora_fim = dados.get('hora_fim', evento['hora_fim'])
                    
                    try:
                        h_inicio = datetime.strptime(hora_inicio, '%H:%M')
                        h_fim = datetime.strptime(hora_fim, '%H:%M')
                        
                        if h_inicio >= h_fim:
                            raise ValueError("Hora de início deve ser anterior à hora de término")
                    except ValueError as e:
                        if "time data" in str(e):
                            raise ValueError("Formato de horário inválido. Use HH:MM")
                        raise
                    
                    # Verificar conflito de horário
                    local = dados.get('local', evento['local'])
                    dia = dados.get('dia', evento['dia'])
                    mes = dados.get('mes', evento['mes'])
                    ano = dados.get('ano', evento['ano'])
                    
                    if self._validar_conflito_horario(local, dia, mes, ano, hora_inicio, hora_fim, evento_id):
                        raise ValueError(f"Conflito de horário no {local} para esta data e horário")
                    
                    # Atualizar campos
                    campos_atualizaveis = ['nome', 'descricao', 'local', 'dia', 'mes', 'ano', 
                                         'hora_inicio', 'hora_fim', 'responsavel', 'participantes_estimados']
                    
                    for campo in campos_atualizaveis:
                        if campo in dados:
                            evento[campo] = dados[campo]
                    
                    evento['atualizado_em'] = datetime.now().isoformat()
                    
                    self._salvar_eventos()
                    
                    # Registrar no histórico
                    try:
                        from .GerenciadorHistorico import GerenciadorHistorico
                        historico = GerenciadorHistorico.get_instance()
                        historico.registrar_alteracao(
                            tipo_entidade='evento',
                            entidade_id=evento_id,
                            operacao='editar',
                            dados_anteriores=evento_antes,
                            dados_novos=evento
                        )
                    except Exception as e_hist:
                        self.logger.warning(f"Falha ao registrar no histórico: {e_hist}")
                    
                    self.logger.info(f"Evento atualizado: {evento['nome']}")

                    # Enviar notificação de alteração em background
                    try:
                        import threading
                        from .GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos

                        def enviar_notificacao_alteracao():
                            try:
                                ger = GerenciadorNotificacaoEventos.get_instance()
                                ger.notificar_evento_alterado(evento_antes, evento)
                            except Exception as e:
                                self.logger.warning(f"Erro ao notificar alteração de evento: {e}")

                        t = threading.Thread(
                            target=enviar_notificacao_alteracao,
                            daemon=True,
                            name=f"NotificacaoAlteracao_{evento_id}"
                        )
                        t.start()
                    except Exception as e:
                        self.logger.warning(f"Falha ao iniciar thread de notificação de alteração: {e}")

                    return evento
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar evento: {e}")
            raise
    
    def remover_evento(self, evento_id: str) -> bool:
        """Remove um evento"""
        try:
            for i, evento in enumerate(self.eventos):
                if evento['id'] == evento_id:
                    # Capturar dados do evento antes de remover para notificação
                    evento_para_notificar = evento.copy()
                    nome = evento['nome']
                    local = evento['local']
                    
                    # Remover evento
                    del self.eventos[i]
                    self._salvar_eventos()
                    
                    # Registrar no histórico
                    try:
                        from .GerenciadorHistorico import GerenciadorHistorico
                        historico = GerenciadorHistorico.get_instance()
                        historico.registrar_alteracao(
                            tipo_entidade='evento',
                            entidade_id=evento_id,
                            operacao='excluir',
                            dados_anteriores=evento_para_notificar
                        )
                    except Exception as e_hist:
                        self.logger.warning(f"Falha ao registrar no histórico: {e_hist}")
                    
                    self.logger.info(f"Evento removido: {nome} do {local}")
                    
                    # Enviar notificação de cancelamento em background thread
                    def enviar_notificacao_cancelamento():
                        try:
                            from .GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
                            gerenciador_notificacao = GerenciadorNotificacaoEventos.get_instance()
                            gerenciador_notificacao.notificar_evento_cancelado(evento_para_notificar)
                            self.logger.info(f"Notificação de cancelamento enviada em background: {nome}")
                        except Exception as e:
                            self.logger.warning(f"Erro ao enviar notificação de cancelamento em background: {e}")
                    
                    # Executar notificação em thread separada (não bloqueante)
                    try:
                        import threading
                        thread_notificacao = threading.Thread(
                            target=enviar_notificacao_cancelamento,
                            daemon=True,
                            name=f"NotificacaoCancelamento_{evento_id}"
                        )
                        thread_notificacao.start()
                        self.logger.debug(f"Thread de notificação de cancelamento iniciada para evento: {nome}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao iniciar thread de notificação de cancelamento: {e}")
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao remover evento: {e}")
            return False
    
    def obter_eventos_por_data(self, dia: int, mes: int, ano: int) -> List[Dict]:
        """Obtém todos os eventos de uma data específica"""
        eventos_data = []
        for evento in self.eventos:
            if evento['dia'] == dia and evento['mes'] == mes and evento['ano'] == ano:
                eventos_data.append(evento)
        
        # Ordenar por hora de início
        eventos_data.sort(key=lambda x: x['hora_inicio'])
        return eventos_data
    
    def obter_eventos_por_local(self, local: str, mes: Optional[int] = None, ano: Optional[int] = None) -> List[Dict]:
        """Obtém todos os eventos de um local específico"""
        if local not in self.LOCAIS_VALIDOS:
            raise ValueError(f"Local inválido. Locais válidos: {', '.join(self.LOCAIS_VALIDOS)}")
        
        eventos_local = [e for e in self.eventos if e['local'] == local]
        
        if ano:
            eventos_local = [e for e in eventos_local if e['ano'] == ano]
        
        if mes:
            eventos_local = [e for e in eventos_local if e['mes'] == mes]
        
        # Ordenar por data e hora
        eventos_local.sort(key=lambda x: (x['ano'], x['mes'], x['dia'], x['hora_inicio']))
        return eventos_local
    
    def obter_locais_disponiveis(self) -> List[str]:
        """Retorna a lista de locais disponíveis"""
        return self.LOCAIS_VALIDOS.copy()
    
    def encerrar_evento_agora(self, evento_id: str) -> Optional[Dict]:
        """
        Encerra um evento mais cedo removendo o dia atual dos CLPs envolvidos.
        Isso fará com que o CLP desligue luzes e ar condicionado imediatamente.
        
        IMPORTANTE: Marca o evento como encerrado para evitar que seja reprogramado
        nas sincronizações automáticas (7h e 18h).
        
        Returns:
            Dict com informações do evento e resultado da operação, ou None se evento não encontrado
        """
        try:
            # Buscar índice do evento para atualizar
            evento_index = None
            for i, evt in enumerate(self.eventos):
                if evt['id'] == evento_id:
                    evento_index = i
                    break
            
            if evento_index is None:
                self.logger.error(f"Evento não encontrado: {evento_id}")
                return None
            
            evento = self.eventos[evento_index]
            
            # Verificar se já está encerrado
            if evento.get('encerrado_em'):
                raise ValueError(f"Evento já foi encerrado em {evento['encerrado_em']}")
            
            # Verificar se o evento é hoje
            data_hoje = date.today()
            data_evento = date(evento['ano'], evento['mes'], evento['dia'])
            
            if data_evento != data_hoje:
                raise ValueError(f"Evento não é de hoje. Data do evento: {data_evento.strftime('%d/%m/%Y')}")
            
            self.logger.info(f"Encerrando evento '{evento['nome']}' do local '{evento['local']}' mais cedo...")
            
            # MARCAR EVENTO COMO ENCERRADO no banco de dados
            timestamp_encerramento = datetime.now().isoformat()
            self.eventos[evento_index]['encerrado_em'] = timestamp_encerramento
            self.eventos[evento_index]['atualizado_em'] = timestamp_encerramento
            
            # Salvar alterações no arquivo
            if not self._salvar_eventos():
                self.logger.error("Falha ao salvar evento encerrado no arquivo")
                raise Exception("Erro ao persistir encerramento do evento")
            
            self.logger.info(f"✅ Evento '{evento['nome']}' marcado como encerrado em {timestamp_encerramento}")
            
            # Retornar dados do evento para processamento externo
            return {
                'evento': self.eventos[evento_index],
                'local': evento['local'],
                'dia': evento['dia'],
                'mes': evento['mes'],
                'ano': evento['ano'],
                'timestamp': timestamp_encerramento
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao encerrar evento: {e}")
            raise
    
    def reativar_evento(self, evento_id: str) -> Optional[Dict]:
        """
        Reativa um evento que foi encerrado mais cedo.
        Remove a marca de encerramento para que o evento volte a ser sincronizado com o CLP.
        
        Returns:
            Dict com informações do evento reativado, ou None se evento não encontrado
        """
        try:
            # Buscar índice do evento para atualizar
            evento_index = None
            for i, evt in enumerate(self.eventos):
                if evt['id'] == evento_id:
                    evento_index = i
                    break
            
            if evento_index is None:
                self.logger.error(f"Evento não encontrado: {evento_id}")
                return None
            
            evento = self.eventos[evento_index]
            
            # Verificar se está encerrado
            if not evento.get('encerrado_em'):
                raise ValueError("Evento não está encerrado")
            
            self.logger.info(f"Reativando evento '{evento['nome']}' do local '{evento['local']}'...")
            
            # REMOVER MARCA DE ENCERRAMENTO
            encerrado_em_anterior = evento['encerrado_em']
            del self.eventos[evento_index]['encerrado_em']
            self.eventos[evento_index]['atualizado_em'] = datetime.now().isoformat()
            
            # Salvar alterações no arquivo
            if not self._salvar_eventos():
                self.logger.error("Falha ao salvar evento reativado no arquivo")
                raise Exception("Erro ao persistir reativação do evento")
            
            self.logger.info(f"✅ Evento '{evento['nome']}' reativado (estava encerrado desde {encerrado_em_anterior})")
            
            return self.eventos[evento_index]
            
        except Exception as e:
            self.logger.error(f"Erro ao reativar evento: {e}")
            raise