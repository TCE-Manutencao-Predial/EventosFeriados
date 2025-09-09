from app.alarmes.ClassesSistema import Tecnico, FuncoesTecnicos, MetodoContato
from typing import List, Tuple

def inicializar_tecnicos() -> List[Tecnico]:
    """Inicializa e retorna a lista de técnicos do sistema"""
    tecnicos = []

    # OBS: Telefones aqui não são mais usados para WhatsApp; o envio por WhatsApp ocorre via API por função.
    # Os emails continuam válidos para quem preferir EMAIL.
    tecnicos.append(Tecnico(
        nome="Flaximan Arruda dos Santos Junior",
    telefone="",  # desabilitado para WhatsApp direto
        email="elderflaximan@gmail.com",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.TELEFONIA,
            FuncoesTecnicos.CABEAMENTO_ESTRUTURADO,
            FuncoesTecnicos.INCENDIO,
            FuncoesTecnicos.INSTALACOES_ELETRICAS,
            FuncoesTecnicos.ALARME_PATRIMONIAL,
            FuncoesTecnicos.SISTEMAS_FOTOVOLTAICOS,
            FuncoesTecnicos.GMGS,
            FuncoesTecnicos.AUTOMACAO,
            FuncoesTecnicos.EVENTOS,
        ],
        jornada=[("08:00", "17:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Grupo Elevadores - Orona",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ELEVADORES
        ],
        jornada=[("05:00", "23:00")],
        ferias=False
    ))
    
    tecnicos.append(Tecnico(
        nome="Grupo Manutenção Predial",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ESPELHOS_DAGUA,
            FuncoesTecnicos.INSTALACOES_HIDRAULICAS
        ],
        jornada=[("05:00", "23:00")],
        ferias=False
    ))
    
    tecnicos.append(Tecnico(
        nome="Grupo Refrigeração - Powersafety",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.REFRIGERACAO
        ],
        jornada=[("05:00", "23:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Pedro Henrique Mota Emiliano",
    telefone="",
        email="phmotaemiliano@gmail.com",
        metodo_contato_preferencial=MetodoContato.EMAIL,
        funcoes=[
            FuncoesTecnicos.ENGENHARIA,
            FuncoesTecnicos.SUPERVISAO,
            FuncoesTecnicos.CHEFE_SERVICO,
            FuncoesTecnicos.EVENTOS,
        ],
        jornada=[("08:00", "12:00"), ("14:00", "23:50")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Kamila Leandro Costa",
    telefone="",
        email="kleandro@tce.go.gov.br",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.SUPERVISAO,
            FuncoesTecnicos.EVENTOS,
        ],
        jornada=[("07:00", "13:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Gilney da Costa Vaz",
    telefone="",
        email="gcosta@tce.go.gov.br",
        metodo_contato_preferencial=MetodoContato.EMAIL,
        funcoes=[
            FuncoesTecnicos.SUPERVISAO,
            FuncoesTecnicos.EVENTOS,
            FuncoesTecnicos.INCENDIO,
            FuncoesTecnicos.ELEVADORES,
        ],
        jornada=[("07:00", "13:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Ângela Cássia Moraes",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ELEVADORES
        ],
        jornada=[("07:00", "13:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Andreia da Silva Pinto",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ESPELHOS_DAGUA,
            FuncoesTecnicos.EVENTOS
        ],
        jornada=[("07:00", "12:00"), ("13:00", "16:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Francimar Pereira dos Santos Oliveira",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ESPELHOS_DAGUA,
            FuncoesTecnicos.INSTALACOES_HIDRAULICAS,
            FuncoesTecnicos.ESPELHOS_DAGUA,
            FuncoesTecnicos.EVENTOS,
        ],
        jornada=[("08:00", "17:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Adriano Alves Ferreira",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ELEVADORES,
            FuncoesTecnicos.INSTALACOES_HIDRAULICAS,
            FuncoesTecnicos.ESPELHOS_DAGUA
        ],
        jornada=[("08:00", "17:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Daniel Gomes de Lima",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.VENTILACAO,
            FuncoesTecnicos.REFRIGERACAO,
            FuncoesTecnicos.EVENTOS,
        ],
        jornada=[("08:00", "17:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Thiago Henrique Lemes Borges Teixeira",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.IRRIGACAO
        ],
        jornada=[("08:00", "17:00")],
        ferias=False
    ))

    tecnicos.append(Tecnico(
        nome="Juliana Borges de Souza",
    telefone="",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ELEVADORES
        ],
        jornada=[("13:00", "19:00")],
        ferias=False
    ))

    return tecnicos
