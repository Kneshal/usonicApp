from decimal import Decimal
from math import pi, sqrt


def calc_RnXnZn(data, start=None, end=None):
    """Расчет параметров R, X, Z для всей серии данных.
    Args:
        start (integer, optional): Стартовая частота для расчета. По
        умолчанию None.
        end (integer, optional): Конечная частота для расчета. По
        умолчанию None.

    Returns:
        dict: СЛоварь с RXZ параметрами для каждого значения частоты из
        заданного диапазона.
    """
    RXZ = {
        'Rn': [],
        'Xn': [],
        'Zn': [],
    }
    creal = Decimal('16.51') / 1000000000

    if start is None:
        start = 0
    if end is None:
        end = len(data.f)
    for i in range(start, end):
        X = data.x[i]
        R = data.r[i]
        F = data.f[i]

        tmp = Decimal(pi) * 2 * F * creal
        a = 1 + X * tmp
        b = -R * tmp
        tmp = a * a + b * b
        Rn = (R * a + X * b) / tmp
        Xn = (X * a - R * b) / tmp
        Zn = sqrt(Rn * Rn + Xn * Xn)

        RXZ['Rn'].append(Rn)
        RXZ['Xn'].append(Xn)
        RXZ['Zn'].append(Zn)
    return RXZ


def calc_ZmaxZminRmax(data, start=None, end=None):
    """Расчет параметров Z_max, F_zmax, Z_min, F_zmin, R_max, F_rmax.

    Args:
        start (integer, optional): Стартовая частота для расчета. По
        умолчанию None.
        end (integer, optional): Конечная частота для расчета. По
        умолчанию None.

    Returns:
        dict: Словарь с параметрами.
    """
    if start is None:
        start = 0
    if end is None:
        end = len(data.f)

    stat = {
        'Z_max': Decimal('0.0'),
        'F_zmax': Decimal('0.0'),
        'Z_min': Decimal('0.0'),
        'F_zmin': Decimal('0.0'),
        'R_max': Decimal('0.0'),
        'F_rmax': Decimal('0.0'),
        'dF': Decimal('0.0'),
    }

    stat['Z_max'] = max(data.z[start:end])
    index = data.z.index(stat['Z_max'])
    stat['F_zmax'] = data.f[index]

    stat['Z_min'] = min(data.z[start:end])
    index = data.z.index(stat['Z_min'])
    stat['F_zmin'] = data.f[index]

    stat['R_max'] = max(data.r[start:end])
    index = data.r.index(stat['R_max'])
    stat['F_rmax'] = data.f[index]

    stat['dF'] = stat['F_rmax'] - stat['F_zmin']
    return stat


def calc_q_t(data, start=None, end=None):
    """Расчет Q_t.

    Args:
        start (integer, optional): Стартовая частота для расчета. По
        умолчанию None.
        end (integer, optional): Конечная частота для расчета. По
        умолчанию None.

    Returns:
        Decimal: Значение Q_t.
    """
    I_max = max(data.i[start:end])
    I_max_index = data.i.index(I_max)
    Freq_I_max = data.f[I_max_index]
    I_max_sqrt = I_max / Decimal(sqrt(2))

    index_I1 = I_max_index
    while data.i[index_I1] > I_max_sqrt:
        if (index_I1 > 0):
            index_I1 -= 1
        else:
            break

    index_I2 = I_max_index
    while data.i[index_I2] > I_max_sqrt:
        if (index_I2 + 1 < len(data.f)):
            index_I2 += 1
        else:
            break

    k1 = Decimal(
        (data.f[index_I1] - data.f[index_I1+1])
        / (data.i[index_I1] - data.i[index_I1+1])
    )
    f1_ = (
        k1*I_max_sqrt +
        data.f[index_I1+1] -
        k1*data.i[index_I1+1]
    )
    k2 = Decimal(
        (data.f[index_I2] - data.f[index_I2-1])
        / (data.i[index_I2] - data.i[index_I2-1])
    )
    f2_ = (
        k2*I_max_sqrt +
        data.f[index_I2-1] -
        k2*data.i[index_I2-1]
    )

    Q_t = Freq_I_max/(f2_ - f1_)
    return Q_t


def calc_QRnLnCn(creal, data, start=None, end=None):
    """Расчет параметров Q, Rn, Ln, Cn.

    Args:
        creal(float): Емкость керамики.
        start (integer, optional): Стартовая частота для расчета. По
        умолчанию None.
        end (integer, optional): Конечная частота для расчета. По
        умолчанию None.

    Returns:
        dict: Словарь с параметрами.
    """
    if start is None:
        start = 0
    if end is None:
        end = len(data.f)

    stat = {'Q': Decimal('0.0'),
            'R_n': Decimal('0.0'),
            'L_n': Decimal('0.0'),
            'C_n': Decimal('0.0'),
            'C': Decimal('16.51'),
            }

    stat['C'] = Decimal(creal) * 10 ** 3
    creal = Decimal(creal) / 10 ** 6

    RXZ = calc_RnXnZn(data)

    f1_pos = 0
    for i in range(start, end):
        if RXZ['Xn'][i] >= 0:
            f1_pos = i
            break
    R_max = max(data.r[start:end])
    f2_pos = data.r.index(R_max)

    W1 = Decimal(pi) * 2 * data.f[f1_pos]

    Freq_1 = data.f[f1_pos]
    Freq_2 = data.f[f2_pos]

    stat['R_n'] = RXZ['Rn'][f1_pos]
    stat['C_n'] = creal * (Freq_2 ** 2-Freq_1 ** 2) / (Freq_1 ** 2)
    stat['L_n'] = 1 / (W1 * W1 * stat['C_n'])
    stat['Q'] = calc_q_t(data, start, end)
    stat['L_n'] *= 10 ** 6
    stat['C_n'] *= 10 ** 9
    return stat


def calc_stat(data, start=None, end=None):
    """Рассчитываем параметры.

    Args:
        start (integer, optional): Стартовая частота для расчета. По
        умолчанию None.
        end (integer, optional): Конечная частота для расчета. По
         умолчанию None.

    Returns:
        list: Список параметров.
        """

    def dec_to_str(num, n):
        """Округление числа типа Decimal до n знаков после запятой и
        преобразование результата в строку.
        Args:
            item (Decimal): Число с неизвестным количеством знаков после
            запятой.
            n (integer): Точность округления.

        Returns:
            String: Результат округления в виде строки.
        """
        if num == 0:
            return '0'
        return str(num.quantize(Decimal('1.' + n * '0')))

    if start is None:
        start = 0
    if end is None:
        end = len(data.f)

    try:
        creal = 16.15
        stat = calc_ZmaxZminRmax(data, start, end)
        stat.update(calc_QRnLnCn(creal, data, start, end))

        return {
            'R': int(stat['Z_min']),
            'F': int(stat['F_zmin']),
            'Q': int(stat['Q']),
        }
    except (ArithmeticError, ValueError):
        return None

