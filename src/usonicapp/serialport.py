from collections import defaultdict

import constants as cts
from PyQt6.QtCore import QIODeviceBase, QObject, QTimer, pyqtSignal
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo


class MySerialPort(QObject):
    signal_port_checked = pyqtSignal(bool)
    signal_data_received = pyqtSignal(dict)

    """Класс для работы с COM портом в отдельном потоке."""
    def __init__(self, terminal, status_label) -> None:
        super().__init__()
        self.terminal = terminal
        self.status_label = status_label
        self.serial = QSerialPort()
        self.serial.setBaudRate(115200)
        self.serial.readyRead.connect(self.read_data)
        self.serial_port = None
        self.factory_number = None
        self.status = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.no_response)

    def open(self, port_name) -> bool:
        """Открываем заданный COM-порт."""
        self.serial.setPortName(port_name)
        return self.serial.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    def get_serial_ports_list(self) -> list:
        """Возвращает список активных COM-портов."""
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        return [port.portName() for port in serial_list]

    def check_serial_port(self, serial_port) -> None:
        """Запрос проверки связи для COM порта."""
        self.status = False
        self.serial.close()
        self.open(serial_port)
        # print('Start serial port check...')
        self.serial.write(cts.CONNECTION_CHECK)
        self.timer.start(cts.TIMER_SINGLE_CHECK_VALUE)

    def create_tasks(self, data) -> list:
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

    def read_data(self):
        """Слот, отвечающий за чтение и обработку поступюащих даееых."""
        rdata = self.serial.readAll()
        # print(rdata)
        tasks = self.create_tasks(rdata.data())
        for command, data_list in tasks.items():
            for data in data_list:
                if command == cts.CONNECTION_CHECK:
                    self.serial_port = self.serial.portName()
                    self.factory_number = int.from_bytes(
                        data[:1],
                        byteorder='little',
                    )
                    self.status = True
                    self.timer.stop()
                    self.status_label.setText(
                        f'Прибор подключен через порт - {self.serial_port}, '
                        f'серийный номер - {self.factory_number}'
                    )
                    # print('Serial port checked successfully')
                    self.signal_port_checked.emit(True)
                elif command == cts.DATA:
                    received_data = {
                        '1': int.from_bytes(data[0:2], byteorder='little'),
                        '2': int.from_bytes(data[2:4], byteorder='little'),
                        '3': int.from_bytes(data[4:6], byteorder='little'),
                        '4': int.from_bytes(data[6:8], byteorder='little'),
                        '5': int.from_bytes(data[8:10], byteorder='little'),
                        '6': int.from_bytes(data[10:12], byteorder='little'),
                    }
                    self.signal_data_received.emit(received_data)
                elif command == cts.CALIBRATION:
                    pass
                elif command == cts.VOLTAGE:
                    pass

    def no_response(self):
        """COM порт не отвечает."""
        # print('No response from COM-port')
        self.timer.stop()
        self.status_label.setText(
            'COM порт не подключен или не прошел проверку'
        )
        self.signal_port_checked.emit(False)
