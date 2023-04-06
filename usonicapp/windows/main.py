import json
from datetime import datetime
from decimal import Decimal

import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSlot, QTimer
from PyQt5.QtWidgets import QMainWindow

import constants as cts
from config import settings
from database import DataBase
from models import Record
from plottab import PlotUpdateWorker, PlotTab
from serialport import SerialPortManager, MeasuredValues
from utils import get_form_path, get_icon, get_pixmap
from windows.settings import SettingsWindow
from windows.table import TableWindow
from windows.upload import UploadWindow


class MainWindow(QMainWindow):
    """Основное окно программы."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi(get_form_path('main.ui'), self)
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
        self.setWindowIcon(get_icon('logo_main.png'))
        self.setWindowTitle('Usonic App')
        self.startstop_button.setIcon(get_icon('start.png'))
        self.settings_button.setIcon(get_icon('settings.png'))
        self.compare_button.setIcon(get_icon('compare.png'))
        self.table_button.setIcon(get_icon('table.png'))
        self.temp_button.setIcon(get_icon('temp_off.png'))
        self.upload_button.setIcon(get_icon('upload_false.png'))
        self.setStyleSheet(cts.STYLESHEET_LIGHT)
        self.fnumber_lineedit.setText(
            settings.PREVIOUS_FACTORY_NUMBER
        )
        self.devicemodel_combobox.addItems(self.db.get_models_pg())
        self.connect_pixmap = get_pixmap('connect.png')
        self.disconnect_pixmap = get_pixmap('disconnect.png')
        self.online_pixmap = get_pixmap('online.png')
        self.offline_pixmap = get_pixmap('offline.png')

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
        self.table_window.download_records_signal.connect(
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
            data = MeasuredValues(
                **json.loads(record.data.tobytes(), use_decimal=True)
            )
            self.plottab.set_data(data)
            self.plot_update_worker.draw(self.plottab)
            self.tabwidget.addTab(self.plottab.page, title)
            self.tabwidget.setCurrentIndex(self.tabwidget.count() - 1)
            self.storage[self.plottab.page] = self.plottab

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
        # freq_stop: Decimal = freq_list[-1]
        return freq_list

    @pyqtSlot(int)
    def toggle_upload_button_status(self, index) -> None:
        """Меняет состояние кнопки и иконку."""
        if index != -1:
            self.upload_button.setIcon(get_icon('upload_true.png'))
            self.upload_button.setEnabled(True)
        else:
            self.upload_button.setIcon(get_icon('upload_false.png'))
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
        self.upload_window.update_window_widgets(plottab.record, plottab.data, pg_db_status)
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
        self.startstop_button.setIcon(get_icon('stop.png'))
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
        self.startstop_button.setIcon(get_icon('start.png'))
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
        device_model = self.db.get_model_by_title(device_model_title)
        user = self.db.get_user_by_username(username)
        record = Record(
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
        self.plot_update_timer.setInterval(int(1000 / settings.FPS))
        self.plot_update_timer.timeout.connect(lambda: self.plot_update_worker.draw(self.plottab))  # noqa
        self.plot_update_timer.start()

        date_str = record.date.strftime('%H:%M:%S')
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
            self.startstop_button.setIcon(get_icon('start'))
        else:
            self.comport_label.setPixmap(self.disconnect_pixmap)
            self.startstop_button.setIcon(get_icon('start_disabled'))
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
        self.settings_window.update_window_widgets(users, serial_ports)
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
            self.temp_button.setIcon(get_icon('temp_on.png'))
            self.label.setVisible(False)
            self.fnumber_lineedit.setVisible(False)
            self.devicemodel_combobox.setEnabled(True)
        else:
            self.temp_button.setIcon(get_icon('temp_off.png'))
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
        current_time: str = datetime.now().time().strftime('%H:%M')
        self.terminal.append(f'{current_time} - {message}')
