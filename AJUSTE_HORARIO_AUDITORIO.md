# 🎭 Ajuste Automático de Horários - Auditório

## 🎯 Objetivo
Implementar ajuste automático de horários para **TODOS** os eventos do Auditório, garantindo que a infraestrutura (luzes, refrigeração) seja preparada adequadamente antes dos eventos.

## ⚙️ Funcionamento

### 🕐 Todos os Eventos do Auditório
- **Detecção**: Qualquer evento no Auditório Nobre ou Foyer do Auditório
- **Ajuste**: 
  - ⏰ **Início**: 1 hora ANTES do horário original
  - ⏰ **Fim**: 1 hora DEPOIS do horário original
- **Limites de segurança**:
  -   ⚠️ Limites respeitados: 6h-23h59
  - 🚫 Não termina depois das **23h59** (mantém intervalos válidos para o CLP)

## 📊 Exemplos Práticos

| Horário Original | Horário Programado no CLP | Tipo de Evento |
|------------------|---------------------------|----------------|
| 08:00 - 10:00    | 07:00 - 11:00            | ✅ Matutino    |
| 09:30 - 11:30    | 08:30 - 12:30            | ✅ Matutino    |
| 14:00 - 16:00    | 13:00 - 17:00            | ✅ Vespertino  |
| 19:00 - 21:00    | 18:00 - 22:00            | ✅ Noturno     |
| 05:00 - 07:00    | 06:00 - 08:00            | ✅ Limite 6h   |
| 22:00 - 24:00    | 21:00 - 23:59            | ✅ Limite 23h59|

## 🏗️ Implementação Técnica

### 📁 Arquivos Modificados
- `SincronizadorCLPAuditorio.py`: Lógica de ajuste de horário
- `config.py`: Documentação das tags e funcionalidade

### 🔧 Função Principal
```python
def _ajustar_horario_auditorio(self, evento: Dict) -> Tuple[str, str, bool]:
    """
    Ajusta horário de eventos do Auditório: inicia 1h antes e termina 1h depois
    Para preparar infraestrutura (luzes, refrigeração) do Auditório
    Aplica-se a TODOS os eventos do Auditório (matutinos e vespertinos)
    """
```

### 📝 Tags do CLP Afetadas
- **N93**: Hora de início (com ajuste automático para todos os eventos)
- **N94**: Minuto de início
- **N95**: Hora de fim (com ajuste automático para todos os eventos)  
- **N96**: Minuto de fim

## 📈 Benefícios

### 🏢 Infraestrutura
- ❄️ **Refrigeração**: Ambiente climatizado antes do evento
- 💡 **Iluminação**: Luzes acesas e ajustadas previamente
- 🔊 **Som**: Sistema preparado e testado
- 🚪 **Acesso**: Controle de entrada funcionando
- 🧹 **Limpeza**: Tempo adequado para preparação do ambiente

### 👥 Experiência do Usuário
- ✅ Ambiente confortável desde o início
- ✅ Sem atrasos por problemas técnicos
- ✅ Melhor qualidade dos eventos
- ✅ Profissionalismo na gestão de espaços
- ✅ Economia de energia com programação otimizada
- ✅ Intervalos válidos sempre programados no CLP (6h-23h59)

## 🔍 Monitoramento

### 📊 Logs Detalhados
```
INFO: Evento matutino ajustado - Original: 09:00-11:00 -> Ajustado: 08:00-12:00 (evento: Reunião Conselheiros...)
INFO: Evento vespertino ajustado - Original: 15:00-17:00 -> Ajustado: 14:00-18:00 (evento: Palestra Técnica...)
INFO: Dados preparados para CLP Auditório: 3 eventos (2 passados, 1 futuros, 3 com ajuste de horário)
INFO: Eventos do Auditório ajustados (+1h antes/-1h depois): 3
INFO:   - Reunião Conselheiros: 09:00-11:00 -> 08:00-12:00
INFO:   - Palestra Técnica: 15:00-17:00 -> 14:00-18:00
```

### 🖥️ Interface Web
- Visualização de eventos com horários ajustados
- Indicação clara de quais eventos foram modificados
- Status de sincronização em tempo real

## 🚀 Ativação Automática

### ⏰ Sincronização
- **Horários**: 07:00 e 18:00 (automática)
- **Manual**: Via interface web
- **Escopo**: Auditório Nobre e Foyer do Auditório

### 🎯 Aplicação
- ✅ Automática para **TODOS** os eventos do Auditório
- ✅ Sem configuração adicional necessária
- ✅ Retrocompatível com eventos existentes
- ✅ Matutinos e vespertinos tratados igualmente

## 🔧 Configuração

### 📋 Locais Gerenciados
```python
'LOCAIS_GERENCIADOS': ['Auditório Nobre', 'Foyer do Auditório']
```

### 🏷️ Tags do CLP
```python
'TAGS_EVENTOS_AUDITORIO': {
    'DIA': 'N91',          # N91:0-9 - dias dos eventos  
    'MES': 'N92',          # N92:0-9 - meses dos eventos
    'HORA_INICIO': 'N93',  # N93:0-9 - hora de início (com ajuste automático para todos os eventos)
    'MIN_INICIO': 'N94',   # N94:0-9 - minuto de início
    'HORA_FIM': 'N95',     # N95:0-9 - hora de fim (com ajuste automático para todos os eventos)
    'MIN_FIM': 'N96'       # N96:0-9 - minuto de fim
}
```

---

**Data de Implementação**: 25/08/2025  
**Versão**: 2.0 - Expandido para todos os eventos  
**Status**: ✅ Ativo
