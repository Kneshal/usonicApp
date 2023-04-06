from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QToolButton, QWidget

from utils import get_icon


class CellCheckbox(QWidget):
    """Класс, описывающий виджет QcheckBox, с выравниваем и без отступов."""

    def __init__(self, table_window, record_id, parent=None):
        super().__init__(parent)
        self.checkbox = QCheckBox()
        layout = QHBoxLayout(self)
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox.stateChanged.connect(
            lambda: table_window.checkbox_change_state(
                self.checkbox, record_id
            )
        )


class EditToolButton(QWidget):
    """Класс, описывающий кнопку редактирования с иконкой и сигналом."""

    def __init__(self, edit_record_window, table, db, id, parent=None):
        super().__init__(parent)
        self.edit_button = QToolButton()
        layout = QHBoxLayout(self)
        layout.addWidget(self.edit_button)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit_button.setIcon(get_icon('edit.png'))
        self.edit_button.clicked.connect(
            lambda: edit_record_window.show_window(table, db, id)
        )
