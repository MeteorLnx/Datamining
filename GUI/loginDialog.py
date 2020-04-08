from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from GUI.titleBar import CustomDialog, TitleBar
import sys

class LoginDialog(CustomDialog):
    def __init__(self, parent, account):
        super().__init__(parent)
        self.resize(250, 200)
        self.setFixedSize(self.width(), self.height())
        self.init_ui(account)

    def init_ui(self, account):
        # 设置界面控件

        self.setWindowIconText(chr(0xf2f6))
        self.setWindowTitle('Login')

        self.main_layout = QGridLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(5)

        name_label = QLabel('User Name')
        passwd_label = QLabel('Password')

        self.name_box = QComboBox()
        self.name_box.setEditable(True)
        for item in account:
            self.name_box.addItem(item)
        self.passwd_box = QLineEdit()
        self.passwd_box.setEchoMode(QLineEdit.Password)

        self.message = QLabel()
        self.message.setFixedHeight(20)
        self.message.setObjectName('tips')
        self.register_btn = QPushButton('Register')

        self.login_btn = QPushButton('Login')
        self.login_btn.setShortcut(Qt.Key_Return)

        self.main_layout.addWidget(name_label, 0, 0, 1, 1)
        self.main_layout.addWidget(passwd_label, 1, 0, 1, 1)
        self.main_layout.addWidget(self.name_box, 0, 1, 1, 2)
        self.main_layout.addWidget(self.passwd_box, 1, 1, 1, 2)
        self.main_layout.addWidget(self.message, 3, 0, 1, 3)
        self.main_layout.addWidget(self.register_btn, 4, 0, 1, 1)
        self.main_layout.addWidget(self.login_btn, 4, 2, 1, 1)

        self._layout.addWidget(self.main_widget)
        self.setModal(True)
        self.show()

    def closeEvent(self, e):
        if isinstance(self.sender(), TitleBar):
            self.parent().close()


class RegisterDialog(CustomDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.resize(350, 250)
        self.setFixedSize(self.width(), self.height())
        self.init_ui()

    def init_ui(self):
        # 设置界面控件
        self.setWindowIconText(chr(0xf234))
        self.setWindowTitle('Register')

        self.main_layout = QGridLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(5)

        name_label = QLabel('Username')
        passwd_label = QLabel('Password')
        confirmpwd_label = QLabel('Confirm Password')
        emial_label = QLabel('E-mail')

        self.name_box = QLineEdit()
        self.name_box.setPlaceholderText('Between 6 and 12 characters')
        self.name_box.setFixedWidth(180)
        self.passwd_box = QLineEdit()
        self.passwd_box.setEchoMode(QLineEdit.Password)
        self.passwd_box.setPlaceholderText('Between 6 and 12 characters')
        self.confirmpwd_box = QLineEdit()
        self.confirmpwd_box.setEchoMode(QLineEdit.Password)
        self.confirmpwd_box.setPlaceholderText('Enter password again')
        self.email_box = QLineEdit()
        self.email_box.setPlaceholderText('Enter email')
        self.message = QLabel()
        self.message.setFixedHeight(28)
        self.message.setObjectName('tips')

        self.register_btn = QPushButton('Register')

        self.main_layout.addWidget(name_label, 0, 0, 1, 1)
        self.main_layout.addWidget(passwd_label, 1, 0, 1, 1)
        self.main_layout.addWidget(confirmpwd_label, 2, 0, 1, 1)
        self.main_layout.addWidget(emial_label, 3, 0, 1, 1)
        self.main_layout.addWidget(self.name_box, 0, 1, 1, 2)
        self.main_layout.addWidget(self.passwd_box, 1, 1, 1, 2)
        self.main_layout.addWidget(self.confirmpwd_box, 2, 1, 1, 2)
        self.main_layout.addWidget(self.email_box, 3, 1, 1, 2)
        self.main_layout.addWidget(self.message, 4, 0, 1, 3)
        self.main_layout.addWidget(self.register_btn, 5, 0, 1, 3)

        self._layout.addWidget(self.main_widget)
        self.setModal(True)
        self.show()


def callDialog(ui):
    dialog = LoginDialog(ui, ['lnx123'])
    dialog.login_btn.clicked.connect(lambda: login(dialog))
    dialog.register_btn.clicked.connect(lambda: register(dialog))

def login(dialog):
    dialog.close()

def register(dialog):
    registerDialog = RegisterDialog(dialog)
    registerDialog.register_btn.clicked.connect(userRegister)

def userRegister():
    print('register')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = open('../qss/mainwindow.qss', 'r', encoding='UTF-8')
    app.setStyleSheet(style.read())
    ui = QMainWindow()
    button = QPushButton('ddd', ui)
    button.clicked.connect(lambda: callDialog(ui))
    ui.show()
    sys.exit(app.exec_())
