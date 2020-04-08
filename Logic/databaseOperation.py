from PyQt5 import QtSql
import datetime


class UserManagement():
    def __init__(self):
        self.db=QtSql.QSqlDatabase.addDatabase('QMYSQL')
        self.db.setHostName("localhost")
        self.db.setPort(3306)
        self.db.setDatabaseName('mining')
        self.db.setUserName('root')
        self.db.setPassword('123456')

    def select(self, userName):
        try:
            self.db.open()
            query = QtSql.QSqlQuery("select * from user where userName = '" + userName + "'")
            if query.first():
                result = []
                for i in range(query.record().count()):
                    result.append(query.value(i))
            else:
                result = None
            self.db.close()
            return result
        except:
            print('Error')

    def register(self, username, password, email):
        today = datetime.date.today()
        try:
            self.db.open()
            query = QtSql.QSqlQuery()
            query.exec_("insert into user values('" + username + "', '" + password + "', '" +
                        email + "', '" + str(today) + "')")
            self.db.close()
            return True
        except Exception as e:
            print(e)
            #print('Register error')
            return False
