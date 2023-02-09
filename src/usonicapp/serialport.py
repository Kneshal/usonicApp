import math
from collections import defaultdict
from decimal import Decimal

import constants as cts
from PyQt6.QtCore import QIODeviceBase, QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo


class MySerialPort(QObject):
    signal_port_checked = pyqtSignal(bool)
    signal_data_received = pyqtSignal(dict)
    signal_calibration_response = pyqtSignal()

    """Класс для работы с COM портом в отдельном потоке."""
    def __init__(self, terminal, comport_label) -> None:
        super().__init__()
        self.terminal = terminal
        self.comport_label = comport_label
        self.connect_pixmap = QPixmap('icons/connect.png')
        self.disconnect_pixmap = QPixmap('icons/disconnect.png')
        self.serial = QSerialPort()
        self.serial.setBaudRate(115200)
        self.serial.readyRead.connect(self.read_data)
        self.serial_port = None
        self.factory_number = None
        self.calibration = None
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
        # print('Start serial port check...')
        self.serial.close()
        self.open(serial_port)
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
                    self.comport_label.setPixmap(self.connect_pixmap)
                    # print('Serial port checked successfully')
                    self.timer.stop()
                    self.signal_port_checked.emit(True)
                elif command == cts.DATA:
                    received_data = {
                        'Vphl': int.from_bytes(data[0:2], byteorder='little'),
                        'VdBI': int.from_bytes(data[2:4], byteorder='little'),
                        'VphU': int.from_bytes(data[4:6], byteorder='little'),
                        'VdBU': int.from_bytes(data[6:8], byteorder='little'),
                        'Vref': int.from_bytes(data[8:10], byteorder='little'),
                        'VI': int.from_bytes(data[10:12], byteorder='little'),
                    }
                    result = self.calc_data(received_data)
                    self.signal_data_received.emit(result)
                elif command == cts.CALIBRATION:
                    self.calibration = int.from_bytes(
                        data[0:2],
                        byteorder='little'
                    )
                    self.signal_calibration_response.emit()
                elif command == cts.VOLTAGE:
                    pass

    def calibration_request(self) -> None:
        """Запрос калибровок."""
        self.serial.write(cts.CALIBRATION)

    def calc_data(self, data) -> dict:
        """Расчет параметров на основе данных от COM-порта."""
        vphl = data.get('Vphl')
        vdbi = data.get('VdBI')
        vphu = data.get('VphU')
        vdbu = data.get('VdBU')
        vref = data.get('Vref')
        vi = data.get('VI')

        z = (self.calibration / 100 * pow(10, (((vdbu - vref / 2) - (vdbi - vref / 2)) / 600)))
        ph = (vphu/10 - vphl/10)
        r = z * math.cos(ph)
        x = z * math.sin(ph)
        i = cts.INDEX_I * pow(10, ((vi - 2500) / 480))
        u = cts.INDEX_U * pow(10, ((vdbu - (vref / 2)) / 600))

        keys = ('z', 'r', 'x', 'ph', 'i', 'u')
        values = (
            round(Decimal(z), 2),
            round(Decimal(r), 2),
            round(Decimal(x), 2),
            round(Decimal(ph), 2),
            round(Decimal(i), 2),
            round(Decimal(u), 2),
        )
        result = dict(zip(keys, values))
        print(result)
        return data

    def no_response(self):
        """COM порт не отвечает."""
        # print('No response from COM-port')
        self.timer.stop()
        self.comport_label.setPixmap(self.disconnect_pixmap)
        self.signal_port_checked.emit(False)
