import os
import sys
import importlib.util

def check_imports():
    sys.path.insert(0, 'd:\\aiworksspace\\vido')
    missing = set()
    for root, dirs, files in os.walk('d:\\aiworksspace\\vido\\backend'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                path = os.path.join(root, file)
                module_name = 'backend.' + os.path.relpath(path, 'd:\\aiworksspace\\vido\\backend').replace(os.sep, '.')[:-3]
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    missing.add(f'{module_name} -> {e}')
                except Exception as e:
                    pass
    for m in missing:
        print(m)

check_imports()
