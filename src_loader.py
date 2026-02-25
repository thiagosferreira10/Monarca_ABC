"""
src_loader.py — Registra import hook para carregar src.* de __pycache__/
Deve ser importado no início de HOME.py, antes de qualquer import de src.*
"""
import sys
import os
import importlib.util
import importlib.abc
import importlib.machinery

class BytecodeOnlyLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """
    Import hook que localiza módulos compilados (.pyc) em __pycache__/
    quando não existe o arquivo .py fonte correspondente.
    """
    
    def __init__(self, package_name: str, package_dir: str):
        self.package_name = package_name
        self.package_dir = package_dir
        py_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        self.cache_dir = os.path.join(package_dir, "__pycache__")
        self.py_tag = py_tag

    def find_spec(self, fullname, path, target=None):
        # Trata o pacote raiz (ex: 'src')
        if fullname == self.package_name:
            init_pyc = os.path.join(self.cache_dir, f"__init__.{self.py_tag}.pyc")
            if os.path.exists(init_pyc):
                spec = importlib.machinery.ModuleSpec(
                    fullname,
                    self,
                    origin=init_pyc,
                    is_package=True,
                )
                spec.submodule_search_locations = [self.package_dir]
                return spec

        # Trata submódulos (ex: 'src.ui_utils')
        if fullname.startswith(self.package_name + "."):
            module_name = fullname[len(self.package_name) + 1:]
            pyc_path = os.path.join(self.cache_dir, f"{module_name}.{self.py_tag}.pyc")
            if os.path.exists(pyc_path):
                spec = importlib.machinery.ModuleSpec(fullname, self, origin=pyc_path)
                return spec

        return None

    def create_module(self, spec):
        return None  # usa o mecanismo padrão

    def exec_module(self, module):
        with open(module.__spec__.origin, "rb") as f:
            data = f.read()
        # Pular header do .pyc (16 bytes em Python 3.8+)
        code = importlib.util.MAGIC_NUMBER
        import marshal
        bytecode = data[16:]
        code = marshal.loads(bytecode)
        exec(code, module.__dict__)


def register(package_name: str = "src"):
    """Registra o hook para o pacote especificado."""
    base_dir = os.getcwd()
    package_dir = os.path.join(base_dir, package_name)
    
    # Só registra se a pasta src/ existe mas não tem .py (producao)
    has_py = any(
        f.endswith(".py") and f != "__init__.py"
        for f in os.listdir(package_dir)
        if os.path.isfile(os.path.join(package_dir, f))
    )
    has_pyc = os.path.exists(os.path.join(package_dir, "__pycache__"))
    
    if not has_py and has_pyc:
        loader = BytecodeOnlyLoader(package_name, package_dir)
        # Insere no início para ter prioridade
        sys.meta_path.insert(0, loader)
