"""Recursos na raiz do código-fonte ou junto aos módulos empacotados."""
from pathlib import Path
import sys


def resource_path(name):
    module_directory = Path(__file__).resolve().parent
    root = module_directory if getattr(sys, 'frozen', False) else module_directory.parent
    return root / name
