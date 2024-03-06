import os
import sys
from datetime import datetime
from decimal import Decimal
from math import ceil
from typing import Dict, List, Union

import constants as cts
import numpy as np
import qdarktheme
import simplejson as json
from calc_stat import calc_stat
from config import settings
from database import DataBase
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from models import Record
from peewee import PostgresqlDatabase, SqliteDatabase
from plottab import ComparePlotTab, PlotTab, PlotUpdateWorker
from PyQt5 import uic
from PyQt5.QtCore import (QDate, QModelIndex, QSize, Qt, QThread, QTimer,
                          pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QCheckBox, QHeaderView, QLabel,
                             QMainWindow, QTableWidget, QTableWidgetItem,
                             QWidget)
from serialport import MeasuredValues, SerialPortManager
from widgets import CellCheckbox, EditToolButton

basedir = os.path.dirname(__file__)


def set_icon(path: str) -> QIcon:
    """Формирует иконку на базе пути к файлу."""
    return QIcon(os.path.join(basedir, path))


def set_pixmap(path: str) -> QPixmap:
    """Формирует изображение на базе пути к файлу."""
    return QPixmap(os.path.join(basedir, path))


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
        uic.loadUi(os.path.join(basedir, 'forms/upload.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_upload.png'))
        self.setWindowTitle('Загрузить запись')
        self.series_combobox.clear()
        self.series_combobox.addItems(cts.DEVICE_MODELS.keys())
        self.device_model_update()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.upload_button.clicked.connect(self.upload_button_clicked)
        self.series_combobox.currentIndexChanged.connect(
            self.device_model_update)

    @pyqtSlot(dict)
    def update_window_widgets(self, record: Record, data: MeasuredValues, pg_db_status: bool) -> None:  # noqa
        """Заполнение виджетов."""
        self.record: Record = record
        self.data: MeasuredValues = data

        index: int = self.series_combobox.findText(
            self.record.series)
        self.series_combobox.setCurrentIndex(index)

        index: int = self.devicemodel_combobox.findText(
            self.record.device_model)
        self.devicemodel_combobox.setCurrentIndex(index)

        index = self.composition_combobox.findText(
            self.record.composition)
        self.composition_combobox.setCurrentIndex(index)

        self.comment_textedit.clear()
        if self.record.temporary:
            self.pg_radiobutton.setVisible(False)
            self.sqlite_radiobutton.setChecked(True)
            self.fnumber_lineedit.setVisible(False)
            self.label_2.setVisible(False)
        else:
            self.pg_radiobutton.setVisible(True)
            self.fnumber_lineedit.setText(self.record.factory_number)
            self.pg_radiobutton.setEnabled(pg_db_status)
            if pg_db_status:
                self.pg_radiobutton.setChecked(True)
            else:
                self.sqlite_radiobutton.setChecked(True)

    @pyqtSlot()
    def device_model_update(self) -> None:
        """Событие обновления combobox с серией аппарата."""
        self.devicemodel_combobox.clear()
        series = self.series_combobox.currentText()
        row_models = cts.DEVICE_MODELS.get(series)
        models = [item.get('name') for item in row_models]
        self.devicemodel_combobox.addItems(sorted(models))

    def upload_button_clicked(self) -> None:
        """Нажатие кнопки загрузки записи в БД."""
        db = self.db_manager.sqlite_db
        if self.pg_radiobutton.isChecked():
            db = self.db_manager.pg_db
            # self.record.local = False

        factory_number = self.fnumber_lineedit.text()
        if self.record.temporary:
            factory_number = self.db_manager.generate_factory_number(db)

        series = self.series_combobox.currentText()
        device_model = self.devicemodel_combobox.currentText()
        composition = self.composition_combobox.currentText()
        self.record.factory_number = factory_number
        self.record.series = series
        self.record.device_model = device_model
        self.record.composition = composition
        self.record.comment = self.comment_textedit.toPlainText()

        result: bool = self.db_manager.upload_record(
            db, self.record, self.data)
        message: str = 'Ошибка при загрузке записи в БД.'
        if result:
            message = 'Запись успешно загружена в БД.'
        self.terminal_signal.emit(message)
        self.hide()


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
        uic.loadUi(os.path.join(basedir, 'forms/edit_record.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_edit.png'))
        self.setWindowTitle('Редактировать запись')
        self.user_combobox.clear()
        self.user_combobox.addItems(cts.USERS)

        self.series_combobox.clear()
        self.series_combobox.addItems(cts.DEVICE_MODELS.keys())
        self.device_model_update()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.save_button.clicked.connect(self.save_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)
        self.series_combobox.currentIndexChanged.connect(
            self.device_model_update)

    @pyqtSlot()
    def device_model_update(self) -> None:
        """Событие обновления combobox с серией аппарата."""
        self.devicemodel_combobox.clear()
        series = self.series_combobox.currentText()
        row_models = cts.DEVICE_MODELS.get(series)
        models = [item.get('name') for item in row_models]
        self.devicemodel_combobox.addItems(sorted(models))

    def show_window(self, table: QTableWidget, db, id: str) -> None:
        """Делает окно видимым и заполняет виджеты данными
        указанной записи."""
        self.table: QTableWidget = table
        self.record: Record = self.db.get_record(db, id)
        self.datetimeedit.setDateTime(self.record.date)
        self.factorynumber_lineedit.setText(self.record.factory_number)

        index: int = self.user_combobox.findText(
            self.record.user)
        self.user_combobox.setCurrentIndex(index)

        index = self.composition_combobox.findText(
            self.record.composition)
        self.composition_combobox.setCurrentIndex(index)

        index: int = self.series_combobox.findText(
            self.record.series)
        self.series_combobox.setCurrentIndex(index)

        index: int = self.devicemodel_combobox.findText(
            self.record.device_model)
        self.devicemodel_combobox.setCurrentIndex(index)

        self.comment_textedit.setText(self.record.comment)
        self.temporary_checkbox.setChecked(self.record.temporary)

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
            'series': self.series_combobox.currentText(),
            'device_model': self.devicemodel_combobox.currentText(),
            'composition': self.composition_combobox.currentText(),
            'user': self.user_combobox.currentText(),
            'factory_number': self.factorynumber_lineedit.text(),
            'comment': self.comment_textedit.toPlainText(),
            'temporary': self.temporary_checkbox.isChecked(),
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

    def init_gui(self) -> None:
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/filter.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_filter.png'))
        self.setWindowTitle('Фильтрация')
        current_date: QDate = QDate.currentDate()
        self.dateedit_1.setDate(current_date)
        self.dateedit_2.setDate(current_date)
        self.user_checkbox.setChecked(True)

        series: list = list(cts.DEVICE_MODELS.keys())
        self.series_combobox.clear()
        self.series_combobox.addItems(series)
        self.device_model_update()

        self.update_widget()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.apply_button.clicked.connect(self.apply_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)
        self.series_combobox.currentIndexChanged.connect(
            self.device_model_update)

    @pyqtSlot()
    def update_widget(self) -> None:
        """Обновляем виджет."""
        self.user_combobox.clear()
        self.user_combobox.addItems(cts.USERS)
        index: int = self.user_combobox.findText(settings.OPERATOR)
        self.user_combobox.setCurrentIndex(index)

    @pyqtSlot()
    def device_model_update(self) -> None:
        """Событие обновления combobox с серией аппарата."""
        self.devicemodel_combobox.clear()
        series = self.series_combobox.currentText()
        row_models = cts.DEVICE_MODELS.get(series)
        models = [item.get('name') for item in row_models]
        self.devicemodel_combobox.addItems(sorted(models))

    @pyqtSlot()
    def get_filter_settings(self) -> dict:
        """Возвращает текущие параметры фильтрации."""
        result: dict = {}
        if self.user_checkbox.isChecked():
            result['user'] = self.user_combobox.currentText()
        if self.series_checkbox.isChecked():
            result['series'] = self.series_combobox.currentText()
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


class PasswordWindow(QWidget):
    """Окно подтверждения действия паролем."""

    def __init__(self, func, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.init_gui()
        self.accept_button.clicked.connect(self.accept_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)
        self.func = func

    def init_gui(self):
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/password.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_password.png'))
        self.setWindowTitle('Введите пароль')

    @pyqtSlot()
    def accept_button_clicked(self) -> None:
        """Слот нажатия кнопки подтверждения пароля."""
        if cts.PASSWORD == self.password_edit.text():
            self.func()
            return self.close()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены."""
        self.close()


class CompareModedWindow(QWidget):
    """Окно выбора режима сравнения записей."""

    def __init__(self, records, tabwidget, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records = records
        self.tabwidget = tabwidget
        self.init_gui()
        self.accept_button.clicked.connect(self.accept_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def init_gui(self):
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/compare_mode.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_compare_mode.png'))
        self.setWindowTitle('Параметры сравнения')

    @pyqtSlot()
    def accept_button_clicked(self) -> None:
        """Слот нажатия кнопки подтверждения."""
        mode = []
        if self.resistance_checkbox.isChecked():
            mode.append("R")
        if self.amperage_checkbox.isChecked():
            mode.append("I")
        if self.phase_checkbox.isChecked():
            mode.append("Ph")

        self.compare_plottab = ComparePlotTab(
            tabwidget=self.tabwidget,
            records=self.records,
            mode=mode,
        )
        params = ', '.join(mode)
        tab_title = f'Сравнение по параметрам: {params}'
        self.tabwidget.addTab(self.compare_plottab.page, tab_title)
        self.tabwidget.setCurrentIndex(self.tabwidget.count() - 1)
        self.close()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены."""
        self.close()


class TableWindow(QWidget):
    terminal_signal: pyqtSignal = pyqtSignal(str)
    donwload_records_signal: pyqtSignal = pyqtSignal(list)

    """Таблица базы данных программы."""
    def __init__(self, db: DataBase) -> None:
        super().__init__()
        self.db: DataBase = db
        self.selected_records: Dict[str, list] = {
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
        self.sync_button.setIcon(set_icon('icons/sync.png'))
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
        self.open_button.clicked.connect(self.download_button_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)
        self.sync_button.clicked.connect(self.sync_button_clicked)
        self.update_button.clicked.connect(self.update_button_clicked)
        self.filter_button.clicked.connect(self.filter_button_clicked)
        self.search_button.clicked.connect(self.search_button_clicked)
        self.sqlite_table.doubleClicked.connect(self.item_double_clicked)
        self.pg_table.doubleClicked.connect(self.item_double_clicked)
        self.temp_button.clicked.connect(self.temp_button_clicked)
        self.pg_filter_window.apply_filter_signal.connect(
            lambda: self.load_data(
                table=self.tabwidget.findChild(QTableWidget, cts.PG_TABLE)
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

    def get_current_selected_records(self) -> List[str]:
        """Возвращает список выбранных записей в текущей таблице."""
        table_name: str = self.get_current_table_name()
        return self.selected_records[table_name]

    def get_current_db(self) -> Union[PostgresqlDatabase, SqliteDatabase]:
        """Возвращает ссылку на БД в зависимости от текущей таблицы."""
        table_name: str = self.get_current_table_name()
        return self.get_db_by_name(table_name)

    def get_db_by_name(self, table_name: str):
        """Возвращает ссылку на Бд в зависимоти от имени таблицы."""
        if table_name == cts.PG_TABLE:
            return self.db.pg_db
        return self.db.sqlite_db

    def clear_current_selected_records(self) -> None:
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
    def load_data(self, table: QTableWidget, search=None) -> None:
        """Загружаем данные из БД и обновляем таблицу."""
        filter_settings: dict = self.get_filter_settings(table)
        self.clear_current_selected_records()
        db: DataBase = self.get_db_by_name(table.objectName())
        filtered_records: dict = self.db.get_filtered_records(
            db, filter_settings, search, self.temporary
        )
        table.clearContents()
        table.setRowCount(0)
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels(
            [
                'id',
                '',
                '',
                'Дата и время',
                'Оператор',
                'Состав',
                'F, Гц',
                'R, Ом',
                'Q',
                'Комментарий',
                '',
            ]
        )
        table.setColumnHidden(0, True)
        table.verticalHeader().setVisible(False)
        header: QHeaderView = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            10, QHeaderView.ResizeMode.ResizeToContents)

        color_flag: bool = False
        gray: QColor = QColor(128, 128, 128)
        lightslategray: QColor = QColor(119, 136, 153)
        row: int = 0  # Текущая строка таблицы
        title: str
        records: list
        for title, records in filtered_records.items():
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
            # item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(rowposition, 0, item)
            table.setSpan(rowposition, 0, 1, 11)
            self.set_color_to_row(table, rowposition, color)

            for record in records:
                table.insertRow(table.rowCount())
                # Скрытая ячейка с id записи
                item = QTableWidgetItem(str(record.id))
                table.setItem(row, 0, item)
                # Ячейка с фото
                item = QTableWidgetItem()
                table.setItem(row, 1, item)
                # Ячейка с checkbox
                checkboxwidget: CellCheckbox = CellCheckbox(
                    self, str(record.id)
                )
                table.setCellWidget(row, 2, checkboxwidget)
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 2, item)
                # Ячейка с датой и временем
                item = QTableWidgetItem(
                    record.date.strftime('%d-%m-%Y %H:%M')
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 3, item)
                # Ячейка с именем пользователя
                item = QTableWidgetItem(record.user)
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 4, item)
                # Ячейка с комплектацией УЗКС
                item = QTableWidgetItem(record.composition)
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 5, item)
                # Ячейка с резонансной частотой
                frequence = (
                    str(record.frequency) if record.frequency != 0 else '')
                item = QTableWidgetItem(frequence)
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 6, item)
                # Ячейка с сопротивлением
                resistance = (
                    str(record.resistance) if record.resistance != 0 else '')
                item = QTableWidgetItem(resistance)
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 7, item)
                # Ячейка с добротность
                quality_factor = (
                    str(record.quality_factor) if record.quality_factor != 0
                    else '')
                item = QTableWidgetItem(quality_factor)
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 8, item)
                # Ячейка с комментарием
                item = QTableWidgetItem(record.comment)
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 9, item)
                # Ячейка с иконкой изменения
                item = QTableWidgetItem()
                edit_button: EditToolButton = EditToolButton(
                    self.edit_record_window, table, db, str(record.id)
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 10, item)
                table.setCellWidget(row, 10, edit_button)

                self.set_color_to_row(table, row, color)
                row += 1

            # Ячейка с фото
            record: Record = records[0]
            models: list = cts.DEVICE_MODELS.get(record.series)
            image_path: str = ''
            for model in models:
                if record.device_model == model.get('name'):
                    image_path = model.get('img')

            # Создаем изображение
            label = QLabel(self)
            pixmap = QPixmap(image_path)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)
            table.setCellWidget(rowposition + 1, 1, label)
            item = QTableWidgetItem()
            table.setItem(rowposition + 1, 1, item)
            table.item(rowposition + 1, 1).setBackground(QColor(255, 255, 255))

            # Добавляем строки, если записей мало, чтобы картинка отображалась
            # корректно
            add_rows = 0

            if len(records) < 5:
                add_rows = 5 - len(records)
                for i in range(0, add_rows):
                    table.insertRow(table.rowCount())
                    item: QTableWidgetItem = QTableWidgetItem()
                    table.setItem(row, 2, item)
                    self.set_color_to_row(table, row, color)
                    row += 1
                table.setSpan(row - add_rows, 2, add_rows, 9)
            # Объединяем ячейки для отображения картинки
            # if len(records) >= 1:
            table.setSpan(rowposition + 1, 1, len(records) + add_rows, 1)

            color_flag = not color_flag

    def update_tables(self) -> None:
        """Обновляет данные таблиц."""
        self.load_data(table=self.pg_table)
        self.load_data(table=self.sqlite_table)

    @pyqtSlot(QModelIndex)
    def item_double_clicked(self, index) -> None:
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
    def download_button_clicked(self) -> None:
        """Слот нажатия кнопки выгрузки данных."""
        table_name: str = self.get_current_table_name()
        db = self.get_db_by_name(table_name)
        selected_id = self.selected_records.get(table_name)
        if not selected_id:
            return
        records = []
        for id in selected_id:
            records.append(self.db.get_record(db, id))
        self.donwload_records_signal.emit(records)
        self.hide()

    def check_selected_records(self) -> bool:
        """Проверка - есть ли выделенные записи в текущей таблице"""
        if self.get_current_selected_records():
            return True
        return False

    @pyqtSlot()
    def delete_button_clicked(self) -> None:
        """Слот нажатия кнопки удаления данных. Удаляет записи из БД и
        отправляет сообщение в терминал."""
        if self.check_selected_records():
            self.password_window: PasswordWindow = PasswordWindow(
                self.delete_records)
            self.password_window.show()

    @pyqtSlot()
    def delete_records(self) -> None:
        """Удаление выделенных записей в текущей БД."""
        db: DataBase = self.get_current_db()
        list_id: list = self.get_current_selected_records()
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
    def sync_button_clicked(self) -> None:
        """Слот нажатия кнопки переноса данных."""
        if self.check_selected_records():
            self.password_window: PasswordWindow = PasswordWindow(
                self.sync_records)
            self.password_window.show()

    @pyqtSlot()
    def sync_records(self) -> None:
        """Создает записи в другой БД, удаляет записи из текущей БД и
        отправляет сообщение в терминал."""
        db: DataBase = self.get_current_db()
        list_id: list = self.get_current_selected_records()
        result: bool = self.db.sync_records(db, list_id)
        if result:
            self.terminal_signal.emit(
                f'Записей перенесено: {len(list_id)}.'
            )
            # Удаляем записи из прошлой БД
            if self.db.delete_records(db, list_id) is False:
                self.terminal_signal.emit(
                    'Не удалось удалить записи из прошлой БД в '
                    'процессе переноса.'
                )
        else:
            self.terminal_signal.emit(
                'Не удалось перенести записи из базы данных.'
            )

        self.update_tables()

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
        self.update_tables()
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
        self.button_cancel.clicked.connect(self.cancel_button_clicked)

    def init_gui(self):
        """Настраиваем графический интерфейс."""
        uic.loadUi(os.path.join(basedir, 'forms/settings.ui'), self)
        self.setWindowIcon(set_icon('icons/logo_settings.png'))
        self.setWindowTitle('Настройки')

    def update_window_widgets(self, serial_ports: list) -> None:
        """Обновляем данные виджетов окна настроек."""
        self.combobox_user.clear()
        self.combobox_user.addItems(cts.USERS)
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
        self.checkbox_realtime_chart.setChecked(settings.REAL_TIME_CHART)
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
        settings.REAL_TIME_CHART = self.checkbox_realtime_chart.isChecked()
        settings.COM_PORT = self.combobox_serialport.currentText()
        settings.FPS = self.fps_spinbox.value()
        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())
        self.terminal_signal.emit('Настройки программы сохранены')
        self.change_settings_signal.emit()
        self.hide()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены."""
        self.close()


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
        self.freq_spinbox.setValue(settings.START_FREQUENCY)
        self.range_spinbox.setValue(settings.RANGE)
        self.step_spinbox.setValue(settings.STEP)

        self.series_combobox.addItems(sorted(cts.DEVICE_MODELS.keys()))
        self.device_model_update()
        # self.devicemodel_combobox.addItems(self.db.get_models_pg())
        self.composition_combobox.addItems(cts.COMPOSITION)
        index = self.composition_combobox.findText(
            settings.PREVIOUS_COMPOSITION)
        self.composition_combobox.setCurrentIndex(index)

        self.connect_pixmap = set_pixmap('icons/connect.png')
        self.disconnect_pixmap = set_pixmap('icons/disconnect.png')
        self.online_pixmap = set_pixmap('icons/online.png')
        self.offline_pixmap = set_pixmap('icons/offline.png')

        self.update_serial_port_interface(False)

    def init_windows(self) -> None:
        """Инициализация дополнительных окон."""
        self.settings_window: SettingsWindow = SettingsWindow()
        self.table_window: TableWindow = TableWindow(db=self.db)
        self.upload_window: UploadWindow = UploadWindow(db_manager=self.db)

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
        self.table_window.donwload_records_signal.connect(
            self.download_records)
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
        # Combobox с моделями
        self.series_combobox.currentIndexChanged.connect(
            self.device_model_update)

    @pyqtSlot(list)
    def download_records(self, records) -> None:
        """Выгружает записи из БД, создает вкладки и строит графики."""
        for record in records:
            date_str = record.date.strftime('%H:%M:%S')
            title = f'{date_str} - {record.factory_number}'
            self.plottab = PlotTab(
                tabwidget=self.tabwidget,
                record=record,
            )
            # Если выгружаемая запись не пуста
            if record.data is None:
                self.terminal_msg(
                    f'Не удалось загрузить запись: {title}. '
                    'Некорректный тип данных.')
                continue
            # От локальной и удаленной БД поступают разные типы данных
            # record.data. Преобразуем при необходимости в Memoryview.
            if not isinstance(record.data, memoryview):
                record.data = memoryview(record.data)

            data = MeasuredValues(
                **json.loads(record.data.tobytes(), use_decimal=True)
            )
            self.plottab.set_data(data)
            self.plot_update_worker.draw(self.plottab)
            self.tabwidget.addTab(self.plottab.page, title)
            self.tabwidget.setCurrentIndex(self.tabwidget.count() - 1)
            self.storage[self.plottab.page] = self.plottab

            # Выводим основные параметры на экран
            self.plottab.label_frequency.setText(
                f"F = {record.frequency} Гц")
            self.plottab.label_resistance.setText(
                f"R = {record.resistance} Ом")
            self.plottab.label_quality_factor.setText(
                f"Q = {record.quality_factor}")
            if record.composition:
                self.plottab.label_composition.setText(
                    f"Сборка - {record.composition}")

    @pyqtSlot(bool)
    def toggle_serial_interface(self, status: bool) -> None:
        """Меняем состояние виджетов COM-порта."""
        self.temp_button.setEnabled(status)
        # self.devicemodel_combobox.setEnabled(status)
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
        # freq_stop: Decimal = freq_list[-1]
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
        if self.upload_window.isVisible():
            self.upload_window.hide()
            return
        pg_db_status = self.db.check_pg_db()
        self.upload_window.update_window_widgets(
            plottab.record, plottab.data, pg_db_status)
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
        settings.PREVIOUS_COMPOSITION = self.composition_combobox.currentText()
        settings.PREVIOUS_DEVICE_MODEL = (
            self.devicemodel_combobox.currentText())
        settings.PREVIOUS_FACTORY_NUMBER = self.fnumber_lineedit.text()

    def start_transfer(self):
        """Начало передачи данных."""
        self.startstop_button.setIcon(set_icon('icons/stop.png'))
        freq_list = self.get_freq_list()
        self.progressbar.setMaximum(len(freq_list))
        self.progressbar.setValue(0)
        self.toggle_serial_interface(False)
        self.terminal_msg(
            f'Передача данных в диапазоне {freq_list[0]} - '
            f'{ceil(freq_list[-1])} с шагом '
            f'{round(self.step_spinbox.value(), 2)}'
        )

        factory_number = self.fnumber_lineedit.text()
        device_model = self.devicemodel_combobox.currentText()
        series = self.series_combobox.currentText()
        user = settings.OPERATOR
        self.create_tab(
            factory_number=factory_number,
            device_model=device_model,
            series=series,
            user=user,
            )
        self.serial_manager.start_data_transfer(freq_list)

    def stop_transfer(self):
        """Остановка передачи данных."""
        self.startstop_button.setIcon(set_icon('icons/start.png'))
        self.toggle_serial_interface(True)
        self.terminal_msg('Передача данных завершена')
        self.serial_manager.stop_data_transfer()
        self.plot_update_timer.stop()

        # Если отрисовка в режиме реального времени
        # отключена, то отрисовываем график при завершении
        # передачи данных.
        if settings.REAL_TIME_CHART is False:
            self.plot_update_worker.draw(self.plottab)
        # не красиво, попробовать переделать
        try:
            self.plot_update_timer.disconnect()
        except TypeError:
            pass

        # Производим расчет параметров и обновляем данные записи
        index = self.tabwidget.currentIndex()
        page = self.tabwidget.widget(index)
        plottab = self.storage.get(page)
        stat = calc_stat(plottab.data)
        if stat:
            plottab.record.frequency = stat['F']
            plottab.record.resistance = stat['R']
            plottab.record.quality_factor = stat['Q']
            plottab.record.composition = (
                self.composition_combobox.currentText())
            plottab.label_frequency.setText(f"F = {stat['F']} Гц")
            plottab.label_resistance.setText(f"R = {stat['R']} Ом")
            plottab.label_quality_factor.setText(f"Q = {stat['Q']}")
            plottab.label_composition.setText(
                f"Сборка - {plottab.record.composition}")

    def create_tab(self, factory_number: str, series: str, device_model: str, user: str):  # noqa
        """Создает новую вкладку QTabwidget и соответствующий объект с
        графиками. Устанавливает связь между получением данных от
        COM-порта и методом объекта plottab."""
        record = Record(
            series=series,
            device_model=device_model,
            user=user,
            factory_number=factory_number,
            temporary=self.temporary,
        )

        self.plottab = PlotTab(
            tabwidget=self.tabwidget,
            record=record,
        )

        self.serial_manager.signal_send_data.connect(self.plottab.get_data)
        # Если отключена функция отрисовки в режиме реального времени, то
        # не включаем таймеры отрисовки графика.
        if settings.REAL_TIME_CHART is True:
            self.plot_update_timer.setInterval(int(1000 / settings.FPS))
            self.plot_update_timer.timeout.connect(lambda: self.plot_update_worker.draw(self.plottab))  # noqa
            self.plot_update_timer.start()

        date_str = record.date.strftime('%H:%M:%S')
        if self.temporary:
            tab_title = f'{date_str} - временная запись'
        else:
            tab_title = f'{date_str} - {factory_number}'
        self.tabwidget.addTab(self.plottab.page, tab_title)
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
            return True
        except KeyError:
            # self.terminal_msg(
            #     'Не удалось удалить запись из локального хранилища.'
            # )
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
            # self.devicemodel_combobox.setEnabled(False)
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
            return
        series: str = self.db.get_series_by_fnumber(
            factory_number=factory_number)
        device_model: str = self.db.get_device_model_title_by_fnumber(
            factory_number=factory_number)
        print(series, device_model)
        if series is None or device_model is None:
            return
        index: int = self.series_combobox.findText(series)
        self.series_combobox.setCurrentIndex(index)
        index: int = self.devicemodel_combobox.findText(device_model)
        self.devicemodel_combobox.setCurrentIndex(index)

    @pyqtSlot()
    def settings_button_clicked(self) -> None:
        """Слот нажатия кнопки настроек. Открывает окно настроек
        и обновляет его актуальными списками пользователей и COM-портов."""
        if self.settings_window.isVisible():
            self.settings_window.hide()
            return
        serial_ports: list = self.serial_manager.get_available_port_names()
        self.settings_window.update_window_widgets(serial_ports)
        self.settings_window.show()

    @pyqtSlot()
    def compare_button_clicked(self) -> None:
        """Слот нажатия кнопки сравнения данных."""
        if not self.storage:
            return self.terminal_msg(
                'Для сравнения необходимо предварительно загрузить до '
                '10 записей из базы данных.'
            )
        if len(self.storage) > 10 or len(self.storage) < 2:
            return self.terminal_msg(
                'Для сравнения необходимо от 2 до 10 записей.'
            )
        records = [value.record for value in self.storage.values()]
        self.compare_mode_window: CompareModedWindow = CompareModedWindow(
            records, self.tabwidget)
        self.compare_mode_window.show()

    @pyqtSlot()
    def table_button_clicked(self) -> None:
        """Слот нажатия кнопки вывода таблицы базы данных."""
        if self.table_window.isVisible():
            self.table_window.hide()
            return
        self.table_window.update_tables()
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
            # self.devicemodel_combobox.setEnabled(True)
        else:
            self.temp_button.setIcon(set_icon('icons/temp_off.png'))
            self.label.setVisible(True)
            self.fnumber_lineedit.setVisible(True)
            self.search_model_by_fnumber()

    @pyqtSlot()
    def device_model_update(self) -> None:
        """Событие обновления combobox с серией аппарата."""
        self.devicemodel_combobox.clear()
        series = self.series_combobox.currentText()
        row_models = cts.DEVICE_MODELS.get(series)
        models = [item.get('name') for item in row_models]
        self.devicemodel_combobox.addItems(sorted(models))

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного."""
        # Запоминаем параметры перед закрытием
        settings.START_FREQUENCY = self.freq_spinbox.value()
        settings.RANGE = self.range_spinbox.value()
        settings.STEP = self.step_spinbox.value()

        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())

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
        current_time: str = datetime.now().time().strftime('%H:%M:%S')
        self.terminal.append(f'{current_time} - {message}')


if __name__ == '__main__':
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app: QApplication = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainwindow: MainWindow = MainWindow()
    mainwindow.show()
    app.exec()
