import sys
from datetime import datetime

import constants as cts
import qdarktheme
from config import settings
from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from models import DeviceModel, Record, User
from PyQt6 import QtGui, uic
from PyQt6.QtCore import QDate, QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (QApplication, QHeaderView, QMainWindow,
                             QTableWidgetItem, QTextBrowser, QWidget)
from serialport import MySerialPort
from widgets import CellCheckbox, EditToolButton


def terminal_msg(terminal: QTextBrowser, message: str) -> None:
    """Добавляем текущее время и текст в терминал."""
    current_time: datetime = datetime.now().time().strftime('%H:%M')
    terminal.append(f'{current_time} - {message}')


class EditRecordWindow(QWidget):
    """Окно редактирования записи БД."""
    edit_signal: pyqtSignal = pyqtSignal()

    def __init__(self, terminal: QTextBrowser, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/edit_record.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_edit.png'))
        self.setWindowTitle('Редактировать запись')
        self.record: Record = Record()
        self.terminal: QTextBrowser = terminal
        self.init_signals()

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.save_button.clicked.connect(self.save_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def show_window(self, record_id: str) -> None:
        """Делает окно видимым и заполняет виджеты данными
        указанной записи."""
        self.record: Record = Record.select().where(
            Record.id == record_id
        ).get_or_none()
        self.datetimeedit.setDateTime(self.record.date)
        self.factorynumber_lineedit.setText(self.record.factory_number)
        users: list = [user.username for user in User.select()]
        device_models: list = [model.title for model in DeviceModel.select()]
        self.user_combobox.clear()
        self.user_combobox.addItems(users)
        self.user_combobox.setCurrentText(self.record.user.username)
        self.devicemodel_combobox.clear()
        self.devicemodel_combobox.addItems(device_models)
        self.devicemodel_combobox.setCurrentText(
            self.record.device_model.title
        )
        self.comment_textedit.setText(self.record.comment)
        self.activateWindow()
        if not self.isVisible():
            self.show()

    @pyqtSlot()
    def save_button_clicked(self) -> None:
        """Слот нажатия кнопки сохранения редактированных данных."""
        title: str = self.devicemodel_combobox.currentText()
        device_model, created = DeviceModel.get_or_create(title=title)
        username: str = self.user_combobox.currentText()
        user: User = User.select().where(User.username == username).get()
        factory_number: str = self.factorynumber_lineedit.text()
        comment: str = self.comment_textedit.toPlainText()
        Record.update(
            {
                Record.device_model: device_model,
                Record.user: user,
                Record.factory_number: factory_number,
                Record.comment: comment,
            }
        ).where(Record.id == self.record.id).execute()
        self.edit_signal.emit()
        self.hide()
        terminal_msg(
            self.terminal,
            f'Запись (id={self.record.id}) была отредактирована. '
            'Изменения внесены в БД.'
        )

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены редактирования."""
        self.hide()


class FilterWindow(QWidget):
    """Окно фильтрация таблицы БД."""
    apply_filter_signal: pyqtSignal = pyqtSignal(dict)

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

    def update_widget(self) -> None:
        """Обновляем виджет при изменении настроек."""
        user: str = settings.OPERATOR
        index: int = self.user_combobox.findText(user)
        self.user_combobox.setCurrentIndex(index)

    def fill_widgets(self) -> None:
        """Заполняем виджеты данными."""
        users: list = [user.username for user in User.select()]
        device_models: list = [model.title for model in DeviceModel.select()]
        self.user_combobox.addItems(users)
        self.devicemodel_combobox.addItems(device_models)
        current_date: QDate = QDate.currentDate()
        self.dateedit_1.setDate(current_date)
        self.dateedit_2.setDate(current_date)
        self.user_checkbox.setChecked(True)
        user: str = settings.OPERATOR
        index: int = self.user_combobox.findText(user)
        self.user_combobox.setCurrentIndex(index)

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
        self.apply_filter_signal.emit(self.get_filter_settings())
        self.hide()

    @pyqtSlot()
    def cancel_button_clicked(self) -> None:
        """Слот нажатия кнопки отмены выбора параметров фильтрации."""
        self.hide()


class TableWindow(QWidget):
    """Таблица базы данных программы."""
    def __init__(self, terminal: QTextBrowser, *args, **kwargs) -> None:
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
        self.edit_record_window: EditRecordWindow = EditRecordWindow(
            self.terminal
        )

        self.init_style()
        self.init_signals()

        self.selected_records: list = []  # Выбранные пользователем записи

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
        self.edit_record_window.edit_signal.connect(
            lambda: self.load_data(self.filter_window.get_filter_settings())
        )
        self.search_edit.returnPressed.connect(self.search_button_clicked)

    def set_color_to_row(self, row_index: int, color: QtGui.QColor) -> None:
        """Задаем цвет заданной строки таблицы."""
        for i in range(self.table.columnCount()):
            item: QTableWidgetItem = self.table.item(row_index, i)
            if item is not None:
                item.setBackground(color)

    def load_data(self, filter_settings: dict = None, search: str = None) -> None:  # noqa
        """Загружаем данные из БД и обновляем таблицу."""
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ['id', '', 'Дата', 'Пользователь', 'Комментарий', '']
        )
        self.table.setColumnHidden(0, True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()  # ATTENTION
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.selected_records: list = []
        factory_numbers: list = []
        all_records: list = []
        if search is None:
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
                date_1: datetime = filter_settings.get('date')[0].toPyDate()
                date_2: datetime = filter_settings.get('date')[1].toPyDate()
                all_records = all_records.where(
                    Record.date.between(date_1, date_2)
                )
            all_records = all_records.limit(settings.DISPLAY_RECORDS)

            for record in all_records.order_by(Record.date):
                if record.factory_number not in factory_numbers:
                    factory_numbers.append(record.factory_number)
        else:
            search_record: list = Record.select().where(
                Record.factory_number == search
            )
            if search_record:
                all_records = search_record
                factory_numbers.append(search)
            else:
                return
        self.records_count.setText(f'Записей - {all_records.count()}')
        color_flag: bool = False
        gray: QtGui.QColor = QtGui.QColor(128, 128, 128)
        lightslategray: QtGui.QColor = QtGui.QColor(119, 136, 153)
        row: int = 0  # Текущая строка таблицы
        for factory_number in factory_numbers:
            color: QtGui.QColor = None
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
            self.table.setSpan(rowposition, 0, 1, 6)
            self.set_color_to_row(rowposition, color)

            for record in records:
                self.table.insertRow(self.table.rowCount())
                # Скрытая ячейка с id записи
                item = QTableWidgetItem(str(record.id))
                self.table.setItem(row, 0, item)
                # Ячейка с checkbox
                checkboxwidget = CellCheckbox(self, str(record.id))
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
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, item)
                # Ячейка с комментарием
                item = QTableWidgetItem(record.comment)
                item.setFlags(flag_selectable_enabled)
                self.table.setItem(row, 4, item)
                self.set_color_to_row(row, color)
                # Ячейка с иконкой изменения
                item = QTableWidgetItem()
                edit_button = EditToolButton(self, str(record.id))
                item.setFlags(flag_selectable_enabled)
                self.table.setItem(row, 5, item)
                self.table.setCellWidget(row, 5, edit_button)
                self.set_color_to_row(row, color)
                row += 1
            color_flag = not color_flag

    @pyqtSlot()
    def edit_record(self, record_id):
        """Слот редактирования записи из таблицы."""
        self.edit_record_window.show_window(record_id)

    @pyqtSlot(QModelIndex)
    def table_double_clicked(self, index) -> None:
        """Слот двойного щелчка мыши по таблице. Меняет статус QCheckbox."""
        ch_item = self.table.cellWidget(index.row(), 1)
        if isinstance(ch_item, CellCheckbox):
            if ch_item.checkbox.isChecked():
                ch_item.checkbox.setChecked(False)
            else:
                ch_item.checkbox.setChecked(True)

    @pyqtSlot()
    def checkbox_change_state(self, checkbox, record_id) -> None:
        """Слот изменения статуса QCheckbox в таблицу. Если статус меняется,
        то соответствующим образом меняется список выбранных записей."""
        if checkbox.isChecked():
            self.selected_records.append(record_id)
        else:
            self.selected_records.remove(record_id)

    @pyqtSlot()
    def open_button_clicked(self) -> None:
        """Слот нажатия кнопки выгрузки данных."""
        if not self.selected_records:
            return
        print('Open button is clicked!')
        print('Выгружаем данные', self.selected_records)
        self.hide()

    @pyqtSlot()
    def delete_button_clicked(self) -> None:
        """Слот нажатия кнопки удаления данных. Удаляет записи из БД и
        отправляет сообщение в терминал."""
        if not self.selected_records:
            return
        Record.delete().where(
            Record.id.in_(self.selected_records)
        ).execute()
        terminal_msg(
            self.terminal,
            f'Из базы данных удалено {len(self.selected_records)} записей.'
        )
        self.load_data(self.filter_window.get_filter_settings())

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
        factory_number = self.search_edit.text()
        self.load_data(
            self.filter_window.get_filter_settings(), factory_number
        )

    @pyqtSlot()
    def closeEvent(self, event):  # noqa
        """Закрываем дополнительные окна при закрытии основного."""
        if self.filter_window:
            self.filter_window.close()
        if self.edit_record_window:
            self.edit_record_window.close()


class SettingsWindow(QWidget):
    """Окно настроек программы."""
    change_settings_signal = pyqtSignal()

    def __init__(self, terminal, serial, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi('forms/settings.ui', self)
        self.setWindowIcon(QtGui.QIcon('icons/logo_settings.png'))
        self.setWindowTitle('Настройки')
        self.terminal: QTextBrowser = terminal
        self.serial = serial
        users = [user.username for user in User.select()]
        self.combobox_user.addItems(users)
        user = settings.OPERATOR
        index = self.combobox_user.findText(user)
        self.combobox_user.setCurrentIndex(index)
        self.disp_records_spinbox.setValue(settings.DISPLAY_RECORDS)
        self.lineedit_dbname.setText(settings.DB_NAME)
        self.lineedit_dbuser.setText(settings.DB_USER)
        self.lineedit_dbpassword.setText(settings.DB_PASSWORD)
        self.lineedit_dbhost.setText(settings.DB_HOST)
        self.spinbox_port.setValue(settings.DB_PORT)
        self.checkbox_bugreport.setChecked(settings.BUG_REPORT)
        serial_ports = self.serial.get_serial_ports_list()
        self.combobox_serialport.addItems(serial_ports)
        index = self.combobox_serialport.findText(settings.COM_PORT)
        self.combobox_serialport.setCurrentIndex(index)
        self.button_save.clicked.connect(self.save_button_clicked)

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
        data: dict = settings.as_dict()
        loaders.write('settings.toml', DynaBox(data).to_dict())
        terminal_msg(self.terminal, 'Настройки программы сохранены')
        self.serial.check_serial_port(settings.COM_PORT)
        self.change_settings_signal.emit()
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
        self.setStyleSheet(cts.STYLESHEET_LIGHT)

        self.init_serial_port()
        # self.toggle_serial_interface(False)

        self.data_transfer: bool = False
        self.settings_window: SettingsWindow = SettingsWindow(
            self.terminal,
            self.serial,
        )
        self.table_window: TableWindow = TableWindow(self.terminal)

        self.init_signals()
        self.fill_widgets()

    def init_serial_port(self) -> None:
        """Настраиваем COM-порт, проверяем доступность последнего
        сохраненного порта."""
        self.serial = MySerialPort()
        self.serial.signal_serial_port.connect(
            self.toggle_serial_interface
        )
        self.serial.check_serial_port(settings.COM_PORT)

    def init_signals(self) -> None:
        """Подключаем сигналы к слотам."""
        self.settings_button.clicked.connect(self.settings_button_clicked)
        self.startstop_button.clicked.connect(self.startstop_button_clicked)
        self.compare_button.clicked.connect(self.compare_button_clicked)
        self.table_button.clicked.connect(self.table_button_clicked)
        self.settings_window.change_settings_signal.connect(
            self.table_window.filter_window.update_widget
        )
        self.fnumber_lineedit.textChanged.connect(
            self.search_model_for_fnumber
        )

    def fill_widgets(self) -> None:
        """Заполняем виджеты главного окна."""
        self.fnumber_lineedit.setText(
            settings.PREVIOUS_FACTORY_NUMBER
        )
        self.devicemodel_combobox.setCurrentText(
            settings.PREVIOUS_DEVICE_MODEL
        )

    @pyqtSlot()
    def search_model_for_fnumber(self) -> None:
        """Слот для подбора модели аппарата из БД под заданный
        заводской номер."""
        factory_number = self.fnumber_lineedit.text()
        record = Record.select().where(
            Record.factory_number == factory_number
        ).get_or_none()
        if record is None:
            self.devicemodel_combobox.setCurrentText('')
            return
        device_model = record.device_model.title
        self.devicemodel_combobox.setCurrentText(device_model)

    @pyqtSlot()
    def settings_button_clicked(self) -> None:
        """Слот нажатия кнопки настроек. Открывает окно настроек."""
        if self.settings_window.isVisible():
            self.settings_window.hide()
            return
        self.settings_window.show()

    def toggle_serial_interface(self, status=False) -> None:
        """Меняем состояние интерфейса передачи данных."""
        if status is False:
            self.startstop_button.setIcon(QtGui.QIcon('icons/recycling'))
            self.serial.close()
        else:
            self.startstop_button.setIcon(QtGui.QIcon('icons/start'))
        self.fnumber_lineedit.setEnabled(status)
        self.devicemodel_combobox.setEnabled(status)
        self.freq_spinbox.setEnabled(status)
        self.range_spinbox.setEnabled(status)
        self.step_spinbox.setEnabled(status)

    @pyqtSlot()
    def startstop_button_clicked(self) -> None:
        """Слот нажатия кнопки пуска/остановки приема данных."""
        self.data_transfer = not self.data_transfer
        if self.data_transfer is True:
            self.startstop_button.setIcon(QtGui.QIcon('icons/stop.png'))
            print('Start button is clicked!')

            # self.serial.check_serial_port(settings.COM_PORT)
            return
        self.startstop_button.setIcon(QtGui.QIcon('icons/start.png'))
        print('Stop button is clicked!')
        self.serial.close()

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
        """Закрываем дополнительные окна при закрытии основного."""
        if self.settings_window:
            self.settings_window.close()
        if self.table_window:
            self.table_window.close()


if __name__ == '__main__':
    """Основная программа - создаем основные объекты и запускаем приложение."""
    app = QApplication(sys.argv)

    qdarktheme.setup_theme()
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec()
