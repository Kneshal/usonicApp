import constants as cts
from config import settings
from models import DeviceModel, Point, Record, User
from peewee import OperationalError, PostgresqlDatabase, SqliteDatabase


class DataBase:
    """Класс описывает действующие базы данных и взаимодействие с ними."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pg_db = PostgresqlDatabase(
            None,
            autoconnect=False,
        )
        self.sqlite_db = SqliteDatabase(
            'db/usonicApp.db',
            autoconnect=False,
        )

    def init_pg_db(self):
        """Инициализация базы данных PostgreSql"""
        self.pg_db.init(
            settings.DB_NAME,
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT,
        )

    def get_users(self) -> list:
        """Возвращает список всех пользователей в выборанной
        базе данных."""
        status = self.check_pg_db()
        print(status)
        if status:
            with self.pg_db.bind_ctx([User]):
                self.pg_db.connect()
                try:
                    print('postgres db')
                    users: list = [user.username for user in User.select()]
                except OperationalError:
                    pass
                self.pg_db.close()
        else:
            with self.sqlite_db.bind_ctx([User]):
                self.sqlite_db.connect()
                print('local db')
                users: list = [user.username for user in User.select()]
                self.sqlite_db.close()
        return users

    def check_pg_db(self) -> bool:
        """Проверка доступности базы данных postgreSQL."""
        try:
            self.init_pg_db()
            self.pg_db.connect()
            self.pg_db.close()
        except OperationalError:
            print('db is offline')
            return False
        print('db is online')
        return True

    def update_sqlite(self) -> None:
        """Создание таблиц и фикстур для базы данных."""
        with self.sqlite_db.bind_ctx([User, Record]):
            self.sqlite_db.connect()
            self.sqlite_db.create_tables([User, DeviceModel, Record, Point])
            for username in cts.USERS:
                User.get_or_create(username=username)
            for title in cts.DEVICE_MODELS:
                DeviceModel.get_or_create(title=title)
            self.sqlite_db.close()
