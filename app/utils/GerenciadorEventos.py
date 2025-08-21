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
    LOCAIS_VALIDOS = ['Auditório Nobre', 'Átrio', 'Plenário', 'Creche', 'Foyer do Auditório']
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.GerenciadorEventos')
        self.arquivo_eventos = os.path.join(DATA_DIR, 'eventos.json')
        self.eventos = []
        self._carregar_eventos()
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do gerenciador (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _carregar_eventos(self):
        """Carrega os eventos do arquivo JSON"""
        if os.path.exists(self.arquivo_eventos):
            try:
                with open(self.arquivo_eventos, 'r', encoding='utf-8') as f:
                    self.eventos = json.load(f)
                self.logger.info(f"Carregados {len(self.eventos)} eventos do arquivo")
            except Exception as e:
                self.logger.error(f"Erro ao carregar eventos: {e}")
                self.eventos = []
        else:
            self.eventos = []
            self._salvar_eventos()
    
    def _salvar_eventos(self):
        """Salva os eventos no arquivo JSON"""
        try:
            with open(self.arquivo_eventos, 'w', encoding='utf-8') as f:
                json.dump(self.eventos, f, ensure_ascii=False, indent=2)
            self.logger.info("Eventos salvos com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar eventos: {e}")
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
            
            # Integração com sistema de notificações
            try:
                from .GerenciadorNotificacaoEventos import GerenciadorNotificacaoEventos
                gerenciador_notificacao = GerenciadorNotificacaoEventos.get_instance()
                gerenciador_notificacao.notificar_evento_criado(novo_evento)
            except Exception as e:
                self.logger.warning(f"Erro ao enviar notificação de evento criado: {e}")
            
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
                    self.logger.info(f"Evento atualizado: {evento['nome']}")
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
                    nome = evento['nome']
                    local = evento['local']
                    del self.eventos[i]
                    self._salvar_eventos()
                    self.logger.info(f"Evento removido: {nome} do {local}")
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