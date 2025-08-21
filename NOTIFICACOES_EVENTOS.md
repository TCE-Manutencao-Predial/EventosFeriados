# Sistema de Notificações de Eventos

Este documento explica como funciona o sistema de notificações automáticas para eventos no TCE-GO.

## 📋 Visão Geral

O sistema foi desenvolvido para notificar automaticamente os técnicos responsáveis pelos eventos em duas situações:

1. **Notificação Imediata**: Quando um evento é criado no sistema
2. **Lembrete Programado**: Um dia antes do evento, às 8h00

## 🎯 Funcionalidades

### ✅ Notificação de Evento Criado
- Enviada automaticamente quando um novo evento é adicionado ao sistema
- Notifica apenas técnicos com a função `EVENTOS`
- Inclui todos os detalhes do evento: nome, data, horário, local, responsável, etc.

### ⏰ Lembrete de Evento
- Enviado automaticamente às 8h00 do dia anterior ao evento
- Lembra os técnicos sobre eventos que acontecerão no dia seguinte
- Inclui informações do evento e alerta para verificação de equipamentos

### 👥 Filtragem de Técnicos
- Apenas técnicos com a função `EVENTOS` recebem as notificações
- Sistema verifica disponibilidade (horário de trabalho, férias)
- Usa o método de contato preferencial de cada técnico (WhatsApp ou Email)

## 🔧 Técnicos Notificados

Atualmente, os seguintes técnicos têm a função `EVENTOS` e receberão as notificações:

1. **Kamila Leandro Costa**
   - 📞 +556284136363
   - ✉️ kleandro@tce.go.gov.br
   - 🕒 07:00 - 13:00
   - 📲 WhatsApp

2. **Gilney da Costa Vaz**
   - 📞 +556299687686
   - ✉️ gcosta@tce.go.gov.br
   - 🕒 07:00 - 13:00
   - 📲 Email

3. **Andreia da Silva Pinto**
   - 📞 +556281173665
   - 🕒 07:00 - 12:00, 13:00 - 16:00
   - 📲 WhatsApp

4. **Juliana Borges de Souza**
   - 📞 +556296586898
   - 🕒 13:00 - 19:00
   - 📲 WhatsApp

## 🚀 Como Usar

### Instalação das Dependências

```bash
pip install -r requirements.txt
```

### Inicialização do Sistema

O sistema é inicializado automaticamente quando a aplicação é executada:

```bash
python EventosFeriados.py
```

### Teste do Sistema

Para testar o sistema de notificações, execute:

```bash
python teste_notificacao_eventos.py
```

Este script permite:
- Listar técnicos com função EVENTOS
- Testar notificação de evento criado
- Testar lembretes de eventos
- Verificar lembretes para amanhã

## 📁 Estrutura dos Arquivos

```
app/
├── alarmes/
│   ├── __init__.py
│   ├── ClassesSistema.py          # Classes e enums do sistema
│   ├── agenda_contatos.py         # Lista de técnicos
│   └── NotificacaoEventos.py      # Sistema de notificação
├── utils/
│   ├── GerenciadorEventos.py      # Gerenciador de eventos (modificado)
│   └── GerenciadorNotificacaoEventos.py  # Coordenador de notificações
└── ...
```

## 🔧 Configuração

### Horários de Notificação

As notificações respeitam os seguintes horários:

- **Dias úteis**: 07:00 - 19:00
- **Fins de semana**: 08:00 - 18:00
- **Feriados**: Tratados como fins de semana

### API WhatsApp

O sistema usa a API TextMeBot para envio de WhatsApp:
- URL: `http://api.textmebot.com/send.php`
- Chave: `pF7RP5Zcgdnw`
- Intervalo entre mensagens: 7 segundos

### Email SMTP

Para envio de emails:
- Servidor: `172.17.120.1`
- Porta: `25`
- Remetente: `automacao@tce.go.gov.br`

## 📨 Formato das Mensagens

### Evento Criado
```
🗓️ *NOVO EVENTO CADASTRADO*

📋 *Evento:* [Nome do Evento]
📅 *Data:* [DD/MM/AAAA]
🕒 *Horário:* [HH:MM às HH:MM]
📍 *Local:* [Local do Evento]
👤 *Responsável:* [Nome do Responsável]
👥 *Participantes:* [Número Estimado]

ℹ️ Um lembrete será enviado 1 dia antes do evento às 08:00h.
```

### Lembrete de Evento
```
⏰ *LEMBRETE DE EVENTO - AMANHÃ*

📋 *Evento:* [Nome do Evento]
📅 *Data:* [DD/MM/AAAA] (AMANHÃ)
🕒 *Horário:* [HH:MM às HH:MM]
📍 *Local:* [Local do Evento]
👤 *Responsável:* [Nome do Responsável]
👥 *Participantes:* [Número Estimado]

⚠️ Verifique se todos os equipamentos e instalações estão funcionando adequadamente.
```

## 🛠️ Manutenção

### Adicionar Novo Técnico

Para adicionar um novo técnico com função EVENTOS, edite o arquivo `app/alarmes/agenda_contatos.py`:

```python
tecnicos.append(Tecnico(
    nome="Nome do Técnico",
    telefone="+5562999999999",
    email="email@tce.go.gov.br",
    metodo_contato_preferencial=MetodoContato.WHATSAPP,
    funcoes=[
        FuncoesTecnicos.EVENTOS,
        # Outras funções se necessário
    ],
    jornada=[("08:00", "17:00")],
    ferias=False
))
```

### Alterar Função de Técnico Existente

Localize o técnico na lista e adicione `FuncoesTecnicos.EVENTOS` à lista de funções:

```python
funcoes=[
    FuncoesTecnicos.SUPERVISAO,
    FuncoesTecnicos.EVENTOS,  # Adicione esta linha
    # Outras funções existentes
],
```

### Logs do Sistema

Os logs são gravados usando o logger padrão do sistema:
- Logger: `'EventosFeriados'`
- Localização dos logs: Verificar configuração em `app/config.py`

## ⚠️ Considerações Importantes

1. **Horário de Lembrete**: Os lembretes são enviados às 8h00. Se o sistema estiver desligado neste horário, os lembretes não serão enviados.

2. **Disponibilidade de Técnicos**: O sistema verifica se o técnico está em seu horário de trabalho antes de enviar a notificação.

3. **Método de Contato**: Cada técnico tem um método preferencial (WhatsApp ou Email). O sistema respeita essa preferência.

4. **Feriados**: O sistema considera feriados através do `GerenciadorFeriados` e os trata como fins de semana.

5. **Rate Limiting**: Há um intervalo de 7 segundos entre envios de WhatsApp para evitar bloqueios da API.

## 🐛 Troubleshooting

### Notificações não são enviadas
1. Verifique se o sistema de notificações foi inicializado
2. Confirme se há técnicos com função `EVENTOS`
3. Verifique se está dentro do horário de notificação
4. Consulte os logs para mensagens de erro

### Erro na API WhatsApp
1. Verifique a conectividade com `api.textmebot.com`
2. Confirme se a chave da API está correta
3. Verifique se não há muitas requisições simultâneas

### Erro no envio de Email
1. Verifique conectividade com o servidor SMTP `172.17.120.1`
2. Confirme se a porta 25 está acessível
3. Verifique se o endereço de email do técnico está correto

## 📞 Suporte

Para dúvidas ou problemas com o sistema de notificações, entre em contato com a equipe de desenvolvimento ou consulte os logs do sistema para informações detalhadas sobre erros.
