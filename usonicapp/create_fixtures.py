# from decimal import Decimal

from config import settings
from models import FactoryNumber, Record
from peewee import PostgresqlDatabase, SqliteDatabase

if __name__ == '__main__':
    pg_db = PostgresqlDatabase(
        settings.DB_NAME,
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        autoconnect=False,
    )

    sqlite_db = SqliteDatabase(
        'db/usonicApp.db',
        autoconnect=False,
        pragmas={'foreign_keys': 1}
    )
    db_list = [pg_db, sqlite_db]
    models = [Record, FactoryNumber]
    # users = ['user_01', 'user_02', 'user_03']
    # device_models = ['model_01', 'model_02', 'model_03']

    for db in db_list:
        db.bind(models)
        db.connect()
        db.create_tables(models)
        print('Создана ', db)
        """
        user_01 = cts.USERS[0]
        series_01 = list(cts.DEVICE_MODELS.keys())[0]
        device_model_01 = cts.DEVICE_MODELS.get(series_01)[0]
        user_02 = cts.USERS[1]
        series_02 = list(cts.DEVICE_MODELS.keys())[1]
        device_model_02 = cts.DEVICE_MODELS.get(series_01)[0]
        user_03 = cts.USERS[2]
        series_03 = list(cts.DEVICE_MODELS.keys())[2]
        device_model_03 = cts.DEVICE_MODELS.get(series_01)[0]

        for i in range(20):
            temporary = False
            if 5 <= i < 10:
                factory_number = f'00{i}.2023-000{i}'
            elif 10 <= i < 20:
                factory_number = f'0{i}.2023-00{i}'
            if i < 5:
                user = user_01
                series = series_01
                device_model = device_model_01
                factory_number = generate_factory_number()
                temporary = True
            elif 5 <= i < 10:
                user = user_02
                series = series_02
                device_model = device_model_02
            else:
                user = user_03
                series = series_03
                device_model = device_model_03

            record = Record.get_or_create(
                device_model=device_model,
                series=series,
                user=user,
                factory_number=factory_number,
                comment=f'comment_{i}',
                temporary=temporary,
                frequency=0,
                resistance=0,
                quality_factor=0,
            )
            print('waiting...')
        """
        db.close()
    print('Таблицы и фикстуры созданы')
