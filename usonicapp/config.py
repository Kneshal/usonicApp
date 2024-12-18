import os

from dynaconf import Dynaconf, Validator

current_directory = os.path.dirname(os.path.realpath(__file__))
settings = Dynaconf(
    envvar_prefix='DYNACONF',
    root_path=current_directory,
    settings_files=['settings.toml'],
    validators=[
        Validator(
            'OPERATOR',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_PORT',
            'START_FREQUENCY',
            'RANGE',
            'STEP',
            'PREVIOUS_FACTORY_NUMBER',
            'PREVIOUS_DEVICE_MODEL',
            'DISPLAY_RECORDS',
            'COM_PORT',
            'FPS',
            'REAL_TIME_CHART',
            'PREVIOUS_COMPOSITION',
            'VOLTAGE',
            must_exist=True
        ),
        Validator('DB_NAME', default='Development'),
        Validator('DB_NAME', default='test'),
        Validator('DB_USER', default='postgres'),
        Validator('DB_PASSWORD', default='admin'),
        Validator('DB_HOST', default='lapa14'),
        Validator('DB_PORT', default=5432, lte=65535),
        Validator('MODEL', default='Волна-П'),
        Validator('START_FREQUENCY', default=20000, lte=100000, gte=15000),
        Validator('RANGE', default=3000, lte=85000, gte=100),
        Validator('STEP', default=1.0, lte=100, gte=0.01),
        Validator('DISPLAY_RECORDS', default=100, lte=10000),
        Validator('FPS', default=30, gte=1, lte=60),
        Validator('VOLTAGE', default=220, gte=25, lte=250),
    ]
)
