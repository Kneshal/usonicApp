from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget

from database import DataBase
from models import Record, generate_factory_number
from serialport import MeasuredValues
from utils import get_form_path, get_icon


class UploadWindow(QWidget):
    """Окно загрузки данных на сервера."""
    terminal_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self, db_manager: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db_manager: DataBase = db_manager
        self.init_gui()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(get_form_path('upload.ui'), self)
        self.setWindowIcon(get_icon('logo_upload.png'))
        self.setWindowTitle('Загрузить запись')

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.upload_button.clicked.connect(self.upload_button_clicked)

    @pyqtSlot(dict)
    def update_window_widgets(self, record: Record, data: MeasuredValues, pg_db_status: bool) -> None:  # noqa
        """Заполнение виджетов."""
        self.record: Record = record
        self.data: MeasuredValues = data
        titles: list = self.db_manager.get_models_pg()
        self.title_combobox.clear()
        self.title_combobox.addItems(titles)
        index: int = self.title_combobox.findText(
            self.record.device_model.title)
        self.title_combobox.setCurrentIndex(index)

        self.comment_textedit.clear()
        if self.record.temporary:
            self.pg_radiobutton.setVisible(False)
            self.sqlite_radiobutton.setChecked(True)
            self.fnumber_lineedit.setVisible(False)
            self.label_2.setVisible(False)
        else:
            self.fnumber_lineedit.setText(self.record.factory_number)
            self.pg_radiobutton.setEnabled(pg_db_status)
            if pg_db_status:
                self.pg_radiobutton.setChecked(True)
            else:
                self.sqlite_radiobutton.setChecked(True)

    def upload_button_clicked(self) -> None:
        """Нажатие кнопки загрузки записи  в БД."""
        db = self.db_manager.sqlite_db
        if self.pg_radiobutton.isChecked():
            db = self.db_manager.pg_db

        factory_number = self.fnumber_lineedit.text()
        if self.record.temporary:
            factory_number = generate_factory_number()

        title = self.title_combobox.currentText()
        device_model = self.db_manager.get_model_by_title(title)
        self.record.factory_number = factory_number
        self.record.device_model = device_model
        self.record.comment = self.comment_textedit.toPlainText()

        result: bool = self.db_manager.upload_record(db, self.record, self.data)
        message: str = 'Ошибка при загрузке записи в БД.'
        if result:
            message = 'Запись успешно загружена в БД.'
        self.terminal_signal.emit(message)
        self.hide()
