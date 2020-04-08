# 测试
from PyQt5 import QtCore, QtGui, QtWidgets
from GUI import operatorWidget
from Logic import pandasModel
import pandas as pd
import pickle
import copy
import sys


class MainUi(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(600, 600)
        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # 以下两句使得表格的单元格大小根据内容调整，但是无法在表头手动拉伸
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # self.tableWidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(3)
        item1 = QtWidgets.QTableWidgetItem()
        item1.setText('xxx')
        self.tableWidget.setSpan(1, 0, 1, 3)
        self.tableWidget.setSpan(0, 0, 1, 3)
        self.tableWidget.setSpan(2, 1, 1, 2)
        self.tableWidget.setHorizontalHeaderItem(1, item1)
        #self.tableWidget.setVerticalHeaderItem(2, item1)
        item2 = QtWidgets.QTableWidgetItem()
        item2.setText('+')
        self.tableWidget.setHorizontalHeaderItem(2, item2)
        item = QtWidgets.QTableWidgetItem('fff')
        item.setBackground(QtGui.QBrush(QtGui.QColor(255,0,0)))
        #btn = custombutton('ddd', self, 1, 0)  # convey the whole window when creates a button
        #btn = QtWidgets.QPushButton()
        btn = upButton()
        self.tableWidget.setCellWidget(1, 0, btn)
        self.tableWidget.setItem(0, 0, item)
        btn = QtWidgets.QPushButton()
        pixmap = QtGui.QPixmap("..\\temp\\11.jpg")

        btn.setIcon(QtGui.QIcon('../temp/temp.png'))
        self.tableWidget.setCellWidget(2, 1, btn)
        self.statusBar()
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.contextMenu)
        self.tableWidget.itemClicked.connect(self.clickitem)
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.addcolumn)
        self.tableWidget.verticalHeader().sectionClicked.connect(self.addrow)
        self.tableWidget.cellClicked.connect(self.clickcell) # put widget in the cell
        btn.clicked.connect(lambda: self.clickbtn(btn))
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 256, 192))
        self.tableWidget.setFixedSize(300, 300)
        # print(self.tableWidget.columnSpan(1, 0))  # 某单元格跨了几列
        ### 只有表格中已经布置好的控件才能根据内容调整大小，在下面的语句之后布置的控件将不生效
        self.tableWidget.resizeRowsToContents()


    def addrow(self, index):
        if index == self.tableWidget.rowCount() - 1:
            self.tableWidget.insertRow(self.tableWidget.rowCount() - 1)

    def addcolumn(self, index):
        if index == self.tableWidget.columnCount()-1:
            self.tableWidget.insertColumn(self.tableWidget.columnCount() - 1)

    def clickitem(self, item):
        print(item.text())
        self.statusBar().showMessage(item.text())


    def clickbtn(self, btn):
        print(btn.parent().parent())

    def clickcell(self):
        if self.tableWidget.cellWidget(self.tableWidget.currentRow(), self.tableWidget.currentColumn()) != None:
            print(self.tableWidget.currentColumn())

    def contextMenu(self, pos):
        popMenu = QtWidgets.QMenu()
        ddd = popMenu.addAction('ddd')
        action = popMenu.exec_(self.tableWidget.viewport().mapToGlobal(pos))
        print(action == ddd)


class upButton(QtWidgets.QPushButton):
    def __init__(self):
        super().__init__()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        qp.setPen(QtGui.QColor(167, 167, 167))
        qp.setBrush(QtGui.QColor(220, 220, 220))

        qp.drawRoundedRect(0, 0, 100, 40, 5, 5)


class custombutton(QtWidgets.QPushButton):
    def __init__(self, str, window, row, column):
        super().__init__(str)
        self.init_ui(window, row, column)

    def init_ui(self, window, row, column):
        self.statusbar = window.statusBar()
        self.clicked.connect(self.clickbtn)
        self.window = window

    def clickbtn(self):
        self.statusbar.showMessage('look')
        #self.window.tableWidget.removeCellWidget(1, 0)
        self.window.tableWidget.clearSpans()
        #self.window.tableWidget.removeCellWidget(1, 0)
        self.window.tableWidget.updateGeometries()  # 合并拆分单元格后item会马上变化，但是cellwidget需要刷新布局才行


class hhh(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        a = 10
        b = a
        a = 5
        print(a)
        print(b)
        self.setMinimumSize(600, 600)
        self.widget = QtWidgets.QWidget(self)
        self.layout = QtWidgets.QGridLayout()
        self.widget.setLayout(self.layout)
        label1 = QtWidgets.QLabel('input')
        layout1 = QtWidgets.QVBoxLayout()
        for i in range(5):
            layout1.addWidget(customButton(str(i), 1), 1)
        self.layout.addWidget(label1, 0, 0, 1, 1, QtCore.Qt.AlignCenter)
        self.layout.addLayout(layout1, 1, 0, 1, 1, QtCore.Qt.AlignCenter)
        label1 = QtWidgets.QLabel('output')
        layout1 = QtWidgets.QVBoxLayout()
        for i in range(6):
            layout1.addWidget(customButton(str(i), 3), 1)
        self.layout.addWidget(label1, 0, 1, 1, 1, QtCore.Qt.AlignCenter)
        self.layout.addLayout(layout1, 1, 1, 1, 1, QtCore.Qt.AlignCenter)
        print(self.layout.itemAt(3).layout().count())
        self.setCentralWidget(self.widget)


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLines(qp)
        qp.end()

    def drawLines(self, qp):
        # We create a QPen object. The colour is black.
        # The width is set to 2 pixels so that we can see the differences between the pen styles.
        # Qt.SolidLine is one of the predefined pen styles
        pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine)

        qp.setPen(pen)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        # drawLine(int x1, int y1, int x2, int y2) draws a line from (x1, y1) to (x2, y2)
        qp.drawLine(self.layout.itemAt(1).layout().itemAt(0).geometry().center(), self.layout.itemAt(3).layout().itemAt(0).geometry().center())
        qp.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 100), 1, QtCore.Qt.SolidLine))
        qp.drawLine(self.layout.itemAt(1).layout().itemAt(1).geometry().center(), self.layout.itemAt(3).layout().itemAt(0).geometry().center())




class customButton(QtWidgets.QPushButton):
    def __init__(self, tooltip: str, color: int):
        super().__init__()
        self.color = ['rgb(250, 233, 209)', 'rgb(233, 233, 233)', 'rgb(220,227,242)']
        self.setStyleSheet("QPushButton{border:1px solid black; border-radius:10px; "
                           "height: 20; width:20; background-color: " + self.color[color % 3] +"}")
        self.setToolTip(tooltip)



def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = hhh()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
