from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QToolButton, QWidget


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
    def __init__(self, table_window, record_id, parent=None):
        super().__init__(parent)
        self.edit_button = QToolButton()
        layout = QHBoxLayout(self)
        layout.addWidget(self.edit_button)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit_button.setIcon(QtGui.QIcon('icons/edit.png'))
        self.edit_button.clicked.connect(
            lambda: table_window.edit_record_window.show_window(record_id)
        )
