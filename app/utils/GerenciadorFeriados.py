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
        # Sempre remover duplicatas na inicialização para garantir integridade
        self._remover_duplicatas_inicializacao()
        
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
        feriados_temp = {}  # Dicionário para controlar duplicatas: (ano, mes, dia) -> feriado
        
        ano_atual = datetime.now().year
        self.logger.info(f"Inicializando feriados padrão para {ano_atual} e {ano_atual + 1}")
        
        # Primeiro: Adicionar feriados nacionais
        for ano in range(ano_atual, ano_atual + 2):
            try:
                feriados_nacionais = holidays.Brazil(years=ano)
                
                for data, nome in feriados_nacionais.items():
                    chave_data = (data.year, data.month, data.day)
                    feriado = {
                        'id': f"{data.strftime('%Y%m%d')}_{self._gerar_id(nome)}",
                        'nome': nome,
                        'descricao': f"Feriado Nacional - {nome}",
                        'dia': data.day,
                        'mes': data.month,
                        'ano': data.year,
                        'hora_inicio': '00:00',
                        'hora_fim': '23:59',
                        'tipo': 'nacional',
                        'criado_em': datetime.now().isoformat()
                    }
                    feriados_temp[chave_data] = feriado
                    
                self.logger.debug(f"Adicionados {len([f for f in feriados_temp.values() if f['ano'] == ano and f['tipo'] == 'nacional'])} feriados nacionais para {ano}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar feriados nacionais para {ano}: {e}")
        
        # Segundo: Adicionar feriados estaduais (Goiás), mas só se não existir um nacional na mesma data
        for ano in range(ano_atual, ano_atual + 2):
            try:
                feriados_estaduais_go = holidays.Brazil(state='GO', years=ano)
                feriados_nacionais = holidays.Brazil(years=ano)
                
                estaduais_adicionados = 0
                for data, nome in feriados_estaduais_go.items():
                    chave_data = (data.year, data.month, data.day)
                    
                    # Só adiciona se não for um feriado nacional e não existir na mesma data
                    if data not in feriados_nacionais and chave_data not in feriados_temp:
                        feriado = {
                            'id': f"{data.strftime('%Y%m%d')}_{self._gerar_id(nome)}",
                            'nome': nome,
                            'descricao': f"Feriado Estadual (GO) - {nome}",
                            'dia': data.day,
                            'mes': data.month,
                            'ano': data.year,
                            'hora_inicio': '00:00',
                            'hora_fim': '23:59',
                            'tipo': 'estadual',
                            'criado_em': datetime.now().isoformat()
                        }
                        feriados_temp[chave_data] = feriado
                        estaduais_adicionados += 1
                        
                self.logger.debug(f"Adicionados {estaduais_adicionados} feriados estaduais únicos para {ano}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar feriados estaduais para {ano}: {e}")
        
        # Terceiro: Adicionar feriados municipais de Goiânia, mas só se não existir nacional ou estadual na mesma data
        feriados_municipais = [
            {'dia': 24, 'mes': 10, 'nome': 'Aniversário de Goiânia', 'descricao': 'Fundação da cidade de Goiânia'},
            {'dia': 24, 'mes': 5, 'nome': 'Nossa Senhora Auxiliadora', 'descricao': 'Padroeira de Goiânia'},
        ]
        
        municipais_adicionados = 0
        for fm in feriados_municipais:
            for ano in range(ano_atual, ano_atual + 2):
                chave_data = (ano, fm['mes'], fm['dia'])
                
                # Só adiciona se não existir um feriado de instância maior na mesma data
                if chave_data not in feriados_temp:
                    feriado = {
                        'id': f"{ano}{fm['mes']:02d}{fm['dia']:02d}_{self._gerar_id(fm['nome'])}",
                        'nome': fm['nome'],
                        'descricao': f"Feriado Municipal (Goiânia) - {fm['descricao']}",
                        'dia': fm['dia'],
                        'mes': fm['mes'],
                        'ano': ano,
                        'hora_inicio': '00:00',
                        'hora_fim': '23:59',
                        'tipo': 'municipal',
                        'criado_em': datetime.now().isoformat()
                    }
                    feriados_temp[chave_data] = feriado
                    municipais_adicionados += 1
        
        self.logger.debug(f"Adicionados {municipais_adicionados} feriados municipais únicos")
        
        # Converter dicionário para lista
        self.feriados = list(feriados_temp.values())
        
        # Ordenar por data para melhor organização
        self.feriados.sort(key=lambda x: (x['ano'], x['mes'], x['dia']))
        
        self._salvar_feriados()
        
        # Log de resumo
        total = len(self.feriados)
        nacionais = len([f for f in self.feriados if f['tipo'] == 'nacional'])
        estaduais = len([f for f in self.feriados if f['tipo'] == 'estadual'])
        municipais = len([f for f in self.feriados if f['tipo'] == 'municipal'])
        
        self.logger.info(f"Feriados padrão inicializados: {total} total ({nacionais} nacionais, {estaduais} estaduais, {municipais} municipais) - SEM DUPLICATAS")
    
    def _gerar_id(self, nome: str) -> str:
        """Gera um ID baseado no nome"""
        return nome.lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    def _verificar_feriado_existente(self, dia: int, mes: int, ano: int) -> Optional[Dict]:
        """Verifica se já existe um feriado na data especificada"""
        for feriado in self.feriados:
            if feriado['dia'] == dia and feriado['mes'] == mes and feriado['ano'] == ano:
                return feriado
        return None
    
    def _determinar_tipo_hierarquia(self, tipo_novo: str, tipo_existente: str) -> str:
        """Determina qual tipo deve prevalecer baseado na hierarquia: nacional > estadual > municipal > customizado"""
        hierarquia = {'nacional': 4, 'estadual': 3, 'municipal': 2, 'customizado': 1}
        
        prioridade_novo = hierarquia.get(tipo_novo, 0)
        prioridade_existente = hierarquia.get(tipo_existente, 0)
        
        return tipo_novo if prioridade_novo > prioridade_existente else tipo_existente
    
    def remover_duplicatas(self) -> int:
        """Remove feriados duplicados, mantendo apenas o de maior hierarquia"""
        feriados_unicos = {}
        feriados_removidos = 0
        total_inicial = len(self.feriados)
        
        self.logger.info(f"Iniciando remoção de duplicatas em {total_inicial} feriados...")
        
        for feriado in self.feriados:
            chave_data = (feriado['ano'], feriado['mes'], feriado['dia'])
            
            if chave_data not in feriados_unicos:
                feriados_unicos[chave_data] = feriado
            else:
                # Existe duplicata, manter o de maior hierarquia
                feriado_existente = feriados_unicos[chave_data]
                tipo_prevalente = self._determinar_tipo_hierarquia(feriado['tipo'], feriado_existente['tipo'])
                
                if tipo_prevalente == feriado['tipo']:
                    # O feriado atual tem prioridade maior
                    self.logger.info(f"Removendo duplicata: {feriado_existente['tipo']} '{feriado_existente['nome']}', mantendo {feriado['tipo']} '{feriado['nome']}' ({feriado['dia']:02d}/{feriado['mes']:02d}/{feriado['ano']})")
                    feriados_unicos[chave_data] = feriado
                else:
                    # O feriado existente tem prioridade maior ou igual
                    self.logger.info(f"Removendo duplicata: {feriado['tipo']} '{feriado['nome']}', mantendo {feriado_existente['tipo']} '{feriado_existente['nome']}' ({feriado['dia']:02d}/{feriado['mes']:02d}/{feriado['ano']})")
                
                feriados_removidos += 1
        
        # Atualizar lista de feriados
        self.feriados = list(feriados_unicos.values())
        # Ordenar por data
        self.feriados.sort(key=lambda x: (x['ano'], x['mes'], x['dia']))
        
        if feriados_removidos > 0:
            self._salvar_feriados()
            self.logger.info(f"Limpeza concluída: {feriados_removidos} duplicatas removidas de {total_inicial} feriados, restando {len(self.feriados)} únicos")
        else:
            self.logger.info(f"Nenhuma duplicata encontrada nos {total_inicial} feriados")
        
        return feriados_removidos
    
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
        """Adiciona um novo feriado, verificando duplicatas e respeitando hierarquia (nacional > estadual > municipal > customizado)"""
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
            
            # Verificar se já existe um feriado na mesma data
            feriado_existente = self._verificar_feriado_existente(dados['dia'], dados['mes'], dados['ano'])
            tipo_novo = dados.get('tipo', 'customizado')
            
            if feriado_existente:
                # Determinar qual tipo deve prevalecer
                tipo_prevalente = self._determinar_tipo_hierarquia(tipo_novo, feriado_existente['tipo'])
                
                if tipo_prevalente == feriado_existente['tipo']:
                    # O feriado existente tem prioridade maior ou igual
                    raise ValueError(f"Já existe um feriado {feriado_existente['tipo']} na data {dados['dia']:02d}/{dados['mes']:02d}/{dados['ano']}: {feriado_existente['nome']}")
                else:
                    # O novo feriado tem prioridade maior, substituir o existente
                    self.logger.info(f"Substituindo feriado {feriado_existente['tipo']} '{feriado_existente['nome']}' por {tipo_novo} '{dados['nome']}'")
                    self.remover_feriado(feriado_existente['id'])
            
            self.feriados.append(novo_feriado)
            self._salvar_feriados()
            
            self.logger.info(f"Feriado adicionado: {novo_feriado['nome']} ({tipo_novo})")
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
    
    def _remover_duplicatas_inicializacao(self):
        """Remove duplicatas automaticamente na inicialização do sistema"""
        try:
            if len(self.feriados) == 0:
                return
            
            feriados_unicos = {}
            feriados_removidos = 0
            total_inicial = len(self.feriados)
            
            self.logger.info(f"Verificando duplicatas em {total_inicial} feriados...")
            
            for feriado in self.feriados:
                chave_data = (feriado['ano'], feriado['mes'], feriado['dia'])
                
                if chave_data not in feriados_unicos:
                    feriados_unicos[chave_data] = feriado
                else:
                    # Existe duplicata, manter o de maior hierarquia
                    feriado_existente = feriados_unicos[chave_data]
                    tipo_prevalente = self._determinar_tipo_hierarquia(feriado['tipo'], feriado_existente['tipo'])
                    
                    if tipo_prevalente == feriado['tipo']:
                        # O feriado atual tem prioridade maior
                        self.logger.info(f"[INIT] Substituindo duplicata: {feriado_existente['tipo']} '{feriado_existente['nome']}' por {feriado['tipo']} '{feriado['nome']}'")
                        feriados_unicos[chave_data] = feriado
                    else:
                        # O feriado existente tem prioridade maior ou igual
                        self.logger.info(f"[INIT] Mantendo: {feriado_existente['tipo']} '{feriado_existente['nome']}', removendo {feriado['tipo']} '{feriado['nome']}'")
                    
                    feriados_removidos += 1
            
            # Atualizar lista de feriados
            self.feriados = list(feriados_unicos.values())
            
            if feriados_removidos > 0:
                self._salvar_feriados()
                self.logger.info(f"[INIT] Limpeza concluída: {feriados_removidos} duplicatas removidas de {total_inicial} feriados, restando {len(self.feriados)} únicos")
            else:
                self.logger.info(f"[INIT] Nenhuma duplicata encontrada nos {total_inicial} feriados")
                
        except Exception as e:
            self.logger.error(f"Erro ao remover duplicatas na inicialização: {e}")