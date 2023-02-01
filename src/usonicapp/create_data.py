

from config import settings
from models import DeviceModel, Point, Record, User
from peewee import PostgresqlDatabase

pg_db = PostgresqlDatabase(
    settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    port=settings.DB_PORT,
)

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
    '''
    for user in User.select():
        print(user.username)

    pg_db.close()
    print('Close connection')
