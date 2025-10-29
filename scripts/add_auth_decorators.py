#!/usr/bin/env python3
"""
Script para adicionar decorador @require_auth_api em todas as rotas de API
"""

import re
import os

# Arquivos de API para modificar
api_files = [
    'app/routes/api_feriados.py',
    'app/routes/api_eventos.py',
    'app/routes/api_clp.py',
    'app/routes/api_clp_auditorio.py',
    'app/routes/api_tce.py'
]

def add_import_if_needed(content):
    """Adiciona import do decorador se não existir"""
    if 'from ..utils.auth_decorators import require_auth_api' in content:
        return content
    
    # Encontrar a posição após os imports
    import_pattern = r'(import logging\n)'
    if re.search(import_pattern, content):
        content = re.sub(
            import_pattern,
            r'\1from ..utils.auth_decorators import require_auth_api\n',
            content,
            count=1
        )
    
    return content

def add_decorator_to_routes(content):
    """Adiciona @require_auth_api antes de cada @route"""
    # Padrão para encontrar rotas sem o decorador
    pattern = r'(@\w+_bp\.route\([^\)]+\)(?:, methods=\[[^\]]+\])?)\n(def \w+)'
    
    def replace_func(match):
        route_decorator = match.group(1)
        func_def = match.group(2)
        
        # Verificar se já tem o decorador acima
        lines_before = content[:match.start()].split('\n')
        if lines_before and '@require_auth_api' in lines_before[-1]:
            return match.group(0)
        
        return f"{route_decorator}\n@require_auth_api\n{func_def}"
    
    return re.sub(pattern, replace_func, content)

def process_file(filepath):
    """Processa um arquivo adicionando o decorador"""
    print(f"Processando {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"  ❌ Arquivo não encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adicionar import
        content = add_import_if_needed(content)
        
        # Adicionar decorador nas rotas
        original_content = content
        content = add_decorator_to_routes(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Arquivo modificado com sucesso")
            return True
        else:
            print(f"  ℹ️  Nenhuma modificação necessária")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao processar arquivo: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  Adicionando autenticação em rotas de API")
    print("="*60 + "\n")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    modified_count = 0
    for api_file in api_files:
        filepath = os.path.join(base_dir, api_file)
        if process_file(filepath):
            modified_count += 1
    
    print("\n" + "="*60)
    print(f"  Concluído: {modified_count} arquivo(s) modificado(s)")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
