# app/utils/GerenciadorFeriados.py
import json
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import holidays
from ..config import DATA_DIR

class GerenciadorFeriados:
    _instance = None
    
    def __init__(self):
        self.logger = logging.getLogger('EventosFeriados.GerenciadorFeriados')
        self.arquivo_feriados = os.path.join(DATA_DIR, 'feriados.json')
        self.feriados = []
        self._carregar_feriados()
        
    @classmethod
    def get_instance(cls):
        """Retorna a instância única do gerenciador (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _carregar_feriados(self):
        """Carrega os feriados do arquivo JSON ou inicializa com feriados padrão"""
        if os.path.exists(self.arquivo_feriados):
            try:
                with open(self.arquivo_feriados, 'r', encoding='utf-8') as f:
                    self.feriados = json.load(f)
                self.logger.info(f"Carregados {len(self.feriados)} feriados do arquivo")
            except Exception as e:
                self.logger.error(f"Erro ao carregar feriados: {e}")
                self._inicializar_feriados_padrao()
        else:
            self._inicializar_feriados_padrao()
    
    def _inicializar_feriados_padrao(self):
        """Inicializa com feriados nacionais, estaduais e municipais de Goiânia"""
        self.feriados = []
        
        # Obter feriados do Brasil usando a biblioteca holidays
        br_holidays = holidays.Brazil(state='GO')
        
        # Adicionar feriados nacionais e estaduais para os próximos 2 anos
        ano_atual = datetime.now().year
        for ano in range(ano_atual, ano_atual + 2):
            feriados_ano = holidays.Brazil(state='GO', years=ano)
            
            for data, nome in feriados_ano.items():
                feriado = {
                    'id': f"{data.strftime('%Y%m%d')}_{self._gerar_id(nome)}",
                    'nome': nome,
                    'descricao': f"Feriado {nome}",
                    'dia': data.day,
                    'mes': data.month,
                    'ano': data.year,
                    'hora_inicio': '00:00',
                    'hora_fim': '23:59',
                    'tipo': 'nacional' if nome in holidays.Brazil().items() else 'estadual',
                    'criado_em': datetime.now().isoformat()
                }
                self.feriados.append(feriado)
        
        # Adicionar feriados municipais de Goiânia
        feriados_municipais = [
            {'dia': 24, 'mes': 10, 'nome': 'Aniversário de Goiânia', 'descricao': 'Fundação da cidade de Goiânia'},
            {'dia': 24, 'mes': 5, 'nome': 'Nossa Senhora Auxiliadora', 'descricao': 'Padroeira de Goiânia'},
        ]
        
        for fm in feriados_municipais:
            for ano in range(ano_atual, ano_atual + 2):
                feriado = {
                    'id': f"{ano}{fm['mes']:02d}{fm['dia']:02d}_{self._gerar_id(fm['nome'])}",
                    'nome': fm['nome'],
                    'descricao': fm['descricao'],
                    'dia': fm['dia'],
                    'mes': fm['mes'],
                    'ano': ano,
                    'hora_inicio': '00:00',
                    'hora_fim': '23:59',
                    'tipo': 'municipal',
                    'criado_em': datetime.now().isoformat()
                }
                self.feriados.append(feriado)
        
        self._salvar_feriados()
        self.logger.info(f"Inicializados {len(self.feriados)} feriados padrão")
    
    def _gerar_id(self, nome: str) -> str:
        """Gera um ID baseado no nome"""
        return nome.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    def _salvar_feriados(self):
        """Salva os feriados no arquivo JSON"""
        try:
            with open(self.arquivo_feriados, 'w', encoding='utf-8') as f:
                json.dump(self.feriados, f, ensure_ascii=False, indent=2)
            self.logger.info("Feriados salvos com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar feriados: {e}")
            return False
    
    def listar_feriados(self, ano: Optional[int] = None, mes: Optional[int] = None, ano_minimo: Optional[int] = None) -> List[Dict]:
        """Lista todos os feriados ou filtra por ano/mês"""
        feriados_filtrados = self.feriados
        
        if ano:
            feriados_filtrados = [f for f in feriados_filtrados if f['ano'] == ano]
        elif ano_minimo:
            feriados_filtrados = [f for f in feriados_filtrados if f['ano'] >= ano_minimo]
        
        if mes:
            feriados_filtrados = [f for f in feriados_filtrados if f['mes'] == mes]
        
        # Ordenar por data
        feriados_filtrados.sort(key=lambda x: (x['ano'], x['mes'], x['dia']))
        
        return feriados_filtrados
    
    def obter_feriado(self, feriado_id: str) -> Optional[Dict]:
        """Obtém um feriado específico pelo ID"""
        for feriado in self.feriados:
            if feriado['id'] == feriado_id:
                return feriado
        return None
    
    def adicionar_feriado(self, dados: Dict) -> Dict:
        """Adiciona um novo feriado"""
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['nome', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    raise ValueError(f"Campo obrigatório ausente: {campo}")
            
            # Validar data
            try:
                data_teste = date(dados['ano'], dados['mes'], dados['dia'])
            except ValueError:
                raise ValueError("Data inválida")
            
            # Validar horários
            try:
                datetime.strptime(dados['hora_inicio'], '%H:%M')
                datetime.strptime(dados['hora_fim'], '%H:%M')
            except ValueError:
                raise ValueError("Formato de horário inválido. Use HH:MM")
            
            # Criar novo feriado
            novo_feriado = {
                'id': f"{dados['ano']}{dados['mes']:02d}{dados['dia']:02d}_{self._gerar_id(dados['nome'])}_{int(datetime.now().timestamp())}",
                'nome': dados['nome'],
                'descricao': dados.get('descricao', ''),
                'dia': dados['dia'],
                'mes': dados['mes'],
                'ano': dados['ano'],
                'hora_inicio': dados['hora_inicio'],
                'hora_fim': dados['hora_fim'],
                'tipo': dados.get('tipo', 'customizado'),
                'criado_em': datetime.now().isoformat(),
                'atualizado_em': datetime.now().isoformat()
            }
            
            self.feriados.append(novo_feriado)
            self._salvar_feriados()
            
            self.logger.info(f"Feriado adicionado: {novo_feriado['nome']}")
            return novo_feriado
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar feriado: {e}")
            raise
    
    def atualizar_feriado(self, feriado_id: str, dados: Dict) -> Optional[Dict]:
        """Atualiza um feriado existente"""
        try:
            for i, feriado in enumerate(self.feriados):
                if feriado['id'] == feriado_id:
                    # Validar data se fornecida
                    if any(k in dados for k in ['dia', 'mes', 'ano']):
                        dia = dados.get('dia', feriado['dia'])
                        mes = dados.get('mes', feriado['mes'])
                        ano = dados.get('ano', feriado['ano'])
                        try:
                            date(ano, mes, dia)
                        except ValueError:
                            raise ValueError("Data inválida")
                    
                    # Validar horários se fornecidos
                    if 'hora_inicio' in dados:
                        try:
                            datetime.strptime(dados['hora_inicio'], '%H:%M')
                        except ValueError:
                            raise ValueError("Formato de hora_inicio inválido")
                    
                    if 'hora_fim' in dados:
                        try:
                            datetime.strptime(dados['hora_fim'], '%H:%M')
                        except ValueError:
                            raise ValueError("Formato de hora_fim inválido")
                    
                    # Atualizar campos
                    for campo in ['nome', 'descricao', 'dia', 'mes', 'ano', 'hora_inicio', 'hora_fim', 'tipo']:
                        if campo in dados:
                            feriado[campo] = dados[campo]
                    
                    feriado['atualizado_em'] = datetime.now().isoformat()
                    
                    self._salvar_feriados()
                    self.logger.info(f"Feriado atualizado: {feriado['nome']}")
                    return feriado
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar feriado: {e}")
            raise
    
    def remover_feriado(self, feriado_id: str) -> bool:
        """Remove um feriado"""
        try:
            for i, feriado in enumerate(self.feriados):
                if feriado['id'] == feriado_id:
                    nome = feriado['nome']
                    del self.feriados[i]
                    self._salvar_feriados()
                    self.logger.info(f"Feriado removido: {nome}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao remover feriado: {e}")
            return False
    
    def verificar_feriado(self, dia: int, mes: int, ano: int) -> Optional[Dict]:
        """Verifica se uma data específica é feriado"""
        for feriado in self.feriados:
            if feriado['dia'] == dia and feriado['mes'] == mes and feriado['ano'] == ano:
                return feriado
        return None