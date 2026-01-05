"""
Script para salvar a logo "Clicou Economizou" na pasta assets.
Execute este script e cole a URL da imagem ou o caminho do arquivo.
"""

import os
import requests
from pathlib import Path

def save_logo_from_url(url: str):
    """Salva logo de uma URL."""
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    try:
        print(f"Baixando logo de: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # Detecta extensão
        content_type = response.headers.get('Content-Type', '')
        if 'png' in content_type.lower():
            ext = '.png'
        elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
            ext = '.jpg'
        else:
            ext = '.png'  # Default
        
        logo_path = assets_dir / f"logo{ext}"
        
        with open(logo_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Logo salva em: {logo_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao baixar logo: {str(e)}")
        return False

def save_logo_from_file(file_path: str):
    """Copia logo de um arquivo local."""
    import shutil
    
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    try:
        source = Path(file_path)
        if not source.exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
        
        # Detecta extensão
        ext = source.suffix.lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            ext = '.png'
        
        logo_path = assets_dir / f"logo{ext}"
        shutil.copy2(source, logo_path)
        
        print(f"✅ Logo copiada para: {logo_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao copiar logo: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Salvar Logo 'Clicou Economizou'")
    print("=" * 50)
    print()
    print("Opções:")
    print("1. Colar URL da imagem")
    print("2. Colar caminho do arquivo local")
    print()
    
    choice = input("Escolha (1 ou 2): ").strip()
    
    if choice == "1":
        url = input("Cole a URL da logo: ").strip()
        if url:
            save_logo_from_url(url)
        else:
            print("❌ URL vazia")
    elif choice == "2":
        file_path = input("Cole o caminho completo do arquivo: ").strip().strip('"')
        if file_path:
            save_logo_from_file(file_path)
        else:
            print("❌ Caminho vazio")
    else:
        print("❌ Opção inválida")
    
    print()
    print("Pressione Enter para sair...")
    input()

