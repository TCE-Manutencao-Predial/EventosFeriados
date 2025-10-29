# Guia de Testes - APIs HelpDesk Monitor

Scripts e procedimentos para testar as APIs do sistema.

## 🧪 Testes Rápidos

### PowerShell (Windows)

```powershell
# Teste 1: Listar usuários htpasswd
$usuarios = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/usuarios_htpasswd"
$usuarios | Format-Table usuario_htpasswd, nome, disponivel

# Teste 2: Buscar técnicos de limpeza
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/limpeza"
Write-Host "Total encontrados: $($response.total)"
$response.tecnicos | Format-Table nome, usuario_htpasswd, disponivel

# Teste 3: Listar todos os técnicos
$tecnicos = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/contatos_tecnicos"
Write-Host "Total de técnicos: $($tecnicos.Count)"

# Teste 4: Buscar usuário htpasswd específico
$usuario = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/usuarios_htpasswd/joao.silva"
$usuario | Format-List

# Teste 5: Filtrar técnicos disponíveis de uma função
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/eletrica"
$disponiveis = $response.tecnicos | Where-Object { $_.disponivel -eq $true -and $_.ferias -eq $false }
Write-Host "Técnicos disponíveis: $($disponiveis.Count)"
$disponiveis | Format-Table nome, usuario_htpasswd, telefone_principal
```

### Bash/curl (Linux/Mac)

```bash
# Teste 1: Listar usuários htpasswd
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/usuarios_htpasswd" | jq '.'

# Teste 2: Buscar técnicos de limpeza
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/limpeza" | \
  jq '{total: .total, tecnicos: [.tecnicos[] | {nome, htpasswd: .usuario_htpasswd, disponivel}]}'

# Teste 3: Apenas técnicos com htpasswd
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/hidraulica" | \
  jq '.tecnicos[] | select(.usuario_htpasswd != null) | {nome, htpasswd: .usuario_htpasswd, disponivel}'

# Teste 4: Contar técnicos por função
for funcao in limpeza eletrica ar_condicionado hidraulica; do
  total=$(curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/$funcao" | jq '.total')
  echo "$funcao: $total técnicos"
done

# Teste 5: Verificar case-insensitive
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/LIMPEZA" | jq '.funcao_normalizada'
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/limpeza" | jq '.funcao_normalizada'
```

---

## 🔬 Teste de Integração Completo

### PowerShell - Script Completo

```powershell
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TESTE COMPLETO - API HELPDESKMONITOR" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Descobrir funções disponíveis
Write-Host "1. Descobrindo funções cadastradas..." -ForegroundColor Yellow
$tecnicos = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/contatos_tecnicos"
$funcoes = $tecnicos | ForEach-Object { $_.funcoes } | Where-Object { $_ } | Select-Object -Unique | Sort-Object
Write-Host "   Encontradas $($funcoes.Count) funções únicas`n" -ForegroundColor Green

# 2. Testar cada função
Write-Host "2. Testando cada função..." -ForegroundColor Yellow
foreach ($funcao in $funcoes) {
    try {
        $response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/$funcao"
        $comHtpasswd = ($response.tecnicos | Where-Object { $_.usuario_htpasswd -ne $null }).Count
        $disponiveis = ($response.tecnicos | Where-Object { $_.disponivel -eq $true }).Count
        
        Write-Host "   ✓ $($funcao.PadRight(20)) - $($response.total) técnicos | $comHtpasswd com htpasswd | $disponiveis disponíveis" -ForegroundColor White
    } catch {
        Write-Host "   ✗ $($funcao.PadRight(20)) - ERRO" -ForegroundColor Red
    }
}

# 3. Teste de case-insensitive
Write-Host "`n3. Testando case-insensitive..." -ForegroundColor Yellow
if ($funcoes.Count -gt 0) {
    $funcaoTeste = $funcoes[0]
    $r1 = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/$($funcaoTeste.ToLower())"
    $r2 = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/$($funcaoTeste.ToUpper())"
    
    if ($r1.total -eq $r2.total) {
        Write-Host "   ✓ Case-insensitive funcionando corretamente" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Problema com case-insensitive" -ForegroundColor Red
    }
}

# 4. Teste de função inexistente
Write-Host "`n4. Testando função inexistente..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/funcao_inexistente_teste"
if ($response.total -eq 0 -and $response.mensagem) {
    Write-Host "   ✓ Resposta vazia funcionando corretamente" -ForegroundColor Green
} else {
    Write-Host "   ✗ Problema com resposta vazia" -ForegroundColor Red
}

# 5. Teste de usuários htpasswd
Write-Host "`n5. Testando API de usuários htpasswd..." -ForegroundColor Yellow
$usuarios = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/usuarios_htpasswd"
Write-Host "   ✓ Encontrados $($usuarios.Count) usuários htpasswd" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TESTE CONCLUÍDO!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
```

---

## 🐍 Teste com Python

```python
import requests
import json

BASE_URL = "https://automacao.tce.go.gov.br/helpdeskmonitor"

def test_usuarios_htpasswd():
    """Testa listagem de usuários htpasswd"""
    response = requests.get(f"{BASE_URL}/api/usuarios_htpasswd")
    assert response.status_code == 200
    usuarios = response.json()
    print(f"✓ {len(usuarios)} usuários htpasswd encontrados")
    return usuarios

def test_tecnicos_por_funcao(funcao):
    """Testa busca de técnicos por função"""
    response = requests.get(f"{BASE_URL}/api/tecnicos/por_funcao/{funcao}")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Função '{funcao}': {data['total']} técnicos encontrados")
    return data

def test_tecnicos_completo():
    """Testa listagem completa de técnicos"""
    response = requests.get(f"{BASE_URL}/api/contatos_tecnicos")
    assert response.status_code == 200
    tecnicos = response.json()
    print(f"✓ {len(tecnicos)} técnicos cadastrados no sistema")
    return tecnicos

def test_case_insensitive():
    """Testa se a busca é case-insensitive"""
    r1 = requests.get(f"{BASE_URL}/api/tecnicos/por_funcao/limpeza")
    r2 = requests.get(f"{BASE_URL}/api/tecnicos/por_funcao/LIMPEZA")
    r3 = requests.get(f"{BASE_URL}/api/tecnicos/por_funcao/Limpeza")
    
    assert r1.json()['total'] == r2.json()['total'] == r3.json()['total']
    print("✓ Case-insensitive funcionando corretamente")

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*50)
    print("  TESTES DA API - HELPDESKMONITOR")
    print("="*50 + "\n")
    
    # Teste 1: Usuários htpasswd
    print("1. Testando usuários htpasswd...")
    usuarios = test_usuarios_htpasswd()
    
    # Teste 2: Técnicos por função
    print("\n2. Testando técnicos por função...")
    funcoes = ["limpeza", "eletrica", "ar_condicionado", "hidraulica"]
    for funcao in funcoes:
        test_tecnicos_por_funcao(funcao)
    
    # Teste 3: Lista completa
    print("\n3. Testando listagem completa...")
    tecnicos = test_tecnicos_completo()
    
    # Teste 4: Case-insensitive
    print("\n4. Testando case-insensitive...")
    test_case_insensitive()
    
    # Teste 5: Descobrir funções
    print("\n5. Descobrindo funções disponíveis...")
    funcoes_unicas = set()
    for tecnico in tecnicos:
        if tecnico.get('funcoes'):
            funcoes_unicas.update(tecnico['funcoes'])
    print(f"✓ Funções disponíveis: {', '.join(sorted(funcoes_unicas))}")
    
    print("\n" + "="*50)
    print("  TODOS OS TESTES CONCLUÍDOS!")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_all_tests()
```

---

## 📝 Casos de Teste

### 1. Consultar Técnicos por Função

**Entrada:** `GET /api/tecnicos/por_funcao/limpeza`

**Resultado Esperado:**
- Status: 200
- Resposta contém array `tecnicos`
- Cada técnico tem: id, nome, cargo, usuario_htpasswd, disponivel, ferias, telefone_principal, email
- Campo `funcao_normalizada` = "LIMPEZA"
- Campo `total` = quantidade de técnicos

### 2. Função Inexistente

**Entrada:** `GET /api/tecnicos/por_funcao/funcao_nao_existe`

**Resultado Esperado:**
- Status: 200
- Array `tecnicos` vazio
- Campo `total` = 0
- Campo `mensagem` presente

### 3. Case-Insensitive

**Entrada:** 
- `GET /api/tecnicos/por_funcao/limpeza`
- `GET /api/tecnicos/por_funcao/LIMPEZA`
- `GET /api/tecnicos/por_funcao/Limpeza`

**Resultado Esperado:**
- Todos retornam o mesmo resultado
- Mesmo valor de `total`
- Mesmo array de `tecnicos`

### 4. Usuário htpasswd Específico

**Entrada:** `GET /api/usuarios_htpasswd/joao.silva`

**Resultado Esperado:**
- Status: 200 se existe, 404 se não existe
- Se existe: retorna objeto com dados completos do usuário

### 5. Técnicos com htpasswd Null

**Entrada:** `GET /api/tecnicos/por_funcao/limpeza`

**Resultado Esperado:**
- Técnicos sem htpasswd configurado têm `usuario_htpasswd: null`
- Técnicos ainda são incluídos na resposta

---

## 🔍 Descobrir Informações do Sistema

### Listar todas as funções cadastradas

```powershell
# PowerShell
$tecnicos = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/contatos_tecnicos"
$funcoes = $tecnicos | ForEach-Object { $_.funcoes } | Where-Object { $_ } | Select-Object -Unique | Sort-Object
Write-Host "Funções disponíveis:"
$funcoes | ForEach-Object { Write-Host "  • $_" }
```

```bash
# Bash
curl -s "https://automacao.tce.go.gov.br/helpdeskmonitor/api/contatos_tecnicos" | \
  jq -r '.[].funcoes[]' | sort -u
```

### Contar técnicos por função

```powershell
# PowerShell
$funcoes = @("limpeza", "eletrica", "ar_condicionado", "hidraulica")
foreach ($funcao in $funcoes) {
    $r = Invoke-RestMethod -Uri "https://automacao.tce.go.gov.br/helpdeskmonitor/api/tecnicos/por_funcao/$funcao"
    Write-Host "$($funcao): $($r.total) técnicos"
}
```

---

## ✅ Checklist de Validação

- [ ] API de usuários htpasswd retorna lista
- [ ] API de técnicos por função funciona
- [ ] Case-insensitive está funcionando
- [ ] Função inexistente retorna array vazio
- [ ] Técnicos sem htpasswd aparecem com null
- [ ] Disponibilidade é calculada corretamente
- [ ] Normalização de funções está ativa
- [ ] Lista completa de técnicos funciona
- [ ] Busca por nome específico funciona
- [ ] Todas as funções cadastradas são acessíveis

---

## 🐛 Troubleshooting

### Erro 404 - Not Found
- Verifique se a URL está correta
- Confirme que o servidor está rodando
- Verifique o path do endpoint

### Erro 500 - Internal Server Error
- Verifique os logs do servidor
- Confirme que o banco de dados está acessível
- Verifique permissões de arquivo

### Resposta Vazia Inesperada
- Verifique se há técnicos cadastrados com a função
- Confirme a normalização do nome da função
- Teste com outras funções conhecidas

### Timeout
- Verifique a conexão de rede
- Confirme que o servidor está respondendo
- Teste com outro endpoint mais simples
