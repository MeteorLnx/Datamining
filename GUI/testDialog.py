# 测试对话框
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from Logic import pandasModel
from os.path import split, splitext
from GUI.titleBar import CustomDialog, CustomMessage
import pandas as pd
import chardet
import sys


def callDialog(ui):
    dialog = QFileDialog.getSaveFileName(ui, 'Save file', '', 'csv(*.csv)')
    print(dialog)

def getData(dialog):
    data = dialog.df
    name = dialog.rename.text()
    print(data)
    print(name)
    dialog.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = QMainWindow()
    button = QPushButton('ddd', ui)
    button.clicked.connect(lambda: callDialog(ui))
    ui.show()
    sys.exit(app.exec_())
