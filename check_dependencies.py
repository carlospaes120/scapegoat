"""
Script para verificar se todas as dependências estão instaladas.
"""

import sys

def check_dependency(module_name, package_name=None):
    """Verifica se um módulo está disponível."""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name} - OK")
        return True
    except ImportError:
        print(f"❌ {package_name} - FALTANDO")
        return False

def main():
    """Verifica todas as dependências."""
    print("Verificando dependências do Mimetics Metrics...")
    print("=" * 50)
    
    dependencies = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("networkx", "networkx"),
        ("matplotlib", "matplotlib"),
        ("scipy", "scipy"),
        ("sklearn", "scikit-learn"),
        ("tqdm", "tqdm"),
        ("seaborn", "seaborn"),
    ]
    
    missing = []
    
    for module, package in dependencies:
        if not check_dependency(module, package):
            missing.append(package)
    
    print("=" * 50)
    
    if missing:
        print(f"❌ Dependências faltando: {', '.join(missing)}")
        print("\nPara instalar todas as dependências:")
        print("pip install " + " ".join(missing))
    else:
        print("✅ Todas as dependências estão instaladas!")
    
    return len(missing) == 0

if __name__ == "__main__":
    main()
