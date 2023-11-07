import os
import sys
from importlib import import_module


def load_class(class_path):
    """
    Tricky method that imports a class form a string.

    Args:
        class_path (str): the path where the class to be imported is.

    Returns:
        class: the class imported and ready to be instantiated.
    """
    sys.path.append(os.getcwd())
    module_path, class_name = class_path.rsplit(".", 1)
    mod = import_module(module_path)
    return getattr(mod, class_name)
