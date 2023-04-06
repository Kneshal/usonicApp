import sys

import qdarktheme
from PyQt5.QtWidgets import QApplication

from windows.main import MainWindow

if __name__ == '__main__':
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app: QApplication = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainwindow: MainWindow = MainWindow()
    mainwindow.show()
    app.exec()
