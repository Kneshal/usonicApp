from __future__ import annotations

import math
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

import constants as cts
from config import settings
from PyQt5.QtCore import QIODevice, QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


@dataclass
class RawMeasuredValue:
    v_ph_i: Decimal
    v_db_i: Decimal
    v_ph_u: Decimal
    v_db_u: Decimal
    v_ref: Decimal
    v_i: Decimal


@dataclass
class MeasuredValue:
    calibration: Decimal
    f: Decimal
    z: Decimal
    r: Decimal
    x: Decimal
    ph: Decimal
    i: Decimal
    u: Decimal


@dataclass
class MeasuredValues:
    f: list = field(default_factory=list)
    z: list = field(default_factory=list)
    r: list = field(default_factory=list)
    x: list = field(default_factory=list)
    ph: list = field(default_factory=list)
    i: list = field(default_factory=list)
    u: list = field(default_factory=list)

    def add_value(self, value: MeasuredValue) -> None:
        """Добавляем новый набор значений к текущим спискам."""
        self.f.append(value.f)
        self.z.append(value.z)
        self.r.append(value.r)
        self.x.append(value.x)
        self.ph.append(value.ph)
        self.i.append(value.i)
        self.u.append(value.u)


def convert_bytes_to_decimal(value: bytes) -> Decimal:
    return Decimal(int.from_bytes(value, byteorder='little'))


class SerialPortManager(QObject):
    """Вспомогательный класс для работы с COM портом."""
    signal_port_checked = pyqtSignal(bool)
    signal_send_data = pyqtSignal(MeasuredValue)
    signal_calibration_response = pyqtSignal()
    signal_stop_data_transfer = pyqtSignal()
    signal_transfer_progress_change = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.serial: QSerialPort = QSerialPort()
        self.serial.setBaudRate(115200)
        self.serial.setStopBits(QSerialPort.StopBits.OneStop)
        self.serial.setParity(QSerialPort.Parity.NoParity)

        self.serial.readyRead.connect(self.read_data)

        self.factory_number = None
        self.calibration = None
        self.serial_port: str = settings.COM_PORT
        self.transfer_status: bool = False
        # self.current_freq = None
        self.start_freq = None
        self.freq_list: list = []
        self.attempts_number: int = 0

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

        self.settings_request_timer = QTimer()
        self.settings_request_timer.setInterval(cts.TIMER_SETTINGS_REQUEST)
        self.settings_request_timer.timeout.connect(
            self.close_serial_connection)

    @staticmethod
    def get_available_port_names() -> list[str]:
        """Возвращает список активных COM-портов."""
        return [port.portName() for port in QSerialPortInfo().availablePorts()]

    @staticmethod
    def create_tasks(data) -> dict:
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
    def close_serial_connection(self) -> None:
        self.settings_request_timer.stop()
        pass

    @pyqtSlot()
    def reconnection(self) -> None:
        """Попытка повторной отправки данных, если COM-порт не
        отвечает."""
        if self.attempts_number < cts.ATTEMPTS_MAXIMUM:
            self.attempts_number += 1
            print(
                'Устройство не отвечает, попытка переподключения '
                f'- {self.attempts_number}.'
            )
            self.send_data(False)
            return

        print('Устройство не отвечает. Завершение передачи данных')
        self.attempts_number = 0
        self.data_receive_timer.stop()
        self.stop_data_transfer()

    def start_data_transfer(self, freq_list) -> None:
        """Начало процесса передачи данных."""
        self.check_connection_timer.stop()
        self.response_serial_port_timer.stop()
        self.start_freq = freq_list[0]
        self.current_freq: int = freq_list[0]
        self.freq_list = freq_list
        self.set_voltage()
        # self.calibration_request()

    def stop_data_transfer(self) -> None:
        """Завершение процесса передачи данных."""
        self.data_receive_timer.stop()
        self.check_connection_timer.start()

    def calibration_request(self) -> None:
        """Запрос калибровок."""
        self.settings_request_timer.start(cts.TIMER_SETTINGS_REQUEST)
        self.serial.write(cts.CALIBRATION)

    def set_voltage(self) -> None:
        """Установка напряжения."""
        self.settings_request_timer.start(cts.TIMER_SETTINGS_REQUEST)
        self.serial.write(cts.VOLTAGE + struct.pack('@B', settings.VOLTAGE))
        # self.serial.waitForReadyRead(100)
        # self.serial.write(cts.VOLTAGE + struct.pack('<h', settings.VOLTAGE))

    def send_data(self, modify: bool = True) -> None:
        """Отправка данных на COM-порт."""
        if modify is True:
            self.current_freq = int(self.freq_list[0] * 100)  # не точно
            self.freq_list.pop(0)
        self.serial.write(
            cts.DATA + struct.pack('<i', self.current_freq)
        )
        self.data_receive_timer.start(cts.TIMER_DATA_RECEIVE)

    # Возможно использовать декоратор, но проверить тип посылки
    def read_data(self):
        """Слот, отвечающий за чтение и обработку поступающих данных."""
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

                    # Если это первая итерация передачи данных, то пропускаем
                    # ее из-за большого отклонения данных.
                    f = self.current_freq / 100
                    if self.start_freq == f:
                        return self.send_data()

                    received_data = RawMeasuredValue(
                        v_ph_i=convert_bytes_to_decimal(data[0:2]),
                        v_db_i=convert_bytes_to_decimal(data[2:4]),
                        v_ph_u=convert_bytes_to_decimal(data[4:6]),
                        v_db_u=convert_bytes_to_decimal(data[6:8]),
                        v_ref=convert_bytes_to_decimal(data[8:10]),
                        v_i=convert_bytes_to_decimal(data[10:12]),
                    )

                    measured_value = self.calc_data(
                        raw_values=received_data,
                        calibration=self.calibration,
                        f=f,
                    )
                    # Возможно проблема
                    self.signal_transfer_progress_change.emit(
                         len(self.freq_list)
                    )
                    self.signal_send_data.emit(measured_value)
                    if not self.freq_list:
                        self.signal_stop_data_transfer.emit()
                    else:
                        self.send_data()
                elif command == cts.VOLTAGE:
                    self.settings_request_timer.stop()
                    self.calibration_request()
                elif command == cts.CALIBRATION:
                    self.settings_request_timer.stop()
                    self.calibration = convert_bytes_to_decimal(data[0:2])/1000
                    self.send_data()
                else:
                    print('Неизвестная команда.')

    @staticmethod
    def calc_data(raw_values: RawMeasuredValue, calibration: Decimal, f: int) -> MeasuredValue:  # noqa
        """Расчет параметров на основе данных от COM-порта."""
        # calibration = calibration
        z = (calibration * pow(10, (((raw_values.v_db_u) - (raw_values.v_db_i))/695)))  # noqa
        # z = (calibration * pow(10, (((raw_values.v_db_u - raw_values.v_ref / 2) - (raw_values.v_db_i - raw_values.v_ref / 2)) / 600)))  # noqa
        ph = (raw_values.v_ph_i/10 - raw_values.v_ph_u/10)
        r = z * Decimal(math.cos(math.radians(ph)))
        x = z * Decimal(math.sin(math.radians(ph)))
        i = cts.INDEX_I * pow(10, ((raw_values.v_i - 2500) / 480))
        u = cts.INDEX_U * pow(10, ((raw_values.v_db_u - (raw_values.v_ref / 2)) / 600))  # noqa

        return MeasuredValue(
            calibration=calibration,
            f=Decimal(f).quantize(Decimal('.01')),
            z=Decimal(z).quantize(Decimal('.01')),
            r=Decimal(r).quantize(Decimal('.01')),
            x=Decimal(x).quantize(Decimal('.01')),
            ph=Decimal(ph).quantize(Decimal('.01')),
            i=Decimal(i).quantize(Decimal('.00000001')),
            u=Decimal(u).quantize(Decimal('.01')),
        )
