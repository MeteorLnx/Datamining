from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from Logic import pandasModel
from os.path import split, splitext
from GUI.titleBar import CustomDialog, CustomMessage
import pandas as pd
import chardet
import sys


class AddDataDialog(CustomDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Data')
        self.setWindowIconText(chr(0xf067))
        self.dialogWidget = QWidget()
        self.dialogLayout = QGridLayout()
        self.dialogWidget.setLayout(self.dialogLayout)
        self._layout.addWidget(self.dialogWidget)
        self.button = QPushButton('Choose File', self)
        self.button.clicked.connect(self.chooseFile)
        self.dialogLayout.addWidget(self.button, 0, 0, 1, 5)
        self.label = QLabel('Rename Dataset:')
        self.rename = QLineEdit()
        self.dialogLayout.addWidget(self.label, 1, 0, 1, 2)
        self.dialogLayout.addWidget(self.rename, 1, 2, 1, 3)
        self.dataArea = QTableView()
        self.dialogLayout.addWidget(self.dataArea, 2, 0, 1, 5)
        self.cancelButton = QPushButton('Cancel')
        self.okButton = QPushButton('OK')
        self.okButton.setDisabled(True)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.okButton)
        self.cancelButton.clicked.connect(self.close)
        self.dialogLayout.addLayout(self.buttonLayout, 3, 0, 1, 5)
        self.setModal(True)
        self.show()


    def chooseFile(self):
        # 打开文件窗口获取文件路径
        fname = QFileDialog.getOpenFileName(self, 'Open file', '../dataset', 'csv(*.csv)')
        # 判断文件路径是否为空，不为空时，以二进制格式打开文件
        if fname[0]:
            with open(fname[0], 'rb') as f1:
                # 获取文件的字符编码，并以该编码再次打开文件
                encode = chardet.detect(f1.read()).get('encoding')
                with open(fname[0], encoding=encode) as f2:
                    try:
                        # 将文件内容存储在Pandas的DataFrame中
                        self.df = pd.read_csv(f2)
                    except:
                        # 如果读取csv文件出错，通知用户，并禁用添加数据窗口的ok按钮
                        CustomMessage(self, 'Error',
                                      'The format of selected dataset is wrong.')
                        self.okButton.setDisabled(True)
                        return

            # 将文件绝对路径的文件名提取出来（不带后缀），并将其显示在重命名输入框中
            self.rename.setText(splitext(split(fname[0])[1])[0])
            # 将数据集内容显示在窗口中
            model = pandasModel.PandasModel(self.df)
            self.dataArea.setModel(model)
            # 不再禁用添加数据窗口的ok按钮
            self.okButton.setDisabled(False)


def callDialog(ui):
    dialog = AddDataDialog(ui)
    dialog.okButton.clicked.connect(lambda: getData(dialog))


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
