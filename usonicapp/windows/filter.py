from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QDate, pyqtSlot
from PyQt5.QtWidgets import QWidget

from config import settings
from database import DataBase
from utils import get_form_path, get_icon


class FilterWindow(QWidget):
    """Окно фильтрация таблицы БД."""
    apply_filter_signal: pyqtSignal = pyqtSignal()

    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: DataBase = db
        self.init_gui()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(get_form_path('filter.ui'), self)
        self.setWindowIcon(get_icon('logo_filter.png'))
        self.setWindowTitle('Фильтрация')
        current_date: QDate = QDate.currentDate()
        self.dateedit_1.setDate(current_date)
        self.dateedit_2.setDate(current_date)
        self.user_checkbox.setChecked(True)
        self.update_widget()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.apply_button.clicked.connect(self.apply_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    @pyqtSlot()
    def update_widget(self) -> None:
        """Обновляем виджет."""
        users: list = self.db.get_users_pg()  # Заменить на выбор БД
        self.user_combobox.clear()
        self.user_combobox.addItems(users)
        index: int = self.user_combobox.findText(settings.OPERATOR)
        if index == -1:
            self.user_combobox.insertItem(0, settings.OPERATOR)
            self.user_combobox.setCurrentIndex(0)
        else:
            self.user_combobox.setCurrentIndex(index)
        device_models: list = self.db.get_models_pg()  # Заменить на выбор БД
        self.devicemodel_combobox.clear()
        self.devicemodel_combobox.addItems(device_models)

    @pyqtSlot()
    def get_filter_settings(self) -> dict:
        """Возвращает текущие параметры фильтрации."""
        result: dict = {}
        if self.user_checkbox.isChecked():
            result['user'] = self.user_combobox.currentText()
        if self.devicemodel_checkbox.isChecked():
            result['devicemodel'] = self.devicemodel_combobox.currentText()
        if self.date_checkbox.isChecked():
            result['date'] = [self.dateedit_1.date(), self.dateedit_2.date()]
        return result

    @pyqtSlot()
    def apply_button_clicked(self) -> None:
        """Слот нажатия кнопки сохранения
         параметров фильтрации. Подготавливает словарь с параметрами и
         вызывает сигнал для передачи данных в дальнейшую обработку."""
        self.apply_filter_signal.emit()
        self.hide()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены выбора параметров фильтрации."""
        self.hide()
