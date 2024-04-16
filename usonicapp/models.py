from datetime import datetime

from peewee import (BlobField, BooleanField, CharField, DateTimeField,
                    IntegerField, Model, TextField)
from playhouse.shortcuts import ThreadSafeDatabaseMetadata


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


class Record(BaseModel):
    """Модель, описывающая записи о проведенных измерениях."""
    user = CharField(
        verbose_name='Пользователь',
        help_text='Укажите пользователя',
        max_length=50,
    )
    device_model = CharField(
        verbose_name='Модель аппарата',
        help_text='Укажите модель аппарата',
        max_length=50,
        # default='УЗТА-0,4/22-ОМ (1)',
    )
    series = CharField(
        verbose_name='Серия аппарата',
        help_text='Укажите серию аппарата',
        max_length=15,
        # default='Волна',
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
        # blank=True,
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
        help_text='Подключите массив данных',
        null=True,
    )
    frequency = IntegerField(
        verbose_name='Резонансная частота',
        help_text='Укажите резонансную частоту',
        default=0,
    )
    resistance = IntegerField(
        verbose_name='Сопротивление',
        help_text='Укажите сопротивление',
        default=0,
    )
    quality_factor = IntegerField(
        verbose_name='Добротность',
        help_text='Укажите добротность',
        default=0,
    )
    composition = CharField(
        verbose_name='Сборка',
        help_text='Укажите состав сборки',
        max_length=40,
        null=True,
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} - {self.factory_number}'

    def to_dict(self):
        return {
            'user': self.user,
            'device_model': self.device_model,
            'series': self.series,
            'factory_number': self.factory_number,
            'comment': self.comment,
            'date': self.date.isoformat(),
            'temporary': self.temporary,
            # 'data': self.data,
            'frequency': self.frequency,
            'resistance': self.resistance,
            'quality_factor': self.quality_factor,
            'composition': self.composition,
        }
