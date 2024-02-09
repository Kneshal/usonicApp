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

TIMER_CHECK_SERIAL_PORT = 1000
TIMER_RESPONSE = 300
TIMER_DATA_RECEIVE = 1000
ATTEMPTS_MAXIMUM = 2
TIMER_DB_CHECK = 5000

PG_TABLE = 'pg_table'
SQLITE_TABLE = 'sqlite_table'

INDEX_I = 20000
INDEX_U = 1

USERS = [
    'user_1',
    'user_2'
]

DEVICE_MODELS = [
    'title_1',
    'title_2'
]

COMPOSITION = [
    'П',
    'ПК',
    'ПКИ',
    'Неизвестно',
]

PASSWORD = "admin"

COLORS = [
    'Red',
    'DarkOrange',
    'Yellow',
    'LawnGreen',
    'Lime',
    'Cyan',
    'DodgerBlue',
    'Blue',
    'Magenta',
    'DeepPink',
]

TABLE_ROW_HEIGHT = 25
