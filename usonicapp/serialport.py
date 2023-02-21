import math
import struct
from collections import defaultdict
from decimal import Decimal

import constants as cts
from config import settings
from PyQt5.QtCore import QIODevice, QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


class SerialPortManager(QObject):
    """Вспомогательный класс для работы с COM портом."""
    signal_port_checked = pyqtSignal(bool)
    signal_send_point = pyqtSignal(dict)
    signal_calibration_response = pyqtSignal()
    signal_stop_data_transfer = pyqtSignal()
    signal_transfer_progress_change = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.serial = QSerialPort()
        self.serial.setBaudRate(115200)
        self.serial.readyRead.connect(self.read_data)

        self.factory_number = None
        self.calibration = None
        self.serial_port = settings.COM_PORT
        self.transfer_status = False
        self.current_freq = None
        self.freq_list = []
        self.attempts_number = 0

    def init_timers(self) -> None:
        """Настройка и запуск таймеров."""
        self.check_connection_timer = QTimer()
        self.check_connection_timer.setInterval(cts.TIMER_CHECK_SERIAL_PORT)
        self.check_connection_timer.timeout.connect(self.check_serial_port)
        self.check_connection_timer.start()

        self.response_serial_port_timer = QTimer()
        self.response_serial_port_timer.setInterval(cts.TIMER_RESPONSE)
        self.response_serial_port_timer.timeout.connect(
            self.no_response_serial_port)

        self.data_receive_timer = QTimer()
        self.data_receive_timer.setInterval(cts.TIMER_DATA_RECEIVE)
        self.data_receive_timer.timeout.connect(self.reconnection)

    @staticmethod
    def get_serial_ports_list() -> list:
        """Возвращает список активных COM-портов."""
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        return [port.portName() for port in serial_list]

    @staticmethod
    def create_tasks(data) -> list:
        """Обработка входящих данных."""
        tasks = defaultdict(list)
        for command, length in cts.COMMANDS.items():
            while True:
                index = data.find(command)
                if index == -1:
                    break
                start = index + len(command)
                end = index + length + len(command)
                tasks[command].append(data[start:end])
                data = data[:index] + data[end:]
        return tasks

    @pyqtSlot()
    def check_serial_port(self) -> None:
        """Запрос проверки связи для COM порта."""
        # Проверка изменения выбора порта в настройках
        if self.serial_port != settings.COM_PORT:
            if self.serial.isOpen() is True:
                self.serial.close()
            self.serial_port = settings.COM_PORT
        # Открываем порт, если он был закрыт
        if self.serial.isOpen() is False:
            self.serial.setPortName(settings.COM_PORT)
            self.serial.open(QIODevice.ReadWrite)
        # Если ошибок нет, запускам таймер для ожидания ответа от порта
        if self.serial.error() == self.serial.SerialPortError.NoError:
            self.serial.write(cts.CONNECTION_CHECK)
            self.response_serial_port_timer.start()
        else:
            # Отправляем сигнал о недоступности порта
            self.serial.clearError()
            self.serial.close()
            self.signal_port_checked.emit(False)

    @pyqtSlot()
    def no_response_serial_port(self) -> None:
        """COM-порт не отвечает."""
        self.signal_port_checked.emit(False)

    def get_transfer_status(self) -> bool:
        """Возвращает текущий статус передачи данных."""
        return self.transfer_status

    def toggle_transfer_status(self) -> None:
        """Меняет статус передачи данных на обратный."""
        self.transfer_status = not self.transfer_status

    @pyqtSlot()
    def reconnection(self) -> None:
        """Попытка повторной отправки данных, если COM-порт не
        отвечает."""
        if self.attempts_number < cts.ATTEMPTS_MAXIMUM:
            print(
                'Устройство не отвечает, попытка переподключения '
                f'- {self.attempts_number + 1}.'
            )
            self.attempts_number += 1
            self.send_data(False)
        else:
            print('Устройство не отвечает. Завершение передачи данных')
            self.attempts_number = 0
            self.data_receive_timer.stop()
            self.stop_data_transfer()

    def start_data_transfer(self, freq_list) -> None:
        """Начало процесса передачи данных."""
        self.check_connection_timer.stop()
        self.response_serial_port_timer.stop()

        self.current_freq = freq_list[0]
        self.freq_list = freq_list
        self.calibration_request()

    def stop_data_transfer(self) -> None:
        """Завершение процесса передачи данных."""
        self.data_receive_timer.stop()
        self.check_connection_timer.start()

    def calibration_request(self) -> None:
        """Запрос калибровок."""
        self.serial.write(cts.CALIBRATION)

    def send_data(self, modify: bool = True) -> None:
        """Отправка данных на COM-порт."""
        if modify is True:
            self.current_freq: int = int(self.freq_list[0] * 100)  # не точно
            self.freq_list.pop(0)
        self.serial.write(
            cts.DATA + struct.pack('<i', self.current_freq)
        )
        self.data_receive_timer.start(cts.TIMER_DATA_RECEIVE)

    # Возможно использовать декоратор, но проверить тип посылки
    def read_data(self):
        """Слот, отвечающий за чтение и обработку поступюащих даееых."""
        rdata = self.serial.readAll()
        tasks = self.create_tasks(rdata.data())
        for command, data_list in tasks.items():
            for data in data_list:
                if command == cts.CONNECTION_CHECK:
                    self.serial_port = self.serial.portName()
                    self.factory_number = int.from_bytes(
                        data[:1],
                        byteorder='little',
                    )
                    self.response_serial_port_timer.stop()
                    self.signal_port_checked.emit(True)
                elif ((command == cts.DATA) and (self.transfer_status)):
                    self.attempts_number = 0
                    self.data_receive_timer.stop()
                    received_data = {
                        'Vphl': int.from_bytes(data[0:2], byteorder='little'),
                        'VdBI': int.from_bytes(data[2:4], byteorder='little'),
                        'VphU': int.from_bytes(data[4:6], byteorder='little'),
                        'VdBU': int.from_bytes(data[6:8], byteorder='little'),
                        'Vref': int.from_bytes(data[8:10], byteorder='little'),
                        'VI': int.from_bytes(data[10:12], byteorder='little'),
                    }
                    result = self.calc_data(received_data, self.calibration)
                    result['f'] = self.current_freq / 100
                    self.signal_transfer_progress_change.emit(
                        len(self.freq_list)
                    )
                    self.signal_send_point.emit(result)
                    if not self.freq_list:
                        self.signal_stop_data_transfer.emit()
                    else:
                        self.send_data()
                elif command == cts.CALIBRATION:
                    self.calibration = int.from_bytes(
                        data[0:2],
                        byteorder='little'
                    )
                    self.calibration = self.calibration / 1000
                    self.send_data()
                elif command == cts.VOLTAGE:
                    pass
                else:
                    print('Неизвестная команда.')

    @staticmethod
    def calc_data(data, calibration) -> dict:
        """Расчет параметров на основе данных от COM-порта."""
        vphi: Decimal = data.get('Vphl')
        vdbi: Decimal = data.get('VdBI')
        vphu: Decimal = data.get('VphU')
        vdbu: Decimal = data.get('VdBU')
        vref: Decimal = data.get('Vref')
        vi: Decimal = data.get('VI')
        calibration = calibration / 100

        z = (calibration * pow(10, (((vdbu - vref / 2) - (vdbi - vref / 2)) / 600)))  # noqa
        ph = (vphi/10 - vphu/10)
        r = z * math.cos(math.radians(ph))
        x = z * math.sin(math.radians(ph))
        i = cts.INDEX_I * pow(10, ((vi - 2500) / 480))
        u = cts.INDEX_U * pow(10, ((vdbu - (vref / 2)) / 600))

        keys = ('calibration', 'z', 'r', 'x', 'ph', 'i', 'u')
        values = (
            calibration,
            round(Decimal(z), 2),
            round(Decimal(r), 2),
            round(Decimal(x), 2),
            round(Decimal(ph), 2),
            round(Decimal(i), 8),
            round(Decimal(u), 2),
        )
        return dict(zip(keys, values))
