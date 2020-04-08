from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QPainter, QPen, QColor, QDrag
from Logic import pandasModel
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans
from sklearn.feature_selection import chi2, f_classif, mutual_info_classif, SelectKBest
from GUI import selectAttributeDialog, editClassDialog
from GUI.titleBar import CustomMessage
from id3 import Id3Estimator, export_graphviz, export_text
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from datetime import datetime
import pandas as pd
import numpy as np
import pyqtgraph as pg
import graphviz
import sys


class CustomWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row = -1
        self.column = -1
        self.input = {}
        self.output = {}
        self.parametersSetting = {}

    def setIndex(self, row:int, column:int):
        self.row = row
        self.column = column

    def setInput(self, input):
        pass

    def getResult(self, which=1):
        pass

    def showResult(self, which=1):
        pass

    def parameterWidget(self):
        pass

    def runOperator(self):
        pass

    def applyModel(self, test_data):
        pass

    def paintEvent(self, e):
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        # 反锯齿
        painter.setRenderHint(QPainter.Antialiasing)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, painter, self)

    # 查找上一个组件
    def findLastOperator(self, process: list, item):
        if process:
            i = process.index(item, 0, len(process)) - 1
            if i >= 0:
                if process[i][1] == item[1]:
                    return process[i]
        return None

    def findNextOperator(self, process: list, item):
        if process:
            i = process.index(item, 0, len(process)) + 1
            if i < len(process):
                if process[i][1] == item[1]:
                    return process[i]
        return None

    def showExampleSet(self, dataset=None):
        resultTab = QtWidgets.QTabWidget()
        resultTab.setTabPosition(QtWidgets.QTabWidget.West)
        if dataset is not None:
            dataWidget = QtWidgets.QWidget()
            dataLayout = QtWidgets.QVBoxLayout()
            dataWidget.setLayout(dataLayout)
            statWidget = QtWidgets.QWidget()
            statLayout = QtWidgets.QVBoxLayout()
            statWidget.setLayout(statLayout)
            resultTab.addTab(dataWidget, 'Data')
            resultTab.addTab(statWidget, 'Statistics')
            numberLayout = QtWidgets.QHBoxLayout()
            numberLayout.addWidget(QtWidgets.QLabel(
                'Exampleset(%d examples)' % dataset.shape[0]))
            saveBtn = QtWidgets.QPushButton('Export')
            saveBtn.setObjectName('exportData')
            saveBtn.clicked.connect(lambda: self.saveDataset(dataset))
            numberLayout.addWidget(saveBtn)
            numberLayout.addStretch(1)
            dataArea = QtWidgets.QTableView()
            model = pandasModel.PandasModel(dataset)
            dataArea.setModel(model)
            dataLayout.addLayout(numberLayout)
            dataLayout.addWidget(dataArea)
            if not dataset.select_dtypes(include=np.number).empty:
                model = pandasModel.PandasModel(dataset.describe(include=np.number).T.round(4))
                statArea = QtWidgets.QTableView()
                statArea.setModel(model)
                statLayout.addWidget(statArea)
            if not dataset.select_dtypes(include=[np.object, 'category']).empty:
                model = pandasModel.PandasModel(dataset.describe(include=[np.object, 'category']).T)
                statArea = QtWidgets.QTableView()
                statArea.setModel(model)
                statLayout.addWidget(statArea)
        return resultTab

    def saveDataset(self, dataset):
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Export dataset', '', 'csv(*.csv)')
        if fname[0]:
            dataset.to_csv(fname[0], index=False)
            CustomMessage(self, 'Success', 'Data successfully exported.', 2)


# 存放cleansing中组件的重复函数
class CleansingWidget(CustomWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setChoice(self, playout, choice):
        setting = playout.takeAt(3)
        if setting != None:
            setting.widget().deleteLater()
            playout.takeAt(2).widget().deleteLater()
        self.parametersSetting['choice'] = choice
        if choice == 'Single':
            self.showSingleSetting(playout)
        elif choice == 'Subset':
            self.showSubsetSetting(playout)
        self.runOperator()

    def showSingleSetting(self, playout):
        label = QtWidgets.QLabel('Attribute')
        attributeBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].select_dtypes(include=np.number).columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            attributeBox.setModel(boxModel)
            if self.choice['Single'] in self.input['data'].select_dtypes(include=np.number).columns:
                attributeBox.setCurrentText(self.choice['Single'])
            else:
                self.choice['Single'] = attributeBox.currentText()
        attributeBox.activated.connect(self.setSingleAttribute)
        playout.addWidget(label)
        playout.addWidget(attributeBox)

    def showSubsetSetting(self, playout):
        label = QtWidgets.QLabel('Attributes')
        attributeBtn = QtWidgets.QPushButton('Select Attributes')
        attributeBtn.setToolTip('Open a dialog to select the attributes')
        attributeBtn.clicked.connect(self.callDialog)
        playout.addWidget(label)
        playout.addWidget(attributeBtn)

    def callDialog(self):
        if self.input['data'] is not None:
            dialog = selectAttributeDialog.SelectAttrDialog(self, self.input['data'].select_dtypes(include=np.number).columns,
                                      self.choice['Subset'])
            dialog.okButton.clicked.connect(lambda: self.setSubsetAttribute(dialog))
        else:
            dialog = selectAttributeDialog.SelectAttrDialog(self, [], [])
            dialog.okButton.clicked.connect(dialog.close)

    def setSingleAttribute(self):
        self.choice['Single'] = self.sender().currentText()
        self.runOperator()

    def setSubsetAttribute(self, dialog):
        subset = []
        for i in range(dialog.selectedList.count()):
            subset.append(dialog.selectedList.item(i).text())
        self.choice['Subset'] = subset
        dialog.close()
        self.runOperator()


# 获取数据的操作符
class Retrieve(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.parametersSetting = {'Dataset': None}
        self.output = {'data': None}
        self.showName = ['Retrieve(example)']
        self.setObjectName('Retrieve')
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(180, 180, 180, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        label = QtWidgets.QLabel(self.__class__.__name__)
        # label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 0, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Output Example'), 2, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    # 返回参数设置页面
    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Choose Dataset')
        datasetBox = QtWidgets.QComboBox()
        datasetBox.setMinimumContentsLength(12)
        boxModel = QStandardItemModel()
        for name in self.datalist.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        datasetBox.setModel(boxModel)
        datasetBox.setCurrentText(self.parametersSetting['Dataset'])
        if self.datalist.keys():
            self.parametersSetting['Dataset'] = datasetBox.currentText()
            self.output['data'] = self.datalist[self.parametersSetting['Dataset']]
        else:
            self.parametersSetting['Dataset'] = None
            self.output['data'] = None
        playout.addWidget(label, 0, 0)
        playout.addWidget(datasetBox, 0, 1)
        datasetBox.activated.connect(self.setDataset)
        playout.setColumnStretch(0, 1)
        playout.setColumnStretch(1, 1)
        return pwidget

    # 设置输入
    def setDataset(self, index):
        self.parametersSetting['Dataset'] = self.sender().itemText(index)
        self.showName[0] = 'Retrieve(' + self.sender().itemText(index) + ')'
        self.output['data'] = self.datalist[self.parametersSetting['Dataset']]

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab


class Select_Attributes(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Select Attributes']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Select\nAttributes')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        playout.addWidget(label)
        playout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(playout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(playout)
        typeBox.activated.connect(lambda: self.setChoice(playout, typeBox.currentText()))
        return pwidget

    def showSingleSetting(self, playout):
        label = QtWidgets.QLabel('Attribute')
        attributeBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            attributeBox.setModel(boxModel)
            if self.choice['Single'] in self.input['data'].columns:
                attributeBox.setCurrentText(self.choice['Single'])
            else:
                self.choice['Single'] = attributeBox.currentText()
        attributeBox.activated.connect(self.setSingleAttribute)
        playout.addWidget(label)
        playout.addWidget(attributeBox)

    def callDialog(self):
        if self.input['data'] is not None:
            dialog = selectAttributeDialog.SelectAttrDialog(self, self.input['data'].columns,
                                      self.choice['Subset'])
            dialog.okButton.clicked.connect(lambda: self.setSubsetAttribute(dialog))
        else:
            dialog = selectAttributeDialog.SelectAttrDialog(self, [], [])
            dialog.okButton.clicked.connect(dialog.close)

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            output = self.input['data'].copy()
            if self.parametersSetting['choice'] == 'All':
                items = output.columns
            elif self.parametersSetting['choice'] == 'Single':
                if self.choice['Single'] not in output.columns:
                    items = []
                else:
                    items = [self.choice['Single']]
            else:
                if set(self.choice['Subset']).issubset(set(output.columns)):
                    items = self.choice['Subset']
                else:
                    items = []
            try:
                output = output[items]
            except:
                print('Selece Attributes error')
                output = None
        self.output['data'] = output


class Select_Examples(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Select Examples']
        self.parametersSetting = {'first': 0, 'last': 0}
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Select\nExamples')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('Input Example Range')
        label2 = QtWidgets.QLabel('First Example')
        first = QtWidgets.QLineEdit(str(self.parametersSetting['first']))
        first.editingFinished.connect(self.setFirst)
        label3 = QtWidgets.QLabel('Last Example')
        last = QtWidgets.QLineEdit(str(self.parametersSetting['last']))
        last.editingFinished.connect(self.setLast)
        playout.addWidget(label1, 0, 0, 1, 2)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(first, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(last, 2, 1, 1, 1)
        return pwidget

    def setFirst(self):
        try:
            self.parametersSetting['first'] = int(self.sender().text())
            self.runOperator()
        except:
            self.parametersSetting['first'] = 0
            self.sender().setText('0')

    def setLast(self):
        try:
            self.parametersSetting['last'] = int(self.sender().text())
            self.runOperator()
        except:
            self.parametersSetting['last'] = 0
            self.sender().setText('0')

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            if 0 <= self.parametersSetting['first'] < self.parametersSetting['last']:
                output = self.input['data'].copy()
                try:
                    output = output.iloc[self.parametersSetting['first']:self.parametersSetting['last'], :]
                except:
                    print('Select examples error')
        self.output['data'] = output


# 数据标准化
class Normalize(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName= ['Normalize(dataset)', 'Normalize(model)']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.mean = {}
        self.standard = {}
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel(self.__class__.__name__)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Preprocessing Model Output'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        playout.addWidget(label)
        playout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(playout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(playout)
        typeBox.activated.connect(lambda: self.setChoice(playout, typeBox.currentText()))
        return pwidget

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        resultTab = QtWidgets.QTabWidget()
        if which == 2:
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)
            descriptionWidget = QtWidgets.QWidget()
            descriptionLayout = QtWidgets.QVBoxLayout()
            descriptionWidget.setLayout(descriptionLayout)
            titleLabel = QtWidgets.QLabel('Z-Transformation')
            titleLabel.setObjectName('subtitle')
            content = 'Normalize ' + str(len(self.mean)) + ' attributes to mean 0 and variance 1.\nUsing\n'
            for attribute in self.mean.keys():
                content = content + attribute + ' --> mean: ' + str(self.mean[attribute]) + \
                          ', variance: ' + str(self.standard[attribute] ** 2) + '\n'
            contentLabel = QtWidgets.QLabel(content)
            contentLabel.setWordWrap(True)
            sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            contentLabel.setSizePolicy(sizepolicy)
            descriptionLayout.addWidget(titleLabel)
            descriptionLayout.addWidget(contentLabel)
            descriptionLayout.addStretch(1)
            resultTab.addTab(descriptionWidget, 'Description')
        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        mean = {}
        standard = {}
        output = None
        if self.input['data'] is not None:
            output = self.input['data'].copy()
            if self.parametersSetting['choice'] == 'All':
                items = output.select_dtypes(include=np.number).columns
            elif self.parametersSetting['choice'] == 'Single':
                if self.choice['Single'] not in output.select_dtypes(include=np.number).columns:
                    items = []
                else:
                    items = [self.choice['Single']]
            else:
                if set(self.choice['Subset']).issubset(set(output.select_dtypes(include=np.number).columns)):
                    items = self.choice['Subset']
                else:
                    items = []
            try:
                for item in items:
                    mean[item] = output[item].mean()
                    standard[item] = output[item].std()
                    output[item] = (output[item] - mean[item]) / standard[item]
            except:
                print('error')
                output = None
        self.mean = mean
        self.standard = standard
        self.output['data'] = output

    def applyModel(self, test_data):
        test_out = test_data.copy()
        for item in self.mean.keys():
            test_out[item] = (test_out[item] - self.mean[item]) / self.standard[item]
        return test_out


# 数据离散化（指定分为几组）
class Discretize_by_Binning(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Discretize by Binning']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.number = 2
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Discretize\nby Binning')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        attrLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        attrLayout.addWidget(label)
        attrLayout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(attrLayout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(attrLayout)
        typeBox.activated.connect(lambda: self.setChoice(attrLayout, typeBox.currentText()))
        playout.addLayout(attrLayout)

        numberLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Number of Bins')
        number = QtWidgets.QLineEdit(str(self.number))
        number.editingFinished.connect(self.setNumber)
        numberLayout.addWidget(label)
        numberLayout.addWidget(number)
        playout.addLayout(numberLayout)
        return pwidget

    def setNumber(self):
        try:
            self.number = int(self.sender().text())
        except:
            self.number = 2
        self.runOperator()

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            output = self.input['data'].copy()
            try:
                if self.parametersSetting['choice'] == 'All':
                    items = output.select_dtypes(include=np.number).columns
                elif self.parametersSetting['choice'] == 'Single':
                    items = [self.choice['Single']]
                else:
                    items = self.choice['Subset']
                for item in items:
                    output[item] = pd.qcut(output[item], self.number)
            except:
                print('Binning error')
        self.output['data'] = output


# 数据离散化（自定义分组）
class Discretize_by_User_Specification(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Discretize by User Specification']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.classList = pd.DataFrame({'className': ['first'], 'limit': [np.Infinity]})

        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Discretize\nby User\nSpecification')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        attrLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        attrLayout.addWidget(label)
        attrLayout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(attrLayout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(attrLayout)
        typeBox.activated.connect(lambda: self.setChoice(attrLayout, typeBox.currentText()))
        playout.addLayout(attrLayout)

        classLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Classes')
        classBtn = QtWidgets.QPushButton('Edit List')
        classBtn.clicked.connect(self.callClassDialog)
        classLayout.addWidget(label)
        classLayout.addWidget(classBtn)
        playout.addLayout(classLayout)
        return pwidget

    def callClassDialog(self):
        dialog = editClassDialog.EditClassDialog(self, self.classList)
        dialog.okButton.clicked.connect(lambda: self.setClassList(dialog))

    def setClassList(self, dialog):
        names = []
        limits = []
        for row in range(dialog.classTable.rowCount()):
            name = dialog.classTable.item(row, 0)
            limit = dialog.classTable.item(row, 1)
            if name is not None and limit is not None:
                if name.text() != '' and limit.text() != '':
                    names.append(name.text())
                    limits.append(float(limit.text()))
        self.classList = pd.DataFrame({'className': names, 'limit': limits}).sort_values('limit')
        dialog.close()
        self.runOperator()

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            output = self.input['data'].copy()
            try:
                if self.parametersSetting['choice'] == 'All':
                    items = output.select_dtypes(include=np.number).columns
                elif self.parametersSetting['choice'] == 'Single':
                    items = [self.choice['Single']]
                else:
                    items = self.choice['Subset']
                bins = pd.concat([pd.Series([-np.Infinity]), self.classList['limit']])
                for item in items:
                    output[item] = pd.cut(output[item], bins, labels=self.classList['className'])
            except:
                print('Binning error')
        self.output['data'] = output


# 移除缺失值
class Remove_Missing_Values(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Remove Missing Values']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Remove\nMissing Values')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)

        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        playout.addWidget(label)
        playout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(playout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(playout)
        typeBox.activated.connect(lambda: self.setChoice(playout, typeBox.currentText()))
        return pwidget

    def showSingleSetting(self, playout):
        label = QtWidgets.QLabel('Attribute')
        attributeBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            attributeBox.setModel(boxModel)
            if self.choice['Single'] in self.input['data'].columns:
                attributeBox.setCurrentText(self.choice['Single'])
            else:
                self.choice['Single'] = attributeBox.currentText()
        attributeBox.activated.connect(self.setSingleAttribute)
        playout.addWidget(label)
        playout.addWidget(attributeBox)

    def callDialog(self):
        if self.input['data'] is not None:
            dialog = selectAttributeDialog.SelectAttrDialog(self, self.input['data'].columns,
                                      self.choice['Subset'])
            dialog.okButton.clicked.connect(lambda: self.setSubsetAttribute(dialog))
        else:
            dialog = selectAttributeDialog.SelectAttrDialog(self, [], [])
            dialog.okButton.clicked.connect(dialog.close)

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            if self.parametersSetting['choice'] == 'All':
                output = self.input['data'].dropna()
            elif self.parametersSetting['choice'] == 'Single':
                output = self.input['data'].dropna(subset=[self.choice['Single']])
            else:
                if self.choice['Subset'] and \
                        set(self.choice['Subset']).issubset(set(self.input['data'].columns)):
                    output = self.input['data'].dropna(subset=self.choice['Subset'])
                else:
                    output = self.input['data']
        self.output['data'] = output


# 替代缺失值
class Replace_Missing_Values(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Replace Missing Values']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.method = ['maximum', 'minimum', 'average', 'value']
        self.fillvalue = 0
        self.parametersSetting = {'choice': 'All', 'method': 'maximum'}
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Replace\nMissing Values')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.resize(self.sizeHint())
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        attrLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        attrLayout.addWidget(label)
        attrLayout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(attrLayout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(attrLayout)
        typeBox.activated.connect(lambda: self.setChoice(attrLayout, typeBox.currentText()))
        playout.addLayout(attrLayout)

        methodLayout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Default')
        methodBox = QtWidgets.QComboBox()
        for item in self.method:
            methodBox.addItem(item)
        methodBox.setCurrentText(self.parametersSetting['method'])
        methodBox.activated.connect(lambda: self.setMethod(methodLayout, methodBox.currentText()))
        methodLayout.addWidget(label)
        methodLayout.addWidget(methodBox)
        playout.addLayout(methodLayout)
        return pwidget

    def showSingleSetting(self, playout):
        label = QtWidgets.QLabel('Attribute')
        attributeBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            attributeBox.setModel(boxModel)
            if self.choice['Single'] in self.input['data'].columns:
                attributeBox.setCurrentText(self.choice['Single'])
            else:
                self.choice['Single'] = attributeBox.currentText()
        attributeBox.activated.connect(self.setSingleAttribute)
        playout.addWidget(label)
        playout.addWidget(attributeBox)

    def callDialog(self):
        if self.input['data'] is not None:
            dialog = selectAttributeDialog.SelectAttrDialog(self, self.input['data'].columns,
                                      self.choice['Subset'])
            dialog.okButton.clicked.connect(lambda: self.setSubsetAttribute(dialog))
        else:
            dialog = selectAttributeDialog.SelectAttrDialog(self, [], [])
            dialog.okButton.clicked.connect(dialog.close)

    # 设置替换缺失值的方法
    def setMethod(self, methodLayout, method):
        setting = methodLayout.takeAt(2)
        if setting != None:
            setting.widget().deleteLater()
        self.parametersSetting['method'] = method
        if method == 'value':
            value = QtWidgets.QLineEdit(str(self.fillvalue))
            value.editingFinished.connect(self.setFillvalue)
            methodLayout.addWidget(value)
        self.runOperator()

    def setFillvalue(self):
        value = self.sender().text()
        if value.isdigit():
            self.fillvalue = int(value)
        else:
            try:
                self.fillvalue = float(value)
            except:
                self.fillvalue = value
        self.runOperator()

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            if self.parametersSetting['choice'] == 'All':
                output = self.fillMissing(self.input['data'], self.input['data'])
            elif self.parametersSetting['choice'] == 'Single':
                output = self.fillMissing(self.input['data'], self.input['data'][[self.choice['Single']]])
            else:
                if self.choice['Subset'] and \
                        set(self.choice['Subset']).issubset(set(self.input['data'].columns)):
                    output = self.fillMissing(self.input['data'], self.input['data'][self.choice['Subset']])
                else:
                    output = self.input['data']
        self.output['data'] = output

    def fillMissing(self, df, filldf):
        if self.parametersSetting['method'] == 'maximum':
            return df.fillna(filldf.dropna().max())
        elif self.parametersSetting['method'] == 'minimum':
            return df.fillna(filldf.dropna().min())
        elif self.parametersSetting['method'] == 'average':
            return df.fillna(filldf.dropna().mean())
        else:
            mapDict = {}
            for item in filldf.columns:
                mapDict[item] = self.fillvalue
            return df.fillna(mapDict)


# 移除重复的样例
class Remove_Duplicates(CleansingWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Remove Duplicates']
        self.choice = {'All': None, 'Single': None, 'Subset': []}
        self.parametersSetting = {'choice': 'All'}
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Remove\nDuplicates')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)

        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Attribute Filter Type')
        typeBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        typeBox.setModel(boxModel)
        typeBox.setCurrentText(self.parametersSetting['choice'])
        playout.addWidget(label)
        playout.addWidget(typeBox)
        if self.parametersSetting['choice'] == 'Single':
            self.showSingleSetting(playout)
        elif self.parametersSetting['choice'] == 'Subset':
            self.showSubsetSetting(playout)
        typeBox.activated.connect(lambda: self.setChoice(playout, typeBox.currentText()))
        return pwidget

    def showSingleSetting(self, playout):
        label = QtWidgets.QLabel('Attribute')
        attributeBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            attributeBox.setModel(boxModel)
            if self.choice['Single'] in self.input['data'].columns:
                attributeBox.setCurrentText(self.choice['Single'])
            else:
                self.choice['Single'] = attributeBox.currentText()
        attributeBox.activated.connect(self.setSingleAttribute)
        playout.addWidget(label)
        playout.addWidget(attributeBox)

    def callDialog(self):
        if self.input['data'] is not None:
            dialog = selectAttributeDialog.SelectAttrDialog(self, self.input['data'].columns,
                                      self.choice['Subset'])
            dialog.okButton.clicked.connect(lambda: self.setSubsetAttribute(dialog))
        else:
            dialog = selectAttributeDialog.SelectAttrDialog(self, [], [])
            dialog.okButton.clicked.connect(dialog.close)

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            if self.parametersSetting['choice'] == 'All':
                output = self.input['data'].drop_duplicates(subset=None, keep='first', inplace=False)
            elif self.parametersSetting['choice'] == 'Single':
                output = self.input['data'].drop_duplicates(subset=[self.choice['Single']], keep='first', inplace=False)
            else:
                if self.choice['Subset'] and \
                        set(self.choice['Subset']).issubset(set(self.input['data'].columns)):
                    output = self.input['data'].drop_duplicates(subset=self.choice['Subset'], keep='first', inplace=False)
                else:
                    output = self.input['data']
        self.output['data'] = output


# 主成分分析
class Principal_Component_Analysis(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.choice = {'Default': 'mle', 'Variance Threshold': 0.95, 'Fixed Number': 1}
        self.parametersSetting = {'choice': 'Default'}
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['PCA(dataset)', 'PCA(model)']
        self.pca = None
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Principal\nComponent\nAnalysis')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Preprocessing Model Output'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)

        playout = QtWidgets.QVBoxLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('The Number of Component:')
        numberBox = QtWidgets.QComboBox()
        boxModel = QStandardItemModel()
        for name in self.choice.keys():
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        numberBox.setModel(boxModel)
        numberBox.setCurrentText(self.parametersSetting['choice'])
        playout.addWidget(label)
        playout.addWidget(numberBox)
        if self.parametersSetting['choice'] != 'Default':
            setting = QtWidgets.QLineEdit(str(self.choice[self.parametersSetting['choice']]))
            if self.parametersSetting['choice'] == 'Variance Threshold':
                setting.editingFinished.connect(self.setThreshold)
            else:
                setting.editingFinished.connect(self.setNumber)
            playout.addWidget(setting)
        numberBox.activated.connect(lambda: self.setChoice(playout, numberBox.currentText()))
        return pwidget

    def setChoice(self, playout, choice):
        setting = playout.takeAt(2)
        if setting != None:
            setting.widget().deleteLater()
        self.parametersSetting['choice'] = choice
        if choice != 'Default':
            setting = QtWidgets.QLineEdit(str(self.choice[self.parametersSetting['choice']]))
            if self.parametersSetting['choice'] == 'Variance Threshold':
                setting.editingFinished.connect(self.setThreshold)
            else:
                setting.editingFinished.connect(self.setNumber)
            playout.addWidget(setting)
        self.runOperator()

    def setThreshold(self):
        try:
            thresshold = float(self.sender().text())
            if 0 <= thresshold <= 1.0:
                self.choice['Variance Threshold'] = thresshold
            else:
                self.choice['Variance Threshold'] = 0.95
        except:
            self.choice['Variance Threshold'] = 0.95
        self.runOperator()

    def setNumber(self):
        try:
            number = int(self.sender().text())
            if number >= 1:
                self.choice['Fixed Number'] = number
            else:
                self.choice['Fixed Number'] = 1
        except:
            self.choice['Fixed Number'] = 1
        self.runOperator()

    def setInput(self, input):
        self.input['data'] = input

    # 待修改，fixednumber不能超过dataframe的行数和列数
    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            self.pca = PCA(n_components=self.choice[self.parametersSetting['choice']])
            self.pca.fit(self.input['data'].select_dtypes(include=np.number))
            transformed_data = self.pca.transform(self.input['data'].select_dtypes(include=np.number))
            name = []
            for i in range(transformed_data.shape[1]):
                name.append('pc_'+str(i+1))
            output = pd.DataFrame(transformed_data, columns=name)
        self.output['data'] = output

    def applyModel(self, test_data):
        result_data = self.pca.transform(test_data.select_dtypes(include=np.number))
        name = []
        for i in range(result_data.shape[1]):
            name.append('pc_'+str(i+1))
        return pd.DataFrame(result_data, columns=name)

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        resultTab = QtWidgets.QTabWidget()
        resultTab.setTabPosition(QtWidgets.QTabWidget.West)
        if which == 2:
            dataWidget = QtWidgets.QWidget()
            dataLayout = QtWidgets.QVBoxLayout()
            dataWidget.setLayout(dataLayout)
            vectorsWidget = QtWidgets.QWidget()
            vectorsLayout = QtWidgets.QVBoxLayout()
            vectorsWidget.setLayout(vectorsLayout)
            resultTab.addTab(dataWidget, 'Eigenvalues')
            resultTab.addTab(vectorsWidget, 'Eigenvectors')
            dataArea = QtWidgets.QTableView()
            eigenvalues = pd.DataFrame(self.output['data'].columns, columns=['Component'])
            eigenvalues['Standard Deviation']  = np.sqrt(self.pca.explained_variance_)
            eigenvalues['Propotion of Variance'] = self.pca.explained_variance_ratio_
            eigenvalues['Cumulative Variance'] = eigenvalues['Propotion of Variance'].cumsum()
            model = pandasModel.PandasModel(eigenvalues.round(4))
            dataArea.setModel(model)
            dataLayout.addWidget(dataArea)

            dataArea = QtWidgets.QTableView()
            eigenvectors = pd.DataFrame(self.input['data'].select_dtypes(include=np.number).columns,
                                       columns=['Attribute'])
            eigenvectors = pd.concat([eigenvectors, pd.DataFrame(self.pca.components_.T,
                                                                 columns=self.output['data'].columns)], axis=1)
            model = pandasModel.PandasModel(eigenvectors.round(4))
            dataArea.setModel(model)
            vectorsLayout.addWidget(dataArea)
        else:
            dataWidget = QtWidgets.QWidget()
            dataLayout = QtWidgets.QVBoxLayout()
            dataWidget.setLayout(dataLayout)
            resultTab.addTab(dataWidget, 'Data')
            dataArea = QtWidgets.QTableView()
            model = pandasModel.PandasModel(self.output['data'].round(4))
            dataArea.setModel(model)
            dataLayout.addWidget(dataArea)
        return resultTab


class Feature_Selection(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['Feature Selection(dataset)', 'Feature Selection(model)']
        self.parametersSetting = {'label': None, 'score_func': chi2, 'k': 2}
        self.select = None
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Feature\nSelection')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Model'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('Labeled attribute')
        label2 = QtWidgets.QLabel('Score function')
        label3 = QtWidgets.QLabel('Number of attributes')
        labelBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            labelBox.setModel(boxModel)
            labelBox.setCurrentText(self.parametersSetting['label'])
            self.parametersSetting['label'] = labelBox.currentText()
            labelBox.activated.connect(self.setLabel)
        else:
            self.parametersSetting['label'] = None
        functionBox = QtWidgets.QComboBox()
        functionBox.addItem('Chi-squared')
        functionBox.addItem('F-classif')
        functionBox.addItem('Mutual information')
        functionBox.activated.connect(self.setScoreFunction)
        number = QtWidgets.QLineEdit(str(self.parametersSetting['k']))
        number.editingFinished.connect(self.setNumber)
        playout.addWidget(label1, 0, 0, 1, 1)
        playout.addWidget(labelBox, 0, 1, 1, 1)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(functionBox, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(number, 2, 1, 1, 1)
        return pwidget

    def setLabel(self):
        self.parametersSetting['label'] = self.sender().currentText()

    def setScoreFunction(self, index):
        if index == 0:
            self.parametersSetting['score_func'] = chi2
        elif index == 1:
            self.parametersSetting['score_func'] = f_classif
        else:
            self.parametersSetting['score_func'] = mutual_info_classif

    def setNumber(self):
        try:
            self.parametersSetting['k'] = int(self.sender().text())
        except:
            self.parametersSetting['k'] = 2
            self.sender().setText('2')

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        if which == 2:
            resultTab = QtWidgets.QTabWidget()
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)
            descriptionWidget = QtWidgets.QWidget()
            descriptionLayout = QtWidgets.QVBoxLayout()
            descriptionWidget.setLayout(descriptionLayout)
            attributes = self.input['data'].drop(self.parametersSetting['label'], axis=1).columns
            df = pd.DataFrame(attributes, columns=['Attribute'])
            df['Score'] = self.select.scores_
            if self.select.pvalues_ is not None:
                df['P-value'] = self.select.pvalues_
            dataArea = QtWidgets.QTableView()
            model = pandasModel.PandasModel(df.round(4))
            dataArea.setModel(model)
            descriptionLayout.addWidget(dataArea)
            resultTab.addTab(descriptionWidget, 'Attributes')

        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            if self.parametersSetting['label'] is not None:
                try:
                    temp = self.input['data'].copy()
                    for item in temp.select_dtypes(include=np.object).columns:
                        temp[item] = temp[item].astype('category').values.codes
                    self.select = SelectKBest(self.parametersSetting['score_func'], k=self.parametersSetting['k'])
                    self.select.fit(temp.drop(self.parametersSetting['label'], axis=1), temp[self.parametersSetting['label']])
                    output = self.input['data'].drop(
                        self.parametersSetting['label'], axis=1).loc[:, self.select.get_support()]
                except:
                    print('Feature selection error')
        self.output['data'] = output

    def applyModel(self, test_data):
        test_out = test_data.copy()
        test_out = test_out.drop(self.parametersSetting['label'], axis=1).loc[:, self.select.get_support()]
        return test_out


class Decision_Trees(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        # 记录组件在工作台程序设计表格中的位置
        self.row = row
        self.column = column
        self.datalist = datalist
        # 获取当前已添加的运算组件列表
        self.process = process
        # 记录组件在程序设计表格中占多少列
        self.columnspan = 2
        # 组件的输入输出集
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['Decision Trees(dataset)', 'Decision Trees(model)']
        # 运算组件的参数记录
        self.parametersSetting = {'label': None, 'max_depth': None, 'min_samples_split': 2,
                                  'gain_ratio': False}
        # 组件对应的估计器
        self.estimator = None
        # 组件的界面展示
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Decision Trees')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Model'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    # 组件的参数设置界面
    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('Labeled attribute')
        label2 = QtWidgets.QLabel('Criterion')
        label3 = QtWidgets.QLabel('Maximal depth')
        label4 = QtWidgets.QLabel('Minimal size for split')
        labelBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            labelBox.setModel(boxModel)
            labelBox.setCurrentText(self.parametersSetting['label'])
            self.parametersSetting['label'] = labelBox.currentText()
            labelBox.activated.connect(self.setLabel)
        else:
            self.parametersSetting['label'] = None
        criterionBox = QtWidgets.QComboBox()
        criterionBox.addItem('information_gain')
        criterionBox.addItem('gain_ratio')
        criterionBox.activated.connect(self.setCriterion)
        max_depth = QtWidgets.QLineEdit(str(self.parametersSetting['max_depth']))
        max_depth.editingFinished.connect(self.setMaxDepth)
        min_split = QtWidgets.QLineEdit(str(self.parametersSetting['min_samples_split']))
        min_split.editingFinished.connect(self.setMinSplit)
        playout.addWidget(label1, 0, 0, 1, 1)
        playout.addWidget(labelBox, 0, 1, 1, 1)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(criterionBox, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(max_depth, 2, 1, 1, 1)
        playout.addWidget(label4, 3, 0, 1, 1)
        playout.addWidget(min_split, 3, 1, 1, 1)
        return pwidget

    # 设置决策树的标签属性
    def setLabel(self):
        self.parametersSetting['label'] = self.sender().currentText()

    # 设置决策树切分质量的评价准则
    def setCriterion(self, index):
        if index == 0:
            self.parametersSetting['gain_ratio'] = False
        else:
            self.parametersSetting['gain_ratio'] = True

    # 设置树的最大深度
    def setMaxDepth(self):
        try:
            self.parametersSetting['max_depth'] = int(self.sender().text())
        except:
            self.parametersSetting['max_depth'] = None
            self.sender().setText('')

    # 设置分裂一个内部节点(非叶子节点)需要的最小样本数
    def setMinSplit(self):
        try:
            self.parametersSetting['min_samples_split'] = int(self.sender().text())
        except:
            self.parametersSetting['min_samples_split'] = 2
            self.sender().setText('2')

    # 设置组件输入
    def setInput(self, input):
        self.input['data'] = input
        self.output['data'] = input

    # 组件结果输出
    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    # 组件结果展示
    def showResult(self, which=1):
        if which == 2:
            resultTab = QtWidgets.QTabWidget()
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)
            # 展示决策树图
            graphWidget = QtWidgets.QWidget()
            graphLayout = QtWidgets.QVBoxLayout()
            scroll = QtWidgets.QScrollArea()
            graphWidget.setLayout(graphLayout)
            dot_data = export_graphviz(self.estimator.tree_,
                                       feature_names=self.input['data'].columns.drop(self.parametersSetting['label']))
            graph = graphviz.Source(dot_data.to_string(), format='png')
            filename = graph.render(filename='tree', directory='../temp/')
            pixmap = QPixmap(filename)
            label = QtWidgets.QLabel()
            label.setPixmap(pixmap)
            scroll.setWidget(label)
            graphLayout.addWidget(scroll)
            resultTab.addTab(graphWidget, 'Graph')

            # 展示决策树的文字描述
            descriptionWidget = QtWidgets.QWidget()
            descriptionLayout = QtWidgets.QVBoxLayout()
            scroll = QtWidgets.QScrollArea()
            descriptionWidget.setLayout(descriptionLayout)
            titleLabel = QtWidgets.QLabel('Tree')
            titleLabel.setObjectName('subtitle')
            contentLabel = QtWidgets.QLabel(export_text(self.estimator.tree_,
                                                        feature_names=self.input['data'].columns.drop(self.parametersSetting['label'])))
            contentLabel.setWordWrap(True)
            sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            contentLabel.setSizePolicy(sizepolicy)
            descriptionLayout.addWidget(titleLabel)
            descriptionLayout.addWidget(contentLabel)
            descriptionLayout.addStretch(1)
            scroll.setWidget(descriptionWidget)
            resultTab.addTab(scroll, 'Description')

        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    # 组件的中心运算程序
    def runOperator(self):
        # 如果组件输入与标签属性设置不为空，运行中心运算程序
        if self.input['data'] is not None:
            if self.parametersSetting['label'] is not None:
                try:
                    # 创建ID3估计器
                    self.estimator = Id3Estimator(self.parametersSetting['max_depth'],
                                                  self.parametersSetting['min_samples_split'],
                                                  False,
                                                  self.parametersSetting['gain_ratio'])
                    # 训练估计器
                    self.estimator.fit(self.input['data'].drop([self.parametersSetting['label']], axis=1).
                                       values.astype(np.str_),
                                       self.input['data'][self.parametersSetting['label']].values.astype(np.str_),
                                       check_input=True)
                except:
                    print('ID3 error')

    # 应用训练好的决策树模型
    def applyModel(self, test_data):
        test_out = test_data.copy()
        predict = self.estimator.predict(test_out.drop([self.parametersSetting['label']], axis=1).values.astype(np.str_))
        test_out[self.parametersSetting['label']+'(predict)'] = predict
        return test_out


class Neural_Network_Models(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['Neural Network(dataset)', 'Neural Network(model)']
        self.parametersSetting = {'label': None, 'hidden_layer_sizes': (7, ), 'activation': 'relu',
                                  'solver': 'adam', 'max_iter': 200, 'learning_rate_init': 0.1,
                                  'momentum': 0.9, 'alpha': 1.0e-5}
        self.estimator = None
        self.hiddenLayer = pd.DataFrame({'name': ['hidden 1'], 'size': [7]})
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Neural Network')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Model'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('Labeled attribute')
        label2 = QtWidgets.QLabel('Hidden layers')
        label3 = QtWidgets.QLabel('Activation')
        label4 = QtWidgets.QLabel('Solver')
        label5 = QtWidgets.QLabel('Training cycles')
        label6 = QtWidgets.QLabel('Learning rate')
        label7 = QtWidgets.QLabel('Momentum')
        label8 = QtWidgets.QLabel('Error epsilon')
        labelBox = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            labelBox.setModel(boxModel)
            labelBox.setCurrentText(self.parametersSetting['label'])
            self.parametersSetting['label'] = labelBox.currentText()
            labelBox.activated.connect(self.setLabel)
        else:
            self.parametersSetting['label'] = None
        hiddenLayerBtn = QtWidgets.QPushButton('Edit List')
        hiddenLayerBtn.clicked.connect(self.callDialog)

        activationBox = QtWidgets.QComboBox()
        activationBox.addItem('identity')
        activationBox.addItem('logistic')
        activationBox.addItem('tanh')
        activationBox.addItem('relu')
        activationBox.setCurrentText(self.parametersSetting['activation'])
        activationBox.activated.connect(self.setActivation)

        solverBox = QtWidgets.QComboBox()
        solverBox.addItem('lbfgs')
        solverBox.addItem('sgd')
        solverBox.addItem('adam')
        solverBox.setCurrentText(self.parametersSetting['solver'])
        solverBox.activated.connect(self.setSolver)

        max_iter = QtWidgets.QLineEdit(str(self.parametersSetting['max_iter']))
        max_iter.editingFinished.connect(self.setMaxIter)
        learning_rate = QtWidgets.QLineEdit(str(self.parametersSetting['learning_rate_init']))
        learning_rate.editingFinished.connect(self.setLearningRate)
        momentum = QtWidgets.QLineEdit(str(self.parametersSetting['momentum']))
        momentum.editingFinished.connect(self.setMomentum)
        alpha = QtWidgets.QLineEdit(str(self.parametersSetting['alpha']))
        alpha.editingFinished.connect(self.setAlpha)
        playout.addWidget(label1, 0, 0, 1, 1)
        playout.addWidget(labelBox, 0, 1, 1, 1)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(hiddenLayerBtn, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(activationBox, 2, 1, 1, 1)
        playout.addWidget(label4, 3, 0, 1, 1)
        playout.addWidget(solverBox, 3, 1, 1, 1)
        playout.addWidget(label5, 4, 0, 1, 1)
        playout.addWidget(max_iter, 4, 1, 1, 1)
        playout.addWidget(label6, 5, 0, 1, 1)
        playout.addWidget(learning_rate, 5, 1, 1, 1)
        playout.addWidget(label7, 6, 0, 1, 1)
        playout.addWidget(momentum, 6, 1, 1, 1)
        playout.addWidget(label8, 7, 0, 1, 1)
        playout.addWidget(alpha, 7, 1, 1, 1)
        return pwidget

    def setLabel(self):
        self.parametersSetting['label'] = self.sender().currentText()

    def callDialog(self):
        dialog = editClassDialog.HiddenLayerDialog(self, self.hiddenLayer)
        dialog.okButton.clicked.connect(lambda: self.setHiddenLayer(dialog))

    def setHiddenLayer(self, dialog):
        names = []
        sizes = []
        for row in range(dialog.classTable.rowCount()):
            name = dialog.classTable.item(row, 0)
            size = dialog.classTable.item(row, 1)
            if name is not None and size is not None:
                if name.text() != '' and size.text() != '':
                    names.append(name.text())
                    sizes.append(int(size.text()))
        self.hiddenLayer = pd.DataFrame({'name': names, 'size': sizes})
        self.parametersSetting['hidden_layer_sizes'] = tuple(self.hiddenLayer['size'])
        dialog.close()

    def setActivation(self):
        self.parametersSetting['activation'] = self.sender().currentText()

    def setSolver(self):
        self.parametersSetting['solver'] = self.sender().currentText()

    def setMaxIter(self):
        try:
            self.parametersSetting['max_iter'] = int(self.sender().text())
        except:
            self.parametersSetting['max_depth'] = 200
            self.sender().setText('200')

    def setLearningRate(self):
        try:
            self.parametersSetting['learning_rate_init'] = float(self.sender().text())
        except:
            self.parametersSetting['learning_rate_init'] = 0.1
            self.sender().setText('0.1')

    def setMomentum(self):
        try:
            self.parametersSetting['momentum'] = float(self.sender().text())
        except:
            self.parametersSetting['momentum'] = 0.9
            self.sender().setText('0.9')

    def setAlpha(self):
        try:
            self.parametersSetting['alpha'] = float(self.sender().text())
        except:
            self.parametersSetting['alpha'] = 1.0e-5
            self.sender().setText('1.0e-5')

    def setInput(self, input):
        self.input['data'] = input
        self.output['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        if which == 2:
            resultTab = QtWidgets.QTabWidget()
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)
            attributes = self.input['data'].drop([self.parametersSetting['label']], axis=1).columns
            graphWidget = NetworkWidget(self.estimator, attributes)
            resultTab.addTab(graphWidget, 'Neural Net')

            descriptionWidget = QtWidgets.QWidget()
            descriptionLayout = QtWidgets.QVBoxLayout()
            scroll = QtWidgets.QScrollArea()
            descriptionWidget.setLayout(descriptionLayout)
            titleLabel = QtWidgets.QLabel('Neural Network')
            titleLabel.setObjectName('subtitle')
            contentLabel = QtWidgets.QLabel(graphWidget.descriptionContent)
            contentLabel.setWordWrap(True)
            sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            contentLabel.setSizePolicy(sizepolicy)
            descriptionLayout.addWidget(titleLabel)
            descriptionLayout.addWidget(contentLabel)
            scroll.setWidget(descriptionWidget)
            descriptionLayout.addStretch(1)
            resultTab.addTab(scroll, 'Description')

        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        if self.input['data'] is not None:
            if self.parametersSetting['label'] is not None:
                self.estimator = MLPClassifier(hidden_layer_sizes=self.parametersSetting['hidden_layer_sizes'],
                                                   activation=self.parametersSetting['activation'],
                                                   solver=self.parametersSetting['solver'],
                                                   alpha=self.parametersSetting['alpha'],
                                                   learning_rate_init=self.parametersSetting['learning_rate_init'],
                                                   max_iter=self.parametersSetting['max_iter'],
                                                   momentum=self.parametersSetting['momentum'])
                self.estimator.fit(self.input['data'].drop([self.parametersSetting['label']], axis=1),
                                       self.input['data'][self.parametersSetting['label']])

    def applyModel(self, test_data):
        test_out = test_data.copy()
        predict = self.estimator.predict(test_out.drop([self.parametersSetting['label']], axis=1))
        test_out[self.parametersSetting['label']+'(predict)'] = predict
        return test_out


class K_means(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['K-means(dataset)', 'K-means(model)']
        self.parametersSetting = {'n_cluster': 2, 'n_init': 10, 'max_iter': 100}
        self.kmeans = None
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input'), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('K-means')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Clustered Set'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Model'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('K')
        label2 = QtWidgets.QLabel('Max runs')
        label3 = QtWidgets.QLabel('Max optimization steps')
        ncluster = QtWidgets.QLineEdit(str(self.parametersSetting['n_cluster']))
        ncluster.editingFinished.connect(self.setNcluster)
        ninit = QtWidgets.QLineEdit(str(self.parametersSetting['n_init']))
        ninit.editingFinished.connect(self.setNinit)
        maxiter = QtWidgets.QLineEdit(str(self.parametersSetting['max_iter']))
        maxiter.editingFinished.connect(self.setMaxiter)
        playout.addWidget(label1, 0, 0, 1, 1)
        playout.addWidget(ncluster, 0, 1, 1, 1)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(ninit, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(maxiter, 2, 1, 1, 1)
        return pwidget

    def setNcluster(self):
        try:
            self.parametersSetting['n_cluster'] = int(self.sender().text())
        except:
            self.parametersSetting['n_cluster'] = 2
            self.sender().setText('2')

    def setNinit(self):
        try:
            self.parametersSetting['n_init'] = int(self.sender().text())
        except:
            self.parametersSetting['n_init'] = 10
            self.sender().setText('10')

    def setMaxiter(self):
        try:
            self.parametersSetting['max_iter'] = int(self.sender().text())
        except:
            self.parametersSetting['max_iter'] = 100
            self.sender().setText('100')

    def setInput(self, input):
        self.input['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        if which == 2:
            resultTab = QtWidgets.QTabWidget()
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)

            descriptionWidget = QtWidgets.QWidget()
            descriptionLayout = QtWidgets.QVBoxLayout()
            descriptionWidget.setLayout(descriptionLayout)
            titleLabel = QtWidgets.QLabel('K-means')
            titleLabel.setObjectName('subtitle')
            content = ''
            cluster = pd.value_counts(self.output['data']['cluster'].astype(np.int)).sort_index()
            for (index, value) in zip(cluster.index, cluster):
                content += 'Cluster ' + str(index) + ': ' + str(value) + ' items\n'
            content += 'Total number of items: ' + str(self.output['data'].shape[0])
            contentLabel = QtWidgets.QLabel(content)
            contentLabel.setWordWrap(True)
            sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            contentLabel.setSizePolicy(sizepolicy)
            descriptionLayout.addWidget(titleLabel)
            descriptionLayout.addWidget(contentLabel)
            descriptionLayout.addStretch(1)
            resultTab.addTab(descriptionWidget, 'Description')

            centroidWidget = QtWidgets.QWidget()
            centroidLayout = QtWidgets.QVBoxLayout()
            centroidWidget.setLayout(centroidLayout)
            attributes = pd.DataFrame(self.input['data'].columns, columns=['Attribute'])
            centroid = pd.DataFrame(self.kmeans.cluster_centers_.T, columns=cluster.index.astype(np.str_))
            tableContent = pd.concat([attributes, centroid], axis=1)
            tableArea = QtWidgets.QTableView()
            model = pandasModel.PandasModel(tableContent.round(4))
            tableArea.setModel(model)
            tableArea.verticalHeader().hide()
            centroidLayout.addWidget(tableArea)
            resultTab.addTab(centroidWidget, 'Centroid Table')

        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        output = None
        if self.input['data'] is not None:
            self.kmeans = KMeans(n_clusters=self.parametersSetting['n_cluster'],
                                     n_init=self.parametersSetting['n_init'],
                                     max_iter=self.parametersSetting['max_iter'])
            y_predict = self.kmeans.fit_predict(self.input['data'])
            output = self.input['data'].copy()
            output['cluster'] = y_predict.astype(np.str_)
            self.output['data'] = output

    def applyModel(self, test_data):
        test_out = test_data.copy()
        predict = self.kmeans.predict(test_out)
        test_out['cluster'] = predict.astype(np.str_)
        return test_out


class Correlation_Matrix(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.datalist = datalist
        self.columnspan = 1
        self.method = ['pearson', 'kendall', 'spearman']
        self.parametersSetting = {'Method': 'pearson'}
        self.input = {'data': None}
        self.output = {'data': None}
        self.showName = ['Correlation Matrix']
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input'), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Correlation\nMatrix')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Matrix'), 3, 0, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label = QtWidgets.QLabel('Choose Method')
        methodBox = QtWidgets.QComboBox()
        methodBox.setMinimumContentsLength(12)
        boxModel = QStandardItemModel()
        for name in self.method:
            item = QStandardItem(name)
            item.setToolTip(name)
            boxModel.appendRow(item)
        methodBox.setModel(boxModel)
        methodBox.setCurrentText(self.parametersSetting['Method'])
        playout.addWidget(label, 0, 0)
        playout.addWidget(methodBox, 0, 1)
        methodBox.activated.connect(self.setMethod)
        playout.setColumnStretch(0, 1)
        playout.setColumnStretch(1, 1)
        return pwidget

    def setMethod(self, index):
        self.parametersSetting['Method'] = self.sender().itemText(index)

    def setInput(self, input):
        self.input['data'] = input

    def runOperator(self):
        self.output['data'] = self.input['data'].corr(method=self.parametersSetting['Method'])

    def getResult(self, which=1):
        return self.output['data']

    def showResult(self, which=1):
        resultTab = QtWidgets.QTabWidget()
        resultTab.setTabPosition(QtWidgets.QTabWidget.West)
        dataWidget = QtWidgets.QWidget()
        dataLayout = QtWidgets.QVBoxLayout()
        dataWidget.setLayout(dataLayout)
        resultTab.addTab(dataWidget, 'Data')
        dataArea = QtWidgets.QTableView()
        model = pandasModel.PandasModel(self.output['data'].round(4))
        dataArea.setModel(model)
        dataLayout.addWidget(dataArea)
        return resultTab


class Exponential_Smoothing(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 2
        self.input = {'data': None}
        self.output = {'data': None, 'model': self}
        self.showName = ['Exponential Smoothing(dataset)', 'Exponential Smoothing(model)']
        self.temp = None
        self.parametersSetting = {'time_label': None, 'target_label': None, 'smoothing_level': 0.5}
        self.expsmoothing = None
        self.setObjectName(self.__class__.__name__)

        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input'), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Exponential\nSmoothing')
        label.setAlignment(Qt.AlignCenter)
        # label.setMinimumHeight(30)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Example Set'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Model'), 3, 1, 1, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            self.setInput(lastOperator[0].getResult(which=lastOperator[3]))
        else:
            self.setInput(None)
        playout = QtWidgets.QGridLayout()
        pwidget.setLayout(playout)
        label1 = QtWidgets.QLabel('Time attribute')
        label2 = QtWidgets.QLabel('Target attribute')
        label3 = QtWidgets.QLabel('Smoothing level')
        labelBox1 = QtWidgets.QComboBox()
        labelBox2 = QtWidgets.QComboBox()
        if self.input['data'] is not None:
            boxModel = QStandardItemModel()
            for attribute in self.input['data'].columns:
                item = QStandardItem(attribute)
                item.setToolTip(attribute)
                boxModel.appendRow(item)
            labelBox1.setModel(boxModel)
            labelBox1.setCurrentText(self.parametersSetting['time_label'])
            labelBox2.setModel(boxModel)
            labelBox2.setCurrentText(self.parametersSetting['target_label'])
            self.parametersSetting['time_label'] = labelBox1.currentText()
            self.parametersSetting['target_label'] = labelBox2.currentText()
            labelBox1.activated.connect(self.setTimeLabel)
            labelBox2.activated.connect(self.setTargetLabel)
        else:
            self.parametersSetting['time_label'] = None
            self.parametersSetting['target_label'] = None
        alpha = QtWidgets.QLineEdit(str(self.parametersSetting['smoothing_level']))
        alpha.editingFinished.connect(self.setSmoothingLevel)
        playout.addWidget(label1, 0, 0, 1, 1)
        playout.addWidget(labelBox1, 0, 1, 1, 1)
        playout.addWidget(label2, 1, 0, 1, 1)
        playout.addWidget(labelBox2, 1, 1, 1, 1)
        playout.addWidget(label3, 2, 0, 1, 1)
        playout.addWidget(alpha, 2, 1, 1, 1)
        return pwidget

    def setTimeLabel(self):
        self.parametersSetting['time_label'] = self.sender().currentText()

    def setTargetLabel(self):
        self.parametersSetting['target_label'] = self.sender().currentText()

    def setSmoothingLevel(self):
        try:
            alpha = float(self.sender().text())
            if 0 <= alpha <= 1:
                self.parametersSetting['smoothing_level'] = alpha
            elif alpha < 0:
                self.parametersSetting['smoothing_level'] = 0
                self.sender().setText('0')
            else:
                self.parametersSetting['smoothing_level'] = 1
                self.sender().setText('1')
        except:
            self.parametersSetting['smoothing_level'] = 0.5
            self.sender().setText('0.5')

    def setInput(self, input):
        self.input['data'] = input
        self.output['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        return self.output['data']

    def showResult(self, which=1):
        if which == 2:
            resultTab = QtWidgets.QTabWidget()
            resultTab.setTabPosition(QtWidgets.QTabWidget.West)
            graphWidget = QtWidgets.QWidget()
            graphLayout = QtWidgets.QVBoxLayout()
            graphWidget.setLayout(graphLayout)
            date_axis = TimeAxisItem(orientation='bottom')
            pw = pg.PlotWidget(axisItems={'bottom': date_axis})  # 实例化一个绘图部件
            pw.addLegend()

            pw.plot([x.timestamp() for x in self.temp['timestamp']], self.input['data'][self.parametersSetting['target_label']], name='Actual')  # 在绘图部件中绘制折线图
            pw.plot([x.timestamp() for x in self.temp['timestamp']], self.expsmoothing.fittedvalues, pen='r', name='Fitted')
            graphLayout.addWidget(pw)  # 添加绘图部件到网格布局层
            resultTab.addTab(graphWidget, 'Graph')

        else:
            resultTab = self.showExampleSet(self.output['data'])
        return resultTab

    def runOperator(self):
        if self.input['data'] is not None:
            if self.parametersSetting['target_label'] is not None and self.parametersSetting['time_label'] is not None:
                self.temp = self.input['data'].copy()
                self.temp['timestamp'] = pd.to_datetime(self.temp[self.parametersSetting['time_label']])
                self.temp.index = self.temp['timestamp']
                self.expsmoothing = SimpleExpSmoothing(self.temp[self.parametersSetting['target_label']].values).\
                    fit(smoothing_level=self.parametersSetting['smoothing_level'], optimized=False)

    def applyModel(self, test_data):
        test_out = test_data.copy()
        predict = self.expsmoothing.forecast(test_out.shape[0])
        test_out[self.parametersSetting['target_label']+'(forecast)'] = predict
        return test_out


class Apply_Model(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.datalist = datalist
        self.process = process
        self.row = row
        self.column = column
        self.columnspan = 2
        self.input = {'data': None, 'model': None}
        self.output = {'data': None, 'model': None}
        self.showName = ['Apply Model(dataset)', 'Apply Model(model)']
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(198, 47, 47, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Example Set Input '), 0, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Trained Model Input'), 0, 1, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel('Apply Model')
        label.setMinimumHeight(30)
        # label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 1, 0, 2, 2, Qt.AlignCenter)
        layout.addWidget(InoutButton('Labelled Data Output'), 3, 0, 1, 1, Qt.AlignCenter)
        layout.addWidget(InoutButton('Trained Model Output'), 3, 1, 1, 1, Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedWidth(200)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        return pwidget

    def runOperator(self):
        self.output['data'] = self.input['model'].applyModel(self.input['data'])
        self.output['model'] = self.input['model']


    def setInput(self, input, which=1):
        if which == 2:
            self.input['model'] = input
        else:
            self.input['data'] = input

    def getResult(self, which=1):
        if which == 2:
            return self.output['model']
        else:
            return self.output['data']

    def showResult(self, which=1):
        if which == 2:
            return self.output['model'].showResult(2)
        return self.showExampleSet(self.output['data'])


class Result(CustomWidget):
    def __init__(self, row: int, column: int, datalist: dict, process: list, parent=None):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.datalist = datalist
        self.process = process
        self.columnspan = 1
        self.input = {'result': None}
        self.setObjectName(self.__class__.__name__)
        self.setStyleSheet('QWidget#' + self.objectName() +
                           '{background-color: rgba(180, 180, 180, 0.5); border-radius: 5}')
        layout = QtWidgets.QGridLayout()
        layout.addWidget(InoutButton('Show Result'), 0, 0, 1, 1, Qt.AlignCenter)
        label = QtWidgets.QLabel(self.__class__.__name__)
        layout.addWidget(label, 1, 0, 2, 1, Qt.AlignCenter)
        self.setLayout(layout)
        self.setFixedWidth(100)

    def parameterWidget(self):
        pwidget = QtWidgets.QWidget()
        return pwidget

    def showResult(self, which=1):
        lastOperator = self.findLastOperator(self.process, [self, self.column, self.row, 1])
        if lastOperator is not None:
            return lastOperator[0].showResult(which=lastOperator[3])


class InoutButton(QtWidgets.QRadioButton):
    def __init__(self, tooltip: str):
        super().__init__()
        self.setToolTip(tooltip)
        self.setFixedSize(13, 13)
        self.setCheckable(False)


class CustomButton(QtWidgets.QPushButton):
    def __init__(self, tooltip: str, color: int):
        super().__init__()
        self.color = ['rgb(250, 233, 209)', 'rgb(233, 233, 233)', 'rgb(220,227,242)']
        self.setStyleSheet("QPushButton{border:1px solid black; border-radius:10px; "
                           "height: 20; width:20; background-color: " + self.color[color % 3] +"}")
        self.setToolTip(tooltip)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(value).date() for value in values]


class NetworkWidget(QtWidgets.QWidget):
    def __init__(self, estimator: MLPClassifier(), attributes):
        super().__init__()
        graphLayout = QtWidgets.QVBoxLayout()
        self.networkLayout = QtWidgets.QGridLayout()
        self.setLayout(graphLayout)
        self.networkLayout.addWidget(QtWidgets.QLabel('Input'), 0, 0, 1, 1, Qt.AlignCenter)
        buttonLayout = QtWidgets.QVBoxLayout()
        self.estimator = estimator
        self.attributes = attributes
        for item in attributes:
            buttonLayout.addWidget(CustomButton(item, 0), 1)
        buttonLayout.addWidget(CustomButton('Bias', 1), 1)
        self.networkLayout.addLayout(buttonLayout, 1, 0, 1, 1, Qt.AlignCenter)
        self.descriptionContent = ''

        for i in range(len(self.estimator.coefs_) - 1):
            self.descriptionContent += 'Hidden ' + str(i + 1) + '\n' + '=' * 8 + '\n\n'
            self.networkLayout.addWidget(QtWidgets.QLabel('Hidden ' + str(i + 1)), 0, i + 1, 1, 1, Qt.AlignCenter)
            array = self.estimator.coefs_[i].T.round(4)
            buttonLayout = QtWidgets.QVBoxLayout()
            for row in range(array.shape[0]):
                self.descriptionContent += 'Node ' + str(row + 1) + '\n' + '-' * 20 + '\n\n'
                content = 'Weights\n'
                for (index, weight) in enumerate(array[row]):
                    if i == 0:
                        self.descriptionContent += self.attributes[index] + ': ' + str(weight) + '\n'
                    else:
                        self.descriptionContent += 'Node ' + str(index + 1) + ': ' + str(weight) + '\n'
                    content += str(weight) + '\n'
                content += str(self.estimator.intercepts_[i][row].round(4)) + '(Bias)'
                self.descriptionContent += 'Bias: ' + str(self.estimator.intercepts_[i][row].round(4)) + '\n\n'
                buttonLayout.addWidget(CustomButton(content, 2), 1)
            buttonLayout.addWidget(CustomButton('Bias', 1), 1)
            self.networkLayout.addLayout(buttonLayout, 1, i + 1, 1, 1, Qt.AlignCenter)
            self.descriptionContent += '\n\n'

        last_column = len(self.estimator.coefs_)
        self.networkLayout.addWidget(QtWidgets.QLabel('Output'), 0, last_column, 1, 1, Qt.AlignCenter)
        buttonLayout = QtWidgets.QVBoxLayout()
        array = self.estimator.coefs_[-1].T.round(4)
        self.descriptionContent += 'Output' + '\n' + '=' * 6 + '\n\n'
        for row in range(array.shape[0]):
            self.descriptionContent += "Class \'" + self.estimator.classes_[row] + "\'\n" + '-' * 20 + '\n\n'
            content = 'Weights\n'
            for (index, weight) in enumerate(array[row]):
                self.descriptionContent += 'Node ' + str(index + 1) + ': ' + str(weight.round(4)) + '\n'
                content += str(weight) + '\n'
            content += str(self.estimator.intercepts_[-1][row].round(4)) + '(Bias)'
            self.descriptionContent += 'Bias: ' + str(self.estimator.intercepts_[-1][row].round(4)) + '\n\n'
            buttonLayout.addWidget(CustomButton(content, 0), 1)
        self.networkLayout.addLayout(buttonLayout, 1, last_column, 1, 1, Qt.AlignCenter)

        graphLayout.addLayout(self.networkLayout)
        graphLayout.addStretch(1)

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawLines(qp)
        qp.end()

    def drawLines(self, qp):
        qp.setRenderHint(QPainter.Antialiasing, True)
        for i in range(len(self.estimator.coefs_) - 1):
            array = self.estimator.coefs_[i].T.round(4)
            max_weight = np.max(np.abs(array))
            max_weight = max(max_weight, np.max(np.abs(self.estimator.intercepts_[i])))
            for row in range(array.shape[0]):
                for (index, weight) in enumerate(array[row]):
                    qp.setPen(QPen(QColor(0, 0, 0, int(np.abs(weight/max_weight*255))), 1, Qt.SolidLine))
                    qp.drawLine(self.networkLayout.itemAt(i*2+1).layout().itemAt(index).geometry().center(),
                                self.networkLayout.itemAt(i*2+3).layout().itemAt(row).geometry().center())
                qp.setPen(QPen(QColor(0, 0, 0, int(np.abs(self.estimator.intercepts_[i][row] / max_weight * 255))),
                               1, Qt.SolidLine))
                qp.drawLine(self.networkLayout.itemAt(i * 2 + 1).layout().itemAt(array.shape[1]).geometry().center(),
                            self.networkLayout.itemAt(i * 2 + 3).layout().itemAt(row).geometry().center())

        i = len(self.estimator.coefs_) - 1
        array = self.estimator.coefs_[-1].T.round(4)
        max_weight = np.max(np.abs(array))
        max_weight = max(max_weight, np.max(np.abs(self.estimator.intercepts_[-1])))
        for row in range(array.shape[0]):
            for (index, weight) in enumerate(array[row]):
                qp.setPen(QPen(QColor(0, 0, 0, int(np.abs(weight / max_weight * 255))), 1, Qt.SolidLine))
                qp.drawLine(self.networkLayout.itemAt(i * 2 + 1).layout().itemAt(index).geometry().center(),
                            self.networkLayout.itemAt(i * 2 + 3).layout().itemAt(row).geometry().center())
            qp.setPen(QPen(QColor(0, 0, 0, int(np.abs(self.estimator.intercepts_[-1][row] / max_weight * 255))),
                     1, Qt.SolidLine))
            qp.drawLine(self.networkLayout.itemAt(i * 2 + 1).layout().itemAt(array.shape[1]).geometry().center(),
                        self.networkLayout.itemAt(i * 2 + 3).layout().itemAt(row).geometry().center())

