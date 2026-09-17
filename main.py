import ctypes
import sys


if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Fuper.GerenciadorDeArmazenamento"
        )
    except (AttributeError, OSError):
        pass


from storage_manager.ui import run


if __name__ == "__main__":
    run()
