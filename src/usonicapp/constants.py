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
TIMER_SINGLE_CHECK_VALUE = 300
TIMER_DATA_RECEIVE_VALUE = 1000
ATTEMPTS_MAXIMUM = 2
TIMER_DB_CHECK = 5000

USERS = (
    'Сливин А.Н.',
    'Барсуков Р.В.',
    'Абраменко Д.С.',
    'Генне Д.В.',
    'Абрамов А.Д.',
)
DEVICE_MODELS = (
    'Волна',
    'Сапфир',
    'Гиминей',
)
