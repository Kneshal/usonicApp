from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QTableWidget

from database import DataBase
from models import Record
from utils import get_form_path, get_icon


class EditRecordWindow(QWidget):
    """Окно редактирования записи БД."""
    edit_signal: pyqtSignal = pyqtSignal(QTableWidget)
    terminal_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: DataBase = db
        self.current_db = None
        self.init_gui()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(get_form_path('edit_record.ui'), self)
        self.setWindowIcon(get_icon('logo_edit.png'))
        self.setWindowTitle('Редактировать запись')

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.save_button.clicked.connect(self.save_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def show_window(self, table: QTableWidget, db, id: str) -> None:
        """Делает окно видимым и заполняет виджеты данными
        указанной записи."""
        self.table: QTableWidget = table
        self.record: Record = self.db.get_record(db, id)
        self.datetimeedit.setDateTime(self.record.date)
        self.factorynumber_lineedit.setText(self.record.factory_number)

        usernames: list = self.db.get_users_pg()
        self.user_combobox.clear()
        self.user_combobox.addItems(usernames)
        index_user: int = self.user_combobox.findText(self.record.user.username)
        self.user_combobox.setCurrentIndex(index_user)

        device_model_titles: list = self.db.get_models_pg()
        self.devicemodel_combobox.clear()
        self.devicemodel_combobox.addItems(device_model_titles)
        index_device: int = self.devicemodel_combobox.findText(
            self.record.device_model.title
        )
        self.devicemodel_combobox.setCurrentIndex(index_device)

        self.comment_textedit.setText(self.record.comment)

        self.current_db = db
        self.activateWindow()
        if not self.isVisible():
            self.show()

    @pyqtSlot()
    def save_button_clicked(self) -> None:
        """Слот нажатия кнопки сохранения редактированных данных."""
        if self.current_db is None:
            return
        data: dict = {
            'title': self.devicemodel_combobox.currentText(),
            'username': self.user_combobox.currentText(),
            'factory_number': self.factorynumber_lineedit.text(),
            'comment': self.comment_textedit.toPlainText(),
        }
        result = self.db.update_record(self.current_db, self.record.id, data)
        if result:
            self.edit_signal.emit(self.table)
            self.terminal_signal.emit(
                f'Запись (id={self.record.id}) была отредактирована. '
                'Изменения внесены в БД.'
            )
        else:
            self.terminal_signal.emit(
                'Ошибка в процессе редактирования записи '
                f'(id={self.record.id}).'
            )
        self.hide()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены редактирования."""
        self.hide()
