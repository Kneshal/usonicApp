import matplotlib.pyplot as plt
import mplcyberpunk  # noqa
from config import settings
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

plt.style.use("cyberpunk")


class MplCanvas(FigureCanvasQTAgg):
    """Класс описывающий настройки холста для графиков."""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(11, 9))
        self.fig.set_facecolor("#202124")
        self.axes_1 = self.fig.add_subplot(211)
        self.axes_2_1 = self.fig.add_subplot(212)
        self.axes_2_2 = self.axes_2_1.twinx()
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
    def __init__(self, tabwidget: QTabWidget, factory_number, device_model_title, username, date) -> None:  # noqa
        super().__init__()
        self.tabwidget: QTabWidget = tabwidget
        self.record: dict = {
            'factory_number': factory_number,
            'title': device_model_title,
            'username': username,
            'date': date,
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
        self.init_timers()

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
        line_i = self.canvas.axes_2_1.plot([], [], label=u'$I$, Ма', zorder=-1)
        line_ph = self.canvas.axes_2_2.plot(
            [], [], label=u'$\phi$, гр.', color='red', zorder=-1)  # noqa
        self.ref_i = line_i[0]
        self.ref_ph = line_ph[0]
        self.canvas.axes_2_1.set_autoscaley_on(True)
        self.canvas.axes_2_2.set_autoscaley_on(True)

        self.canvas.axes_1.legend(loc='upper right')
        self.canvas.axes_2_1.legend(loc='upper left')
        self.canvas.axes_2_2.legend(loc='upper right')

    def init_timers(self) -> None:
        """Настройка таймеров."""
        self.update_timer = QTimer()
        interval = int(1000 / settings.FPS)
        self.update_timer.setInterval(interval)
        self.update_timer.timeout.connect(self.update_plot)

    @pyqtSlot()
    def update_plot(self) -> None:
        """Обновление графика по таймеру."""
        data_freq = self.record['data']['f']
        data_z = self.record['data']['z']
        data_r = self.record['data']['r']
        data_x = self.record['data']['x']
        data_i = self.record['data']['i']
        data_ph = self.record['data']['ph']

        self.ref_z.set_ydata(data_z)
        self.ref_z.set_xdata(data_freq)
        self.ref_r.set_ydata(data_r)
        self.ref_r.set_xdata(data_freq)
        self.ref_x.set_ydata(data_x)
        self.ref_x.set_xdata(data_freq)

        self.ref_i.set_ydata(data_i)
        self.ref_i.set_xdata(data_freq)
        self.ref_ph.set_ydata(data_ph)
        self.ref_ph.set_xdata(data_freq)

        self.canvas.axes_1.relim()
        self.canvas.axes_1.autoscale_view()
        self.canvas.axes_2_1.relim()
        self.canvas.axes_2_1.autoscale_view()
        self.canvas.axes_2_2.relim()
        self.canvas.axes_2_2.autoscale_view()

        self.canvas.draw()
        self.canvas.flush_events()

    @pyqtSlot(dict)
    def add_data(self, data) -> None:
        """Добавление данных в локальное хранилище."""
        options = ['f', 'z', 'r', 'x', 'ph', 'i', 'u']
        for option in options:
            self.record['data'][option].append(data[option])
