import os
from dataclasses import asdict
from datetime import datetime

import constants as cts
import simplejson as json
from config import settings
from models import FactoryNumber, Record
from peewee import OperationalError, PostgresqlDatabase, SqliteDatabase
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

basedir = os.path.dirname(__file__)

# Может прописать декоратор на проверку подключения к бд


class DataBase(QObject):
    """Класс описывает действующие базы данных и взаимодействие с ними."""
    pg_db_checked_signal: pyqtSignal = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.pg_db = PostgresqlDatabase(
            None,
            autoconnect=False,
        )
        self.sqlite_db = SqliteDatabase(
            os.path.join(basedir, 'db/usonicApp.db'),
            autoconnect=False,
            pragmas={'foreign_keys': 1}
        )

    def init_timers(self) -> None:
        """Настройка и запуск таймеров."""
        self.db_check_timer: QTimer = QTimer()
        self.db_check_timer.setInterval(cts.TIMER_DB_CHECK)
        self.db_check_timer.timeout.connect(self.check_db_status)
        self.check_db_status()
        self.db_check_timer.start()

    def upload_record(self, db, record, data=None) -> bool:
        """Загружает запись и связанные данные на сервер."""
        if not self.connect_and_bind_models(db, [Record]):
            return False
        # add validation
        if data is not None:
            encode_data = json.dumps(asdict(data), use_decimal=True)
            record.data = encode_data
        result = record.save()
        # decode_data = json.loads(encode_data, use_decimal=True)
        if not result:
            return False
        self.close(db)
        return True

    def init_pg_db(self) -> None:
        """Инициализация базы данных PostgreSql"""
        self.pg_db.init(
            settings.DB_NAME,
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT,
        )

    @pyqtSlot()
    def check_db_status(self) -> None:
        """Изменение иконки доступности БД."""
        status = self.check_pg_db()
        self.pg_db_checked_signal.emit(status)

    def connect_and_bind_models(self, db, models) -> bool:
        """Подключаемся к бд и привязываем модели."""
        if isinstance(db, PostgresqlDatabase):
            self.init_pg_db()
        try:
            db.connect()
            db.bind(models)
            return True
        except OperationalError as error:
            print(error)
            return False

    def get_device_model_title_by_fnumber(self, factory_number: str):  # noqa  -> str | None
        """Возвращает название модели по указанной записи."""
        record = self.get_record(factory_number=factory_number)
        if record is None:
            return None
        return record.device_model

    def get_series_by_fnumber(self, factory_number: str):  # noqa  -> str | None
        """Возвращает название серии аппарата по указанной записи."""
        record = self.get_record(factory_number=factory_number)
        if record is None:
            return None
        return record.series

    def get_record(self, db=None, id=None, factory_number=None) -> Record:  # noqa  -> Record | None
        """Возвращает запись с заданным id из указанной БД."""
        if db is None:
            db = self.get_ready_db()
        if not self.connect_and_bind_models(db, [Record]):
            return None
        query = (Record.select(Record))
        if id:
            record: Record = (query
                              .where(Record.id == id)
                              .get_or_none())
        else:
            record = (query
                      .where(Record.factory_number == factory_number)
                      .get_or_none())
        self.close(db)
        return record

    def generate_factory_number(self, db=None) -> str:
        """Генерация нового заводского номера."""
        if not self.connect_and_bind_models(db, [FactoryNumber]):
            return None
        obj, created = FactoryNumber.get_or_create()
        if not created:
            number = obj.number
            prefix = number[:3]
            value = int(number[3:]) + 1
            result = prefix + str(value)
            obj.number = result
            obj.save()
        self.close(db)
        return obj.number

    @staticmethod
    def record_data_validation(data):  # -> dict | None
        """Валидация входящих данных для записи."""
        user = data.get('user')
        device_model = data.get('device_model')
        series = data.get('series')
        factory_number = data.get('factory_number')
        if ((not factory_number)
                or (user is None) or (user == '')
                or (device_model is None) or (device_model == '')
                or (series is None) or (series == '')):
            return None
        return data

    def update_record(self, db, id: int, data: dict) -> bool:  # noqa
        """Обновляем запись в заданной БД."""
        if not self.connect_and_bind_models(db, [Record,]):
            return False

        user = data.get('user')
        series = data.get('series')
        device_model = data.get('device_model')
        composition = data.get('composition')
        temporary = data.get('temporary')

        if not DataBase.record_data_validation(data):
            print('Validation failed')
            self.close(db)
            return False
        Record.update(
            {
                Record.series: series,
                Record.device_model: device_model,
                Record.composition: composition,
                Record.user: user,
                Record.factory_number: data.get('factory_number'),
                Record.comment: data.get('comment'),
                Record.temporary: temporary,
            }
        ).where(Record.id == id).execute()
        self.close(db)
        return True

    def get_filtered_records(self, db, filter_settings=None, search=None, temporary=False) -> dict:  # noqa
        """Получаем список записей в соответствии с настройками фильтрации."""
        result: dict = {}

        connection = self.connect_and_bind_models(db, [Record])
        if connection is False:
            return result

        query = (Record.select(Record))

        if search:
            query = query.where(Record.factory_number == search)
        elif filter_settings:
            if 'user' in filter_settings:
                query = query.where(Record.user == filter_settings.get('user'))
            if 'series' in filter_settings:
                series = filter_settings.get('series')
                query = query.where(Record.series == series)
            if 'devicemodel' in filter_settings:
                device_model = filter_settings.get('devicemodel')
                query = query.where(Record.device_model == device_model)
            if 'date' in filter_settings:
                date_1: datetime = filter_settings.get('date')[0].toPyDate()
                date_2: datetime = filter_settings.get('date')[1].toPyDate()
                query = query.where(Record.date.between(date_1, date_2))
        query = (query
                 .where(Record.temporary == temporary)
                 .limit(settings.DISPLAY_RECORDS)
                 .order_by(Record.date.desc()))
        for record in query:
            # title - подзаголовок для серии записей в таблице
            title = (
                f'             {record.factory_number}'
                f'     "{record.series}"'
                f'     {record.device_model}'
            )
            if title in result:
                result[title].append(record)
            else:
                result[title] = [record]
        db.close()
        return result

    def delete_records(self, db, list_id) -> bool:
        """Удаляет записи из выбранной БД."""
        try:
            db.connect()
            with db.bind_ctx([Record]):
                Record.delete().where(
                    Record.id.in_(list_id)
                ).execute()
            db.close()
            return True
        except OperationalError:
            return False

    def sync_records(self, db, list_id) -> bool:
        """Перенос данных из одной БД в другую."""
        transfer_db = self.pg_db
        if db == self.pg_db:
            transfer_db = self.sqlite_db
        # Получаем записи по id
        records = [self.get_record(db, id) for id in list_id]

        # Переносим данные в другую БД
        try:
            transfer_db.connect()
            with transfer_db.bind_ctx([Record]):
                for record in records:
                    temp, created = Record.get_or_create(
                        device_model=record.device_model,
                        series=record.series,
                        user=record.user,
                        factory_number=record.factory_number,
                        comment=record.comment,
                        date=record.date,
                        temporary=record.temporary,
                        data=record.data,
                        frequency=record.frequency,
                        resistance=record.resistance,
                        quality_factor=record.quality_factor,
                        composition=record.composition,
                    )
            transfer_db.close()
            return True
        except OperationalError:
            return False

    '''
    def get_model_by_title(self, title) -> Union[DeviceModel, None]:
        """Возвращает объект DeviceModel по названию аппарата. Если в БД
        его нет, возвращает None."""
        db = self.get_ready_db()
        if not self.connect_and_bind_models(db, [DeviceModel]):
            return None
        device_model = DeviceModel.get_or_none(title=title)
        db.close()
        return device_model

    def get_user_by_username(self, username) -> Union[User, None]:
        """Возвращает объект DeviceModel по названию аппарата. Если в БД
        его нет, возвращает None."""
        db = self.get_ready_db()
        if not self.connect_and_bind_models(db, [User]):
            return None
        user = User.get_or_none(username=username)
        db.close()
        return user

    def get_models_pg(self) -> list:
        """Возвращает список всех моделей аппаратов в бд PostgreSQL."""
        if not self.check_pg_db():
            return self.get_models_sqlite()
        self.pg_db.connect()
        with self.pg_db.bind_ctx([DeviceModel]):
            models: list = [model.title for model in DeviceModel.select()]
        self.pg_db.close()
        return models

    def get_models_sqlite(self) -> list:
        """Возвращает список всех моделей в бд SQLite."""
        models: list = []
        if not self.check_sqlite_db():
            return models
        self.sqlite_db.connect()
        with self.sqlite_db.bind_ctx([DeviceModel]):
            models = [model.title for model in DeviceModel.select()]
        self.sqlite_db.close()
        return models

    def get_users_pg(self) -> list:
        """Возвращает список всех пользователей в бд PostgreSQL."""
        if not self.check_pg_db():
            return self.get_users_sqlite()
        self.pg_db.connect()
        with self.pg_db.bind_ctx([User]):
            users: list = [user.username for user in User.select()]
        self.pg_db.close()
        return users

    def get_users_sqlite(self) -> list:
        """Возвращает список всех пользователей в бд SQLite."""
        users: list = []
        if not self.check_sqlite_db():
            return users
        self.sqlite_db.connect()
        with self.sqlite_db.bind_ctx([User]):
            users = [user.username for user in User.select()]
        self.sqlite_db.close()
        return users
    '''

    def get_ready_db(self):
        """Возвращает ссылку на рабочую базу данных.
        Приоритет отдается удаленной БД."""
        if self.check_pg_db():
            return self.pg_db
        return self.sqlite_db

    def check_pg_db(self) -> bool:
        """Проверка доступности базы данных postgreSQL."""
        self.init_pg_db()
        try:
            self.pg_db.connect()
            self.pg_db.close()
        except OperationalError:
            # print('PostgreSql is offline')
            return False
        # print('PostgreSql is online')
        return True

    def check_sqlite_db(self) -> bool:
        """Проверка доступности базы данных SQlite."""
        try:
            self.sqlite_db.connect()
            self.sqlite_db.close()
        except OperationalError:
            # print('SQlite db is offline')
            return False
        # print('SQlite db is online')
        return True

    def update_sqlite(self) -> None:
        """Создание таблиц и фикстур для базы данных."""
        with self.sqlite_db.bind_ctx([Record]):
            self.sqlite_db.connect()
            self.sqlite_db.create_tables([Record])
            self.sqlite_db.close()

    def close(self, db) -> None:
        """Разрываем соединение с БД."""
        db.close()
