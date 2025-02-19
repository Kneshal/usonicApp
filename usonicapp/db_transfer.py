from dataclasses import asdict
from decimal import Decimal
from json import loads

import psycopg2
import simplejson as json
from calc_stat import calc_stat
from config import settings
from models import Record
from peewee import (DataError, IntegrityError, OperationalError,
                    PostgresqlDatabase)
from serialport import MeasuredValue, MeasuredValues


def str_to_list(str_data):
    str_data = str_data.split(', ')
    new_list = []
    for item in str_data:
        new_list.append(Decimal(item))
    return new_list


def update_data(byte_data):
    """Преобразуем байты в табличные данные для дальнейшего использования
    в программе."""
    data = loads(byte_data)
    data = {
        'z': str_to_list(data['Z']),
        'r': str_to_list(data['R']),
        'x': str_to_list(data['X']),
        'ph': str_to_list(data['Phi']),
        'f': str_to_list(data['Freq']),
        'i': str_to_list(data['I']),
        'u': str_to_list(data['U'])
    }

    new_data = MeasuredValues()
    length = len(data.get('z'))
    for i in range(0, length):
        value = MeasuredValue(
            calibration=1,
            f=data.get('f')[i],
            z=data.get('z')[i],
            r=data.get('r')[i],
            x=data.get('x')[i],
            ph=data.get('ph')[i],
            i=data.get('i')[i],
            u=data.get('u')[i],
        )

        new_data.add_value(value)
    return new_data


def set_connection():
    """Создаем соединение с сервером БД PostgreSQL.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            database='test',
            user='postgres',
            password='admin',
            host='lapa14',
            port=5432,
        )
        print('Соединение установлено')
    except OperationalError as error:
        print(
            'Ошибка соединения с SQL сервером',
            f'При попытке соединения с сервером обнаружена ошибка: {error}',
        )
    return connection


def execute_read_query(connection, query):
    """Считываем данные из БД по SQL запросу."""
    if not connection:
        print(
            'SQL сервер не отвечает',
            'Сервер базы данных не подает признаков жизни.',
        )
        return None
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(
            'Ошибка чтения данных',
            f'При попытке чтения данных обнаружена ошибка: {e}',
        )
    except psycopg2.errors.UndefinedTable:
        print(
            'Некорретный формат БД',
            'SQL сервер, к которому подключена программа '
            'имеет БД другого формата.',
        )
    finally:
        connection.close()


def connect_db(db) -> Record:
    """Загружаем объект типа Record в базу"""
    db.init(
        settings.DB_NAME,
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
    )
    db.connect()
    db.bind([Record,])


def close_db(db):
    db.close()


def update_device_model(device_model):
    result = ''
    temp = device_model.split(' ')
    if len(temp) > 1:
        temp1 = temp[0]
        temp2 = '/'.join(temp[1].split('-'))
        temp3 = ' '.join(temp[2:])
        result = ' '.join([temp1, temp2, temp3])
        result = result.strip()
        result = result.replace(' ', '-')
        result = result.replace('-вариант-1', ' (1)')
        result = result.replace('-вариант-2', ' (2)')
        result = result.replace('-вариант-3', ' (3)')
        result = result.replace('-вариант-4', ' (4)')
        result = result.replace('-вариант-5', ' (5)')
        result = result.replace('-вариант-6', ' (6)')
        result = result.replace('-орв', '-ОРв')
        result = result.replace('-ом', '-ОМ')
    if result == '':
        result = 'Неизвестно'
    return result


def load_records() -> list:
    """Выгружаем записи из БД.
    """
    query = (
        "SELECT date, operator, version, device_number, device_name, "
        "information, data "
        "FROM base_table "
        "WHERE date > '2024-03-14'"  # 19.02.25
        "LIMIT 1000;"
    )

    id = 0
    # records = []
    connection = set_connection()
    query_result = execute_read_query(connection, query)
    db = PostgresqlDatabase(
        None,
        autoconnect=False,
    )
    connect_db(db)
    for item in query_result:
        row_data = item[6].tobytes()
        data = update_data(row_data)
        stats = calc_stat(data)
        if stats is None:
            stats = {'R': 0, 'F': 0, 'Q': 0}
        if item[4] is None:
            series = 'Неизвестно'
            device_model = 'Неизвестно'
        else:
            series = item[4].split(' ')[0]
            row_device_model = item[4].split(' ')[1:]
            device_model = ' '.join(row_device_model)

        device_model = update_device_model(device_model)
        # print(series.title(), '---', device_model, '---', temp)
        comment = item[5]
        if comment is None:
            comment = ''

        if data is not None:
            data = json.dumps(asdict(data), use_decimal=True)
        try:
            record, created = Record.get_or_create(
                user=item[1],
                series=series.title(),
                device_model=device_model,
                factory_number=item[3],
                comment=comment,
                date=item[0],
                data=data,
                frequency=stats.get('F'),
                resistance=stats.get('R'),
                quality_factor=stats.get('Q'),
                composition='ПКИ',
            )

            if created:
                print('Запись загружена', record)
            else:
                print('Запись существует')
        except IntegrityError:
            print('Ошибка - запись с таким клюом уже существует')
        except DataError:
            print('Ошибка - некорректный формат данных')
        id += 1
    close_db(db)


def main():
    load_records()


if __name__ == '__main__':
    main()
