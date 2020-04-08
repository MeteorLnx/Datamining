import sys
sys.path.append('D:\\develop\\Python\\DataMining')  # 在pycharm中运行时可不加此语句，路径记得修改为自己的路径
from PyQt5 import QtCore, QtWidgets, QtGui
from GUI import mainwindow_nologic, addDataDialog, operatorWidget, addOperatorDialog, loginDialog, titleBar
from Logic import databaseOperation
import pandas as pd
import numpy as np
import json
import operator
import re
import sys
import copy


class MainWindow(object):
    def __init__(self):
        self.dataset = {'example': pd.DataFrame({'a': [1, np.nan, 3, 4, 1],
                                                 'b': [4, 5, np.nan, 6, 4],
                                                 'c': ['d', 'e', np.nan, 'g', 'd']}),
                        'tips': pd.read_csv('../dataset/tips.csv')}
        # 使用字典存放操作符名称
        self.operators = {'Retrieve': {},
                          'Blending': {'Attributes': ['Select Attributes'],
                                       'Examples': ['Select Examples']},
                          'Cleansing': {'Normalization': ['Normalize'],
                                        'Binning': ['Discretize by Binning', 'Discretize by User Specification'],
                                        'Missing': ['Remove Missing Values', 'Replace Missing Values'],
                                        'Duplicates': ['Remove Duplicates'],
                                        'Dimensonality Reductuion': ['Principal Component Analysis']},
                          'Modeling': {'Classification': ['Feature Selection', 'Decision Trees', 'Neural Network Models'],
                                  'Clustering': ['K-means'],
                                  'Correlations': ['Correlation Matrix'],
                                  'Time Series Analysis': ['Exponential Smoothing']},
                          'Apply Model': {},
                          'Result': {}}
        with open('help_message.json', 'r') as f:
            self.message = json.load(f)
        self.process = []
        self.account = ['lnx123']
        app = QtWidgets.QApplication(sys.argv)
        style = open('../qss/mainwindow.qss', 'r', encoding='UTF-8')
        app.setStyleSheet(style.read())
        self.ui = mainwindow_nologic.MainUi(self.dataset, self.operators)
        self.ui.addDataButt.clicked.connect(self.showAddDataDialog)  # 点击按钮添加数据源
        self.ui.processWidget.horizontalHeader().sectionClicked.connect(self.addcolumn)  # 表格增加一列
        self.ui.processWidget.verticalHeader().sectionClicked.connect(self.addrow)  # 表格增加一行
        # 通过右键菜单进行控件添加
        self.ui.processWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.processWidget.customContextMenuRequested.connect(self.processContextMenu)
        # 关闭标签页
        self.ui.result_layout.itemAt(0).widget().tabCloseRequested.connect(self.closeTab)
        # 数据区右键菜单
        self.ui.dataList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.dataList.customContextMenuRequested.connect(self.dataContextMenu)
        # 操作符区点击响应帮助信息
        self.ui.treeWidget.clicked.connect(self.showHelpMessage)
        # 点击工作区的单元格出现对应操作符的参数设置
        self.ui.processWidget.cellClicked.connect(self.showParameterSetting)
        # 运行运算程序
        self.ui.runProject.clicked.connect(self.runProject)
        # 打开已有程序
        self.ui.open_process.triggered.connect(self.openProcess)
        # 保存程序
        self.ui.save_process.triggered.connect(self.saveProcess)
        # 清空工作台
        self.ui.clearProcess.clicked.connect(self.clearProcess)
        # 将全部界面放进无边框的窗口
        self.window = titleBar.FramelessWindow()
        # 窗口的登出按钮绑定事件
        self.window.logout.triggered.connect(self.logout)
        self.window.setObjectName('mainwindow')
        self.window.setWindowTitle('Data Mining')
        self.window.setWidget(self.ui)  # 把自己的窗口添加进来
        # 让窗口居中
        deskdop = QtWidgets.QApplication.desktop()
        width = (deskdop.width() - self.window.width()) / 2
        height = (deskdop.height() - self.window.height()) / 2
        self.window.move(QtCore.QPoint(width, height))
        self.ui.exit_action.triggered.connect(self.window.close)
        # 弹出登录窗口，为登录窗口的登录按钮和注册按钮绑定事件
        # 由于登录需要连接数据库，所以没有数据库时可不使用下面登录相关的语句，避免弹出登录窗口
        #self.login = loginDialog.LoginDialog(self.window, self.account)
        #self.login.login_btn.clicked.connect(self.loginCheck)
        #self.login.register_btn.clicked.connect(self.register)
        # 记录当前是否有复制操作符
        self.pasteop = None

        self.window.show()
        sys.exit(app.exec_())

    def loginCheck(self):
        userName = self.login.name_box.currentText()
        password = self.login.passwd_box.text()
        query = databaseOperation.UserManagement()
        result = query.select(userName)
        if result:
            if password == result[1]:
                self.login.close()
                self.window.userMenu.setTitle(userName)
                if userName not in self.account:
                    self.account.append(userName)
            else:
                self.login.message.setText('* Incorrect username or password!')
        else:
            self.login.message.setText('* User does not exist!')

    def register(self):
        dialog = loginDialog.RegisterDialog(self.login)
        dialog.register_btn.clicked.connect(lambda: self.registerUser(dialog))

    def registerUser(self, dialog: loginDialog.RegisterDialog):
        userName = dialog.name_box.text()
        pwd = dialog.passwd_box.text()
        cpwd = dialog.confirmpwd_box.text()
        email = dialog.email_box.text()
        query = databaseOperation.UserManagement()
        result = query.select(userName)
        if result:
            dialog.message.setText('* User already exist! \n  Please enter another username.')
            return
        if len(userName) < 6 or len(userName) > 12:
            dialog.message.setText('* The length of username is incorrect.')
            return
        if len(pwd) < 6 or len(pwd) > 12:
            dialog.message.setText('* The length of password is incorrect.')
            return
        if pwd != cpwd:
            dialog.message.setText('* The two passwords differ.')
            return
        p = re.compile('^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
        x = p.match(email)
        if x is None:
            dialog.message.setText('* The E-mail address format is incorrect.')
            return
        res = query.register(userName, pwd, email)
        if res:
            dialog.close()
            self.login.name_box.setEditText(userName)
        else:
            dialog.message.setText(' User created failed')

    def logout(self):
        self.login = loginDialog.LoginDialog(self.window, self.account)
        self.login.login_btn.clicked.connect(self.loginCheck)
        self.login.register_btn.clicked.connect(self.register)

    def runProject(self):
        # 记录输入是否满足
        connect_flag = True
        # 记录是否有结果展示组件
        result_flag = False
        for item in self.process:
            if isinstance(item[0], operatorWidget.Result):
                result_flag = True
            if len(item[0].input) >= item[3]:
                lastOperator = item[0].findLastOperator(self.process, item)
                if lastOperator is None or len(lastOperator[0].output) == 0:
                    connect_flag = False
                    titleBar.CustomMessage(self.ui, 'Warning', item[0].objectName()+': Input is missing.')
                    break
        # 如果输入和结果展示组件都满足，继续运行程序，否则通知用户
        if connect_flag:
            if result_flag:
                try:
                    tabWidget = QtWidgets.QTabWidget()
                    tabWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
                    tabWidget.setTabsClosable(True)
                    tabWidget.tabCloseRequested.connect(self.closeTab)
                    tabWidget.setMovable(True)
                    tabWidget.setObjectName('resultTab')
                    '''
                    首先找出运算符的正确运算顺序，即拓扑排序
                    （因为有输入输出的先后关系，若有多个输入，
                    则多个输入之前的运算符都应该运算完毕）
                    '''
                    temp = []
                    queue = []
                    for item in self.process:
                        if item[3] == 1:
                            temp.append([item, len(item[0].input)])
                    while temp:
                        temp.sort(key=operator.itemgetter(1))
                        # 找到第一个0输入的运算符
                        first = temp[0][0]
                        next = []
                        # 找出与第一个连接的下一个运算符（注意：有可能有两个）
                        next.append(first[0].findNextOperator(self.process, first))
                        if first[0].columnspan == 2:
                            next.append(first[0].findNextOperator(self.process, [first[0], first[1]+1, first[2], 2]))

                        # 让后边的结点入度减一（即输入数量减一）
                        for (i, next_op) in enumerate(next):
                            if next_op is not None:
                                if len(next_op[0].input) > 0:
                                    op = next_op
                                    if next_op[3] == 2:
                                        op = [next_op[0], next_op[1] - 1, next_op[2], 1]
                                    op = temp[[x[0] for x in temp].index(op, 0, len(temp))]
                                    if op[1] > 0:
                                        op[1] -= 1
                        # 将temp中第一个弹出，并加入队列中
                        queue.append(temp.pop(0)[0])

                    # 正式开始执行队列中的运算符
                    current = ''
                    for item in queue:
                        '''检查运算符输入数量，一次性获取所有的输入
                        （根据输入数量不同有不同的做法）后运行程序，
                        如果是retrieve或者result，则区别对待'''
                        current = item[0].objectName()
                        if len(item[0].input) == 1:
                            if isinstance(item[0], operatorWidget.Result):
                                result = item[0].showResult()
                                last = item[0].findLastOperator(self.process, item)
                                tabWidget.addTab(result, last[0].showName[last[3]-1])
                            else:
                                last = item[0].findLastOperator(self.process, item)
                                item[0].setInput(last[0].getResult(last[3]))
                                item[0].runOperator()
                        elif len(item[0].input) == 2:
                            last = item[0].findLastOperator(self.process, item)
                            item[0].setInput(last[0].getResult(last[3]), 1)
                            last = item[0].findLastOperator(self.process, [item[0], item[1]+1, item[2], 2])
                            item[0].setInput(last[0].getResult(last[3]), 2)
                            item[0].runOperator()
                    _lasttab = self.ui.result_layout.itemAt(0)
                    if _lasttab is not None:
                        _lasttab.widget().deleteLater()
                    self.ui.result_layout.addWidget(tabWidget, 0, 0)
                    self.ui.main_widget.setCurrentIndex(1)
                except:
                    print('run error')
                    titleBar.CustomMessage(self.ui, 'Error', 'An error occured: ' + current + '.')
            else:
                titleBar.CustomMessage(self.ui, 'Warning', 'To view results, please add Result operator.')

    def closeTab(self, index):
        self.ui.result_layout.itemAt(0).widget().removeTab(index)

    def showAddDataDialog(self):
        dialog = addDataDialog.AddDataDialog(self.ui)
        dialog.okButton.clicked.connect(lambda: self.getData(dialog))

    def getData(self, dialog):
        # 获取数据集重命名，如果导入的数据集名称与系统中其他数据集相同，通知用户
        name = dialog.rename.text()
        if name in self.dataset.keys():
            titleBar.CustomMessage(self.ui, 'Warning', 'Duplicate dataset name.')
            return
        # 将存放数据集内容的DataFrame及名称存储到字典中
        self.dataset[name] = dialog.df
        dialog.close()
        # 将数据集名称添加到程序设计页面中
        item = QtWidgets.QListWidgetItem(name)
        self.ui.dataList.addItem(item)
        self.ui.dataList.updateGeometry()

    def addrow(self, index):
        if index == self.ui.processWidget.rowCount() - 1:
            self.ui.processWidget.insertRow(self.ui.processWidget.rowCount() - 1)

    def addcolumn(self, index):
        if index == self.ui.processWidget.columnCount()-1:
            self.ui.processWidget.insertColumn(self.ui.processWidget.columnCount() - 1)

    def addOperator(self, row, column):
        if self.ui.processWidget.cellWidget(row, column) is None:
            dialog = addOperatorDialog.AddOperatorDialog(self.ui, self.operators)
            dialog.okButton.clicked.connect(lambda: self.getOperator(dialog, row, column))

    def getOperator(self, dialog, row, column):
        name = dialog.comboboxs[-1].currentText()
        dialog.close()
        newoperator = eval('operatorWidget.' + name.replace(' ', '_').replace('-', '_'))(row, column, self.dataset, self.process)
        self.insertOperator(row, column, newoperator)
        self.showParameterSetting(row, column)

    def insertOperator(self, row: int, column: int, newoperator):
        for i in range(0, newoperator.columnspan):
            self.process.insert(self.insertOperatorIndex(column+i, row), [newoperator, column+i, row, i+1])
        self.ui.processWidget.setSpan(row, column, 1, newoperator.columnspan)
        self.ui.processWidget.setCellWidget(row, column, newoperator)
        self.ui.processWidget.resizeRowToContents(row)

    def deleteOperator(self, row, column):
        operator = self.ui.processWidget.cellWidget(row, column)
        self.ui.processWidget.removeCellWidget(row, column)
        for i in range(0, operator.columnspan):
            self.process.remove([operator, column + i, row, i + 1])
        operator.deleteLater()
        self.ui.processWidget.setSpan(row, column, 1, 1)

    def insertOperatorIndex(self, column, row):
        if self.process:
            i = 0
            for item in self.process:
                if item[1] > column or (item[1] == column and item[2] > row):
                    return i
                i += 1
            return i
        else:
            return 0

    def clearProcess(self):
        for item in self.process:
            if item[3] == 1:
                self.ui.processWidget.removeCellWidget(item[2], item[1])
                self.ui.processWidget.setSpan(item[2], item[1], 1, 1)
        self.process = []

    def openProcess(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self.ui, 'Open process', '../process', 'csv(*.csv)')
        # 判断文件路径是否为空
        if fname[0]:
            with open(fname[0]) as f:
                try:
                    # 将文件内容存储在Pandas的DataFrame中
                    df = pd.read_csv(f)
                    if set(['row', 'column', 'operator']) == set(df.columns):
                        self.clearProcess()
                        for i in range(df.shape[0]):
                            op = eval('operatorWidget.' + df.iloc[i,2])(df.iloc[i, 0],
                                                                        df.iloc[i, 1], self.dataset, self.process)
                            self.insertOperator(df.iloc[i, 0], df.iloc[i, 1], op)
                        self.ui.processWidget.updateGeometry()
                    else:
                        titleBar.CustomMessage(self.ui, 'Error',
                                               'The file is not a process.')
                except:
                    # 如果读取csv文件出错，通知用户
                    titleBar.CustomMessage(self.ui, 'Error',
                                    'Can not open the process.')


    def saveProcess(self):
        if self.process:
            fname = QtWidgets.QFileDialog.getSaveFileName(self.ui, 'Save process', '../process', 'csv(*.csv)')
            if fname[0]:
                df = pd.DataFrame(columns=['row', 'column', 'operator'])
                for item in self.process:
                    if item[3] == 1:
                        df = df.append({'row': item[2], 'column': item[1],
                                        'operator': item[0].__class__.__name__}, ignore_index=True)
                df.to_csv(fname[0], index=False)
                titleBar.CustomMessage(self.ui, 'Success', 'Process successfully saved.', 2)
        else:
            titleBar.CustomMessage(self.ui, 'Error', 'The process is empty.')

    def processContextMenu(self, pos):
        index = self.ui.processWidget.indexAt(pos)
        if index.isValid():
            popMenu = QtWidgets.QMenu()
            add = popMenu.addAction(QtGui.QIcon('../icon/add.ico'), 'Add Operator')
            delete = popMenu.addAction(QtGui.QIcon('../icon/delete.ico'), 'Delete Operator')
            cut = popMenu.addAction(QtGui.QIcon('../icon/cut.ico'), 'Cut')
            copy = popMenu.addAction(QtGui.QIcon('../icon/copy.ico'), 'Copy')
            paste = popMenu.addAction(QtGui.QIcon('../icon/paste.ico'), 'Paste')
            child = self.ui.processWidget.cellWidget(index.row(), index.column())
            if child is not None:
                add.setEnabled(False)
                paste.setEnabled(False)
                action = popMenu.exec_(self.ui.processWidget.viewport().mapToGlobal(pos))
                if action == cut or action == copy:
                    self.pasteop = self.copyOperator(child)
                if action == delete or action == cut:
                    self.deleteOperator(index.row(), index.column())
                    self.showParameterSetting(index.row(), index.column())
            else:
                delete.setEnabled(False)
                cut.setEnabled(False)
                copy.setEnabled(False)
                if self.pasteop is None:
                    paste.setEnabled(False)
                action = popMenu.exec_(self.ui.processWidget.viewport().mapToGlobal(pos))
                if action == add:
                    self.addOperator(index.row(), index.column())
                elif action == paste:
                    newOp = self.copyOperator(self.pasteop)
                    newOp.setIndex(index.row(), index.column())
                    self.insertOperator(index.row(), index.column(), newOp)
                    self.showParameterSetting(index.row(), index.column())

    def copyOperator(self, op):
        newOp = eval('operatorWidget.'+op.__class__.__name__)(-1, -1, self.dataset, self.process)
        newOp.parametersSetting = copy.deepcopy(op.parametersSetting)
        setting = op.__dict__
        if 'choice' in setting.keys():
            newOp.choice = copy.deepcopy(setting['choice'])
        if 'classList' in setting.keys():
            newOp.classList = copy.deepcopy(setting['classList'])
        if 'fillvalue' in setting.keys():
            newOp.fillvalue = setting['fillvalue']
        if 'hiddenLayer' in setting.keys():
            newOp.hiddenLayer = copy.deepcopy(setting['hiddenLayer'])
        return newOp

    def dataContextMenu(self, pos):
        item = self.ui.dataList.itemAt(pos)
        if item is not None:
            popMenu = QtWidgets.QMenu()
            view = popMenu.addAction(QtGui.QIcon('../icon/view.ico'), 'View example set')
            delete = popMenu.addAction(QtGui.QIcon('../icon/delete.ico'), 'Delete example set')
            action = popMenu.exec_(self.ui.dataList.viewport().mapToGlobal(pos))
            if action == view:
                addPage = operatorWidget.CustomWidget().showExampleSet(self.dataset[item.text()])
                tab = self.ui.result_layout.itemAt(0).widget()
                tab.addTab(addPage, item.text())
                tab.setCurrentIndex(tab.indexOf(addPage))
                self.ui.main_widget.setCurrentIndex(1)
            elif action == delete:
                self.dataset.pop(item.text())
                self.ui.dataList.takeItem(self.ui.dataList.row(item))
                del item

    def showHelpMessage(self):
        item = self.ui.treeWidget.currentItem()
        if item.text(0) in self.message.keys():
            self.ui.helpLayout.itemAt(1).widget().setText(item.text(0))
            self.ui.helpMessage.setText(self.message[item.text(0)])

    def showParameterSetting(self, row, column):
        currentOperator = self.ui.processWidget.cellWidget(row, column)
        last_setting = self.ui.splitLayout.takeAt(0).widget()
        last_setting.deleteLater()
        if currentOperator is not None:
            self.ui.settingLayout.itemAt(1).widget().setText(currentOperator.__class__.__name__.replace('_', ' '))
            self.ui.splitLayout.insertWidget(0, currentOperator.parameterWidget())
        else:
            self.ui.settingLayout.itemAt(1).widget().setText('Process')
            self.ui.splitLayout.insertWidget(0, QtWidgets.QWidget())


if __name__ == "__main__":
    MainWindow()
