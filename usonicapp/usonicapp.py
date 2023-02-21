import os
import sys
from datetime import datetime
from decimal import Decimal

import constants as cts
import numpy as np
import qdarktheme
from config import settings
from database import DataBase
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from models import Record, generate_factory_number
from plottab import PlotTab, PlotUpdateWorker
from PyQt5 import uic
from PyQt5.QtCore import (QDate, QModelIndex, QSize, Qt, QThread, QTimer,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QCheckBox, QHeaderView, QMainWindow,
                             QTableWidget, QTableWidgetItem, QWidget)
from serialport import SerialPortManager
from widgets import CellCheckbox, EditToolButton

basedir = os.path.dirname(__file__)


def set_icon(path: str) -> QIcon:
    """Формирует иконку на базе пути к файлу."""
    return QIcon(os.path.join(basedir, path))


def set_pixmap(path: str) -> QPixmap:
    """Формирует иконку на базе пути к файлу."""
    return QPixmap(os.path.join(basedir, path))


class UploadWindow(QWidget):
    """Окно загрузки данных на сервера."""
    terminal_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.record = None
        self.temporary = False
        self.db = db
        self.init_gui()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/upload.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_upload.png'))
        self.setWindowTitle('Загрузить запись')

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.upload_button.clicked.connect(self.upload_button_clicked)

    @pyqtSlot(dict)
    def update(self, record: dict, pg_db_status: bool, temporary: bool) -> None:  # noqa
        """Заполнение виджетов."""
        titles: list = self.db.get_models_pg()
        self.title_combobox.clear()
        self.title_combobox.addItems(titles)
        index: int = self.title_combobox.findText(record.get('title'))
        self.title_combobox.setCurrentIndex(index)

        self.comment_textedit.clear()
        # print(pg_db_status)
        self.temporary = temporary
        if self.temporary:
            self.pg_radiobutton.setVisible(False)
            self.sqlite_radiobutton.setChecked(True)
            self.fnumber_lineedit.setVisible(False)
            self.label_2.setVisible(False)
        else:
            self.fnumber_lineedit.setText(record.get('factory_number'))
            self.pg_radiobutton.setEnabled(pg_db_status)
            if pg_db_status:
                self.pg_radiobutton.setChecked(True)
            else:
                self.sqlite_radiobutton.setChecked(True)
            self.record = record

    def upload_button_clicked(self) -> None:
        """Нажатие кнопки загрузки записи  в БД."""
        db = self.db.sqlite_db
        if self.pg_radiobutton.isChecked():
            db = self.db.pg_db

        factory_number = self.fnumber_lineedit.text()
        if self.temporary:
            factory_number = generate_factory_number()

        title = self.title_combobox.currentText()
        comment = self.comment_textedit.toPlainText()
        self.record['factory_number'] = factory_number
        self.record['title'] = title
        self.record['comment'] = comment
        self.record['temporary'] = self.temporary
        result = self.db.upload_record(db, self.record)
        if result:
            message = 'Запись успешно загружена в БД.'
        else:
            message = 'Ошибка при загрузке записи в БД.'
        self.terminal_signal.emit(message)
        self.hide()


class EditRecordWindow(QWidget):
    """Окно редактирования записи БД."""
    edit_signal: pyqtSignal = pyqtSignal(QTableWidget)
    terminal_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: DataBase = db
        self.record: Record = Record()
        self.current_db = None
        self.table = None
        self.init_gui()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/edit_record.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_edit.png'))
        self.setWindowTitle('Редактировать запись')

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.save_button.clicked.connect(self.save_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def show_window(self, table: QTableWidget, db, id: str) -> None:
        """Делает окно видимым и заполняет виджеты данными
        указанной записи."""
        self.table = table
        self.record: Record = self.db.get_record(db, id)
        self.datetimeedit.setDateTime(self.record.date)
        self.factorynumber_lineedit.setText(self.record.factory_number)

        usernames: list = self.db.get_users_pg()
        self.user_combobox.clear()
        self.user_combobox.addItems(usernames)
        index: int = self.user_combobox.findText(self.record.user.username)
        self.user_combobox.setCurrentIndex(index)

        device_model_titles: list = self.db.get_models_pg()
        self.devicemodel_combobox.clear()
        self.devicemodel_combobox.addItems(device_model_titles)
        index: int = self.devicemodel_combobox.findText(
            self.record.device_model.title
        )
        self.devicemodel_combobox.setCurrentIndex(index)

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


class FilterWindow(QWidget):
    """Окно фильтрация таблицы БД."""
    apply_filter_signal: pyqtSignal = pyqtSignal()

    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: DataBase = db
        self.init_gui()
        self.init_signals()

    def init_gui(self):
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/filter.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_filter.png'))
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


class TableWindow(QWidget):
    terminal_signal: pyqtSignal = pyqtSignal(str)
    """Таблица базы данных программы."""
    def __init__(self, db: DataBase, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: DataBase = db
        self.selected_records: dict = {
            cts.PG_TABLE: [],
            cts.SQLITE_TABLE: [],
        }
        self.temporary: bool = False

        self.init_gui()
        self.init_windows()
        self.init_signals()

    def init_gui(self) -> None:
        """Настраиваем интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/table.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_table.png'))
        self.setWindowTitle('База данных')
        self.tabwidget.setTabIcon(0, set_icon('icons/remote_server.png'))
        self.tabwidget.setTabIcon(1, set_icon('icons/local_server.png'))
        self.tabwidget.setIconSize(QSize(20, 20))
        self.open_button.setIcon(set_icon('icons/load.png'))
        self.update_button.setIcon(set_icon('icons/update.png'))
        self.filter_button.setIcon(set_icon('icons/filter.png'))
        self.search_button.setIcon(set_icon('icons/search.png'))
        self.delete_button.setIcon(set_icon('icons/delete.png'))
        self.temp_button.setIcon(set_icon('icons/temp_off.png'))
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

    def init_windows(self) -> None:
        """Инициализация дополнительных окон."""
        self.pg_filter_window: FilterWindow = FilterWindow(self.db)
        self.sqlite_filter_window: FilterWindow = FilterWindow(self.db)
        self.edit_record_window: EditRecordWindow = EditRecordWindow(
            self.db)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.open_button.clicked.connect(self.open_button_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)
        self.update_button.clicked.connect(self.update_button_clicked)
        self.filter_button.clicked.connect(self.filter_button_clicked)
        self.search_button.clicked.connect(self.search_button_clicked)
        self.sqlite_table.doubleClicked.connect(self.item_double_clicked)
        self.pg_table.doubleClicked.connect(self.item_double_clicked)
        self.temp_button.clicked.connect(self.temp_button_clicked)
        self.pg_filter_window.apply_filter_signal.connect(
            lambda: self.load_data(
                self.tabwidget.findChild(QTableWidget, cts.PG_TABLE)
            )
        )
        self.sqlite_filter_window.apply_filter_signal.connect(
            lambda: self.load_data(
                self.tabwidget.findChild(QTableWidget, cts.SQLITE_TABLE)
            )
        )
        self.edit_record_window.edit_signal.connect(self.load_data)
        self.search_edit.returnPressed.connect(self.search_button_clicked)

    def get_current_table(self) -> QTableWidget:
        """Возвращает ссылку на текущую таблицу в QTabWidget."""
        return self.tabwidget.currentWidget().findChild(QTableWidget)

    def get_current_table_name(self) -> str:
        """Возвращает имя текущей таблицы."""
        return self.tabwidget.currentWidget().findChild(
            QTableWidget).objectName()

    def get_current_selected_records(self) -> list:
        """Возвращает список выбранных записей в текущей таблице."""
        table_name: str = self.get_current_table_name()
        return self.selected_records.get(table_name)

    def get_current_db(self):
        """Возвращает ссылку на БД в зависимости от текущей таблицы."""
        table_name: str = self.get_current_table_name()
        return self.get_db_by_name(table_name)

    def get_db_by_name(self, table_name: str):
        """Возвращает ссылку на Бд в зависимоти от имени таблицы."""
        if table_name == cts.PG_TABLE:
            return self.db.pg_db
        return self.db.sqlite_db

    def clear_current_selected_records(self):
        """Очищает список выбранных записей для текущей таблицы."""
        table_name: str = self.get_current_table_name()
        self.selected_records[table_name] = []

    def get_filter_settings(self, table: QTableWidget) -> dict:
        """Возвращает текущие настройки фильтрации для заданной таблицы."""
        if table.objectName() == cts.PG_TABLE:
            return self.pg_filter_window.get_filter_settings()
        return self.sqlite_filter_window.get_filter_settings()

    @staticmethod
    def set_color_to_row(table: QTableWidget, row_index: int, color: QColor) -> None:  # noqa
        """Задаем цвет заданной строки таблицы."""
        for i in range(table.columnCount()):
            item: QTableWidgetItem = table.item(row_index, i)
            if item is not None:
                item.setBackground(color)

    @pyqtSlot(QTableWidget)
    def load_data(self, table: QTableWidget, search: str = None) -> None:  # noqa
        """Загружаем данные из БД и обновляем таблицу."""
        filter_settings: dict = self.get_filter_settings(table)
        self.clear_current_selected_records()
        db: DataBase = self.get_db_by_name(table.objectName())
        filtered_records: dict = self.db.get_filtered_records(
            db, filter_settings, search, self.temporary
        )
        table.clearContents()
        table.setRowCount(0)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ['id', '', 'Дата', 'Пользователь', 'Комментарий', '']
        )
        table.setColumnHidden(0, True)
        table.verticalHeader().setVisible(False)
        header: QHeaderView = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        color_flag: bool = False
        gray: QColor = QColor(128, 128, 128)
        lightslategray: QColor = QColor(119, 136, 153)
        row: int = 0  # Текущая строка таблицы
        title: str
        records: list
        for title, records in filtered_records.items():
            color: QColor = None
            if color_flag:
                color = gray
            else:
                color = lightslategray
            flag_selectable_enabled = (
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            rowposition: int = table.rowCount()
            table.insertRow(rowposition)
            row += 1
            # Объединяем ячейки и выводим номер аппарата и модель
            item: QTableWidgetItem = QTableWidgetItem(title)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(rowposition, 0, item)
            table.setSpan(rowposition, 0, 1, 6)
            self.set_color_to_row(table, rowposition, color)

            record: Record
            for record in records:
                table.insertRow(table.rowCount())
                # Скрытая ячейка с id записи
                item: QTableWidgetItem = QTableWidgetItem(str(record.id))
                table.setItem(row, 0, item)
                # Ячейка с checkbox
                checkboxwidget: CellCheckbox = CellCheckbox(
                    self, str(record.id)
                )
                table.setCellWidget(row, 1, checkboxwidget)
                item: QTableWidgetItem = QTableWidgetItem()
                table.setItem(row, 1, item)
                # Ячейка с датой и временем
                item: QTableWidgetItem = QTableWidgetItem(
                    record.date.strftime('%m-%d-%Y %H:%M')
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 2, item)
                # Ячейка с именем пользователя
                item: QTableWidgetItem = QTableWidgetItem(
                    record.user.username
                )
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 3, item)
                # Ячейка с комментарием
                item: QTableWidgetItem = QTableWidgetItem(record.comment)
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 4, item)
                self.set_color_to_row(table, row, color)
                # Ячейка с иконкой изменения
                item: QTableWidgetItem = QTableWidgetItem()
                edit_button: EditToolButton = EditToolButton(
                    self.edit_record_window, table, db, str(record.id)
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 5, item)
                table.setCellWidget(row, 5, edit_button)
                self.set_color_to_row(table, row, color)
                row += 1
            color_flag = not color_flag

    def update(self) -> None:
        """Обновляет данные таблиц."""
        self.load_data(table=self.pg_table)
        self.load_data(table=self.sqlite_table)

    @pyqtSlot(QModelIndex)
    def item_double_clicked(self, index: int) -> None:
        """Слот двойного щелчка мыши по таблице. Меняет статус QCheckbox."""
        table: QTableWidget = self.get_current_table()
        ch_item: CellCheckbox = table.cellWidget(index.row(), 1)
        if (isinstance(ch_item, CellCheckbox) and
                (ch_item.checkbox.isChecked())):
            ch_item.checkbox.setChecked(False)
        elif isinstance(ch_item, CellCheckbox):
            ch_item.checkbox.setChecked(True)

    @pyqtSlot(QCheckBox, str)
    def checkbox_change_state(self, checkbox: QCheckBox, record_id: str) -> None:  # noqa
        """Слот изменения статуса QCheckbox в таблице. Если статус меняется,
        то соответствующим образом меняется список выбранных записей."""
        table_name: str = self.get_current_table_name()
        if checkbox.isChecked():
            self.selected_records[table_name].append(record_id)
        else:
            self.selected_records[table_name].remove(record_id)

    @pyqtSlot()
    def open_button_clicked(self) -> None:
        """Слот нажатия кнопки выгрузки данных."""
        list_id: list = self.get_current_selected_records()
        if not list_id:
            return
        print('Open button is clicked!')
        print('Выгружаем данные', list_id)
        self.hide()

    @pyqtSlot()
    def delete_button_clicked(self) -> None:
        """Слот нажатия кнопки удаления данных. Удаляет записи из БД и
        отправляет сообщение в терминал."""
        db: DataBase = self.get_current_db()
        list_id: list = self.get_current_selected_records()
        if not list_id:
            return
        result: bool = self.db.delete_records(db, list_id)
        if result:
            self.terminal_signal.emit(
                f'Из базы данных удалено записей: {len(list_id)}.'
            )
        else:
            self.terminal_signal.emit(
                'Не удалось удалить данные из базы данных.'
            )
        self.load_data(self.get_current_table())

    @pyqtSlot()
    def update_button_clicked(self) -> None:
        """Слот нажатия кнопки обновления таблицы."""
        self.load_data(self.get_current_table())

    @pyqtSlot()
    def filter_button_clicked(self) -> None:
        """Слот нажатия кнопки фильтрации данных. Открывает отдельное окно."""
        table_name: str = self.get_current_table_name()
        if table_name == cts.PG_TABLE:
            if self.pg_filter_window.isVisible():
                self.pg_filter_window.hide()
                return
            self.pg_filter_window.show()
        elif table_name == cts.SQLITE_TABLE:
            if self.sqlite_filter_window.isVisible():
                self.sqlite_filter_window.hide()
                return
            self.sqlite_filter_window.show()

    @pyqtSlot()
    def search_button_clicked(self) -> None:
        """Слот нажатия кнопки поиска записи."""
        factory_number: str = self.search_edit.text()
        self.load_data(table=self.get_current_table(), search=factory_number)

    @pyqtSlot()
    def temp_button_clicked(self) -> None:
        """Слот смены режима отображения временных записей."""
        self.temporary = not self.temporary
        self.update()
        if self.temporary:
            self.temp_button.setIcon(set_icon('icons/temp_on.png'))
        else:
            self.temp_button.setIcon(set_icon('icons/temp_off.png'))

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного."""
        if self.pg_filter_window:
            self.pg_filter_window.close()
        if self.sqlite_filter_window:
            self.sqlite_filter_window.close()
        if self.edit_record_window:
            self.edit_record_window.close()


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
        uic.loadUi(os.path.join(basedir, 'forms/settings.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_settings.png'))
        self.setWindowTitle('Настройки')

    def update(self, users: list, serial_ports: list) -> None:
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
        index: int = self.combobox_serialport.findText(settings.COM_PORT)
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
        settings.OPERATOR: str = self.combobox_user.currentText()
        settings.DISPLAY_RECORDS: int = self.disp_records_spinbox.value()
        settings.DB_NAME: str = self.lineedit_dbname.text()
        settings.DB_USER: str = self.lineedit_dbuser.text()
        settings.DB_PASSWORD: str = self.lineedit_dbpassword.text()
        settings.DB_HOST: str = self.lineedit_dbhost.text()
        settings.DB_PORT: int = self.spinbox_port.value()
        settings.BUG_REPORT: bool = self.checkbox_bugreport.isChecked()
        settings.COM_PORT: str = self.combobox_serialport.currentText()
        settings.FPS: int = self.fps_spinbox.value()
        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())
        self.terminal_signal.emit('Настройки программы сохранены')
        self.change_settings_signal.emit()
        self.hide()


class MainWindow(QMainWindow):
    """Основное окно программы."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(basedir, 'forms/mainwindow.ui'), self)
        self.temporary: bool = False
        self.db: DataBase = DataBase()
        self.serial_manager: SerialPortManager = SerialPortManager()
        self.storage: dict = {}

        self.init_gui()
        self.init_windows()
        self.init_timers()
        self.init_threads()
        self.init_signals()

        self.db.init_timers()
        self.serial_manager.init_timers()

    def init_gui(self) -> None:
        """Настройка графического интерфейса."""
        self.centralwidget.setContentsMargins(6, 6, 6, 6)
        self.setWindowIcon(set_icon('icons/logo_main.png'))
        self.setWindowTitle('Usonic App')
        self.startstop_button.setIcon(set_icon('icons/start.png'))
        self.settings_button.setIcon(set_icon('icons/settings.png'))
        self.compare_button.setIcon(set_icon('icons/compare.png'))
        self.table_button.setIcon(set_icon('icons/table.png'))
        self.temp_button.setIcon(set_icon('icons/temp_off.png'))
        self.upload_button.setIcon(set_icon('icons/upload_false.png'))
        self.setStyleSheet(cts.STYLESHEET_LIGHT)
        self.fnumber_lineedit.setText(
            settings.PREVIOUS_FACTORY_NUMBER
        )
        self.devicemodel_combobox.addItems(self.db.get_models_pg())
        self.connect_pixmap = set_pixmap('icons/connect.png')
        self.disconnect_pixmap = set_pixmap('icons/disconnect.png')
        self.online_pixmap = set_pixmap('icons/online.png')
        self.offline_pixmap = set_pixmap('icons/offline.png')

        self.update_serial_port_interface(False)

    def init_windows(self) -> None:
        """Инициализация дополнительных окон."""
        self.settings_window: SettingsWindow = SettingsWindow()
        self.table_window: TableWindow = TableWindow(db=self.db)
        self.upload_window: UploadWindow = UploadWindow(db=self.db)

    def init_timers(self) -> None:
        """Настройка таймеров."""
        self.plot_update_timer: QTimer = QTimer()
        interval: int = int(1000 / settings.FPS)
        self.plot_update_timer.setInterval(interval)

    def init_threads(self) -> None:
        """Инициализация потоков."""
        self.plot_update_worker = PlotUpdateWorker()
        self.plot_update_thread = QThread(parent=self)
        self.plot_update_worker.moveToThread(self.plot_update_thread)
        self.plot_update_thread.start()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        # Попробовать перенести инициализацию сигналов в соответствующие классы
        # Кнопки и другие виджеты
        self.settings_button.clicked.connect(self.settings_button_clicked)
        self.startstop_button.clicked.connect(self.startstop_button_clicked)
        self.compare_button.clicked.connect(self.compare_button_clicked)
        self.table_button.clicked.connect(self.table_button_clicked)
        self.temp_button.clicked.connect(self.temp_button_clicked)
        self.fnumber_lineedit.textChanged.connect(
            self.search_model_by_fnumber)
        self.upload_button.clicked.connect(self.upload_button_clicked)
        # Окно настроек
        self.settings_window.change_settings_signal.connect(
            self.table_window.pg_filter_window.update_widget)
        self.settings_window.change_settings_signal.connect(
            self.table_window.sqlite_filter_window.update_widget)
        self.settings_window.terminal_signal.connect(self.terminal_msg)
        # Окно базы данных
        self.table_window.terminal_signal.connect(self.terminal_msg)
        # Окно редактирования записи
        self.table_window.edit_record_window.terminal_signal.connect(
            self.terminal_msg)
        # COM-порт
        self.serial_manager.signal_port_checked.connect(
            self.update_serial_port_interface)
        self.serial_manager.signal_stop_data_transfer.connect(
            self.startstop_button_clicked)
        self.serial_manager.signal_transfer_progress_change.connect(
            self.update_progress_bar)
        # БД
        self.db.pg_db_checked_signal.connect(self.update_pg_db_pixmap)
        # Tabwidget
        self.tabwidget.tabCloseRequested.connect(self.close_tab)
        self.tabwidget.currentChanged.connect(self.toggle_upload_button_status)
        # Окно загрузки
        self.upload_window.terminal_signal.connect(self.terminal_msg)

    @pyqtSlot(bool)
    def toggle_serial_interface(self, status: bool) -> None:
        """Меняем состояние виджетов COM-порта."""
        self.temp_button.setEnabled(status)
        self.devicemodel_combobox.setEnabled(status)
        self.fnumber_lineedit.setEnabled(status)
        self.freq_spinbox.setEnabled(status)
        self.range_spinbox.setEnabled(status)
        self.step_spinbox.setEnabled(status)

    def get_freq_list(self) -> list:
        """Возвращает заданные пользователем данные по частоте."""
        freq_start: int = self.freq_spinbox.value()
        freq_stop: int = freq_start + self.range_spinbox.value()
        step: Decimal = round(Decimal(self.step_spinbox.value()), 2)
        freq_list: list = np.arange(
            freq_start,
            freq_stop,
            step
        ).tolist()
        freq_stop: Decimal = freq_list[-1]
        return freq_list

    @pyqtSlot(int)
    def toggle_upload_button_status(self, index) -> None:
        """Меняет состояние кнопки и иконку."""
        if index != -1:
            self.upload_button.setIcon(set_icon('icons/upload_true.png'))
            self.upload_button.setEnabled(True)
        else:
            self.upload_button.setIcon(set_icon('icons/upload_false.png'))
            self.upload_button.setEnabled(False)

    @pyqtSlot()
    def upload_button_clicked(self) -> None:
        """Нажатие кнопки выгрузки данных на сервер."""
        index = self.tabwidget.currentIndex()
        page = self.tabwidget.widget(index)
        plottab = self.storage.get(page)
        if plottab is None:
            return

        # print(plottab.record)

        if self.upload_window.isVisible():
            self.upload_window.hide()
            return
        pg_db_status = self.db.check_pg_db()
        self.upload_window.update(plottab.record, pg_db_status, self.temporary)
        self.upload_window.show()

    @pyqtSlot()
    def startstop_button_clicked(self) -> None:
        """Слот нажатия кнопки пуска/остановки приема данных."""
        transfer_status = self.serial_manager.get_transfer_status()
        self.serial_manager.toggle_transfer_status()
        if transfer_status is False:
            self.start_transfer()
        else:
            self.stop_transfer()

    def start_transfer(self):
        """Начало передачи данных."""
        self.startstop_button.setIcon(set_icon('icons/stop.png'))
        freq_list = self.get_freq_list()
        self.progressbar.setMaximum(len(freq_list))
        self.progressbar.setValue(0)
        self.toggle_serial_interface(False)
        self.terminal_msg(
            f'Передача данных в диапазоне {freq_list[0]} - '
            f'{freq_list[-1]} с шагом '
            f'{self.step_spinbox.value()}'
        )

        factory_number = self.fnumber_lineedit.text()
        device_model_title = self.devicemodel_combobox.currentText()
        username = settings.OPERATOR
        self.create_tab(
            factory_number=factory_number,
            device_model_title=device_model_title,
            username=username,
            )
        self.serial_manager.start_data_transfer(freq_list)

    def stop_transfer(self):
        """Остановка передачи данных."""
        self.startstop_button.setIcon(set_icon('icons/start.png'))
        self.toggle_serial_interface(True)
        self.terminal_msg('Передача данных завершена')
        self.serial_manager.stop_data_transfer()
        self.plot_update_timer.stop()
        # не красиво, попробовать переделать
        try:
            self.plot_update_timer.disconnect()
        except TypeError:
            pass

    def create_tab(self, factory_number: str, device_model_title: str, username: str):  # noqa
        """Создает новую вкладку QTabwidget и соответствующий объект с
        графиками. Устанавливает связь между полученрием данных от
        COM-порта и методом объекта plottab."""
        date = datetime.now()
        date_str = date.strftime('%H:%M:%S')
        title = f'{date_str} - {factory_number}'
        self.plottab = PlotTab(
            self.tabwidget,
            factory_number,
            device_model_title,
            username,
            date,
        )

        self.serial_manager.signal_send_point.connect(self.plottab.add_data)

        self.plot_update_timer.setInterval(int(1000 / settings.FPS))
        self.plot_update_timer.timeout.connect(lambda: self.plot_update_worker.draw(self.plottab))  # noqa
        self.plot_update_timer.start()

        self.tabwidget.addTab(self.plottab.page, title)
        self.tabwidget.setCurrentIndex(self.tabwidget.count() - 1)
        self.storage[self.plottab.page] = self.plottab

    @pyqtSlot(int)
    def close_tab(self, index: int) -> bool:
        """Удаляет запись из локального хранилища. Поиск по вложенному
        виджету."""
        try:
            page = self.tabwidget.widget(index)
            # Если закрыли рабочую вкладку, то останавливаем все процессы
            if self.plottab.page == page:
                transfer_status = self.serial_manager.get_transfer_status()
                if transfer_status:
                    self.serial_manager.toggle_transfer_status()
                    self.stop_transfer()
            self.tabwidget.removeTab(index)
            del self.storage[page]
            # print(self.storage)
            return True
        except KeyError:
            self.terminal_msg(
                'Не удалось удалить запись из локального хранилища.'
            )
            return False

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        """Обновляет по срабатыванию сигнала значение
        виджета progressbar."""
        maximum = self.progressbar.maximum()
        value = maximum - value
        self.progressbar.setValue(value)

    @pyqtSlot(bool)
    def update_serial_port_interface(self, status) -> None:
        """Меняем интерфейс работы с COM-портом в зависимости от
        его доступности."""
        if status:
            self.comport_label.setPixmap(self.connect_pixmap)
            self.startstop_button.setIcon(set_icon('icons/start'))
        else:
            self.comport_label.setPixmap(self.disconnect_pixmap)
            self.startstop_button.setIcon(set_icon('icons/start_disabled'))
            self.devicemodel_combobox.setEnabled(False)
        self.temp_button.setEnabled(status)
        self.startstop_button.setEnabled(status)
        self.fnumber_lineedit.setEnabled(status)
        self.freq_spinbox.setEnabled(status)
        self.range_spinbox.setEnabled(status)
        self.step_spinbox.setEnabled(status)

    @pyqtSlot()
    def search_model_by_fnumber(self) -> None:
        """Слот для подбора модели аппарата из БД под заданный
        заводской номер."""
        factory_number: str = self.fnumber_lineedit.text()
        if len(factory_number) != 13:
            self.devicemodel_combobox.setEnabled(False)
            return
        title: str = self.db.get_device_model_title_by_fnumber(
            factory_number=factory_number)
        if title is None:
            self.devicemodel_combobox.setEnabled(True)
            return
        index: int = self.devicemodel_combobox.findText(title)
        self.devicemodel_combobox.setCurrentIndex(index)
        self.devicemodel_combobox.setEnabled(False)

    @pyqtSlot()
    def settings_button_clicked(self) -> None:
        """Слот нажатия кнопки настроек. Открывает окно настроек
        и обновляет его актуальными списками пользователей и COM-портов."""
        if self.settings_window.isVisible():
            self.settings_window.hide()
            return
        users: list = self.db.get_users_pg()
        serial_ports: list = self.serial_manager.get_available_port_names()
        self.settings_window.update(users, serial_ports)
        self.settings_window.show()

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
        self.table_window.update()
        self.table_window.show()

    @pyqtSlot(bool)
    def update_pg_db_pixmap(self, status) -> None:
        """Изменение иконки доступности БД."""
        if status:
            self.database_label.setPixmap(self.online_pixmap)
            return
        self.database_label.setPixmap(self.offline_pixmap)

    @pyqtSlot()
    def temp_button_clicked(self) -> None:
        """Слот изменения типа записи на временную или постоянную.
        Меняет видимость виджета ввода заводского номера."""
        self.temporary = not self.temporary
        if self.temporary:
            self.temp_button.setIcon(set_icon('icons/temp_on.png'))
            self.label.setVisible(False)
            self.fnumber_lineedit.setVisible(False)
            self.devicemodel_combobox.setEnabled(True)
        else:
            self.temp_button.setIcon(set_icon('icons/temp_off.png'))
            self.label.setVisible(True)
            self.fnumber_lineedit.setVisible(True)
            self.search_model_by_fnumber()

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного."""
        self.plot_update_thread.quit()
        self.plot_update_thread.wait()
        if self.settings_window:
            self.settings_window.close()
        if self.table_window:
            self.table_window.close()
        if self.upload_window:
            self.upload_window.close()

    @pyqtSlot(str)
    def terminal_msg(self, message: str) -> None:
        """Добавляем текущее время и текст в терминал."""
        current_time: datetime = datetime.now().time().strftime('%H:%M')
        self.terminal.append(f'{current_time} - {message}')


if __name__ == '__main__':
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app: QApplication = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainwindow: MainWindow = MainWindow()
    mainwindow.show()
    app.exec()
