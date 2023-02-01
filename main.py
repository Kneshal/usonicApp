"""
Список изменений:
2019.04.02:
- в файл csv добавляется колонка с вычисленным значением тока.

2020.02.20:
- переход на новый формат хранения информации

"""

import csv
import math
import os
import time
from dataclasses import dataclass
from decimal import Decimal

import matplotlib.gridspec as gridspec
import progressbar
import serial
from consolemenu import ConsoleMenu, SelectionMenu
from consolemenu.items import FunctionItem, SubmenuItem
from matplotlib.widgets import Slider, Button
from rich.progress import Progress

from core.logger import get_logger
from core.serial_port import get_available_port
from core.settings import get_settings

logger = get_logger()

settings = get_settings()


# def kbfunc():
#     return ord(msvcrt.getch()) if msvcrt.kbhit() else 0
#
#
# def Omega(f):
#     return Decimal(math.pi) * 2 * f
#
#
# def dec_round(item):
#     return item.quantize(Decimal("1.00"))
#
#
# def dec2str(item):
#     if item == 0:
#         return '0'
#     else:
#         return str(item.quantize(Decimal("1")))


# plt.rcParams['figure.figsize'] = 11, 9

# num_error_on_graph = 50
#
# freq_max = 100000
# freq_min = 0
#
# dec_zero = Decimal("0.0")
#
# skip_item_from_com = 5
# skip_item_from_file = 0
#
# uid = ''
# for i in range(5):
#     uid += str(random.randrange(0, 9, 1))
#
# graph_one_title = ["Impedance", "Reactance", "Active resistance", "Current", "Phase"]
# graph_one_ylabel = ["Resistance, Omh", "Resistance, Omh", "Resistance, Omh", "Current, mA", "Phase, deg."]
# graph_one_filename = ["set_Z", "set_X", "set_R", "set_I", "set_Phi"]

@dataclass
class FrequencyCharacteristic:
    z = []
    x = []
    r = []
    i = []
    phi = []
    f = []

    @property
    def get_length(self):
        return len(self.z)


FREQUENCY_PREFIX = b'\xff\xff'
TOTAL_PARAMETERS = 6
PARAMETER_SIZE = 2

def read_frequency_characteristic_from_com(port_name: str, voltage_level: int,
                                           filename: str,
                                           min_frequency_in_cHz: int,
                                           max_frequency_in_cHz: int,
                                           frequency_step_in_cHz: int):

    with serial.Serial(port_name) as serial_port:
        with Progress() as progress:
            frequency_range = range(min_frequency_in_cHz, max_frequency_in_cHz, frequency_step_in_cHz)
            data_load_task = progress.add_task('Загрузка данных', len(frequency_range))

            for current_frequency_in_cHz in frequency_range:
                frame_of_current_frequency = FREQUENCY_PREFIX + current_frequency_in_cHz.to_bytes(4, byteorder='big')
                serial_port.write(frame_of_current_frequency)

                values_in_bytes = serial_port.read()
                raw_values = [values_in_bytes[n * PARAMETER_SIZE:(n + 1) * PARAMETER_SIZE] for n in range(TOTAL_PARAMETERS)]


                progress.update(data_load_task, advance=1)



    # with open(filename, 'w') as f:
    #             z = Decimal(pow(10, (30 * Decimal(data[0]) - 15360) / 10240) / 0.003053)
    #             phi_grad = (Decimal(data[1] * 90 - 180 * 512) / 512)
    #             phi_rad = math.radians(phi_grad);
    #             r = z * Decimal(math.cos(phi_rad))
    #             x = z * Decimal(math.sin(phi_rad))
    #             i = pow(10, ((Decimal(data[3]) - 270) / 300))
    #             st = str(dec_round(z)) + ';' + str(dec_round(r)) + ';' + str(dec_round(x)) + ';' + str(
    #                 dec_round(phi_grad)) + ';' + str(dec_round(freq_cur)) + ';' + str(data[0]) + ';' + str(
    #                 data[1]) + ';' + str(data[2]) + ';' + str(data[3]) + ';' + str(dec_round(i)) + ';\n'
    #             f.write(st.replace('.', ','))
    #             freq_cur += Decimal(frequency_step_in_cHz) / 100
    #             ct = ct + 1 if ct < max_v else ct


def main():
    port_name = get_available_port()
    if not port_name:
        logger.info('COM-порт не найден. Часть функций недоступна.')

    menu = ConsoleMenu('Sparkman2', "Программа для измерения частотных характеристик УЗКС.")

    function_item = FunctionItem('Измерить частотные характеристики УЗКС.', input, ["Enter an input"])
    selection_menu = SelectionMenu(["item1", "item2", "item3"])
    submenu_item = SubmenuItem("Submenu item", selection_menu, menu)

    menu.append_item(function_item)
    menu.append_item(submenu_item)
    menu.show()


if __name__ == '__main__':
    main()


# label_rus = {'R_dim': 'Ом', 'F_dim': 'Гц', 'L_dim': 'мГн', 'C_dim': 'пФ', 'I_dim': 'мА', 'Phi_dim': 'гр.',
#              'F_name': 'Частота', 'Z_name': 'Комплексное сопротивление', 'R_name': 'Активное сопротивление',
#              'X_name': 'Реактивное сопротивления', 'I_name': 'Ток', 'Phi_name': 'Фаза', 'Q_dim': ''}
# label_eng = {'R_dim': 'Omh', 'F_dim': 'Hz', 'L_dim': 'mH', 'C_dim': 'pF', 'I_dim': 'мА', 'Phi_dim': 'deg.',
#              'F_name': 'Frequency', 'Z_name': 'Impedance', 'R_name': 'Active resistance', 'X_name': 'Reactance',
#              'I_name': 'Current', 'Phi_name': 'Phase'}
#
# item_def = ['Z_max', 'F_zmax', 'Z_min', 'F_zmin', 'R_max', 'F_rmax', 'dF', 'Q', 'R_n', 'L_n', 'C_n', 'C', 'Z_first',
#             'Qi', 'Qt']
# item_name = ['$Z_{max}$', '$F_{Zmax}$', '$Z_{min}$', '$F_{Zmin}$', '$R_{max}$', '$F_{Rmax}$', '$\Delta F$', '$Q$',
#              '$R_{n}$', '$L_{n}$', '$C_{n}$', '$C$', '$Z_{first}$', '$Q_{i}$', '$Q_{t}$']
#
#
# graph_one_title = [label['Z_name'], label['X_name'], label['R_name'], label['I_name'], label['Phi_name']]
# graph_one_ylabel = [label['Z_name'] + ", " + label['R_dim'], label['Z_name'] + ", " + label['R_dim'],
#                     label['Z_name'] + ", " + label['R_dim'], label['I_name'] + ", " + label['I_dim'],
#                     label['Phi_name'] + ", " + label['Phi_dim']]
# graph_one_filename = ["set_Z", "set_X", "set_R", "set_I", "set_Phi"]
#
# item_unit = ['$' + label['R_dim'] + '$', '$' + label['F_dim'] + '$', '$' + label['R_dim'] + '$',
#              '$' + label['F_dim'] + '$', '$' + label['R_dim'] + '$', '$' + label['F_dim'] + '$',
#              '$' + label['F_dim'] + '$', '', '$' + label['R_dim'] + '$', '$' + label['L_dim'] + '$',
#              '$' + label['C_dim'] + '$', '$' + label['C_dim'] + '$', '$' + label['R_dim'] + '$', '', '']
#
# stat_name = dict(zip(item_def, item_name))
# stat_unit = dict(zip(item_def, item_unit))
#


# Класс для хранения и обработки измеренных данных
class Graph_data:
    def calc_stat(self, freq_min=0, freq_max=0):
        if freq_min == freq_max:
            start = 0
            stop = self.item_num
        else:
            start = 0
            while (self.F[start] < freq_min) and (start < self.item_num - 1):
                start += 1
            stop = start
            while (self.F[stop] < freq_max) and (start < self.item_num - 1):
                stop += 1

        # Нахождение характеристик
        self.stat['Z_max'] = max(self.Z[start:stop])
        self.stat['F_zmax'] = self.F[self.Z.index(self.stat['Z_max'])]
        self.stat['Z_min'] = min(self.Z[start:stop])
        self.stat['F_zmin'] = self.F[self.Z.index(self.stat['Z_min'])]
        self.stat['Z_first'] = self.Z[start]

        f1_pos = f2_pos = 0
        for i in range(start, stop):
            if self.Xn[i] >= 0:
                f1_pos = i
                break
        #        f1_pos = self.Xn.index(min(self.Xn[start:stop]))
        print(f1_pos, len(self.Xn))

        self.stat['R_max'] = max(self.R[start:stop])
        self.stat['F_rmax'] = self.F[self.R.index(self.stat['R_max'])]

        self.dots_stat[0] = self.stat['Z_max']
        self.dots_stat[1] = self.stat['Z_min']
        self.dots_stat[2] = self.stat['R_max']
        self.dots_stat[3] = self.Xn[f1_pos]

        self.dots_stat_freq[0] = self.stat['F_zmax']
        self.dots_stat_freq[1] = self.stat['F_zmin']
        self.dots_stat_freq[2] = self.stat['F_rmax']
        self.dots_stat_freq[3] = self.F[f1_pos]

        i_max = max(self.I)
        i_max_index = self.I.index(i_max)
        f_i_max = self.F[i_max_index]
        i_max_sqrt = i_max / Decimal(math.sqrt(2))
        index_i1 = i_max_index
        while self.I[index_i1] > i_max_sqrt:
            if (index_i1 > 0):
                index_i1 -= 1
            else:
                break;

        index_i2 = i_max_index
        while self.I[index_i2] > i_max_sqrt:
            if (index_i2 + 1 < len(self.I)):
                index_i2 += 1
            else:
                break;

        #        k1 = Decimal((self.F[index_i1] - self.F[index_i1-1])/(self.I[index_i1] - self.I[index_i1-1]))
        #        f1_ = k1*i_max_sqrt + self.F[index_i1-1] - k1*self.I[index_i1]

        #        k2 = Decimal((self.F[index_i2] - self.F[index_i2-1])/(self.I[index_i2] - self.I[index_i2-1]))
        #        f2_ = k2*i_max_sqrt + self.F[index_i2-1] - k2*self.I[index_i2]
        #        Q_t = f_i_max/(f2_ - f1_)
        Q_t = 0
        f1_ = f2_ = 0

        self.dots_stat2[0] = self.dots_stat2[1] = i_max_sqrt
        self.dots_stat2[2] = i_max
        self.dots_stat_freq2[0] = f1_
        self.dots_stat_freq2[1] = f2_
        self.dots_stat_freq2[2] = f_i_max

        #    print(i_max, i_max_index, f_i_max, i_max/Decimal(math.sqrt(2)), self.I[index_i1], self.F[index_i1], f1_, self.I[index_i2], self.F[index_i2], f2_, Q_t)

        f2_pos = self.R.index(self.stat['R_max'])
        self.stat['R_n'] = self.Rn[f1_pos]
        W1 = Omega(self.F[f1_pos])
        self.stat['C_n'] = self.stat['C'] * (self.F[f2_pos] * self.F[f2_pos] - self.F[f1_pos] * self.F[f1_pos]) / (
                self.F[f1_pos] * self.F[f1_pos])
        self.stat['L_n'] = 1 / (W1 * W1 * self.stat['C_n'])
        self.stat['Q'] = W1 * self.stat['L_n'] / self.stat['R_n'] if (self.stat['R_n'] != 0) else 0
        self.stat['dF'] = self.stat['F_rmax'] - self.stat['F_zmin']
        self.stat['Qt'] = self.stat['Q']
        self.stat['Qi'] = Q_t

    def calc_RLC(self, start=0, end=0):
        init = 0
        if start == end:
            end = self.item_num
            init = 1

        for i in range(start, end):
            tmp = Omega(self.F[i]) * self.stat['C']
            a = 1 + self.X[i] * tmp
            b = -self.R[i] * tmp

            tmp = a * a + b * b

            Rn1 = (self.R[i] * a + self.X[i] * b) / tmp
            Xn1 = (self.X[i] * a - self.R[i] * b) / tmp
            Zn1 = math.sqrt(Rn1 * Rn1 + Xn1 * Xn1)
            if init == 1:
                self.Rn.append(Rn1)
                self.Xn.append(Xn1)
                self.Zn.append(Zn1)
            else:
                self.Rn[i] = Rn1
                self.Xn[i] = Xn1
                self.Zn[i] = Zn1

        if param['Zn'] != 0:
            self.Zn = self.make_filtration(self.Zn, param['Zn'])
        if param['Xn'] != 0:
            self.Xn = self.make_filtration(self.Xn, param['Xn'])
        if param['Rn'] != 0:
            self.Rn = self.make_filtration(self.Rn, param['Rn'])

    # --------------------------------------------------------------------

    # --------------------------------------------------------------------
    def __init__(self, fname, param):
        tmp = [dec_zero for i in range(len(item_def))]
        self.stat = dict(zip(item_def, tmp))
        del (tmp)

        start_time = time.time()
        self.Z = []
        self.R = []
        self.X = []
        self.Phi = []
        self.F = []
        self.I = []
        self.Zn = []
        self.Rn = []
        self.Xn = []

        self.dots_stat = [0 for i in range(4)]
        self.dots_stat_freq = list(self.dots_stat)

        self.dots_stat2 = [0 for i in range(3)]
        self.dots_stat_freq2 = list(self.dots_stat2)

        with open(fname, newline='') as csv_file:
            line = csv.reader(csv_file, delimiter=';')
            time_read_file = time.time()
            self.item_num = 0
            ct_skip = 0
            for row in line:
                if (ct_skip < skip_item_from_file):
                    ct_skip += 1
                else:
                    row2 = list(map(lambda x: x.replace(',', '.'), row))
                    self.Z.append(Decimal(row2[0]))
                    self.R.append(Decimal(row2[1]))
                    self.X.append(Decimal(row2[2]))
                    self.Phi.append(Decimal(row2[3]))
                    self.F.append(Decimal(row2[4]))
                    if (len(row2) == 11):
                        self.I.append(Decimal(row2[9]))
                    else:
                        self.I.append(pow(10, ((Decimal(row2[8]) - 270) / 300)))
                    self.item_num += 1

        self.filename = fname.replace('.csv', '')

        st = 'чтение файла - ' + str(round(time_read_file - start_time, 1))
        st += '; заполнение массивов. - ' + str(round(time.time() - time_read_file, 1))
        start_time2 = time.time()

        self.calc_capacity()
        self.calc_RLC()
        self.calc_stat()

        self.dot_x = []
        self.dot_y = []
        self.dot_index = []

        flag = 0
        self.dot_x = [self.F[0]]
        self.dot_y = [self.Phi[0]]
        self.dot_index = [0]

        for i in range(0, self.item_num):
            if self.Phi[i] > dPhi:
                if flag == 0:
                    index_start = i
                    flag = 1
            else:
                if flag == 1:
                    local_max = max(self.Phi[index_start:i])
                    index_max = self.Phi[index_start:i].index(local_max) + index_start
                    flag = 0

                    self.dot_y.append(local_max)
                    self.dot_x.append(self.F[index_max])
                    self.dot_index.append(index_max)

        self.dot_y.append(self.Phi[-1])
        self.dot_x.append(self.F[-1])
        self.dot_index.append(len(self.F) - 1)

        st += '; обраб. - ' + str(round(time.time() - start_time2, 1))

        print("""=== Файл""", self.filename, """загружен ===
Диапазон частот от""", self.F[0], """Гц до""", self.F[-1], """Гц
Количество точек -""", self.item_num, """
Время обработки -""", round(time.time() - start_time, 1), """с (""", st, """)
--------------------------------------------------
""")


# files = []
# data = []
# show = 0


def recieve_from_com(filename, freq_start, freq_stop, freq_step):
    ser = serial.Serial(param['COM_name'], baudrate=param['COM_baudrate'], stopbits=1)
    byte = b'\x02' + freq_start.to_bytes(2, byteorder='big') + b'\x03' + freq_stop.to_bytes(2,
                                                                                            byteorder='big') + b'\x04' + freq_step.to_bytes(
        2, byteorder='big') + b'\x01'
    ser.write(byte)

    ct = 4
    while ct != 0:
        ct = ct - 1 if (ser.read(1) == b'\xFF') else 4

    with open(filename, 'w') as f:
        ct = 0
        ser.read(2 * 4 * skip_item_from_com)

        max_v = (freq_stop - freq_start) / (freq_step / 100)
        bar = progressbar.ProgressBar(max_value=int(max_v))
        freq_cur = freq_start + Decimal(freq_step) / 100 * skip_item_from_com

        flag = 0
        while (flag == 0) and (kbfunc() == 0):
            data = []
            for i in range(0, 4):
                data.append(int.from_bytes(ser.read(2), byteorder='big'))
                if i == 1:
                    if (data[0] == 65535) and (data[1] == 65535):
                        flag = 1
                        break
            if flag == 0:
                z = Decimal(pow(10, (30 * Decimal(data[0]) - 15360) / 10240) / 0.003053)
                phi_grad = (Decimal(data[1] * 90 - 180 * 512) / 512)
                phi_rad = math.radians(phi_grad);
                r = z * Decimal(math.cos(phi_rad))
                x = z * Decimal(math.sin(phi_rad))
                i = pow(10, ((Decimal(data[3]) - 270) / 300))
                st = str(dec_round(z)) + ';' + str(dec_round(r)) + ';' + str(dec_round(x)) + ';' + str(
                    dec_round(phi_grad)) + ';' + str(dec_round(freq_cur)) + ';' + str(data[0]) + ';' + str(
                    data[1]) + ';' + str(data[2]) + ';' + str(data[3]) + ';' + str(dec_round(i)) + ';\n'
                f.write(st.replace('.', ','))
                freq_cur += Decimal(freq_step) / 100
                ct = ct + 1 if ct < max_v else ct
                bar.update(ct)
    ser.close()


index_cur = 0


def make_graph_all(index_max):
    global fig, lined, ax1, text_stat, line_stat, sfreq_min, sfreq_max, index, line_I, line_R, line_X, line_Zn, line_Xn, line_Rn, line_I, line_Phi, line_stat, line_Z, graph_all_ct, k

    index = 0
    ct_save = 0

    #    def update(event):
    #        global ax1, text_stat, line_stat
    #        freq_min = sfreq_min.val
    #        freq_max = sfreq_max.val
    #        ax1.set_xlim(left=freq_min, right=freq_max)

    def save(event):
        global ct_save
        ct_save += 1
        plt.savefig('Picture\\' + data[index].file_name + '_' + str(ct_save) + '.png', dpi=300)

    def change_line_data():
        line_Z.set_data(data[index].F, data[index].Z)
        line_R.set_data(data[index].F, data[index].R)
        line_X.set_data(data[index].F, data[index].X)
        line_I.set_data(data[index].F, data[index].I)
        line_Phi.set_data(data[index].F, data[index].Phi)
        line_Zn.set_data(data[index].F, data[index].Zn)
        line_Rn.set_data(data[index].F, data[index].Rn)
        line_Xn.set_data(data[index].F, data[index].Xn)
        plt.draw()

    def prev(event):
        global index
        index = index - 1 if index > 0 else 0
        change_line_data()

    def next(event):
        global index, lines
        index = index + 1 if index < index_max else index_max
        change_line_data()

    def update(event):
        global ax1, text_stat, line_stat
        freq_min = sfreq_min.val
        freq_max = sfreq_max.val
        data[index].calc_stat(freq_min, freq_max)
        text_stat.set_text(data[index].get_all_value())

        line_stat.set_data(data[index].dots_stat_freq, data[index].dots_stat)

        ax1.set_xlim(left=freq_min, right=freq_max)
        ax2.set_xlim(left=freq_min, right=freq_max)
        plt.draw()

    gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1])

    ax1 = plt.subplot(gs[0])
    ax1.grid(True, linestyle='-', color='0.75')

    line_Z, = ax1.plot(data[index].F, data[index].Z, label=u'$Z$, ' + label['R_dim'])
    line_R, = ax1.plot(data[index].F, data[index].R, label=u'$R$, ' + label['R_dim'])
    line_X, = ax1.plot(data[index].F, data[index].X, label=u'$X$, ' + label['R_dim'])

    line_Rn, = ax1.plot(data[index].F, data[index].Rn, label=u'$Rn$, ' + label['R_dim'])
    line_Xn, = ax1.plot(data[index].F, data[index].Xn, label=u'$Xn$, ' + label['R_dim'])
    line_Zn, = ax1.plot(data[index].F, data[index].Zn, label=u'$Zn$, ' + label['R_dim'])

    line_stat, = ax1.plot(data[index].dots_stat_freq, data[index].dots_stat, "x", color='black', label=u'Dots')

    plt.xlabel(label['F_name'] + ", " + label['F_dim'])
    plt.ylabel(label['R_name'] + ", " + label['R_dim'])
    leg = ax1.legend(loc='upper right')

    line_Rn.set_visible(False)
    line_Xn.set_visible(False)
    line_Zn.set_visible(False)
    L = leg.get_lines()
    L[3].set_alpha(0.2)
    L[4].set_alpha(0.2)
    L[5].set_alpha(0.2)

    ax1.relim(visible_only=True)
    ax1.autoscale(enable=True, axis='both', tight=None)

    fig.canvas.mpl_connect('pick_event', onpick)

    ax2 = plt.subplot(gs[2])
    ax2.grid(True, linestyle='-', color='0.75')

    line_I, = ax2.plot(data[index].F, data[index].I, label=u'$I$, ' + label['I_dim'])

    plt.xlabel(label['F_name'] + ", " + label['F_dim'])
    plt.ylabel(label['I_name'] + ", " + label['I_dim'])
    ax2.legend(loc='upper left')

    ax22 = ax2.twinx()
    plt.ylim(-100, 100)
    line_Phi, = ax22.plot(data[index].F, data[index].Phi, label=u'$\phi$, гр.', color='red')
    ax2.set_ylabel(label['Phi_name'] + ", " + label['Phi_dim'])
    leg2 = plt.legend(loc='upper right')

    line_stat2, = ax2.plot(data[index].dots_stat_freq2, data[index].dots_stat2, "x", color='black', label=u'Dots2')

    lines = [line_Z, line_R, line_X, line_Rn, line_Xn, line_Zn, line_stat, line_I, line_Phi, line_stat2]
    lined = dict()
    for legline, origline in zip(leg.get_lines(), lines):
        legline.set_picker(7)
        lined[legline] = origline

    legline = leg2.get_lines()
    legline[0].set_picker(7)
    lined[legline[0]] = line_Phi

    ax22.plot(data[index].dot_x, data[index].dot_y, 'o', picker=5, color='red')

    ax3 = plt.subplot(gs[1])
    ax3.tick_params(labelbottom=False, labelleft=False, right=False, top=False, left=False, bottom=False)
    plt.xlim(0, 10)
    plt.ylim(0, 10)
    text_stat = plt.text(0.5, -0.3, data[index].get_all_value())

    ax4 = plt.subplot(gs[3])
    ax4.tick_params(labelbottom=False, labelleft=False, right=False, top=False, left=False, bottom=False)
    plt.xlim(0, 10)
    plt.ylim(0, 10)

    axfreq_min = plt.axes([0.09, 0.025, 0.30, 0.02])
    sfreq_min = Slider(axfreq_min, '$F_{min}$', int(freq_min), int(freq_max), valinit=int(freq_min), valstep=1)

    axfreq_max = plt.axes([0.50, 0.025, 0.30, 0.02])
    sfreq_max = Slider(axfreq_max, '$F_{max}$', int(freq_min), int(freq_max), valinit=int(freq_max), valstep=1)

    but_save = plt.axes([0.95, 0.025, 0.015, 0.02])
    button_save = Button(but_save, 'S')
    button_save.on_clicked(save)

    but_prev = plt.axes([0.01, 0.025, 0.015, 0.02])
    button_prev = Button(but_prev, '<')
    button_prev.on_clicked(prev)

    but_next = plt.axes([0.97, 0.025, 0.015, 0.02])
    button_next = Button(but_next, '>')
    button_next.on_clicked(next)

    but_update = plt.axes([0.88, 0.025, 0.06, 0.02])
    button = Button(but_update, 'Update')
    button.on_clicked(update)

    if not os.path.exists('Picture'):
        os.makedirs('Picture')

    plt.savefig('Picture\\' + data[index].filename + '.png', dpi=300)
    if show == 1:
        plt.show()
    plt.clf()


def make_graph_one(title, y_text, fname):
    global lined, ax1, fig, plt, graph_one_ct

    graph_one_ct = 0

    def update(event):
        global ax1, text_stat, line_stat
        freq_min = sfreq_min.val
        freq_max = sfreq_max.val
        ax1.set_xlim(left=freq_min, right=freq_max)

    def save(event):
        plt.savefig('Picture\\' + graph_one_filename[graph_one_ct] + '.png', dpi=300)

    def prev(event):
        global graph_one_ct
        if graph_one_ct > 0:
            graph_one_ct -= 1
        ax1.set_title(graph_one_title[graph_one_ct])
        ax1.set_ylabel(graph_one_ylabel[graph_one_ct])
        for i in range(len(lines)):
            lines[i].set_data(data[i].F, data[i].get_datay(graph_one_ct))
        ax1.relim(visible_only=True)
        ax1.autoscale(enable=True, axis='both', tight=None)
        freq_min = sfreq_min.val
        freq_max = sfreq_max.val
        ax1.set_xlim(left=freq_min, right=freq_max)
        plt.draw()

    def next(event):
        global graph_one_ct
        if graph_one_ct < 4:
            graph_one_ct += 1
        ax1.set_title(graph_one_title[graph_one_ct])
        ax1.set_ylabel(graph_one_ylabel[graph_one_ct])
        for i in range(len(lines)):
            lines[i].set_data(data[i].F, data[i].get_datay(graph_one_ct))
        ax1.relim(visible_only=True)
        ax1.autoscale(enable=True, axis='both', tight=None)
        freq_min = sfreq_min.val
        freq_max = sfreq_max.val
        ax1.set_xlim(left=freq_min, right=freq_max)
        plt.draw()

    ax1 = plt.subplot()

    if _p_show_title == 'yes':
        plt.title(title)

    plt.xlabel(label['F_name'] + ", " + label['F_dim'], fontsize=_p_xylabel_font_size)
    plt.ylabel(y_text, fontsize=_p_xylabel_font_size)

    #    marker = list(["o", "v", "s", "p", "*", "+", "x", "d", "^", "<", ">"])

    lines = []
    freq_max = 0
    freq_min = 100000
    y_max = 0
    y_min = 100000
    for i in range(len(data)):
        ln, = ax1.plot(data[i].F, data[i].get_datay(graph_one_ct), label=data[i].filename)
        #       ln, = ax1.plot(data[i].F, data[i].get_datay(graph_one_ct), label=data[i].filename, marker=marker[i], markersize=param['marker_size'], markevery=data[i].item_num//len(marker), linewidth=1, color="black")

        lines.append(ln)
        if data[i].F[0] < freq_min:
            freq_min = data[i].F[0]
        if data[i].F[-1] > freq_max:
            freq_max = data[i].F[-1]

        """
        if max(data[i].get_datay(graph_one_ct)) > y_max:
            y_max = max(data[i].get_datay(graph_one_ct))
        if min(data[i].get_datay(graph_one_ct)) < y_min:
            y_min = min(data[i].get_datay(graph_one_ct))
        """
        y_mas = data[i].get_datay(graph_one_ct)
        y_mas2 = y_mas[int(len(y_mas) / 3):]
        print(len(y_mas2))
        y_max = max(y_mas2)
        y_max_pos = y_mas2.index(y_max) + 100 + int(len(y_mas) / 3)
        print(y_max_pos)
        y_max = y_mas[y_max_pos]
        x_max = data[i].F[y_max_pos]
        if i < _p_show_annotate:
            ax1.annotate(data[i].filename, xy=(x_max, y_max), xytext=(freq_max * Decimal(0.8), y_max), fontsize=20,
                         arrowprops=dict(arrowstyle='-'),
                         )

    if param['show_legend'] == 'yes':
        leg = ax1.legend(loc='best')
        lined = dict()
        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(7)
            lined[legline] = origline
        fig.canvas.mpl_connect('pick_event', onpick)

    plt.grid(True, linestyle='-', color='0.75')
    plt.tick_params(axis='both', which='major', labelsize=_p_label_tick_font_size)

    if _p_show_buttons == 'yes':
        axfreq_min = plt.axes([0.09, 0.025, 0.30, 0.02])
        sfreq_min = Slider(axfreq_min, '$F_{min}$', int(freq_min), int(freq_max), valinit=int(freq_min), valstep=1)

        axfreq_max = plt.axes([0.50, 0.025, 0.30, 0.02])
        sfreq_max = Slider(axfreq_max, '$F_{max}$', int(freq_min), int(freq_max), valinit=int(freq_max), valstep=1)

        but_save = plt.axes([0.95, 0.025, 0.015, 0.02])
        button_save = Button(but_save, 'S')
        button_save.on_clicked(save)

        but_prev = plt.axes([0.01, 0.025, 0.015, 0.02])
        button_prev = Button(but_prev, '<')
        button_prev.on_clicked(prev)

        but_next = plt.axes([0.97, 0.025, 0.015, 0.02])
        button_next = Button(but_next, '>')
        button_next.on_clicked(next)

        but_update = plt.axes([0.88, 0.025, 0.06, 0.02])
        button = Button(but_update, 'Update')
        button.on_clicked(update)

    if not os.path.exists('Picture'):
        os.makedirs('Picture')

    plt.savefig('Picture\\' + fname + '.png', dpi=300)

    if show == 1:
        plt.show()
    plt.clf()


def make_graph_stat(files):
    data_z = []
    data_f = []
    data_n = []

    for i in range(0, len(files)):
        data_z.append(data_stat[i][2])
        data_f.append(data_stat[i][3])
        data_n.append(i)

    plt.title("Изменение $Z_{min}$ во времени. $MAX(Z_{min})$=" + str(max(data_z)) + "; $MIN(Z_{min})$=" + str(
        min(data_z)) + "; MAX/MIN=" + str(dec_round(max(data_z) / min(data_z))) + ";\n$F_{max}$=" + str(
        max(data_f)) + " Гц; $F_{min}$=" + str(min(data_f)) + "Гц; $dF$=" + str(max(data_f) - min(data_f)) + "Гц")
    plt.xlabel("Номер эксперимента")
    plt.grid(True, linestyle='-', color='0.75')

    plt.plot(data_n, data_z, 'go:', label="$Z_{min}$")
    plt.legend(loc='upper left')
    plt.ylabel("Комплексное сопротивление, Ом")

    plt.twinx()

    plt.plot(data_n, data_f, 'r^:', label="$F_{Rmax}$", color='red')
    plt.legend(loc='upper right')
    plt.ylabel("Частота, Гц")

    if not os.path.exists('Picture'):
        os.makedirs('Picture')

    plt.savefig('Picture\\' + 'stat_R' + '.png', dpi=300)

    if show == 1:
        plt.show()
    plt.clf()

# key = msvcrt.getch()
# if (key >= b'0' and key <= b'5'):
#     for file1 in os.listdir(path):
#         if file1.endswith('.csv'):
#             if file1 != 'log.csv' and file1 != param['def_filename_preview'] and file1 != param['def_filename_average']:
#                 files.append(file1)
#     files.sort()
#
#     uid = set()
#     for file in files:
#         pos = file.find('_uid') + 4
#         uid.add(file[pos:pos + 5])
#
#     sets = 0
#     #    print("Найдено "+str(len(files))+" csv файлов.")
#     #    if len(uid) > 0:
#     #        print('Обнаружено серий экспериментов: ', len(uid))
#     #        print('Серии будут обрабатываться независимо')
#     #        print("   1 - Да,\n   Enter - Нет\n")
#     #        sets = 1 if msvcrt.getch() == b'1' else 0
#
#     print('Файлы с данными считываются...\n')
#     load_data_from_files(files)
#     print('Выполнение операции завершено.\n')
#
# if (key >= b'1' and key <= b'3') or key == b'7' or key == b'5':
#     print('Отображать графики?')
#     print("   1 - Да,\n   Enter - Нет\n")
#     show = 1 if msvcrt.getch() == b'1' else 0
#     print('Производится выполнение операции...')
#     fig = plt.figure(figsize=(11, 9))
#
# if key == b'1':
#     for i in range(len(files)):
#         make_graph_all(i)
# #    make_graph_all(len(files))
#
# if key == b'2':
#     make_graph_one(graph_one_title[0], graph_one_ylabel[0], graph_one_filename[0])
# #    make_graph_one("Ток","Ток, мА", "set_I")
# #    make_graph_one("Полное сопротивление", "Сопротивление, Ом", "set_Z")
# #    make_graph_one("Активное сопротивление", "Сопротивление, Ом", "set_R")
# #    make_graph_one("Реактивное сопротивление", "Сопротивление, Ом", "set_X")
#
# if key == b'3':
#     data_avg = []
#     calc_avg_all()
#     files = [def_filename_average]
#     load_data_from_files(files)
#     make_graph_all(0)
#
# if key == b'4':
#     save_stat_to_file()
#
# if key == b'5':
#     make_graph_stat()
#
# if key == b'6':
#     files = []
#     files.append(param['def_filename_preview'])
#     print("\nПолучение данных, подождите...")
#     recieve_from_com(files[0], param['def_freq_start_preview'], param['def_freq_stop_preview'],
#                      param['def_freq_step_preview'])
#     load_data_from_files(files)
#     show = 1
#     make_graph_all(0)
#
# if key == b'7' or key == b'8':
#     key_tmp = key
#     print('Введите начальную частоту в кГц. Enter - значение по умолчанию (' + str(
#         int(param['def_freq_start'] / 1000)) + ')')
#     temp = input()
#     freq_start = param['def_freq_start'] if temp == "" else int(float(temp) * 1000)
#     print('Введите конечную частоту в кГц. Enter - значение по умолчанию (' + str(
#         int(param['def_freq_stop'] / 1000)) + ')')
#     temp = input()
#     freq_stop = param['def_freq_stop'] if temp == "" else int(float(temp) * 1000)
#     print(
#         'Введите шаг частоты в Гц. Enter - значение по умолчанию (' + str(round(param['def_freq_step'] / 100, 2)) + ')')
#     temp = input()
#     freq_step = param['def_freq_step'] if temp == "" else int(float(temp) * 100)
#
#     filename = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')
#
#     ct = 1
#     if key_tmp == b'7':
#         while ord(key) != 27:
#             files = []
#             files.append(filename + '_uid' + uid + '_n' + ('0' if ct <= 9 else '') + str(ct) + '.csv')
#             print("Получение данных, подождите...")
#             recieve_from_com(files[0], freq_start, freq_stop, freq_step)
#             load_data_from_files(files)
#             make_graph_all(0)
#             ct += 1
#
#             print('\n\nНажмите любую клавишу для получения нового графика. Esc - отмена.\n')
#             key = msvcrt.getch()
#
#     if key_tmp == b'8':
#         print('Введите количество графиков в серии (значение по умолчанию - 10): ', end='')
#         n = input()
#         n = 10 if n == "" else int(n)
#         print('Введите паузу между графиками в минутах (значение по умолчанию - 1): ', end='')
#         t = input()
#         t = 1 if t == "" else float(t)
#
#         for i in range(0, n):
#             files = []
#             data = []
#             files.append(filename + '_uid' + uid + '_n' + ('0' if ct <= 9 else '') + str(ct) + '.csv')
#             print("Получение данных, подождите...")
#             recieve_from_com(files[0], freq_start, freq_stop, freq_step)
#             ct += 1
#             load_data_from_files(files)
#             print('\nZmin = ' + str(data_stat[0][2]) + "; Fzmin = " + str(data_stat[0][3]))
#             print("\rВыполняется временная задержка " + str(t) + ' минут')
#             time.sleep(int(t * 60))
