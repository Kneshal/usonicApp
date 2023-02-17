from datetime import datetime

import constants as cts
from config import settings
from models import Data, DeviceModel, Record, User
from peewee import OperationalError, PostgresqlDatabase, SqliteDatabase
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot


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
            'db/usonicApp.db',
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
        return self.pg_db_checked_signal.emit(status)

    def connect_and_bind_models(self, db, models) -> None:
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

    def close(self, db) -> None:
        """Разрываем соединение с БД."""
        db.close()

    def get_device_model_title_by_fnumber(self, factory_number: str) -> str | None:  # noqa
        """Возвращает название модели по указанной записи."""
        record = self.get_record(factory_number=factory_number)
        if record is None:
            return None
        return record.device_model.title

    def get_record(self, db: PostgresqlDatabase | SqliteDatabase = None, id: int = None, factory_number: str = None) -> Record | None:  # noqa
        """Возвращает запись с заданным id из указанной БД."""
        if db is None:
            db = self.get_ready_db()
        if not self.connect_and_bind_models(db, [Record]):
            return None
        query = (Record
                 .select(Record, User, DeviceModel)
                 .join(User)
                 .switch(Record)
                 .join(DeviceModel))
        record = None
        if id:
            record: Record = (query
                              .where(Record.id == id)
                              .get_or_none())
        elif factory_number:
            record: Record = (query
                              .where(Record.factory_number == factory_number)
                              .get_or_none())
        self.close(db)
        return record

    @staticmethod
    def record_data_validation(data, user, device_model) -> dict | None:
        """Валидация входящих данных для записи."""
        username = data.get('username')
        factory_number = data.get('factory_number')
        title = data.get('title')
        if ((not username or not factory_number or not title)
                or (user is None)
                or (device_model is None)
                or (len(factory_number) != 13)):
            return None
        return data

    def update_record(self, db: PostgresqlDatabase | SqliteDatabase, id: int, data: dict) -> bool:  # noqa
        """Обновляем запись в заданной БД."""
        if not self.connect_and_bind_models(db, [Record, User, DeviceModel]):
            return False

        user = User.get_or_none(username=data.get('username'))
        device_model = DeviceModel.get_or_none(title=data.get('title'))

        if not DataBase.record_data_validation(data, user, device_model):
            print('Validation failed')
            return False
        Record.update(
            {
                Record.device_model: device_model,
                Record.user: user,
                Record.factory_number: data.get('factory_number'),
                Record.comment: data.get('comment'),
            }
        ).where(Record.id == id).execute()
        self.close(db)
        return True

    def get_filtered_records(self, db, filter_settings=None, search=None, temporary=False):  # noqa
        """Получаем список записей в соответствии с настройками фильтрации."""
        result = {}

        connection = self.connect_and_bind_models(
            db, [Record, DeviceModel, User]
        )
        if connection is False:
            return result

        query = (Record
                 .select(Record, DeviceModel, User)
                 .join(DeviceModel)
                 .switch(Record)
                 .join(User))

        if search:
            query = query.where(Record.factory_number == search)
        elif filter_settings:
            if 'user' in filter_settings:
                username = filter_settings.get('user')
                query = query.where(User.username == username)
            if 'devicemodel' in filter_settings:
                title = filter_settings.get('devicemodel')
                query = query.where(DeviceModel.title == title)
            if 'date' in filter_settings:
                date_1: datetime = filter_settings.get('date')[0].toPyDate()
                date_2: datetime = filter_settings.get('date')[1].toPyDate()
                query = query.where(Record.date.between(date_1, date_2))
        query = (query
                 .where(Record.temporary == temporary)
                 .limit(settings.DISPLAY_RECORDS)
                 .order_by(Record.date))
        # постараться избавиться от лишних return и использовать elif
        for record in query:
            factory_number = record.factory_number
            title = f'{factory_number} - {record.device_model.title}'
            if title in result:
                result[title].append(record)
            else:
                result[title] = [record]
        db.close()
        # print(result)
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
        models = []
        if not self.check_sqlite_db():
            return models
        self.sqlite_db.connect()
        with self.sqlite_db.bind_ctx([DeviceModel]):
            models: list = [model.title for model in DeviceModel.select()]
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
        users = []
        if not self.check_sqlite_db():
            return users
        self.sqlite_db.connect()
        with self.sqlite_db.bind_ctx([User]):
            users: list = [user.username for user in User.select()]
        self.sqlite_db.close()
        return users

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
        with self.sqlite_db.bind_ctx([User, Record]):
            self.sqlite_db.connect()
            self.sqlite_db.create_tables([User, DeviceModel, Record, Data])
            for username in cts.USERS:
                User.get_or_create(username=username)
            for title in cts.DEVICE_MODELS:
                DeviceModel.get_or_create(title=title)
            self.sqlite_db.close()
