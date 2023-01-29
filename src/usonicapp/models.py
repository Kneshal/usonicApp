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


if __name__ == '__main__':
    pg_db.connect()
    print('Connected')
    '''
    user_1 = User.select().where(User.username == 'user_1')
    user_2 = User.select().where(User.username == 'user_2')
    device_model_1 = DeviceModel.select().where(DeviceModel.title == 'Гименей')
    device_model_2 = DeviceModel.select().where(DeviceModel.title == 'Волна')
    record_1 = Record.create(device_model=device_model_1, user=user_1, factory_number='005.2023-0005', comment='comment_22')
    record_2 = Record.create(device_model=device_model_1, user=user_1, factory_number='006.2023-0006', comment='comment_23')
    record_3 = Record.create(device_model=device_model_2, user=user_2, factory_number='007.2023-0007', comment='comment_24')
    record_4 = Record.create(device_model=device_model_1, user=user_1, factory_number='008.2023-0008', comment='comment_25')
    record_5 = Record.create(device_model=device_model_1, user=user_1, factory_number='009.2023-0009', comment='comment_26')
    record_6 = Record.create(device_model=device_model_2, user=user_2, factory_number='010.2023-0010', comment='comment_27')
    record_1 = Record.create(device_model=device_model_1, user=user_1, factory_number='005.2023-0005', comment='comment_16')
    record_2 = Record.create(device_model=device_model_1, user=user_1, factory_number='006.2023-0006', comment='comment_17')
    record_3 = Record.create(device_model=device_model_2, user=user_2, factory_number='007.2023-0007', comment='comment_18')
    record_4 = Record.create(device_model=device_model_1, user=user_1, factory_number='008.2023-0008', comment='comment_19')
    record_5 = Record.create(device_model=device_model_1, user=user_1, factory_number='009.2023-0009', comment='comment_20')
    record_6 = Record.create(device_model=device_model_2, user=user_2, factory_number='010.2023-0010', comment='comment_21')
    '''
    
    pg_db.create_tables([User, DeviceModel, Record, Point])
    print('Tables created')
    user_1 = User.create(username='user_1')
    user_2 = User.create(username='user_2')
    user_3 = User.create(username='user_3')
    model_1 = DeviceModel.create(title='Волна')
    model_2 = DeviceModel.create(title='Гименей')
    model_3 = DeviceModel.create(title='Сапфир')
    record_1 = Record.create(device_model=model_1, user=user_3, factory_number='002.2023-0002', comment='comment_1')
    record_2 = Record.create(device_model=model_2, user=user_3, factory_number='003.2023-0003', comment='comment_2')
    record_3 = Record.create(device_model=model_3, user=user_3, factory_number='004.2023-0004', comment='comment_3')
    record_4 = Record.create(device_model=model_1, user=user_1, factory_number='005.2023-0005', comment='comment_4')
    record_5 = Record.create(device_model=model_1, user=user_1, factory_number='006.2023-0006', comment='comment_5')
    record_6 = Record.create(device_model=model_2, user=user_2, factory_number='007.2023-0007', comment='comment_6')
    record_7 = Record.create(device_model=model_1, user=user_1, factory_number='008.2023-0008', comment='comment_7')
    record_8 = Record.create(device_model=model_1, user=user_1, factory_number='009.2023-0009', comment='comment_8')
    record_9 = Record.create(device_model=model_2, user=user_2, factory_number='010.2023-0010', comment='comment_9')
    record_10 = Record.create(device_model=model_1, user=user_1, factory_number='005.2023-0005', comment='comment_10')
    record_11 = Record.create(device_model=model_1, user=user_1, factory_number='006.2023-0006', comment='comment_11')
    record_12 = Record.create(device_model=model_2, user=user_2, factory_number='007.2023-0007', comment='comment_12')
    record_13 = Record.create(device_model=model_1, user=user_1, factory_number='008.2023-0008', comment='comment_13')
    record_14 = Record.create(device_model=model_1, user=user_1, factory_number='009.2023-0009', comment='comment_14')
    record_15 = Record.create(device_model=model_2, user=user_2, factory_number='010.2023-0010', comment='comment_15')
    point_1 = Point.create(record=record_1, freq=20000, z=1.1, x=1.1, r=1.1, phi=1.1, i=1.1, u=1.1)
    point_2 = Point.create(record=record_1, freq=20001, z=1.2, x=1.2, r=1.2, phi=1.2, i=1.1, u=1.2)
    point_3 = Point.create(record=record_1, freq=20002, z=1.3, x=1.3, r=1.3, phi=1.3, i=1.1, u=1.3)
    point_4 = Point.create(record=record_1, freq=20003, z=1.4, x=1.4, r=1.4, phi=1.4, i=1.1, u=1.4)
    point_5 = Point.create(record=record_1, freq=20004, z=1.5, x=1.5, r=1.5, phi=1.5, i=1.1, u=1.5)

    for user in User.select():
        print(user.username)

    pg_db.close()
    print('Close connection')
