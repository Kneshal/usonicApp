from datetime import datetime

from peewee import (BooleanField, CharField, DateTimeField, DecimalField,
                    ForeignKeyField, Model, TextField)
from playhouse.shortcuts import ThreadSafeDatabaseMetadata


def generate_factory_number():
    """Генерация нового заводского номера."""
    obj, created = FactoryNumber.get_or_create()
    if not created:
        number = obj.number
        prefix = number[:3]
        value = int(number[3:]) + 1
        result = prefix + str(value)
        obj.number = result
        obj.save()
    return obj.number


class BaseModel(Model):
    class Meta:
        model_metadata_class = ThreadSafeDatabaseMetadata


class FactoryNumber(BaseModel):
    """Модель заводского номера."""
    number = CharField(
        verbose_name='Заводской номер',
        help_text='Укажите заводской номер',
        max_length=13,
        default='TMP1',
        unique=True,
    )

    def __str__(self):
        return self.number


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
    temporary = BooleanField(
        verbose_name='Тип записи',
        help_text='Укажите тип записи',
        default=False,
    )
    # Добавить расчетные параметры
    # class Meta:
    #     constraints = [SQL('UNIQUE (device_model, factory_number)')]
    #     indexes = (
    #         (('device_model', 'factory_number'), True),
    #     )

    def __str__(self):
        return f'{self.date} - {self.factory_number}'


class Point(BaseModel):
    record = ForeignKeyField(
        Record,
        verbose_name='Запись об измерении',
        help_text='Укажите запись об измерении',
        backref='points',
        on_delete='CASCADE',
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
