from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

class FuncoesTecnicos(Enum):
    """Enum para as funções que os técnicos podem exercer"""
    TELEFONIA = "TELEFONIA"
    CABEAMENTO_ESTRUTURADO = "CABEAMENTO_ESTRUTURADO"
    INCENDIO = "INCENDIO"
    INSTALACOES_ELETRICAS = "INSTALACOES_ELETRICAS"
    ALARME_PATRIMONIAL = "ALARME_PATRIMONIAL"
    SISTEMAS_FOTOVOLTAICOS = "SISTEMAS_FOTOVOLTAICOS"
    GMGS = "GMGS"
    AUTOMACAO = "AUTOMACAO"
    ELEVADORES = "ELEVADORES"
    ESPELHOS_DAGUA = "ESPELHOS_DAGUA"
    INSTALACOES_HIDRAULICAS = "INSTALACOES_HIDRAULICAS"
    REFRIGERACAO = "REFRIGERACAO"
    ENGENHARIA = "ENGENHARIA"
    SUPERVISAO = "SUPERVISAO"
    CHEFE_SERVICO = "CHEFE_SERVICO"
    EVENTOS = "EVENTOS"
    VENTILACAO = "VENTILACAO"
    IRRIGACAO = "IRRIGACAO"

class MetodoContato(Enum):
    """Enum para os métodos de contato disponíveis"""
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"

@dataclass
class Tecnico:
    """Classe que representa um técnico do sistema"""
    nome: str
    telefone: str
    email: str
    metodo_contato_preferencial: MetodoContato
    funcoes: List[FuncoesTecnicos]
    jornada: List[Tuple[str, str]]  # Lista de tuplas (hora_inicio, hora_fim)
    ferias: bool = False

@dataclass
class ConfigNotificacao:
    """Configurações para o sistema de notificações"""
    disparar_dias_semana: bool = True
    disparar_finais_semana: bool = True
    horario_dias_semana: Tuple[str, str] = ("08:00", "18:00")
    horario_finais_semana: Tuple[str, str] = ("08:00", "18:00")
    repetir_notificacao: bool = False
    intervalo_repeticao_minutos: int = 60
    max_repeticoes: int = 3
