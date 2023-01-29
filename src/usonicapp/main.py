import sys
from datetime import datetime
from typing import List

import constants as cts
import qdarktheme
from config import settings
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from models import DeviceModel, Record, User
from PyQt6 import QtGui, uic
from PyQt6.QtCore import QDate, QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QHeaderView,
                             QMainWindow, QTableWidgetItem, QTextBrowser,
                             QWidget)


def terminal_msg(terminal: QTextBrowser, message) -> None:
    """Добавляем текущее время и текст в терминал."""
    current_time = datetime.now().time().strftime('%H-%M-%S')
    terminal.append(f'{current_time}: {message}')


class CellCheckbox(QWidget):
    """Класс, описывающий виджет QcheckBox, с выравниваем и без отступов."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkbox = QCheckBox()
        layout = QHBoxLayout(self)
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)


class FilterWindow(QWidget):
    """Окно фильтрация таблицы БД."""
    apply_filter_signal = pyqtSignal(dict)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/filter.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_filter.png'))
        self.setWindowTitle('Фильтрация')
        self.init_signals()
        self.fill_widgets()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.apply_button.clicked.connect(self.apply_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def fill_widgets(self) -> None:
        """Заполняем виджеты данными."""
        users = [user.username for user in User.select()]
        device_models = [model.title for model in DeviceModel.select()]
        self.user_combobox.addItems(users)
        self.devicemodel_combobox.addItems(device_models)
        current_date = QDate.currentDate()
        self.dateedit_1.setDate(current_date)
        self.dateedit_2.setDate(current_date)
        self.user_checkbox.setChecked(True)
        user = settings.OPERATOR
        index = self.user_combobox.findText(user)
        self.user_combobox.setCurrentIndex(index)

    def get_filter_settings(self) -> dict:
        """Возвращает текущие параметры фильтрации."""
        result = {}
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
        self.apply_filter_signal.emit(self.get_filter_settings())
        self.hide()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены выбора параметров фильтрации."""
        self.hide()


class TableWindow(QWidget):
    """Таблица базы данных программы."""
    def __init__(self, terminal, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/table.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_table.png'))
        self.setWindowTitle('База данных')
        self.terminal: QTextBrowser = terminal
        self.open_button.setIcon(QtGui.QIcon('icons/load.png'))
        self.update_button.setIcon(QtGui.QIcon('icons/update.png'))
        self.filter_button.setIcon(QtGui.QIcon('icons/filter.png'))
        self.search_button.setIcon(QtGui.QIcon('icons/search.png'))
        self.delete_button.setIcon(QtGui.QIcon('icons/delete.png'))

        self.filter_window: FilterWindow = FilterWindow()

        self.init_style()
        self.init_signals()

    def init_style(self) -> None:
        """Подключаем пользовательские стили."""
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.open_button.clicked.connect(self.open_button_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)
        self.update_button.clicked.connect(self.update_button_clicked)
        self.filter_button.clicked.connect(self.filter_button_clicked)
        self.search_button.clicked.connect(self.search_button_clicked)
        self.table.doubleClicked.connect(self.table_double_clicked)
        self.filter_window.apply_filter_signal.connect(self.load_data)

    def set_color_to_row(self, row_index, color) -> None:
        """Задаем цвет заданной строки таблицы."""
        for i in range(self.table.columnCount()):
            item = self.table.item(row_index, i)
            if item is not None:
                item.setBackground(color)

    def load_data(self, filter_settings=None) -> None:
        """Загружаем данные из БД и обновляем таблицу."""
        all_records = Record.select()

        if (filter_settings) and ('user' in filter_settings):
            user = User.select().where(
                User.username == filter_settings.get('user')
            )
            all_records = all_records.where(Record.user == user)
        if (filter_settings) and ('devicemodel' in filter_settings):
            device_model = DeviceModel.select().where(
                DeviceModel.title == filter_settings.get('devicemodel')
            )
            all_records = all_records.where(
                Record.device_model == device_model
            )
        if (filter_settings) and ('date' in filter_settings):
            date_1 = filter_settings.get('date')[0].toPyDate()
            date_2 = filter_settings.get('date')[1].toPyDate()
            all_records = all_records.where(
                Record.date.between(date_1, date_2)
            )

        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ['id', '', 'Дата', 'Пользователь', 'Комментарий']
        )
        self.table.setColumnHidden(0, True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        factory_numbers: List[str] = []
        for record in all_records.order_by(Record.date):
            if record.factory_number not in factory_numbers:
                factory_numbers.append(record.factory_number)

        color_flag = False
        gray = QtGui.QColor(128, 128, 128)
        lightslategray = QtGui.QColor(119, 136, 153)
        row: int = 0  # Текущая строка таблицы
        for factory_number in factory_numbers:
            color = None
            if color_flag:
                color = gray
            else:
                color = lightslategray

            flag_selectable_enabled = (
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            records = all_records.where(
                Record.factory_number == factory_number
            )
            rowposition: int = self.table.rowCount()
            self.table.insertRow(rowposition)
            row += 1
            # Объединяем ячейки и выводим номер аппарата и модель
            item = QTableWidgetItem(
                f'{records[0].factory_number} - '
                f'{records[0].device_model.title}'
            )
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(rowposition, 0, item)
            self.table.setSpan(rowposition, 0, 1, 5)
            self.set_color_to_row(rowposition, color)

            for record in records:
                self.table.insertRow(self.table.rowCount())
                # Скрытая ячейка с id записи
                item = QTableWidgetItem(str(record.id))
                self.table.setItem(row, 0, item)
                # Ячейка с checkbox
                checkboxwidget = CellCheckbox()
                self.table.setCellWidget(row, 1, checkboxwidget)
                item = QTableWidgetItem()
                self.table.setItem(row, 1, item)
                # Ячейка с датой и временем
                item = QTableWidgetItem(
                    record.date.strftime('%m-%d-%Y %H:%M')
                )
                item.setFlags(flag_selectable_enabled)
                self.table.setItem(row, 2, item)
                # Ячейка с именем пользователя
                item = QTableWidgetItem(record.user.username)
                item.setFlags(flag_selectable_enabled)
                self.table.setItem(row, 3, item)
                # Ячейка с комментарием
                item = QTableWidgetItem(record.comment)
                item.setFlags(flag_selectable_enabled)
                self.table.setItem(row, 4, item)
                self.set_color_to_row(row, color)
                row += 1
            color_flag = not color_flag

    @pyqtSlot(QModelIndex)
    def table_double_clicked(self, index) -> None:
        """Слот двойного щелчка мыши по таблице. Меняет статус QCheckbox."""
        row = index.row()
        item = self.table.cellWidget(row, 1)
        if isinstance(item, CellCheckbox):
            if item.checkbox.isChecked():
                item.checkbox.setChecked(False)
            else:
                item.checkbox.setChecked(True)

    @pyqtSlot()
    def open_button_clicked(self) -> None:
        """Слот нажатия кнопки выгрузки данных."""
        print('Open button is clicked!')

    @pyqtSlot()
    def delete_button_clicked(self) -> None:
        """Слот нажатия кнопки удаления данных."""
        print('Delete button is clicked!')

    @pyqtSlot()
    def update_button_clicked(self) -> None:
        """Слот нажатия кнопки обновления таблицы."""
        self.load_data(self.filter_window.get_filter_settings())

    @pyqtSlot()
    def filter_button_clicked(self) -> None:
        """Слот нажатия кнопки фильтрации данных. Открывает отдельное окно."""
        if self.filter_window.isVisible():
            self.filter_window.hide()
            return
        self.filter_window.show()

    @pyqtSlot()
    def search_button_clicked(self) -> None:
        """Слот нажатия кнопки поиска записи."""
        print('Search button is clicked!')

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного.

        Args:
            event (Event): Событие закрытия главного окна.
        """
        if self.filter_window:
            self.filter_window.close()


class SettingsWindow(QWidget):
    """Окно настроек программы."""
    def __init__(self, terminal, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/settings.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_settings.png'))
        self.setWindowTitle('Настройки')
        self.terminal: QTextBrowser = terminal

        users = [user.username for user in User.select()]
        self.combobox_user.addItems(users)
        user = settings.OPERATOR
        index = self.combobox_user.findText(user)
        self.combobox_user.setCurrentIndex(index)
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
        settings.OPERATOR = self.combobox_user.currentText()
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
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/mainwindow.ui', self)
        self.centralwidget.setContentsMargins(6, 6, 6, 6)
        self.setWindowIcon(QtGui.QIcon('icons/logo_main.png'))
        self.setWindowTitle('Usonic App')
        self.startstop_button.setIcon(QtGui.QIcon('icons/start.png'))
        self.settings_button.setIcon(QtGui.QIcon('icons/settings.png'))
        self.compare_button.setIcon(QtGui.QIcon('icons/compare.png'))
        self.table_button.setIcon(QtGui.QIcon('icons/table.png'))
        self.select_button.setIcon(QtGui.QIcon('icons/select.png'))

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

        self.table_window.filter_window.apply_filter_signal.emit(
            self.table_window.filter_window.get_filter_settings()
        )
        self.table_window.show()

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного.

        Args:
            event (Event): Событие закрытия главного окна.
        """
        if self.settings_window:
            self.settings_window.close()
        if self.table_window:
            self.table_window.close()


def main() -> None:
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec()


if __name__ == '__main__':
    main()
