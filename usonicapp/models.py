from datetime import datetime

from peewee import (BlobField, BooleanField, CharField, DateTimeField,
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
        verbose_name='Комментарий',
        help_text='Укажите комментарий',
    )
    date = DateTimeField(
        default=datetime.now,
        verbose_name='Дата и время измерения',
        help_text='Укажите дату и время измерения',
        unique=True,
    )
    temporary = BooleanField(
        verbose_name='Тип записи',
        help_text='Укажите тип записи',
        default=False,
    )
    data = BlobField(
        verbose_name='Массив данных',
        help_text='подключите массив данных',
        null=True,
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} - {self.factory_number}'
