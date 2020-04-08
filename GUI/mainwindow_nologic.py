# coding:utf-8

from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class MainUi(QtWidgets.QWidget):
    def __init__(self, datalist: dict, operators: dict, parent=None):
        super().__init__(parent)
        self.init_ui(datalist, operators)

    def init_ui(self, datalist, operators):
        self.setObjectName('mainUi')
        self.setMinimumSize(960, 650)

        self.main_widget = QtWidgets.QTabWidget()  # 创建窗口主部件
        self.main_widget.setObjectName('mainTab')
        # self.main_widget.setStyleSheet('QTabWidget::tab-bar{alignment:middle; }')
        self.design_widget = QtWidgets.QWidget()
        self.design_layout = QtWidgets.QGridLayout()  # 创建设计部件的网格布局
        self.design_widget.setLayout(self.design_layout)  # 设置设计部件布局为网格布局
        self.result_widget = QtWidgets.QWidget()
        self.result_widget.setObjectName('result_widget')
        self.result_layout = QtWidgets.QGridLayout()  # 创建结果部件的网格布局
        self.result_widget.setLayout(self.result_layout)  # 设置结果部件布局为网格布局
        self.main_widget.addTab(self.design_widget, 'Design')  # 将设计页面放到标签页中
        self.main_widget.addTab(self.result_widget, 'Result')  # 将结果页面放到标签页中

        self.left_widget = QtWidgets.QWidget()  # 创建左侧部件
        self.left_widget.setObjectName('left_widget')
        self.left_layout = QtWidgets.QGridLayout()  # 创建左侧部件的网格布局层
        self.left_widget.setLayout(self.left_layout)  # 设置左侧部件布局为网格

        self.center_widget = QtWidgets.QWidget()  # 创建中间部件
        self.center_widget.setObjectName('center_widget')
        self.center_layout = QtWidgets.QGridLayout()
        self.center_widget.setLayout(self.center_layout)  # 设置中间部件布局为网格

        self.right_widget = QtWidgets.QWidget()  # 创建右侧部件
        self.right_widget.setObjectName('right_widget')
        self.right_layout = QtWidgets.QGridLayout()
        self.right_widget.setLayout(self.right_layout)  # 设置右侧部件布局为网格

        self.design_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)  # 在design页面放置一个水平布局的splitter
        self.design_splitter.addWidget(self.left_widget)  # 将左中右三个widget放入splitter
        self.design_splitter.addWidget(self.center_widget)
        self.design_splitter.addWidget(self.right_widget)
        self.design_splitter.handle(1).setFixedWidth(2)
        self.design_splitter.handle(2).setFixedWidth(2)
        self.design_splitter.setStretchFactor(0, 3)  # 设置splitter初始比例为3:8:3
        self.design_splitter.setStretchFactor(1, 8)
        self.design_splitter.setStretchFactor(2, 5)
        self.design_layout.addWidget(self.design_splitter)  # 将splitter放进design_layout
        #self.setCentralWidget(self.main_widget)  # 设置窗口主部件
        layout = QtWidgets.QVBoxLayout(self, spacing=0)
        menuBar = QtWidgets.QMenuBar()
        menuBar.setObjectName('Menu')
        menuBar.setFixedHeight(22)
        file_menu = menuBar.addMenu('File')
        self.open_process = QtWidgets.QAction('Open Process')
        self.save_process = QtWidgets.QAction('Save Process')
        file_menu.addAction(self.open_process)
        file_menu.addAction(self.save_process)
        file_menu.addSeparator()
        self.exit_action = QtWidgets.QAction('Exit')
        file_menu.addAction(self.exit_action)
        layout.addWidget(menuBar)
        layout.addWidget(self.main_widget)

        # 在左侧栏放置控件
        self.dataWidget = QtWidgets.QFrame()  # 创建数据区部件
        self.dataLayout = QtWidgets.QVBoxLayout()
        self.dataWidget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.dataWidget.setObjectName('outPanel')
        self.dataWidget.setLayout(self.dataLayout)
        self.addDataButt = QtWidgets.QPushButton('Add Data')
        self.addDataButt.setObjectName('addData')
        self.dataLayout.setContentsMargins(0, 5, 0, 0)
        label = QtWidgets.QLabel('Datasets')
        label.setObjectName('title')
        self.dataLayout.addWidget(label)
        self.dataLayout.addWidget(self.addDataButt, 1, QtCore.Qt.AlignHCenter)
        self.dataList = QtWidgets.QListWidget()  # 创建数据列表部件
        for item in datalist.keys():
            self.dataList.addItem(QtWidgets.QListWidgetItem(item))

        self.dataLayout.addWidget(self.dataList)

        self.treeWidget = QtWidgets.QTreeWidget()  # 创建操作符区部件
        self.treeWidget.header().setSectionResizeMode(3)
        self.treeWidget.header().setStretchLastSection(False)
        self.treeWidget.setAutoScroll(False)
        self.treeWidget.headerItem().setText(0, 'Operators')

        self.left_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)  # 创建一个垂直布局的splitter
        self.left_splitter.addWidget(self.dataWidget)  # 将数据区与操作符区放进splitter
        self.left_splitter.addWidget(self.treeWidget)
        self.left_splitter.handle(1).setFixedHeight(2)
        self.left_splitter.setStretchFactor(0, 1)  # 设置splitter初始比例为1:1
        self.left_splitter.setStretchFactor(1, 1)
        self.left_layout.addWidget(self.left_splitter)  # 将splitter放进left_layout

        self.operators = operators
        # 使用字典存放treeitem
        self.treeitem = {'level1': [], 'level2': [], 'level3': []}

        # 根据operators中的操作符循环生成treeitem对象
        for level1 in operators.keys():
            temp1 = QtWidgets.QTreeWidgetItem(self.treeWidget)
            temp1.setText(0, level1)
            temp1.setToolTip(0, level1)
            temp1.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            self.treeitem['level1'].append(temp1)
            for level2 in operators[level1].keys():
                temp2 = QtWidgets.QTreeWidgetItem(temp1)
                temp2.setText(0, level2)
                temp2.setToolTip(0, level2)
                temp2.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                self.treeitem['level2'].append(temp2)
                for level3 in operators[level1][level2]:
                    temp3 = QtWidgets.QTreeWidgetItem(temp2)
                    temp3.setText(0, level3)
                    temp3.setToolTip(0, level3)
                    self.treeitem['level3'].append(temp3)

        # 在中间区域放置控件
        self.runProject = QtWidgets.QPushButton('Run')
        self.clearProcess = QtWidgets.QPushButton('Clear')
        self.center_layout.addWidget(self.runProject, 0, 0, 1, 2)
        self.center_layout.addWidget(self.clearProcess, 0, 2, 1, 2)
        self.processWidget = QtWidgets.QTableWidget()
        self.processWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.processWidget.setAcceptDrops(True)
        self.center_layout.addWidget(self.processWidget, 1, 0, 12, 12)
        self.processWidget.setColumnCount(3)
        self.processWidget.setRowCount(5)
        fontId = QtGui.QFontDatabase.addApplicationFont('..\\font\\Regular-400.otf')
        fontName = QtGui.QFontDatabase.applicationFontFamilies(fontId)[0]
        self.font = QtGui.QFont(fontName, 12)

        item1 = QtWidgets.QTableWidgetItem()
        item1.setFont(self.font)
        item1.setText(chr(0xf0fe))
        self.processWidget.setVerticalHeaderItem(4, item1)
        item2 = QtWidgets.QTableWidgetItem()
        item2.setFont(self.font)
        item2.setText(chr(0xf0fe))
        self.processWidget.setHorizontalHeaderItem(2, item2)

        # 在右侧栏放置控件
        self.settingWidget = QtWidgets.QFrame()
        self.settingWidget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.settingWidget.setObjectName('outPanel')
        self.settingLayout = QtWidgets.QVBoxLayout()
        self.settingLayout.setContentsMargins(0, 3, 0, 0)
        self.settingWidget.setLayout(self.settingLayout)
        label = QtWidgets.QLabel('Parameters')
        label.setObjectName('title')
        label.setFixedHeight(25)
        self.settingLayout.addWidget(label)

        label = QtWidgets.QLabel('Process')
        label.setFixedHeight(20)
        label.setObjectName('subtitle')
        self.settingLayout.addWidget(label)
        splitPanel = QtWidgets.QFrame()
        splitPanel.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.splitLayout = QtWidgets.QVBoxLayout()
        splitPanel.setLayout(self.splitLayout)
        splitPanel.setObjectName('splitPanel')
        self.settingLayout.addWidget(splitPanel)

        self.parameterWidget = QtWidgets.QWidget()
        self.splitLayout.addWidget(self.parameterWidget)
        self.splitLayout.addStretch(1)

        # layout.itemAt().widget可以获取layout的子widget

        self.helpWidget = QtWidgets.QFrame()
        self.helpWidget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.helpWidget.setObjectName('outPanel')
        self.helpLayout = QtWidgets.QVBoxLayout()
        self.helpLayout.setContentsMargins(0, 3, 0, 0)
        self.helpWidget.setLayout(self.helpLayout)
        label = QtWidgets.QLabel('Help')
        label.setObjectName('title')
        label.setFixedHeight(25)
        self.helpLayout.addWidget(label)
        label = QtWidgets.QLabel('Process')
        label.setFixedHeight(20)
        label.setObjectName('subtitle')
        self.helpLayout.addWidget(label)

        splitPanel = QtWidgets.QFrame()
        splitPanel.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.splitHelp = QtWidgets.QVBoxLayout()
        splitPanel.setLayout(self.splitHelp)
        splitPanel.setObjectName('splitPanel')


        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        self.helpMessage = QtWidgets.QLabel('No message can be found. Please wait for the operation.')
        self.helpMessage.setWordWrap(True)
        sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.helpMessage.setSizePolicy(sizepolicy)
        scroll.setWidget(splitPanel)
        self.splitHelp.addWidget(self.helpMessage)
        self.splitHelp.addStretch(1)
        self.helpLayout.addWidget(scroll)


        self.right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)  # 创建一个垂直布局的splitter
        self.right_splitter.addWidget(self.settingWidget)  # 将设置区与帮助区放进splitter
        self.right_splitter.addWidget(self.helpWidget)
        self.right_splitter.handle(1).setFixedHeight(2)
        self.right_splitter.setStretchFactor(0, 1)  # 设置splitter初始比例为1:1
        self.right_splitter.setStretchFactor(1, 1)
        self.right_layout.addWidget(self.right_splitter)  # 将splitter放进right_layout

        # 现在结果页面放一个空的tabwidget
        tabWidget = QtWidgets.QTabWidget()
        tabWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
        tabWidget.setTabsClosable(True)
        tabWidget.setMovable(True)
        tabWidget.setObjectName('resultTab')
        self.result_layout.addWidget(tabWidget, 0, 0)

    def paintEvent(self, e):
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        painter = QtGui.QPainter(self)
        # 反锯齿
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, painter, self)


def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = MainUi({'d': 1}, {})
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
