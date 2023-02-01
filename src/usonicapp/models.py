from datetime import datetime

from config import settings
from peewee import (CharField, DateTimeField, DecimalField, ForeignKeyField,
                    Model, PostgresqlDatabase, TextField)

pg_db = PostgresqlDatabase(
    settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    port=settings.DB_PORT,
)


class BaseModel(Model):
    class Meta:
        database = pg_db


class User(BaseModel):
    """Модель пользователя."""
    username = CharField(
        verbose_name='Пользователь',
        help_text='Укажите пользователя',
        max_length=50,
        unique=True
    )

    def __str__(self):
        return self.username


class DeviceModel(BaseModel):
    """Модель, описывающая типы аппаратов."""
    title = CharField(
        verbose_name='Модель аппарата',
        help_text='Укажите модель аппарата',
        max_length=200,
        unique=True
    )

    def __str__(self):
        return self.title


class Record(BaseModel):
    """Модель, описывающая записи о проведенных измерениях."""
    device_model = ForeignKeyField(
        DeviceModel,
        verbose_name='Модель аппарата',
        help_text='Укажите модель аппарата',
        backref='records'
    )
    user = ForeignKeyField(
        User,
        verbose_name='Пользователь',
        help_text='Укажите пользователя',
        backref='records'
    )
    factory_number = CharField(
        verbose_name='Заводской номер',
        help_text='Укажите заводской номер',
        max_length=13,
        default=f'001.{datetime.now().year}-0001'
    )
    comment = TextField(
        verbose_name='Заводской номер',
        help_text='Укажите заводской номер',
    )
    date = DateTimeField(
        default=datetime.now,
        verbose_name='Заводской номер',
        help_text='Укажите заводской номер',
    )
    # Добавить расчетные параметры
    # class Meta:
    #     constraints = [SQL('UNIQUE (device_model, factory_number)')]
    #     indexes = (
    #         (('device_model', 'factory_number'), True),
    #     )

    def __str__(self):
        return f'{self.date} - {self.factory_number} -{self.device_model}'


class Point(BaseModel):
    record = ForeignKeyField(
        Record,
        verbose_name='Запись об измерении',
        help_text='Укажите запись об измерении',
        backref='points'
    )
    freq = DecimalField(
        verbose_name='Частота',
        help_text='Укажите частоту',
    )
    z = DecimalField(
        verbose_name='Полное сопротивление',
        help_text='Укажите полное сопротивление',
    )
    r = DecimalField(
        verbose_name='Активное сопротивление',
        help_text='Укажите активное сопротивление',
    )
    x = DecimalField(
        verbose_name='Реактивное сопротивление',
        help_text='Укажите реактивное сопротивление',
    )
    phi = DecimalField(
        verbose_name='Фаза',
        help_text='Укажите фазу',
    )
    i = DecimalField(
        verbose_name='Ток',
        help_text='Укажите ток',
    )
    u = DecimalField(
        verbose_name='Напряжение',
        help_text='Укажите напряжение',
    )

    def __str__(self):
        return f'{self.record} --- {self.freq}'

    class Meta:
        ordering = ['freq']
