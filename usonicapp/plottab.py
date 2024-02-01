import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
from matplotlib.figure import Figure
from models import Record
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QSpacerItem,
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
        """Добавление данных в локальное хранилище."""
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
