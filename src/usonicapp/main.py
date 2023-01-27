import sys
from datetime import datetime

import constants as cts
import qdarktheme
from config import settings
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from PyQt6 import QtGui, uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextBrowser, QWidget


def terminal_msg(terminal: QTextBrowser, message) -> None:
    """Добавляем текущее время и текст в терминал."""
    current_time = datetime.now().time().strftime('%H-%M-%S')
    terminal.append(f'{current_time}: {message}')


class TableWindow(QWidget):
    """Таблица базы данных программы."""
    def __init__(self, terminal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/table.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_table.png'))
        self.setWindowTitle('База данных')
        self.terminal: QTextBrowser = terminal
        self.open_button.setIcon(QtGui.QIcon('icons/load.png'))
        self.update_button.setIcon(QtGui.QIcon('icons/update.png'))
        self.filter_button.setIcon(QtGui.QIcon('icons/filter.png'))
        self.search_button.setIcon(QtGui.QIcon('icons/search.png'))

        self.init_style()
        self.init_signals()

    def init_style(self) -> None:
        """Подключаем пользовательские стили."""
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.open_button.clicked.connect(self.open_button_clicked)
        self.update_button.clicked.connect(self.update_button_clicked)
        self.filter_button.clicked.connect(self.filter_button_clicked)
        self.search_button.clicked.connect(self.search_button_clicked)

    def load_postgres_data(self) -> None:
        """Загружаем данные из БД."""
        pass

    @pyqtSlot()
    def open_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        print('Open button is clicked!')

    @pyqtSlot()
    def update_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        print('Update button is clicked!')

    @pyqtSlot()
    def filter_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        print('Filter button is clicked!')

    @pyqtSlot()
    def search_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        print('Search button is clicked!')


class SettingsWindow(QWidget):
    """Окно настроек программы."""
    def __init__(self, terminal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/settings.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_settings.png'))
        self.setWindowTitle('Настройки')
        self.terminal: QTextBrowser = terminal
        self.lineedit_operator.setText(settings.OPERATOR)
        self.lineedit_dbname.setText(settings.DB_NAME)
        self.lineedit_dbuser.setText(settings.DB_USER)
        self.lineedit_dbpassword.setText(settings.DB_PASSWORD)
        self.lineedit_dbhost.setText(settings.DB_HOST)
        self.spinbox_port.setValue(settings.DB_PORT)
        self.checkbox_bugreport.setChecked(settings.BUG_REPORT)
        self.button_save.clicked.connect(self.save_button_clicked)

    @pyqtSlot()
    def save_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных. Сохраняем данные
        в объект dynaconf и файл."""
        settings.OPERATOR = self.lineedit_operator.text()
        settings.DB_NAME = self.lineedit_dbname.text()
        settings.DB_USER = self.lineedit_dbuser.text()
        settings.DB_PASSWORD = self.lineedit_dbpassword.text()
        settings.DB_HOST = self.lineedit_dbhost.text()
        settings.DB_PORT = self.spinbox_port.value()
        settings.BUG_REPORT = self.checkbox_bugreport.isChecked()
        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())
        terminal_msg(self.terminal, 'Настройки программы сохранены')
        self.hide()


class MainWindow(QMainWindow):
    """Основное окно программы."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/mainwindow.ui', self)
        self.centralwidget.setContentsMargins(6, 6, 6, 6)
        self.setWindowIcon(QtGui.QIcon('icons/logo_main.png'))
        self.setWindowTitle('Usonic App')
        self.startstop_button.setIcon(QtGui.QIcon('icons/start.png'))
        self.settings_button.setIcon(QtGui.QIcon('icons/settings.png'))
        self.compare_button.setIcon(QtGui.QIcon('icons/compare.png'))
        self.table_button.setIcon(QtGui.QIcon('icons/table.png'))

        self.init_signals()
        self.init_style()
        self.data_transfer: bool = False
        self.settings_window: SettingsWindow = SettingsWindow(self.terminal)
        self.table_window: TableWindow = TableWindow(self.terminal)

    def init_style(self) -> None:
        """Подключаем пользовательские стили."""
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.settings_button.clicked.connect(self.settings_button_clicked)
        self.startstop_button.clicked.connect(self.startstop_button_clicked)
        self.compare_button.clicked.connect(self.compare_button_clicked)
        self.table_button.clicked.connect(self.table_button_clicked)

    @pyqtSlot()
    def settings_button_clicked(self) -> None:
        """Слот нажатия кнопки настроек. Открывает окно настроек."""
        if self.settings_window.isVisible():
            self.settings_window.hide()
            return
        self.settings_window.show()

    @pyqtSlot()
    def startstop_button_clicked(self) -> None:
        """Слот нажатия кнопки пуска/остановки приема данных."""
        self.data_transfer = not self.data_transfer
        if self.data_transfer is True:
            self.startstop_button.setIcon(QtGui.QIcon('icons/stop.png'))
            print('Start button is clicked!')
            return
        self.startstop_button.setIcon(QtGui.QIcon('icons/start.png'))
        print('Stop button is clicked!')

    @pyqtSlot()
    def compare_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        print('Compare button is clicked!')

    @pyqtSlot()
    def table_button_clicked(self) -> None:
        """Слот нажатия кнопки вывода таблицы базы данных."""
        if self.table_window.isVisible():
            self.table_window.hide()
            return
        self.table_window.load_postgres_data()
        self.table_window.show()


def main() -> None:
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec()


if __name__ == '__main__':
    main()
