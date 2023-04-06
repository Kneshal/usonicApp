from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox

from config import settings
from utils import get_form_path, get_icon


class SettingsWindow(QWidget):
    """Окно настроек программы."""
    change_settings_signal: pyqtSignal = pyqtSignal()
    terminal_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.init_gui()
        self.button_save.clicked.connect(self.save_button_clicked)

    def init_gui(self):
        """Настраиваем графический интерфейс."""
        uic.loadUi(get_form_path('settings.ui'), self)
        self.setWindowIcon(get_icon('logo_settings.png'))
        self.setWindowTitle('Настройки')

    def update_window_widgets(self, users: list, serial_ports: list) -> None:
        """Обновляем данные виджетов окна настроек."""
        self.combobox_user.clear()
        self.combobox_user.addItems(users)
        index: int = self.combobox_user.findText(settings.OPERATOR)
        if index != -1:
            self.combobox_user.setCurrentIndex(index)

        else:
            self.combobox_user.insertItem(0, settings.OPERATOR)
            self.combobox_user.setCurrentIndex(0)

        self.combobox_serialport.clear()
        self.combobox_serialport.addItems(serial_ports)
        index = self.combobox_serialport.findText(settings.COM_PORT)
        if index != -1:
            self.combobox_serialport.setCurrentIndex(index)

        self.disp_records_spinbox.setValue(settings.DISPLAY_RECORDS)
        self.lineedit_dbname.setText(settings.DB_NAME)
        self.lineedit_dbuser.setText(settings.DB_USER)
        self.lineedit_dbpassword.setText(settings.DB_PASSWORD)
        self.lineedit_dbhost.setText(settings.DB_HOST)
        self.spinbox_port.setValue(settings.DB_PORT)
        self.checkbox_bugreport.setChecked(settings.BUG_REPORT)
        self.fps_spinbox.setValue(settings.FPS)

    @pyqtSlot()
    def save_button_clicked(self) -> None:
        """Слот нажатия кнопки сохранения настроек. Сохраняем данные
        в объект dynaconf и файл."""
        settings.OPERATOR = self.combobox_user.currentText()
        settings.DISPLAY_RECORDS = self.disp_records_spinbox.value()
        settings.DB_NAME = self.lineedit_dbname.text()
        settings.DB_USER = self.lineedit_dbuser.text()
        settings.DB_PASSWORD = self.lineedit_dbpassword.text()
        settings.DB_HOST = self.lineedit_dbhost.text()
        settings.DB_PORT = self.spinbox_port.value()
        settings.BUG_REPORT = self.checkbox_bugreport.isChecked()
        settings.COM_PORT = self.combobox_serialport.currentText()
        settings.FPS = self.fps_spinbox.value()
        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())
        self.terminal_signal.emit('Настройки программы сохранены')
        self.change_settings_signal.emit()
        self.hide()
