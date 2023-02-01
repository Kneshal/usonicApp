import sys

import constants as cts
from PyQt6.QtCore import QIODeviceBase, QObject, QTimer, pyqtSignal
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import QApplication, QMainWindow


class MySerialPort(QObject):
    signal_serial_port = pyqtSignal(bool)
    """Класс для работы с COM портом в отдельном потоке."""
    def __init__(self) -> None:
        super().__init__()
        self.serial = QSerialPort()
        # print(QSerialPort.BaudRate.Baud1200)
        self.serial.setBaudRate(1200)
        self.serial.readyRead.connect(self.read_data)
        self.serial_port = None
        self.factory_number = None
        self.status = False
        self.timer = QTimer()

    def open(self, port_name) -> bool:
        self.serial.setPortName(port_name)
        return self.serial.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    def close(self):
        self.serial.close()

    def write_data(self, data):
        self.serial.write(data)

    def read_data(self):
        rdata = self.serial.readAll()
        print(rdata)
        if rdata[:2] == cts.CONNECTION_CHECK:  # Проверка COM порта
            self.serial_port = self.serial.portName()
            self.factory_number = int.from_bytes(rdata[2], byteorder='big')
            print(
                f'Устройство проверено. Порт - {self.serial_port}, '
                f'серийный номер прибора - {self.factory_number}'
            )
            self.status = True
            self.signal_serial_port.emit(True)

    def no_response(self):
        """COM порт не отвечает."""
        if self.status is False:
            print('COM-порт не прошел проверку')
            self.signal_serial_port.emit(False)

    def get_serial_ports_list(self) -> list:
        """Возвращает список активных COM-портов."""
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        return [port.portName() for port in serial_list]

    def check_serial_port(self, serial_port) -> None:
        """Запрос проверки связи для COM порта."""
        self.close()
        self.status = False
        self.open(serial_port)
        self.write_data(cts.CONNECTION_CHECK)
        self.timer.singleShot(300, self.no_response)


class MainWindow(QMainWindow):
    """Основное окно программы."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Usonic App')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    serial = MySerialPort()
    serial.search_port()
    serial.write_data()
    app.exec()
