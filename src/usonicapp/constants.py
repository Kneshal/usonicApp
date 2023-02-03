STYLESHEET_LIGHT = """QToolTip {background-color: white;
    color: black; border: black solid 1px}"""

DATA = b'\xff\xff'
CALIBRATION = b'\xfd\xff'
VOLTAGE = b'\xfd\xfe'
CONNECTION_CHECK = b'\xfc\xff'

COMMANDS = {
    DATA: 12,
    CALIBRATION: 2,
    VOLTAGE: 2,
    CONNECTION_CHECK: 2,
}

TIMER_CHECK_VALUE = 1000
TIMER_SINGLE_CHECK_VALUE = 200
TIMER_DATA_RECEIVE_VALUE = 3000
