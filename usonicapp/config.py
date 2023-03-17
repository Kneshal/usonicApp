from pathlib import Path

from dynaconf import Dynaconf, Validator, loaders

BASE_DIR = Path(__file__).resolve().parent

SQLITE_FILE = BASE_DIR / 'db/usonicApp.db'
FORMS_BASE_DIR = BASE_DIR / 'forms'
ICONS_BASE_DIR = BASE_DIR / 'icons'

settings = Dynaconf(
    envvar_prefix='DYNACONF',
    settings_files=['settings.toml'],
    validators=[
        Validator('OPERATOR', default='test_user'),
        Validator('BUG_REPORT', default=True),
        Validator('DB_NAME', default='usonicapp'),
        Validator('DB_USER', default='postgres'),
        Validator('DB_PASSWORD', default='admin'),
        Validator('DB_HOST', default='localhost'),
        Validator('DB_PORT', default=5432, lte=65535),
        Validator('MODEL', default='Волна-П'),
        Validator('START_FREQUENCY', default=20000, lte=100000, gte=15000),
        Validator('RANGE', default=3000, lte=85000, gte=100),
        Validator('STEP', default=1.0, lte=1, gte=0.01),
        Validator('PREVIOUS_FACTORY_NUMBER', default='002.2023.0002'),
        Validator('PREVIOUS_DEVICE_MODEL', default='Сапфир'),
        Validator('DISPLAY_RECORDS', default=100, lte=10000),
        Validator('FPS', default=30, gte=1, lte=60),
        Validator('COM_PORT', default='COM17'),
    ]
)


def save_settings():
    loaders.write('settings.toml', settings.as_dict())
