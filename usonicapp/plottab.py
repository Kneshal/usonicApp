import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QWidget
from qbstyles import mpl_style

mpl_style(True)


class MplCanvas(FigureCanvasQTAgg):
    """Класс описывающий настройки холста для графиков."""
    def __init__(self, parent=None):

        self.fig = Figure(figsize=(11, 9))
        self.fig.set_facecolor('#202124')
        self.axes_1 = self.fig.add_subplot(211)
        self.axes_2_1 = self.fig.add_subplot(212)
        self.axes_2_2 = self.axes_2_1.twinx()
        self.axes_2_2.grid(False)
        self.fig.subplots_adjust(
            left=0.09,
            bottom=0.05,
            right=0.91,
            top=0.95,
            wspace=None,
            hspace=None,
        )
        super(MplCanvas, self).__init__(self.fig)


class PlotTab(QObject):
    """Класс описывающий вкладку QTabwidget и графики."""
    def __init__(self, tabwidget: QTabWidget, factory_number=None, device_model_title=None, username=None, date=None) -> None:  # noqa
        super().__init__()
        self.tabwidget: QTabWidget = tabwidget
        self.record: dict = {
            'factory_number': factory_number,
            'title': device_model_title,
            'username': username,
            'date': date,
            'comment': None,
            'temporary': False,
            'data': {
                'f': [],
                'z': [],
                'r': [],
                'x': [],
                'ph': [],
                'i': [],
                'u': [],
            }
        }
        self.init_widgets()
        self.init_plots()

    def init_widgets(self) -> None:
        """Инициализация основного виджета."""
        self.page = QWidget(self.tabwidget)
        page_layout = QVBoxLayout()
        self.page.setLayout(page_layout)
        self.canvas = MplCanvas(self)
        page_layout.addWidget(self.canvas)
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
        self.canvas.axes_2_1.set_autoscaley_on(True)
        self.canvas.axes_2_2.set_autoscaley_on(True)

        self.canvas.axes_1.legend(loc='upper right')
        self.canvas.axes_2_1.legend(loc='upper left')
        self.canvas.axes_2_2.legend(loc='upper right')

    @pyqtSlot(dict)
    def add_data(self, data) -> None:
        """Добавление данных в локальное хранилище."""
        # print(data)
        options = ['f', 'z', 'r', 'x', 'ph', 'i', 'u']
        for option in options:
            self.record['data'][option].append(data[option])


class PlotUpdateWorker(QObject):
    """Класс, описывающий обновление графиков в отдельном потоке."""
    def __init__(self):
        super(PlotUpdateWorker, self).__init__()

    @pyqtSlot(PlotTab)
    def draw(self, plottab: PlotTab) -> None:
        """Обновление графиков."""
        data_freq = plottab.record['data']['f']
        data_z = plottab.record['data']['z']
        data_r = plottab.record['data']['r']
        data_x = plottab.record['data']['x']
        data_i = plottab.record['data']['i']
        data_ph = plottab.record['data']['ph']

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

        plottab.canvas.draw()
        plottab.canvas.flush_events()
