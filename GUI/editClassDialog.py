from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from GUI.titleBar import CustomDialog
import pandas as pd
import numpy as np
import sys


class EditClassDialog(CustomDialog):
    def __init__(self, parent, classList=pd.DataFrame()):
        super().__init__(parent)
        self.init_ui(classList)

    def init_ui(self, classList):
        self.setWindowTitle('Edit Parameter List: classes')
        self.setWindowIconText(chr(0xf044))
        self.dialogLayout = QVBoxLayout()
        self.dialogWidget = QWidget()
        self.dialogWidget.setLayout(self.dialogLayout)
        self._layout.addWidget(self.dialogWidget)
        self.listLayout = QHBoxLayout()

        # 设置对话框的介绍信息
        labelLayout = QHBoxLayout()
        labelBtn = QPushButton(QIcon('../icon/edit.ico'), '')
        labelBtn.setObjectName('labelButton')
        labelBtn.setStyleSheet('#labelButton{border: 0}')
        labelBtn.setIconSize(QSize(48, 48))
        labelText = QLabel('Defines the classes and the upper limits of each class.')
        labelLayout.addWidget(labelBtn, 3)
        labelLayout.addWidget(labelText, 7)

        # 放置table用于编辑classes
        self.classTable = QTableWidget()
        self.classTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.classTable.setColumnCount(2)
        self.classTable.setRowCount(classList.shape[0])
        for row in range(classList.shape[0]):
            self.classTable.setItem(row, 0, QTableWidgetItem(classList.iloc[row, 0]))
            self.classTable.setItem(row, 1, QTableWidgetItem(str(classList.iloc[row, 1])))
        self.classTable.setHorizontalHeaderItem(0, QTableWidgetItem('class names'))
        self.classTable.setHorizontalHeaderItem(1, QTableWidgetItem('upper limit'))
        self.classTable.verticalHeader().hide()
        self.classTable.itemChanged.connect(self.contentChange)

        # 放置对话框的取消和确定按钮
        self.buttonBox = QHBoxLayout()
        self.buttonBox.addStretch(1)
        self.addButton = QPushButton(QIcon('../icon/add_notes'), 'Add Entry')
        self.addButton.setIconSize(QSize(24, 24))
        self.addButton.clicked.connect(self.addEntry)
        self.deleteButton = QPushButton(QIcon('../icon/delete_notes'), 'Remove Entry')
        self.deleteButton.setIconSize(QSize(24, 24))
        self.deleteButton.clicked.connect(self.removeEntry)
        self.cancelButton = QPushButton(QIcon('../icon/cancel'), 'Cancel')
        self.cancelButton.setIconSize(QSize(24, 24))
        self.okButton = QPushButton(QIcon('../icon/apply'), 'Apply')
        self.okButton.setIconSize(QSize(24, 24))
        self.buttonBox.addWidget(self.addButton)
        self.buttonBox.addWidget(self.deleteButton)
        self.buttonBox.addWidget(self.okButton)
        self.buttonBox.addWidget(self.cancelButton)
        self.cancelButton.clicked.connect(self.close)

        self.dialogLayout.addLayout(labelLayout)
        self.dialogLayout.addWidget(self.classTable)
        self.dialogLayout.addLayout(self.buttonBox)

        self.setModal(True)
        self.show()

    def addEntry(self):
        self.classTable.insertRow(self.classTable.rowCount())

    def removeEntry(self):
        self.classTable.removeRow(self.classTable.currentRow())

    def contentChange(self, itemchange):
        if itemchange.column() == 1:
            try:
                limit = float(itemchange.text())
            except:
                itemchange.setText('')


class HiddenLayerDialog(CustomDialog):
    def __init__(self, parent, classList=pd.DataFrame()):
        super().__init__(parent)
        self.init_ui(classList)

    def init_ui(self, classList):
        self.setWindowTitle('Edit Parameter List: hidden layers')
        self.setWindowIconText(chr(0xf044))
        self.dialogLayout = QVBoxLayout()
        self.dialogWidget = QWidget()
        self.dialogWidget.setLayout(self.dialogLayout)
        self._layout.addWidget(self.dialogWidget)
        self.listLayout = QHBoxLayout()

        # 设置对话框的介绍信息
        labelLayout = QHBoxLayout()
        labelBtn = QPushButton(QIcon('../icon/edit.ico'), '')
        labelBtn.setObjectName('labelButton')
        labelBtn.setStyleSheet('#labelButton{border: 0}')
        labelBtn.setIconSize(QSize(48, 48))
        labelText = QLabel('Describes the name and the size of all hidden layers.')
        labelLayout.addWidget(labelBtn, 3)
        labelLayout.addWidget(labelText, 7)

        # 放置table用于编辑classes
        self.classTable = QTableWidget()
        self.classTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.classTable.setColumnCount(2)
        self.classTable.setRowCount(classList.shape[0])
        for row in range(classList.shape[0]):
            self.classTable.setItem(row, 0, QTableWidgetItem(classList.iloc[row, 0]))
            self.classTable.setItem(row, 1, QTableWidgetItem(str(classList.iloc[row, 1])))
        self.classTable.setHorizontalHeaderItem(0, QTableWidgetItem('hidden layer names'))
        self.classTable.setHorizontalHeaderItem(1, QTableWidgetItem('hidden layer size'))
        self.classTable.verticalHeader().hide()
        self.classTable.itemChanged.connect(self.contentChange)

        # 放置对话框的取消和确定按钮
        self.buttonBox = QHBoxLayout()
        self.buttonBox.addStretch(1)
        self.addButton = QPushButton(QIcon('../icon/add_notes'), 'Add Entry')
        self.addButton.setIconSize(QSize(24, 24))
        self.addButton.clicked.connect(self.addEntry)
        self.deleteButton = QPushButton(QIcon('../icon/delete_notes'), 'Remove Entry')
        self.deleteButton.setIconSize(QSize(24, 24))
        self.deleteButton.clicked.connect(self.removeEntry)
        self.cancelButton = QPushButton(QIcon('../icon/cancel'), 'Cancel')
        self.cancelButton.setIconSize(QSize(24, 24))
        self.okButton = QPushButton(QIcon('../icon/apply'), 'Apply')
        self.okButton.setIconSize(QSize(24, 24))
        self.buttonBox.addWidget(self.addButton)
        self.buttonBox.addWidget(self.deleteButton)
        self.buttonBox.addWidget(self.okButton)
        self.buttonBox.addWidget(self.cancelButton)
        self.cancelButton.clicked.connect(self.close)

        self.dialogLayout.addLayout(labelLayout)
        self.dialogLayout.addWidget(self.classTable)
        self.dialogLayout.addLayout(self.buttonBox)

        self.setModal(True)
        self.show()

    def addEntry(self):
        self.classTable.insertRow(self.classTable.rowCount())

    def removeEntry(self):
        self.classTable.removeRow(self.classTable.currentRow())

    def contentChange(self, itemchange):
        if itemchange.column() == 1:
            try:
                size = int(itemchange.text())
                if size <= 0:
                    itemchange.setText('5')
            except:
                itemchange.setText('5')




def callDialog(ui):
    df = pd.DataFrame({'className': ['first'], 'limit': [np.Infinity]})
    dialog = HiddenLayerDialog(ui, df)
    dialog.okButton.clicked.connect(lambda : setClass(dialog))

def setClass(dialog):
    names = []
    limits = []
    for row in range(dialog.classTable.rowCount()):
        name = dialog.classTable.item(row, 0)
        limit = dialog.classTable.item(row, 1)
        if name is not None and limit is not None:
            if name.text() != '' and limit.text() != '':
                names.append(name.text())
                limits.append(int(limit.text()))
    df = pd.DataFrame({'className': names, 'limit': limits})
    print(df)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = open('../qss/mainwindow.qss', 'r', encoding='UTF-8')
    app.setStyleSheet(style.read())
    ui = QMainWindow()
    button = QPushButton('ddd', ui)
    button.clicked.connect(lambda: callDialog(ui))
    ui.show()
    sys.exit(app.exec_())
