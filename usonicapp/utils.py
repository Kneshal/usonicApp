import pathlib

from PyQt5.QtGui import QIcon, QPixmap

BASE_DIR = pathlib.Path(__file__).resolve().parent


def get_icon(path: str) -> QIcon:
    """Формирует иконку на базе пути к файлу."""
    return QIcon(str(BASE_DIR / 'icons' / path))


def get_pixmap(path: str) -> QPixmap:
    """Формирует изображение на базе пути к файлу."""
    return QPixmap(str(BASE_DIR / 'icons' / path))


def get_form_path(path: str) -> str:
    """Формирует абсолютный путь до файла формы."""
    return str(BASE_DIR / 'forms' / path)
