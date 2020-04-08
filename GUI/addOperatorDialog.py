from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from GUI.titleBar import CustomDialog
import sys


class AddOperatorDialog(CustomDialog):
    def __init__(self, parent, operators: dict):
        super().__init__(parent)
        self.init_ui(operators)

    def init_ui(self, operators):
        self.operators = operators
        self._layout.setSpacing(5)
        self.setWindowTitle('Add Operator')
        self.setWindowIconText(chr(0xf5d2))
        self.dialogWidget = QWidget()
        self.dialogLayout = QGridLayout()
        self.dialogWidget.setLayout(self.dialogLayout)
        self.dialogLayout.setSpacing(5)
        self._layout.addWidget(self.dialogWidget)
        self.label = QLabel('Choose Operator')
        self.comboboxs = [QComboBox()]
        for item in self.operators.keys():
            self.comboboxs[0].addItem(item)
        self.first = self.comboboxs[0].currentText()
        self.chooseFisrt(self.comboboxs[0].currentIndex())
        self.dialogLayout.addWidget(self.label, 0, 0, 1, 2)
        self.dialogLayout.addWidget(self.comboboxs[0], 0, 2, 1, 3)
        self.comboboxs[0].activated.connect(self.chooseFisrt)
        self.cancelButton = QPushButton('Cancel')
        self.okButton = QPushButton('OK')
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.okButton)
        self.cancelButton.clicked.connect(self.close)
        self._layout.addStretch(1)
        self._layout.addLayout(self.buttonLayout)
        self.setFixedSize(320, 175)
        self.setModal(True)
        self.show()

    def chooseFisrt(self, index):
        self.first = self.comboboxs[0].itemText(index)
        self.deleteCombobox(2)
        self.addCombobox2()

    def chooseSecond(self, index):
        second = self.comboboxs[1].itemText(index)
        self.deleteCombobox(1)
        self.addCombobox1(second)

    def deleteCombobox(self, number: int):
        if self.comboboxs.__len__() >=2:
            if self.comboboxs.__len__() == 3:
                third = self.comboboxs.pop(2)
                self.dialogLayout.removeWidget(third)
                third.deleteLater()
            if number == 2:
                second = self.comboboxs.pop(1)
                self.dialogLayout.removeWidget(second)
                second.deleteLater()

    def addCombobox2(self):
        if self.operators[self.first]:
            self.comboboxs.append(QComboBox())
            self.comboboxs[1].activated.connect(self.chooseSecond)
            for item in self.operators[self.first].keys():
                self.comboboxs[1].addItem(item)
            self.dialogLayout.addWidget(self.comboboxs[1], 1, 2, 1, 3)
            second = self.comboboxs[1].currentText()
            self.addCombobox1(second)

    def addCombobox1(self, second):
        if self.operators[self.first][second]:
            self.comboboxs.append(QComboBox())
            for item in self.operators[self.first][second]:
                self.comboboxs[2].addItem(item)
            self.dialogLayout.addWidget(self.comboboxs[2], 2, 2, 1, 3)


def callDialog(ui):
    dialog = AddOperatorDialog(ui, {'ddd': {}})

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = QMainWindow()
    button = QPushButton('ddd', ui)
    button.clicked.connect(lambda: callDialog(ui))
    ui.show()
    sys.exit(app.exec_())
