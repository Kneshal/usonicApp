STYLESHEET_LIGHT = """QToolTip {background-color: white;
    color: black; border: black solid 1px}"""

DATA = b'\xff\xff'
CALIBRATION = b'\xfd\xff'
VOLTAGE = b'\xfe\xff'
CONNECTION_CHECK = b'\xfc\xff'

COMMANDS = {
    DATA: 12,
    CALIBRATION: 2,
    VOLTAGE: 2,
    CONNECTION_CHECK: 2,
}

TIMER_CHECK_SERIAL_PORT = 1000
TIMER_RESPONSE = 300
TIMER_DATA_RECEIVE = 500
TIMER_SETTINGS_REQUEST = 500
ATTEMPTS_MAXIMUM = 2
TIMER_DB_CHECK = 5000

PG_TABLE = 'pg_table'
SQLITE_TABLE = 'sqlite_table'

INDEX_I = 20000
INDEX_U = 1

USERS = [
    'Абраменко Д.С.',
    'Генне Д.В.',
    'Барсуков Р.В.',
    'Барсуков А.Р',
    'Сливин А.Н.',
    'Нестеров В.А.',
    'Цыганок С.Н.',
    'Шакура В.А.',
    'Маняхин И.А.',
    'Аноним',
]
TEST = {'name': '', 'img': 'img/.jpg'}

DEVICE_MODELS = {
    'Алена':
    [
        {'name': 'УЗТА-0,1/28-О', 'img': 'img/uzta-01-28-o.jpg'},
        {'name': 'УЗТА-0,15/22-ОCy', 'img': 'img/uzta-015-22-osu.jpg'},
    ],
    'Волна':
    [
        {'name': 'УЗТА-0,4/22-ОМ (1)', 'img': 'img/uzta-04-22-om-1.jpg'},
        {'name': 'УЗТА-0,4/22-ОМ (2)', 'img': 'img/uzta-04-22-om-2.jpg'},
        {'name': 'УЗТА-0,4/22-ОМ (3)', 'img': 'img/uzta-04-22-om-3.jpg'},
        {'name': 'УЗТА-0,4/22-ОМ (4)', 'img': 'img/uzta-04-22-om-4.jpg'},
        {'name': 'УЗТА-0,4/22-ОМ (5)', 'img': 'img/uzta-04-22-om-5.jpg'},
        {'name': 'УЗТА-0,4/22-ОМ (6)', 'img': 'img/uzta-04-22-om-6.jpg'},
        {'name': 'УЗО-0,4/22-О', 'img': 'img/uzo-04-22-o.jpg'},
        {'name': 'УЗТА-0,63/22-ОМ (1)', 'img': 'img/uzta-063-22-om-1.jpg'},
        {'name': 'УЗТА-0,63/22-ОМ (2)', 'img': 'img/uzta-063-22-om-2.jpg'},
        {'name': 'УЗТА-0,8/22-ОМУ', 'img': 'img/uzta-08-22-omu.jpg'},
    ],
    'Волна-М':
    [
        {'name': 'УЗТА-1/22-ОМ (1)', 'img': 'img/uzta-1-22-om-1.jpg'},
        {'name': 'УЗТА-1/22-ОМ (2)', 'img': 'img/uzta-1-22-om-2.jpg'},
        {'name': 'УЗТА-1/22-ОРв', 'img': 'img/uzta-1-22-orv.jpg'},
        {'name': 'УЗТА-1/22-ОПг', 'img': 'img/uzta-1-22-opg.jpg'},
        {'name': 'УЗТА-1/22-ОПД (1)', 'img': 'img/uzta-1-22-opd-1.jpg'},
        {'name': 'УЗТА-1/22-ОПД (2)', 'img': 'img/uzta-1-22-opd-2.jpg'},
    ],
    'Волна-Т':
    [
        {'name': 'УЗТА-1/22-ОРв-1 (1)', 'img': 'img/uzta-1-22-orv-1-1.jpg'},
        {'name': 'УЗТА-1/22-ОРв-1 (2)', 'img': 'img/uzta-1-22-orv-1-2.jpg'},
        {'name': 'УЗТА-1/22-ОРв-2', 'img': 'img/uzta-1-22-orv-2.jpg'},
    ],
    'Волна-П':
    [
        {'name': 'УЗАП-0,4/22-ОП (1)', 'img': 'img/uzap-04-22-op-1.jpg'},
        {'name': 'УЗАП-0,4/22-ОП (2)', 'img': 'img/uzap-04-22-op-2.jpg'},
        {'name': 'УЗАП-1/22-ОП (1)', 'img': 'img/uzap-1-22-op-1.jpg'},
        {'name': 'УЗАП-1/22-ОП (2)', 'img': 'img/uzap-1-22-op-2.jpg'},
        {'name': 'УЗАП-1/22-ОПСт', 'img': 'img/uzap-1-22-opst.jpg'},
        {'name': 'УЗАП-1x3/22-ОП', 'img': 'img/uzap-1x3-22-op.jpg'},
        {'name': 'УЗАП-4/22-ОП', 'img': 'img/uzap-4-22-op.jpg'},
    ],
    'Волна-Л':
    [
        {'name': 'УЗТА-0,63/22-ОЛ', 'img': 'img/uzta-063-22-ol.jpg'},
        {'name': 'МЛУК-3/22-ОЛ', 'img': 'img/mluk-3-22-ol.jpg'},
        {'name': 'ЛУК-0,5/20-О (1)', 'img': 'img/luk-05-20-o-1.jpg'},
        {'name': 'ЛУК-0,5/20-О (2)', 'img': 'img/luk-05-20-o-2.jpg'},
        {'name': 'ЛУК-0,125/50-О', 'img': 'img/luk-0125-50-o.jpg'},
        {'name': 'ЛУК-0,15/60-О', 'img': 'img/luk-015-60-o.jpg'},
        {'name': 'ЛУК-0,05/100-О', 'img': 'img/luk-005-100-o.jpg'},
    ],
    'Булава':
    [
        {'name': 'УЗТА-2/18-О', 'img': 'img/uzta-2-18-o.jpg'},
        {'name': 'УЗТА-3/22-О', 'img': 'img/uzta-3-22-o.jpg'},
        {'name': 'УЗТА-3/30-О', 'img': 'img/uzta-3-30-o.jpg'},
        {'name': 'УЗТА-8/22-О', 'img': 'img/uzta-8-22-o.jpg'},
        {'name': 'УЗТА-8/22–ОПг', 'img': 'img/uzta-8-22-opg.jpg'},
        {'name': 'УЗТА-10/18–ОПг', 'img': 'img/uzta-10-18-opg.jpg'},
    ],
    'Булава-П':
    [
        {'name': 'УЗАП-2/18-ОП', 'img': 'img/uzap-2-18-op.jpg'},
        {'name': 'УЗАП-3/22-ОП', 'img': 'img/uzap-3-22-op.jpg'},
        {'name': 'УЗАП-8/22-ОП', 'img': 'img/uzap-8-22-op.jpg'},
        {'name': 'УЗАП-8/22-ОПг (1)', 'img': 'img/uzap-8-22-opg-1.jpg'},
        {'name': 'УЗАП-8/22-ОПг (2)', 'img': 'img/uzap-8-22-opg-2.jpg'},
        {'name': 'УЗАП-10/18-ОПг', 'img': 'img/uzap-10-18-opg.jpg'},
    ],
    'Запаиватель':
    [
        {'name': 'ЗУЗ-0,1/44-М', 'img': 'img/zuz-01-44-m.jpg'},
        {'name': 'ЗУЗ-0,1/44-ОКб', 'img': 'img/zuz-01-44-okb.jpg'},
        {'name': 'ЗУЗ-0,063/44-ОР', 'img': 'img/zuz-0063-44-or.jpg'},
    ],
    'Гиминей-Ультра':
    [
        {'name': 'АУС-0,1/27-ОМА (1)', 'img': 'img/aus-01-27-oma-1.jpg'},
        {'name': 'АУС-0,1/27-ОМА (2)', 'img': 'img/aus-01-27-oma-2.jpg'},
        {'name': 'АУС-0,1/44-ОМ', 'img': 'img/aus-01-44-om.jpg'},
        {'name': 'АУС-0,1/60-ОМ', 'img': 'img/aus-01-60-om.jpg'},
        {'name': 'АУС-0,4/22-ОМ (1)', 'img': 'img/aus-04-22-om-1.jpg'},
        {'name': 'АУС-0,4/22-ОМ (2)', 'img': 'img/aus-04-22-om-2.jpg'},
        {'name': 'АУС-0,4/22-ОМЛн', 'img': 'img/aus-04-22-omln.jpg'},
        {'name': 'АУС-0,4/36-ОМ (1)', 'img': 'img/aus-04-36-om-1.jpg'},
        {'name': 'АУС-0,4/36-ОМ (2)', 'img': 'img/aus-04-36-om-2.jpg'},
        {'name': 'АУС-0,4/44-ОМЛн (1)', 'img': 'img/aus-04-44-omln-1.jpg'},
        {'name': 'АУС-0,4/44-ОМЛн (2)', 'img': 'img/aus-04-44-omln-2.jpg'},
        {'name': 'АУС-0,63/22-ОМ', 'img': 'img/aus-063-22-om.jpg'},
        {'name': 'АУС-1/22-ОМ (1)', 'img': 'img/aus-1-22-om-1.jpg'},
        {'name': 'АУС-1/22-ОМ (2)', 'img': 'img/aus-1-22-om-2.jpg'},
        {'name': 'АУС-1/22-ОМ (3)', 'img': 'img/aus-1-22-om-3.jpg'},
    ],
    'Гиминей-К':
    [
        {'name': 'АУС-0,63/22-ОК-25', 'img': 'img/aus-063-22-ok-25.jpg'},
        {'name': 'АУС-0,8/22-ОК-30', 'img': 'img/aus-08-22-ok-30.jpg'},
        {'name': 'АУС-1/22-ОК-40', 'img': 'img/aus-1-22-ok-40.jpg'},
        {'name': 'АУС-1/22-ОК-50 (1)', 'img': 'img/aus-1-22-ok-50-1.jpg'},
        {'name': 'АУС-1/22-ОК-50 (2)', 'img': 'img/aus-1-22-ok-50-2.jpg'},
        {'name': 'АУС-1/22-ОК-50 (3)', 'img': 'img/aus-1-22-ok-50-3.jpg'},
        {'name': 'АУС-3/22-ОК-100', 'img': 'img/aus-3-22-ok-100.jpg'},
    ],
    'Гиминей-Ш':
    [
        {'name': 'АУС-0,8/22-ОШ-40', 'img': 'img/aus-08-22-osh-40.jpg'},
        {'name': 'АУС-1/22-ОШ-30', 'img': 'img/aus-1-22-osh-30.jpg'},
        {'name': 'АУС-1/22-ОШ-75 (1)', 'img': 'img/aus-1-22-osh-75-1.jpg'},
        {'name': 'АУС-1/22-ОШ-75 (2)', 'img': 'img/aus-1-22-osh-75-2.jpg'},
        {'name': 'АУС-3/22-ОШ-220 (1)', 'img': 'img/aus-3-22-osh-220-1.jpg'},
        {'name': 'АУС-3/22-ОШ-220 (2)', 'img': 'img/aus-3-22-osh-220-2.jpg'},
        {'name': 'АУС-3/22-ОШ-220 (3)', 'img': 'img/aus-3-22-osh-220-3.jpg'},
        {'name': 'АУС-3/22-ОШ-220 (4)', 'img': 'img/aus-3-22-osh-220-4.jpg'},
        {'name': 'АУС-3/22-ОШ-220 (5)', 'img': 'img/aus-3-22-osh-220-5.jpg'},
        {'name': 'АУС-3/22-ОШ-270 (1)', 'img': 'img/aus-3-22-osh-270-1.jpg'},
        {'name': 'АУС-3/22-ОШ-270 (2)', 'img': 'img/aus-3-22-osh-270-2.jpg'},
        {'name': 'АУС-3/22-ОШ-320', 'img': 'img/aus-3-22-osh-320.jpg'},
    ],
    'Гиминей-Р':
    [
        {'name': 'АУР-0,2/22-ОС', 'img': 'img/aur-02-22-os.jpg'},
        {'name': 'АУР-0,2/22-О (1)', 'img': 'img/aur-02-22-o-1.jpg'},
        {'name': 'АУР-0,2/22-О (2)', 'img': 'img/aur-02-22-o-2.jpg'},
        {'name': 'АУР-0,4/22-О', 'img': 'img/aur-04-22-o.jpg'},
        {'name': 'АУР-3/22-О', 'img': 'img/aur-3-22-o.jpg'},
    ],
    'Сапфир':
    [
        {'name': 'СУЗ-0,8/22-О (1)', 'img': 'img/suz-08-22-o-1.jpg'},
        {'name': 'СУЗ-0,8/22-О (2)', 'img': 'img/suz-08-22-o-2.jpg'},
        {'name': 'СУЗ-0,6/22-О', 'img': 'img/suz-06-22-o.jpg'},
        {'name': 'СУЗ-0,4/22-О', 'img': 'img/suz-04-22-o.jpg'},
    ],
    'Туман-Н':
    [
        {'name': 'УЗР-0,15/22-О (1)', 'img': 'img/uzr-015-22-o-1.jpg'},
        {'name': 'УЗР-0,15/22-О (2)', 'img': 'img/uzr-015-22-o-2.jpg'},
        {'name': 'УЗР-0,15/22-ОСв', 'img': 'img/uzr-015-22-osv.jpg'},
        {'name': 'УЗР-0,1/35-ОСв', 'img': 'img/uzr-01-35-osv.jpg'},
        {'name': 'УЗР-0,1/35-ОМв', 'img': 'img/uzr-01-35-omv.jpg'},
        {'name': 'УЗР-0,1/40-ОМв', 'img': 'img/uzr-01-40-omv.jpg'},
        {'name': 'УЗР-0,1/44-ОМв (1)', 'img': 'img/uzr-01-44-omv-1.jpg'},
        {'name': 'УЗР-0,1/44-ОМв (2)', 'img': 'img/uzr-01-44-omv-2.jpg'},
        {'name': 'УЗР-0,15/44-ОМ', 'img': 'img/uzr-015-44-om.jpg'},
        {'name': 'УЗР-0,1/44-ОСв', 'img': 'img/uzr-01-44-osv.jpg'},
        {'name': 'УЗР-0,1/80-ОМ', 'img': 'img/uzr-01-80-om.jpg'},
    ],
    'Туман-В':
    [
        {'name': 'УЗР-0,1/130-ОМв', 'img': 'img/uzr-01-130-omv.jpg'},
        {'name': 'УЗР-0,1/160-ОМв', 'img': 'img/uzr-01-160-omv.jpg'},
    ],
    'Соловей':
    [
        {'name': 'УЗАГС-0,1/22-О', 'img': 'img/uzags-01-22-o.jpg'},
        {'name': 'УЗАГС-0,2/22-О', 'img': 'img/uzags-02-22-o.jpg'},
        {'name': 'УЗАГС-0,3/22-О', 'img': 'img/uzags-03-22-o.jpg'},
        {'name': 'УЗАГС-0,3/22-ОРв', 'img': 'img/uzags-03-22-orv.jpg'},
        {'name': 'УЗАГС-0,4/22-О', 'img': 'img/uzags-04-22-o.jpg'},
        {'name': 'УЗАГС-0,5/22-О', 'img': 'img/uzags-05-22-o.jpg'},
        {'name': 'УЗАГС-0,6/18-О', 'img': 'img/uzags-06-18-o.jpg'},
        {'name': 'УЗС–1,2/27–О', 'img': 'img/uzs-12-27-o.jpg'},
    ],
    'Надежда':
    [
        {'name': 'УЗП-0,25/44-О', 'img': 'img/uzp-025-44-o.jpg'},
        {'name': 'УЗП-1/18-ОУ (1)', 'img': 'img/uzp-1-18-ou-1.jpg'},
        {'name': 'УЗП-1/18-ОУ (2)', 'img': 'img/uzp-1-18-ou-2.jpg'},
    ],
    'УЗ установка':
    [
        {'name': 'УЗТА-0,3/15-О', 'img': 'img/uzta-03-15-o.jpg'},
        {'name': 'УЗТА-0,4/22-О', 'img': 'img/uzta-04-22-o.jpg'},
        {'name': 'АУСЛ-0,4/22-ОМ', 'img': 'img/ausl-04-22-om.jpg'},
        {'name': 'СУЗП-0,8/22-О', 'img': 'img/suzp-08-22-o.jpg'},
        {'name': 'АУСП-1/22-ОМ', 'img': 'img/ausl-1-22-om.jpg'},
        {'name': 'АУП-1/22-О', 'img': 'img/aup-1-22-o.jpg'},
        {'name': 'УЗТА-1/22-О', 'img': 'img/uzta-1-22-o.jpg'},
        {'name': 'УЗТА-0,3/60-О', 'img': 'img/uzta-03-60-o.jpg'},
        {'name': 'УЗТА-0,3/100-О', 'img': 'img/uzta-03-100-o.jpg'},
    ],
    'Линия':
    [
        {'name': 'АУСЛ-0,4/22-ОМ (1)', 'img': 'img/ausl-04-22-om-1.jpg'},
        {'name': 'АУСЛ-0,4/22-ОМ (2)', 'img': 'img/ausl-04-22-om-2.jpg'},
        {'name': 'АУСЛ-0,4/22-ОМ (3)', 'img': 'img/ausl-04-22-om-3.jpg'},
        {'name': 'АУСЛ-0,4/22-ОМЛн', 'img': 'img/ausl-04-22-omln.jpg'},
        {'name': 'АУСЛ-1/22-ОМ (1)', 'img': 'img/ausl-1-22-om-1.jpg'},
        {'name': 'АУСЛ-1/22-ОМ (2)', 'img': 'img/ausl-1-22-om-2.jpg'},
        {'name': 'АУСЛ-1/22-ОМ (3)', 'img': 'img/ausl-1-22-om-3.jpg'},
        {'name': 'АУСЛ-1/22-ОМЛн', 'img': 'img/ausl-1-22-omln.jpg'},
        {'name': 'АУСЛ-1,6/22-ОК-60', 'img': 'img/ausl-1_6-22-osh-60.jpg'},
        {'name': 'АУСЛ-3/22-ОШ-270', 'img': 'img/ausl-3-22-osh-270.jpg'},
        {'name': 'УЗРЛ-0,15/44', 'img': 'img/uzrl-015-44.jpg'},
    ],
}

COMPOSITION = [
    'П',
    'ПК',
    'ПКИ',
    'Неизвестно',
]

PASSWORD = "admin"

COLORS = [
    'Red',
    'DarkOrange',
    'Yellow',
    'LawnGreen',
    'Lime',
    'Cyan',
    'DodgerBlue',
    'Blue',
    'Magenta',
    'DeepPink',
]

TABLE_ROW_HEIGHT = 25
