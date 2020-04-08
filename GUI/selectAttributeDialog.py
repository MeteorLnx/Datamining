from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from GUI.titleBar import CustomDialog
import sys


class SelectAttrDialog(CustomDialog):
    def __init__(self, parent, attribute: list, selected: list):
        super().__init__(parent)
        self.init_ui(attribute, selected)

    def init_ui(self, attribute, selected):
        self.setWindowTitle('Select Attributes')
        self.setWindowIconText(chr(0xf14a))
        self.dialogWidget = QWidget()
        self.dialogLayout = QVBoxLayout()
        self.dialogWidget.setLayout(self.dialogLayout)
        self._layout.addWidget(self.dialogWidget)
        self.listLayout = QHBoxLayout()

        # 显示未选择的属性
        self.attributeBox = QGroupBox()
        self.attributeBox.setTitle('Attributes')
        self.attributeLayout = QVBoxLayout()
        self.attributeList = QListWidget()
        for item in attribute:
            if item not in selected:
                self.attributeList.addItem(QListWidgetItem(item))
        self.attributeLayout.addWidget(self.attributeList)
        self.attributeBox.setLayout(self.attributeLayout)

        # 显示已选择的属性
        self.selectedBox = QGroupBox()
        self.selectedBox.setTitle('Selected Attributes')
        self.selectedLayout = QVBoxLayout()
        self.selectedList = QListWidget()
        for item in selected:
            self.selectedList.addItem(QListWidgetItem(item))
        self.selectedLayout.addWidget(self.selectedList)
        self.selectedBox.setLayout(self.selectedLayout)

        # 放置两个按钮，控制属性的选择和取消选择
        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.addStretch(1)
        self.selectButton = QPushButton(QIcon('..\\icon\\right.ico'), '')
        self.unselectButton = QPushButton(QIcon('..\\icon\\left.ico'), '')
        self.selectButton.clicked.connect(self.selectAttribute)
        self.unselectButton.clicked.connect(self.unselectAttribute)
        self.buttonLayout.addWidget(self.selectButton)
        self.buttonLayout.addWidget(self.unselectButton)
        self.buttonLayout.addStretch(1)

        # 放置对话框的取消和确定按钮
        self.buttonBox = QHBoxLayout()
        self.buttonBox.addStretch(1)
        self.cancelButton = QPushButton('Cancel')
        self.okButton = QPushButton('Apply')
        self.buttonBox.addWidget(self.cancelButton)
        self.buttonBox.addWidget(self.okButton)
        self.cancelButton.clicked.connect(self.close)

        self.listLayout.addWidget(self.attributeBox, 6)
        self.listLayout.addLayout(self.buttonLayout, 1)
        self.listLayout.addWidget(self.selectedBox, 6)
        self.dialogLayout.addLayout(self.listLayout)
        self.dialogLayout.addLayout(self.buttonBox)

        self.setModal(True)
        self.show()

    def selectAttribute(self):
        if self.attributeList.currentItem() is not None:
            self.selectedList.addItem(self.attributeList.takeItem(self.attributeList.currentRow()).text())

    def unselectAttribute(self):
        if self.selectedList.currentItem() is not None:
            self.attributeList.addItem(self.selectedList.takeItem(self.selectedList.currentRow()).text())

def callDialog(ui):
    dialog = SelectAttrDialog(ui, ['a', 'b', 'c'], ['a'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = QMainWindow()
    button = QPushButton('ddd', ui)
    button.clicked.connect(lambda: callDialog(ui))
    ui.show()
    sys.exit(app.exec_())
