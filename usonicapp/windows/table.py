from typing import Dict, List, Union

from PyQt5 import uic
from PyQt5.QtCore import (QModelIndex, QSize, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QCheckBox, QHeaderView, QTableWidget, QTableWidgetItem, QWidget)
from peewee import PostgresqlDatabase, SqliteDatabase

import constants as cts
from database import DataBase
from models import Record
from utils import get_form_path, get_icon
from windows.edit_record import EditRecordWindow
from windows.filter import FilterWindow


class TableWindow(QWidget):
    """Таблица базы данных программы."""

    terminal_signal: pyqtSignal = pyqtSignal(str)
    download_records_signal: pyqtSignal = pyqtSignal(list)

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
        uic.loadUi(get_form_path('table.ui'), self)
        self.setWindowIcon(get_icon('logo_table.png'))
        self.setWindowTitle('База данных')
        self.tabwidget.setTabIcon(0, get_icon('remote_server.png'))
        self.tabwidget.setTabIcon(1, get_icon('local_server.png'))
        self.tabwidget.setIconSize(QSize(20, 20))
        self.open_button.setIcon(get_icon('load.png'))
        self.update_button.setIcon(get_icon('update.png'))
        self.filter_button.setIcon(get_icon('filter.png'))
        self.search_button.setIcon(get_icon('search.png'))
        self.delete_button.setIcon(get_icon('delete.png'))
        self.temp_button.setIcon(get_icon('temp_off.png'))
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

    def init_windows(self) -> None:
        """Инициализация дополнительных окон."""
        self.pg_filter_window: FilterWindow = FilterWindow(self.db)
        self.sqlite_filter_window: FilterWindow = FilterWindow(self.db)
        self.edit_record_window: EditRecordWindow = EditRecordWindow(self.db)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.open_button.clicked.connect(self.download_button_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)
        self.update_button.clicked.connect(self.update_button_clicked)
        self.filter_button.clicked.connect(self.filter_button_clicked)
        self.search_button.clicked.connect(self.search_button_clicked)
        self.sqlite_table.doubleClicked.connect(self.item_double_clicked)
        self.pg_table.doubleClicked.connect(self.item_double_clicked)
        self.temp_button.clicked.connect(self.temp_button_clicked)
        self.pg_filter_window.apply_filter_signal.connect(
            lambda: self.load_data(  # type: ignore
                table=self.tabwidget.findChild(QTableWidget, cts.PG_TABLE)
            )
        )
        self.sqlite_filter_window.apply_filter_signal.connect(
            lambda: self.load_data(  # type: ignore
                self.tabwidget.findChild(QTableWidget, cts.SQLITE_TABLE)
            )
        )
        self.edit_record_window.edit_signal.connect(self.load_data)  # type: ignore
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
                item = QTableWidgetItem(str(record.id))
                table.setItem(row, 0, item)
                # Ячейка с checkbox
                checkboxwidget: CellCheckbox = CellCheckbox(
                    self, str(record.id)
                )
                table.setCellWidget(row, 1, checkboxwidget)
                item = QTableWidgetItem()
                table.setItem(row, 1, item)
                # Ячейка с датой и временем
                item = QTableWidgetItem(
                    record.date.strftime('%m-%d-%Y %H:%M')
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 2, item)
                # Ячейка с именем пользователя
                item = QTableWidgetItem(
                    record.user.username
                )
                item.setFlags(flag_selectable_enabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 3, item)
                # Ячейка с комментарием
                item = QTableWidgetItem(record.comment)
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 4, item)
                self.set_color_to_row(table, row, color)
                # Ячейка с иконкой изменения
                item = QTableWidgetItem()
                edit_button: EditToolButton = EditToolButton(
                    self.edit_record_window, table, db, str(record.id)
                )
                item.setFlags(flag_selectable_enabled)
                table.setItem(row, 5, item)
                table.setCellWidget(row, 5, edit_button)
                self.set_color_to_row(table, row, color)
                row += 1
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
        self.download_records_signal.emit(records)
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
        self.update_tables()
        if self.temporary:
            self.temp_button.setIcon(get_icon('temp_on.png'))
        else:
            self.temp_button.setIcon(get_icon('temp_off.png'))

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного."""
        if self.pg_filter_window:
            self.pg_filter_window.close()
        if self.sqlite_filter_window:
            self.sqlite_filter_window.close()
        if self.edit_record_window:
            self.edit_record_window.close()
