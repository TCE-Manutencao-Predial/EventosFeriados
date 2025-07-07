# 🧪 Teste de Integração CLP TCE

## Configuração Implementada

✅ **CLP TCE Térreo B1**: `172.17.85.104`  
✅ **API URL**: `https://automacao.tce.go.gov.br/scadaweb/api`  
✅ **Autenticação**: HTTP Basic Auth (usuário: `eventosferiados`, senha: `WzPcMMFU`)  
✅ **Tags de Feriados**: N33 (dias) e N34 (meses), slots 0-19  
✅ **Sincronização**: Automática às 7h00 e 18h00  

## 🔐 Autenticação

O sistema utiliza HTTP Basic Authentication para todas as operações com o CLP:
- **Usuário**: `eventosferiados`
- **Senha**: `WzPcMMFU`

**Nota**: As credenciais estão configuradas diretamente no código (`app/config.py`) para garantir funcionalidade imediata.

## Como Testar

### 1. 🚀 Teste Rápido via Script

```bash
cd EventosFeriados
python teste_clp_tce.py
```

Este script irá:
- ✅ Testar conectividade com o CLP
- ✅ Ler todos os slots de feriados
- ✅ Testar escrita e verificação
- ✅ Restaurar valores originais

### 2. 🌐 Teste via Interface Web

1. Inicie o sistema: `python EventosFeriados.py`
2. Acesse: `http://localhost:5000/EventosFeriados/sincronizacao-clp`
3. Use os botões de teste:
   - **"Testar Conexão"** - Verifica conectividade
   - **"Testar Tag N33:0"** - Teste específico de leitura/escrita
   - **"Ler Dados do CLP"** - Lista todos os feriados atuais
   - **"Sincronizar Agora"** - Sincronização completa

### 3. 🔧 Teste Manual de Tags

Na interface web, use a seção "Teste Manual de Tags":

**Exemplos:**
- **Ler N33:0**: Tag=`N33:0`, Valor=vazio
- **Escrever N33:0**: Tag=`N33:0`, Valor=`25`
- **Ler N34:5**: Tag=`N34:5`, Valor=vazio

## 📊 Formato dos Dados

### Mapeamento de Feriados
```
Slot 0: N33:0 (dia), N34:0 (mês)
Slot 1: N33:1 (dia), N34:1 (mês)
...
Slot 19: N33:19 (dia), N34:19 (mês)
```

### Exemplo Prático
```
Natal → N33:0=25, N34:0=12
Ano Novo → N33:1=1, N34:1=1
Independência → N33:2=7, N34:2=9
```

## 🔍 URLs de Teste Direto

### Leitura
```
https://automacao.tce.go.gov.br/scadaweb/api/tag_read/172.17.85.104/N33%253A0
```

### Escrita
```
https://automacao.tce.go.gov.br/scadaweb/api/tag_write/172.17.85.104/N33%253A0/25
```

## 📈 Monitoramento

### Status da Sincronização
- ✅ **Logs em tempo real** na interface web
- ✅ **Arquivo de status**: `app/dados/clp_status.json`
- ✅ **Backup automático**: `app/dados/clp_backup.json`
- ✅ **Logs detalhados**: `app/logs/eventos_feriados.log`

### Endpoints de API
```
GET /api/clp/sincronizacao/status - Status atual
POST /api/clp/sincronizacao/executar - Sincronização manual
GET /api/clp/conectividade - Teste de conexão
GET /api/clp/dados-clp - Dados atuais do CLP
```

## 🛠️ Resolução de Problemas

### ❌ "CLP não acessível"
1. Verifique conectividade de rede
2. Teste URL diretamente no navegador
3. Verifique se o CLP está online

### ❌ "Erro HTTP 404/500"
1. Confirme se as tags N33/N34 existem no CLP
2. Verifique se o IP 172.17.85.104 está correto
3. Teste com outras tags conhecidas

### ❌ "Sincronização parcial"
1. Verifique logs detalhados na interface
2. Alguns slots podem ter falhado (normal)
3. Execute nova sincronização se necessário

### ❌ "Muitos feriados"
- O CLP suporta apenas 20 feriados
- Os primeiros 20 feriados do ano serão sincronizados
- Considere priorizar feriados por importância

## 🎯 Próximos Passos

1. **✅ Teste inicial completo** com o script
2. **✅ Validação via interface web**
3. **🔄 Configurar sincronização automática**
4. **📊 Monitorar logs e status**
5. **🚀 Expandir para eventos** (quando necessário)

## 📞 Suporte

- **Logs**: Verifique `app/logs/eventos_feriados.log`
- **Status**: Interface web em `/sincronizacao-clp`
- **Debug**: Use endpoints de teste da API
