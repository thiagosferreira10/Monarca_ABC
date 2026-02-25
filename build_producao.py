"""
Build de Produção — Monarca Curva ABC
============================================================
Monta uma pasta de produção protegendo o código-fonte:

- HOME.py e pages/*.py são mantidos como .py (Streamlit exige)
- src/*.py são compilados para .pyc (regras de negócio protegidas)
- Assets (exe, imagens, config) são copiados

Uso:
    python build_producao.py

Resultado:
    Pasta 'producao/' pronta para deploy no cliente.
"""

import os
import sys
import py_compile
import shutil
from pathlib import Path

# === CONFIGURAÇÃO ===
PROJECT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_DIR / "producao"

# Versão do Python para nomear o .pyc corretamente
PY_TAG = f"cpython-{sys.version_info.major}{sys.version_info.minor}"

# Arquivos .py que o Streamlit precisa (copiados como estão)
STREAMLIT_FILES = [
    "HOME.py",
    "src_loader.py",  # import hook para carregar src.* de __pycache__/
]

# Pastas com .py que o Streamlit precisa (pages/ — descoberta de páginas)
STREAMLIT_DIRS = [
    "pages",
]

# Pastas com .py de negócio a compilar para .pyc (protegidas)
BUSINESS_DIRS = [
    "src",
]

# Assets a copiar sem modificação
# Formato: string simples ou tuple (origem, destino)
ASSETS = [
    ("dist/Ferramentas.exe", "Ferramentas.exe"),
    ("Instalacao/config.ini", "config.ini"),
    "instalar.bat",
    "diagnostico.bat",
    "diagnostico_test.py",
    "Logo.jpg",
    "Icone.ico",
    ".env",
    ".streamlit",
    "requirements.txt",
]


def clean_output():
    """Remove pasta de produção anterior."""
    if OUTPUT_DIR.exists():
        print(f"  Removendo pasta anterior: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)


def copy_streamlit_files():
    """Copia arquivos que o Streamlit precisa como .py (sem compilar)."""
    print("\n📄 Copiando arquivos Streamlit (.py necessários)")
    count = 0

    # Arquivos individuais
    for filename in STREAMLIT_FILES:
        src = PROJECT_DIR / filename
        dest = OUTPUT_DIR / filename
        if src.exists():
            shutil.copy2(str(src), str(dest))
            print(f"  📄 {filename}")
            count += 1
        else:
            print(f"  ⚠️  Não encontrado: {filename}")

    # Pastas (pages/)
    for dirname in STREAMLIT_DIRS:
        src_dir = PROJECT_DIR / dirname
        if not src_dir.exists():
            print(f"  ⚠️  Pasta não encontrada: {dirname}/")
            continue

        dest_dir = OUTPUT_DIR / dirname
        dest_dir.mkdir(parents=True, exist_ok=True)

        for py_file in sorted(src_dir.glob("*.py")):
            dest = dest_dir / py_file.name
            shutil.copy2(str(py_file), str(dest))
            print(f"  📄 {dirname}/{py_file.name}")
            count += 1

    return count


def compile_business_logic():
    """Compila src/*.py para __pycache__/*.cpython-XXX.pyc (sem fonte)."""
    print(f"\n🔒 Compilando lógica de negócio → .pyc (Python {PY_TAG})")
    total, ok, fail = 0, 0, 0

    for dirname in BUSINESS_DIRS:
        src_dir = PROJECT_DIR / dirname
        if not src_dir.exists():
            print(f"  ⚠️  Pasta não encontrada: {dirname}/")
            continue

        # Criar a estrutura __pycache__ no destino
        dest_cache = OUTPUT_DIR / dirname / "__pycache__"
        dest_cache.mkdir(parents=True, exist_ok=True)

        for py_file in sorted(src_dir.glob("*.py")):
            total += 1
            pyc_name = f"{py_file.stem}.{PY_TAG}.pyc"
            dest_path = dest_cache / pyc_name

            try:
                # TIMESTAMP mode (default) — mais confiável para imports sem fonte
                py_compile.compile(
                    str(py_file),
                    cfile=str(dest_path),
                    doraise=True,
                )
                print(f"  🔒 {dirname}/{py_file.name} → {dirname}/__pycache__/{pyc_name}")
                ok += 1
            except py_compile.PyCompileError as e:
                print(f"  ❌ Erro: {py_file.name}: {e}")
                fail += 1

        # Criar __init__.py vazio e compilá-lo para que Python reconheça src/ como pacote
        init_src = OUTPUT_DIR / dirname / "__init__.py"
        init_src.write_text("# package marker\n", encoding="utf-8")
        init_pyc = dest_cache / f"__init__.{PY_TAG}.pyc"
        py_compile.compile(str(init_src), cfile=str(init_pyc), doraise=True)
        print(f"  📄 {dirname}/__init__.py + __pycache__/__init__.{PY_TAG}.pyc")

    return total, ok, fail


def copy_assets():
    """Copia assets (exe, imagens, config) para produção."""
    print("\n📁 Copiando assets")
    for item in ASSETS:
        if isinstance(item, tuple):
            src_rel, dest_rel = item
        else:
            src_rel = item
            dest_rel = item

        src = PROJECT_DIR / src_rel
        dest = OUTPUT_DIR / dest_rel

        if not src.exists():
            print(f"  ⚠️  Não encontrado: {src_rel}")
            continue

        if src.is_dir():
            shutil.copytree(str(src), str(dest))
            print(f"  📂 {dest_rel}/")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
            size_kb = src.stat().st_size / 1024
            print(f"  📄 {dest_rel} ({size_kb:.0f} KB)")


def verify_security():
    """Verifica que src/ não contém .py (apenas __pycache__)."""
    print("\n🔍 Verificação de segurança")
    issues = []

    # Verificar que src/ NÃO tem .py
    src_output = OUTPUT_DIR / "src"
    if src_output.exists():
        py_in_src = [f for f in src_output.glob("*.py") if f.name != "__init__.py"]
        if py_in_src:
            issues.append(f"  ❌ Arquivos .py encontrados em src/:")
            for f in py_in_src:
                issues.append(f"     - {f.name}")

    if issues:
        for line in issues:
            print(line)
        return False
    else:
        print("  ✅ Lógica de negócio (src/) protegida — apenas .pyc!")
        # Listar o que é exposto
        exposed = []
        for f in OUTPUT_DIR.rglob("*.py"):
            exposed.append(f.relative_to(OUTPUT_DIR))
        if exposed:
            print(f"  ℹ️  Arquivos .py mantidos (exigidos pelo Streamlit):")
            for f in exposed:
                print(f"     - {f}")
        return True


def show_summary():
    """Exibe resumo da pasta de produção."""
    print("\n" + "=" * 60)
    print("📋 RESUMO DA PASTA DE PRODUÇÃO")
    print("=" * 60)

    total_size = 0
    file_count = 0
    for f in OUTPUT_DIR.rglob("*"):
        if f.is_file():
            file_count += 1
            total_size += f.stat().st_size

    print(f"   Pasta: {OUTPUT_DIR}")
    print(f"   Arquivos: {file_count}")
    print(f"   Tamanho total: {total_size / (1024*1024):.1f} MB")

    print("\n   Estrutura:")
    for f in sorted(OUTPUT_DIR.rglob("*")):
        if f.is_file():
            rel = f.relative_to(OUTPUT_DIR)
            size = f.stat().st_size / 1024
            if f.suffix == ".pyc":
                icon = "🔒"
            elif f.suffix == ".py":
                icon = "📝"
            else:
                icon = "📄"
            print(f"   {icon} {rel} ({size:.0f} KB)")

    print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("🏗️  BUILD DE PRODUÇÃO — Monarca Curva ABC")
    print("=" * 60)

    # 1. Limpar
    print("\n🧹 Preparando pasta de saída")
    clean_output()

    # 2. Copiar arquivos Streamlit (.py)
    st_count = copy_streamlit_files()

    # 3. Compilar lógica de negócio
    total, ok, fail = compile_business_logic()
    print(f"\n   Resultado: {ok}/{total} compilados, {fail} falhas")

    if fail > 0:
        print("\n❌ Build falhou! Corrija os erros acima.")
        sys.exit(1)

    # 4. Copiar assets
    copy_assets()

    # 5. Verificar segurança
    verify_security()

    # 6. Resumo
    show_summary()

    print("\n✅ BUILD CONCLUÍDO COM SUCESSO!")
    print("   A pasta 'producao/' está pronta para deploy.")
    print("   Copie todo o conteúdo para o computador do cliente.")
    print(f"\n   📝 Arquivos Streamlit expostos: {st_count} (necessários para funcionar)")
    print(f"   🔒 Módulos protegidos: {ok} (lógica de negócio compilada)")


if __name__ == "__main__":
    main()
