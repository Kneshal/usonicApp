from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix='DYNACONF',
    settings_files=['settings.toml'],
    validators=[
        Validator(
            'OPERATOR',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_PORT',
            'MODEL',
            'START_FREQUENCY',
            'RANGE',
            'STEP',
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
        Validator('STEP', default=1.0, lte=1, gte=0.01),
    ]
)
