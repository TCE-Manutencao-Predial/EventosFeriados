from app.alarmes.ClassesSistema import Tecnico, FuncoesTecnicos, MetodoContato
from typing import List, Tuple

def inicializar_tecnicos() -> List[Tecnico]:
    """Inicializa e retorna a lista de técnicos do sistema"""
    tecnicos = []

    tecnicos.append(Tecnico(
        nome="Flaximan Arruda dos Santos Junior",
        telefone="+556291229363",
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
        telefone="120363159016507640@g.us",
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
        telefone="556293688928-1505225593@g.us",
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
        telefone="120363311856919908@g.us",
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
        telefone="+556299686668",
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
        telefone="+556284136363",
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
        telefone="+556299687686",
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
        telefone="+556292961460",
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
        telefone="+556281173665",
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
        telefone="+556299782182",
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
        telefone="+556291773139",
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
        telefone="+556282710569",
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
        telefone="+556292246845",
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
        telefone="+556296586898",
        email="",
        metodo_contato_preferencial=MetodoContato.WHATSAPP,
        funcoes=[
            FuncoesTecnicos.ELEVADORES
        ],
        jornada=[("13:00", "19:00")],
        ferias=False
    ))

    return tecnicos
