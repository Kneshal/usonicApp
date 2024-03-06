import constants as cts
import matplotlib.pyplot as plt
import simplejson as json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
from matplotlib.figure import Figure
from models import Record
from PyQt5.QtCore import QObject, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QSizePolicy,
                             QSpacerItem, QTableWidget, QTableWidgetItem,
                             QTabWidget, QVBoxLayout, QWidget)
from qbstyles import mpl_style
from serialport import MeasuredValue, MeasuredValues

mpl_style(True)


class NavigationToolbar(Toolbar):
    """Переобпределяем инструменты для класса Toolbar.

    Args:
        Toolbar (NavigationToolbar2QT): Наследуемый класс.
    """
    # Выбираем кнопки для панели инструментов графика
    toolitems = [
        t for t in Toolbar.toolitems if
        t[0] in ('Home', 'Back', 'Forward', 'Zoom')
    ]
    # Можно добавить кнопки: 'Pan', 'Save', 'Subplots'


class MplCanvas(FigureCanvasQTAgg):
    """Класс описывающий настройки холста для графиков."""
    def __init__(self, parent=None):
        fig = Figure(figsize=(11, 9))
        fig.set_facecolor('#202124')
        fig.tight_layout()
        self.axes_1 = fig.add_subplot(211)
        self.axes_2_1 = fig.add_subplot(212)
        self.axes_2_2 = self.axes_2_1.twinx()
        self.axes_2_2.grid(False)
        fig.subplots_adjust(
            left=0.1,
            bottom=0.1,
            right=0.9,
            top=0.9,
            wspace=None,
            hspace=None,
        )
        super(MplCanvas, self).__init__(fig)


class CompareMplCanvas(FigureCanvasQTAgg):
    """Класс описывающий настройки холста для графиков при сравнении."""
    def __init__(self, parent=None, mode=None):
        fig = Figure(figsize=(11, 9))
        fig.set_facecolor('#202124')
        fig.tight_layout()
        count = len(mode)
        pos = 1
        if 'R' in mode:
            self.axes_R = fig.add_subplot(count, 1, pos)
            self.axes_R.set_autoscaley_on(True)
            pos += 1
        if 'I' in mode:
            self.axes_I = fig.add_subplot(count, 1, pos)
            self.axes_I.set_autoscaley_on(True)
            pos += 1
        if 'Ph' in mode:
            self.axes_Ph = fig.add_subplot(count, 1, pos)
            self.axes_Ph.set_autoscaley_on(True)

        fig.subplots_adjust(
            left=0.1,
            bottom=0.05,
            right=0.9,
            top=0.95,
            wspace=None,
            hspace=None,
        )
        super(CompareMplCanvas, self).__init__(fig)


class ComparePlotTab(QObject):
    """Класс описывающий вкладку QTabwidget и графики."""
    def __init__(self, tabwidget: QTabWidget, records, mode) -> None:  # noqa
        super().__init__()
        self.tabwidget: QTabWidget = tabwidget
        self.records = records
        self.mode = mode
        self.init_widgets()
        self.init_plots()

    def init_widgets(self) -> None:
        """Инициализация основного виджета."""
        self.page = QWidget(self.tabwidget)
        page_layout = QVBoxLayout()
        self.page.setLayout(page_layout)

        table = QTableWidget()
        table.clearContents()
        table.setColumnCount(10)
        table.setRowCount(len(self.records))
        table.setHorizontalHeaderLabels(
            [
                'Цвет',
                'Дата и время',
                'Заводской номер',                
                'Комплектация',
                'Серия',
                'Модель',
                'F, Гц',
                'R, Ом',
                'Q',
                'Комментарий',
            ]
        )
        header: QHeaderView = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        flag_selectable_enabled = (
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
        row: int = 0
        for record in self.records:
            table.setRowHeight(row, cts.TABLE_ROW_HEIGHT)

            # Ячейка с цветом
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QColor(cts.COLORS[row]))
            table.setItem(row, 0, item)

            # Ячейка с датой и временем
            item = QTableWidgetItem(
                record.date.strftime('%d-%m-%Y %H:%M:%S'))
            item.setFlags(flag_selectable_enabled)
            table.setItem(row, 1, item)

            # Ячейка с заводским номером
            item = QTableWidgetItem(record.factory_number)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, item)

            # Ячейка с комплектацией УЗКС
            item = QTableWidgetItem(record.composition)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 3, item)
            
            # Ячейка с серией аппарата
            item = QTableWidgetItem(record.series)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 4, item)

            # Ячейка с моделью аппарата
            item = QTableWidgetItem(record.device_model)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 5, item)

            # Ячейка с резонансной частотой
            frequence = (
                str(record.frequency) if record.frequency != 0 else '')
            item = QTableWidgetItem(frequence)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 6, item)

            # Ячейка с сопротивлением
            resistance = (
                str(record.resistance) if record.resistance != 0 else '')
            item = QTableWidgetItem(resistance)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 7, item)

            # Ячейка с добротность
            quality_factor = (
                str(record.quality_factor) if record.quality_factor != 0
                else '')
            item = QTableWidgetItem(quality_factor)
            item.setFlags(flag_selectable_enabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 8, item)

            # Ячейка с комментарием
            item = QTableWidgetItem(record.comment)
            item.setFlags(flag_selectable_enabled)
            table.setItem(row, 9, item)
            row += 1

        height = len(self.records)*cts.TABLE_ROW_HEIGHT + 27
        table.setMinimumHeight(height)
        page_layout.addWidget(table)

        self.canvas = CompareMplCanvas(self, self.mode)
        page_layout.addWidget(self.canvas)

        # Навигационная панель
        widget = QWidget()
        toolbar = Toolbar(self.canvas, widget)
        toolbar.setStyleSheet('font-size: 14px; color: white;')
        toolbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        page_layout.addWidget(toolbar)
        page_layout.setContentsMargins(0, 0, 0, 0)

    def init_plots(self) -> None:
        """Настройка отображения графиков на виджете."""
        pos = 0
        for record in self.records:
            if record.data is None:
                continue
            if not isinstance(record.data, memoryview):
                record.data = memoryview(record.data)
            data = MeasuredValues(
                **json.loads(record.data.tobytes(), use_decimal=True)
            )

            if 'R' in self.mode:
                ref_r = self.canvas.axes_R.plot(
                    [], [], label=u'$R$, Ом',
                    color=cts.COLORS[pos], zorder=-1)[0]
                ref_r.set_ydata(data.r)
                ref_r.set_xdata(data.f)
            if 'I' in self.mode:
                ref_i = self.canvas.axes_I.plot(
                    [], [], label=u'$I$, Ом',
                    color=cts.COLORS[pos], zorder=-1)[0]
                ref_i.set_ydata(data.i)
                ref_i.set_xdata(data.f)
            if 'Ph' in self.mode:
                ref_ph = self.canvas.axes_Ph.plot(
                    [], [], label=u'$Ph$, Ом',
                    color=cts.COLORS[pos], zorder=-1)[0]
                ref_ph.set_ydata(data.ph)
                ref_ph.set_xdata(data.f)
            pos += 1

        if 'R' in self.mode:
            self.canvas.axes_R.set_ylabel('R, Ом')
            self.canvas.axes_R.relim()
            self.canvas.axes_R.autoscale_view()
        if 'I' in self.mode:
            self.canvas.axes_I.set_ylabel('I, мА.')
            self.canvas.axes_I.relim()
            self.canvas.axes_I.autoscale_view()
        if 'Ph' in self.mode:
            self.canvas.axes_Ph.set_ylabel('Ph, гр.')
            self.canvas.axes_Ph.relim()
            self.canvas.axes_Ph.autoscale_view()

        self.canvas.draw()


class PlotTab(QObject):
    """Класс описывающий вкладку QTabwidget и графики."""
    def __init__(self, tabwidget: QTabWidget, record) -> None:  # noqa
        super().__init__()
        self.tabwidget: QTabWidget = tabwidget

        self.record: Record = record
        self.data = MeasuredValues()

        self.init_widgets()
        self.init_plots()

    def init_widgets(self) -> None:
        """Инициализация основного виджета."""
        self.page = QWidget(self.tabwidget)
        page_layout = QVBoxLayout()
        self.page.setLayout(page_layout)

        # График
        self.canvas = MplCanvas(self)
        page_layout.addWidget(self.canvas)

        # Слой с параметрами
        stat_layout = QHBoxLayout()
        self.label_frequency = QLabel()
        self.label_resistance = QLabel()
        self.label_quality_factor = QLabel()
        self.label_composition = QLabel()
        stat_layout.addWidget(self.label_frequency)
        stat_layout.addWidget(self.label_resistance)
        stat_layout.addWidget(self.label_quality_factor)
        stat_layout.addWidget(self.label_composition)
        spacerItem = QSpacerItem(
            400, 10, QSizePolicy.Expanding, QSizePolicy.Expanding)
        stat_layout.addItem(spacerItem)
        self.label_frequency.setStyleSheet(
            'font-size: 14px; color: white;')
        self.label_resistance.setStyleSheet(
            'font-size: 14px; color: white;')
        self.label_quality_factor.setStyleSheet(
            'font-size: 14px; color: white;')
        self.label_composition.setStyleSheet(
            'font-size: 14px; color: white;')
        page_layout.addLayout(stat_layout)

        # Навигационная панель
        widget = QWidget()
        toolbar = Toolbar(self.canvas, widget)
        toolbar.setStyleSheet('font-size: 14px; color: white;')
        toolbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        page_layout.addWidget(toolbar)
        page_layout.setContentsMargins(0, 0, 0, 0)

    def init_plots(self) -> None:
        """Настройка отображения графиков на виджете."""
        self.canvas.axes_1.set_xlabel('Частота, Гц')
        self.canvas.axes_1.set_ylabel('Активное сопротивление, Ом')
        line_z = self.canvas.axes_1.plot([], [], label=u'$Z$, Ом', zorder=-1)
        line_r = self.canvas.axes_1.plot([], [], label=u'$R$, Ом', zorder=-1)
        line_x = self.canvas.axes_1.plot([], [], label=u'$X$, Ом', zorder=-1)
        self.ref_z = line_z[0]
        self.ref_r = line_r[0]
        self.ref_x = line_x[0]
        self.canvas.axes_1.set_autoscaley_on(True)
        plt.ylim(-100, 100)

        self.canvas.axes_2_1.set_xlabel('Частота, Гц')
        self.canvas.axes_2_1.set_ylabel('Ток, мА.')
        line_i = self.canvas.axes_2_1.plot(
            [], [], label=u'$I$, Ма', color='blue',  zorder=-1)
        line_ph = self.canvas.axes_2_2.plot(
            [], [], label=u'$\phi$, гр.', color='red', zorder=-1)  # noqa
        self.ref_i = line_i[0]
        self.ref_ph = line_ph[0]

        self.canvas.axes_2_2.set_xlabel('Частота, Гц')
        self.canvas.axes_2_2.set_ylabel('Фаза, гр.')
        self.canvas.axes_2_1.set_autoscaley_on(True)
        self.canvas.axes_2_2.set_autoscaley_on(True)

        self.canvas.axes_1.legend(loc='upper right')
        self.canvas.axes_2_1.legend(loc='upper left')
        self.canvas.axes_2_2.legend(loc='upper right')

    @pyqtSlot(MeasuredValue)
    def get_data(self, data: MeasuredValue) -> None:
        """Добавление данных в локальное хранилище."""
        self.data.add_value(data)

    def set_data(self, data: MeasuredValue) -> None:
        """"""
        self.data = data


class PlotUpdateWorker(QObject):
    """Класс, описывающий обновление графиков в отдельном потоке."""
    def __init__(self):
        super(PlotUpdateWorker, self).__init__()

    @pyqtSlot(PlotTab)
    def draw(self, plottab: PlotTab) -> None:
        """Обновление графиков."""
        if not plottab.data.f:
            return
        data_freq = plottab.data.f
        data_z = plottab.data.z
        data_r = plottab.data.r
        data_x = plottab.data.x
        data_i = plottab.data.i
        data_ph = plottab.data.ph

        plottab.ref_z.set_ydata(data_z)
        plottab.ref_z.set_xdata(data_freq)

        plottab.ref_r.set_ydata(data_r)
        plottab.ref_r.set_xdata(data_freq)

        plottab.ref_x.set_ydata(data_x)
        plottab.ref_x.set_xdata(data_freq)

        plottab.ref_i.set_ydata(data_i)
        plottab.ref_i.set_xdata(data_freq)

        plottab.ref_ph.set_ydata(data_ph)
        plottab.ref_ph.set_xdata(data_freq)

        plottab.canvas.axes_1.relim()
        plottab.canvas.axes_1.autoscale_view()

        plottab.canvas.axes_2_1.relim()
        plottab.canvas.axes_2_1.autoscale_view()

        plottab.canvas.axes_2_2.relim()
        plottab.canvas.axes_2_2.autoscale_view()

        f_start = plottab.data.f[0]
        f_end = plottab.data.f[-1]
        plottab.canvas.axes_1.set_xbound(f_start, f_end)
        plottab.canvas.axes_2_1.set_xbound(f_start, f_end)
        plottab.canvas.axes_2_2.set_xbound(f_start, f_end)

        plottab.canvas.draw()
        plottab.canvas.flush_events()
