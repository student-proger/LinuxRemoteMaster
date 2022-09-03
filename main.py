#!/usr/bin/python3

'''
* Author:         Gladyshev Dmitriy (2020-2022)
*
* Design Name:    Linux Remote Master
* Description:    Программа для удалённого администрирования Linux систем
'''

import os
import queue
import socket
import sys  # sys нужен для передачи argv в QApplication
from datetime import datetime
import time
import json
import paramiko
from playsound import playsound
import re
from queue import Queue

# Qt
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QMdiSubWindow, QMessageBox, QFileDialog, QMdiArea, QInputDialog, QLineEdit
from PyQt5.Qt import pyqtSignal
from PyQt5.QtGui import QColor
# design
import mainform
import mdiform
import aboutform

VER = "0.0.1"

# Количество одновременных потоков
THREADS_COUNT = 4

settings = {
    "EnableLog": True
}

# Путь к каталогу хранения данных
datapath = ""
# Путь к логам
logpath = ""
# Путь к каталогу программы
path = ""
# Портативная версия
portable = True
# Словарь хостов
list_hosts = {}
# Словарь групп хостов
list_groups = {}
# Список команд
list_commands = []


def messageBox(title: str, msg: str):
    """
    Отображение диалогового окна с сообщением.

    :param title: заголовок окна
    :param msg: сообщение
    """
    msgbox = QMessageBox()
    msgbox.setIcon(QMessageBox.Information)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    msgbox.exec_()


def logger(msg):
    """
    Логирование.

    :param msg: текст сообщения
    """
    if settings["EnableLog"]:
        now = datetime.now()
        ss = datetime.strftime(now, "%Y-%m")
        s = datetime.strftime(now, "%d.%m.%Y  %H:%M:%S")
        s = s + " > " + msg
        f = open(datapath + "log/log" + ss + ".txt", "at")
        f.write(s + "\n")
        print(s)
        f.close()


def isWindows():
    """ Проверяет, под какой ОС запущено приложение. True, если Windows. """
    if os.name == "nt":
        return True
    else:
        return False


def saveSettings():
    """ Сохранение настроек в файл. """
    logger("Сохранение настроек.")
    try:
        with open(datapath + 'settings.json', 'w') as f:
            json.dump(settings, f)
    except:
        logger("ОШИБКА: Не удалось сохранить настройки.")
        messageBox("Критическая ошибка", "Ошибка сохранения файла настроек. Возможно нет прав доступа на запись.")


def loadSettings():
    """ Загрузка настроек из файла. """
    global settings
    global list_hosts
    global list_groups

    try:
        with open(datapath + 'settings.json') as f:
            settings = json.load(f)
    except FileNotFoundError:
        pass
    except:
        logger("Ошибка чтения файла настроек. Возможно нет прав доступа на чтение.")
        messageBox("Критическая ошибка", "Ошибка чтения файла настроек. Возможно нет прав доступа на чтение.")

    try:
        with open(datapath + 'hosts.txt') as f:
            for line in f:
                pass
    except FileNotFoundError:
        pass
    except:
        logger("Ошибка чтения файла настроек. Возможно нет прав доступа на чтение.")
        messageBox("Критическая ошибка", "Ошибка чтения файла настроек. Возможно нет прав доступа на чтение.")


class LRMApp(QtWidgets.QMainWindow, mainform.Ui_MainWindow):
    """ Класс главного окна приложения. """
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Очередь хостов
        self.host_queue = Queue()

        # Главный таймер перебора хостов
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.stop()

        # Список MDI форм с консолью
        self.mdi_console = {}
        # Список подформ (необходимо для правильного отображения формочек в mdiArea)
        self.mdi_console_sub_form = {}
        # Список потоков
        self.thrn = {}
        # Текущее количество запущенных потоков
        self.count_threads = 0
        # Завершено хостов
        self.completed = 0

        loadSettings()
        self.loadHostsDB()

        self.aboutwindow = AboutApp()

        self.loadCommandsButton.clicked.connect(self.loadListCommands)
        self.loadTaskHostsButton.clicked.connect(self.loadListTaskHosts)
        self.commandLinkButton.clicked.connect(self.executeClick)
        self.loadCommandsAction.triggered.connect(self.loadListCommands)
        self.saveCommandsAction.triggered.connect(self.saveListCommands)
        self.clearCommandsAction.triggered.connect(self.clearListCommands)
        self.loadTaskHostsAction.triggered.connect(self.loadListTaskHosts)
        self.aboutAction.triggered.connect(self.aboutClick)
        self.subWindowViewAction.triggered.connect(self.subWindowView)
        self.tabbedWindowViewAction.triggered.connect(self.tabbedWindowView)
        self.hostsTable.__class__.keyPressEvent = self.hostsTablePressEvent

        self.progressBar.setValue(0)
        self.setWindowTitle("Linux Remote Master v" + VER)

        # В файле mainform.py не учитывается возможность несовпадения каталога программы с рабочим каталогом.
        # Такое происходит, например, при автостарте программы. И в этом случае изображения не подгружаются.
        # Данные строки исправляют эту ошибку и повторно загружают ресурсы, но уже с учётом пути.
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap(path + "images/alarm_32px.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #self.setWindowIcon(icon)

    def hostsTablePressEvent(self, event):
        """
        Событие нажатия кнопок клавиатуры на списке хостов.

        :param event: событие
        """
        if event.key() == QtCore.Qt.Key_Delete:
            for item in self.hostsTable.selectedItems():
                self.hostsTable.removeRow(item.row())
            self.hostsTable.resizeColumnsToContents()
        if event.key() == QtCore.Qt.Key_Insert:
            text, okPressed = QInputDialog.getText(self, "Get text", "Your name:", QLineEdit.Normal, "")
            if okPressed and text != '':
                print(text)

    def createConsole(self, id, title):
        """
        Создание окна консоли.

        :param id: ID хоста
        :param title: Заголовок окна
        """
        self.mdi_console[id] = MDIForm()
        self.mdi_console_sub_form[id] = QMdiSubWindow()
        self.mdi_console_sub_form[id].setWidget(self.mdi_console[id])
        self.mdiArea.addSubWindow(self.mdi_console_sub_form[id])
        self.mdi_console_sub_form[id].resize(self.mdi_console[id].size())
        self.mdi_console_sub_form[id].setWindowTitle(title)
        self.mdi_console_sub_form[id].show()

    def subWindowView(self):
        self.mdiArea.setViewMode(QMdiArea.SubWindowView)

    def tabbedWindowView(self):
        self.mdiArea.setViewMode(QMdiArea.TabbedView)

    @staticmethod
    def loadHostsDB():
        """ Загрузка списка всех хостов. """
        global list_hosts
        global list_groups
        list_hosts = {}
        list_groups = {}
        try:
            db = open(datapath + "hosts.txt", "rt")
            for line in db:
                line = line.strip()
                if line[0] == "@":
                    line = line[1:]
                    q = line.split("=")
                    w = q[1].split(",")
                    list_groups[q[0]] = []
                    list_groups[q[0]].extend(w)
                else:
                    q = line.split("=")
                    w = q[1].split("|")
                    list_hosts[q[0]] = {"ip": "", "user": "", "password": ""}
                    list_hosts[q[0]]["ip"] = w[0]
                    list_hosts[q[0]]["user"] = w[1]
                    list_hosts[q[0]]["password"] = w[2]
            db.close()
        except:
            messageBox("LinuxRemoteMaster", "Ошибка чтения файла со списком хостов.")
        #print(list_hosts)
        #print(list_groups)
    
    def loadListCommands(self):
        """ Загрузка списка команд из файла. """
        fname = QFileDialog.getOpenFileName(self, 'Выбор файла', path, "Текстовые файлы (*.txt);;Все файлы (*.*)")[0]
        if fname != "":
            try:
                f = open(fname, "rt")
                self.listCommands.clear()
                for item in f:
                    self.listCommands.addItem(item.strip())
                f.close()
            except:
                messageBox("Linux Remote Master", "Ошибка загрузки файла с командами.")

    def saveListCommands(self):
        """ Сохранение списка команд в файл. """
        fname = QFileDialog.getSaveFileName(self, 'Выбор файла', path, "Текстовые файлы (*.txt);;Все файлы (*.*)")[0]
        if fname != "":
            try:
                f = open(fname, "wt")
                for i in range(0, self.listCommands.count()):
                    f.write(self.listCommands.item(i).text() + "\n")
                f.close()
            except:
                messageBox("Linux Remote Master", "Ошибка сохранения файла с командами.")

    def clearListCommands(self):
        """ Очистка списка команд. """
        self.listCommands.clear()

    def loadListTaskHosts(self):
        """ Загрузка списка хостов из файла для задания. """
        fname = QFileDialog.getOpenFileName(self, 'Выбор файла', path, "Текстовые файлы (*.txt);;Все файлы (*.*)")[0]
        if fname != "":
            f = open(fname, "rt")
            self.hostsTable.clear()
            self.hostsTable.setRowCount(0)
            self.hostsTable.setHorizontalHeaderLabels(["Хост", "IP", "Статус"])
            row = 0
            for item in f:
                item = item.strip()
                if item[0] == "@":  # Группа
                    item = item[1:]
                    if item in list_groups:
                        gr = list_groups[item]
                        print(gr)
                        for h in gr:
                            ip = list_hosts[h]["ip"]
                            self.hostsTable.setRowCount(row + 1)
                            self.hostsTable.setItem(row, 0, QTableWidgetItem(h.strip()))
                            self.hostsTable.setItem(row, 1, QTableWidgetItem(ip))
                            row = row + 1
                else:  # Хост
                    if item in list_hosts:
                        ip = list_hosts[item]["ip"]
                        self.hostsTable.setRowCount(row + 1)
                        self.hostsTable.setItem(row, 0, QTableWidgetItem(item.strip()))
                        self.hostsTable.setItem(row, 1, QTableWidgetItem(ip))
                        row = row + 1
            f.close()
            self.hostsTable.resizeColumnsToContents()

    def aboutClick(self):
        self.aboutwindow.exec_()

    def executeClick(self):
        """ Обработчик клика по кнопке запуска выполнения команд. """
        global list_commands

        # Создаём список команд
        list_commands = []
        for i in range(0, self.listCommands.count()):
            s = self.listCommands.item(i).text()
            list_commands.append(s)

        # Создаём очередь хостов
        self.host_queue.queue.clear()
        for row in range(0, self.hostsTable.rowCount()):
            self.host_queue.put((self.hostsTable.item(row, 0).text(), row))

        self.progressBar.setMaximum(self.hostsTable.rowCount())
        self.progressBar.setValue(0)
        self.completed = 0

        self.timer.start(100)

    def on_timer(self):
        """ Обработчик событий таймера. """
        if self.count_threads < THREADS_COUNT:
            try:
                s = self.host_queue.get_nowait()
            except queue.Empty:
                print("Очередь закончилась.")
                self.timer.stop()
                return
            print("Очередь: " + s[0])
            id = s[1]
            host = list_hosts[s[0]]["ip"]
            username = list_hosts[s[0]]["user"]
            password = list_hosts[s[0]]["password"]

            self.createConsole(id, s[0] + " [" + host + "]")
            self.thrn[id] = processWork(id, host, username, password)
            self.thrn[id].usignal.connect(self.on_data_ready)
            self.thrn[id].statesignal.connect(self.on_statesignal)
            self.thrn[id].progress_signal.connect(self.on_progress_signal)
            self.thrn[id].start()

    def on_data_ready(self, id: int, data: str, newline: bool):
        """
        Обработка данных поступивших из потоков.

        :param id: ID потока
        :param data: данные
        :param newline: перенос на новую строку
        """
        if self.mdi_console[id].listWidget.count() == 0:
            self.mdi_console[id].listWidget.addItem("")
        self.mdi_console[id].listWidget.item(self.mdi_console[id].listWidget.count() - 1).setText(data)
        if newline:
            self.mdi_console[id].listWidget.addItem("")

    def on_statesignal(self, state: bool):
        """
        Обработка события запуска/останова потока.

        :param state: True - старт потока, False - завершение
        """
        if state:
            self.count_threads = self.count_threads + 1
        else:
            self.count_threads = self.count_threads - 1
            self.completed = self.completed + 1
            self.progressBar.setValue(self.completed)

    def on_progress_signal(self, id, progress, flag):
        """
        Обработка событий прогресса выполнения команд.

        :param id: ID хоста
        :param progress: текущий прогресс
        :param flag: флаг ошибки: 0 - OK, 1 - Готов, -1 - ошибка подключения, -2 - ошибка команды
        """
        self.hostsTable.setItem(id, 2, QTableWidgetItem(progress))
        if flag == 1:
            for i in range(0, 3):
                self.hostsTable.item(id, i).setBackground(QColor(184, 251, 170))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(path + "images/checked-checkbox-24.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.mdi_console_sub_form[id].setWindowIcon(icon)
        elif flag == -1:
            for i in range(0, 3):
                self.hostsTable.item(id, i).setBackground(QColor(255, 166, 166))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(path + "images/error-24.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.mdi_console_sub_form[id].setWindowIcon(icon)
        elif flag == -2:
            for i in range(0, 3):
                self.hostsTable.item(id, i).setBackground(QColor(248, 248, 116))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(path + "images/error-24.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.mdi_console_sub_form[id].setWindowIcon(icon)
        self.hostsTable.resizeColumnsToContents()


class MDIForm(QtWidgets.QMainWindow, mdiform.Ui_MDIWindow):
    """ Класс MDI окон консолей """
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class AboutApp(QtWidgets.QDialog, aboutform.Ui_AboutDialog):
    """ Класс окна <О программе> """
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.versionLabel.setText("Версия " + VER)


class processWork(QtCore.QThread):
    """ Класс потока выполнения команд """
    # Сигнал для передачи результатов выполнения команд в консоль
    usignal = pyqtSignal(object, object, object)
    # Сигнал состояния потока
    statesignal = pyqtSignal(object)
    # Сигнал прогресса выполнения
    progress_signal = pyqtSignal(object, object, object)

    def __init__(self, id, host, username, password):
        """
        Инициализация экземпляра потока.

        :param id: ID хоста
        :param host: IP хоста
        :param username: имя пользователя
        :param password: пароль
        """
        QtCore.QThread.__init__(self)
        self.id = id
        self.host = host
        self.username = username
        self.password = password
        self.startPosition = True
        self.consolebuf = ""

    def append_console_string(self, text):
        """
        Добавление строки результата выполнения команды в консоль. Учитывается наличие escape-последовательностей,
        в т.ч. стирание строки (например, прогресс при выполнении команды wget).

        :param text: текст, который необходимо отправить в консоль
        """
        text = repr(text)

        if text != "''":
            text = text[1:-1]  # избавляемся от кавычек в начале и конце
            while '\\r\\n' in text:
                text = text.replace('\\r\\n', '\\n')
            text = re.sub(r'\\x1b\[\d+m', "", text)  # регулярка для удаления escape последовательностей вида \x1b[33m

            skipNext = False
            for i in range(0, len(text)):
                if skipNext:
                    skipNext = False
                    continue
                if text[i] == "\\" and text[i + 1] == "r":  # символ перехода в начало строки
                    self.startPosition = True
                    skipNext = True
                    self.usignal.emit(self.id, self.consolebuf, False)
                    continue
                if text[i] == "\\" and text[i + 1] == "n":  # символ переноса каретки
                    self.startPosition = True
                    skipNext = True
                    self.usignal.emit(self.id, self.consolebuf, True)
                    self.consolebuf = ""
                    continue
                if self.startPosition:  # курсор в начале строки
                    self.consolebuf = text[i]
                    self.startPosition = False
                else:
                    self.consolebuf = self.consolebuf + text[i]
            self.usignal.emit(self.id, self.consolebuf, False)

    def run(self):
        """ Запуск потока. """
        self.statesignal.emit(True)
        sess = self.connectToHost(self.host, self.username, self.password, 22)
        if sess != False:  # Удалось подключиться
            row = 1
            ok = True
            # По очереди отправляем все команды из списка на выполнение
            for item in list_commands:
                self.progress_signal.emit(self.id, str(row) + "/" + str(len(list_commands)), 0)
                ok = self.executeLine(sess, item)
                if not ok:
                    break
            self.closeConnection(sess)
            if ok == True:
                self.progress_signal.emit(self.id, "Готово", 1)
            else:
                self.progress_signal.emit(self.id, ok, -2)
        else:
            self.usignal.emit(self.id, "Ошибка подключения", True)
            self.progress_signal.emit(self.id, "Ошибка", -1)
        self.statesignal.emit(False)

    @staticmethod
    def connectToHost(hostname, username, password, port=22):
        """
        Подключение к хосту по SSH.

        :param hostname: IP хоста
        :param username: имя пользователя
        :param password: пароль
        :param port: порт SSH
        :return: кортеж из объекта-клиента SSH и пароля пользователя. При ошибке подключения возвращается False.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=hostname, username=username, password=password, port=port, timeout=5)
        except TimeoutError:
            return False
        except socket.timeout:
            return False

        return client, password

    def executeLine(self, session, cmd):
        """
        Выполнение команды для указанного подключения.

        :param session: кортеж из объекта-клиента SSH и пароля пользователя
        :param cmd: команда
        :return: True, если команда выполнена
        """
        self.usignal.emit(self.id, "# " + cmd, True)

        channel = session[0].get_transport().open_session()
        channel.get_pty()
        channel.settimeout(60)
        password = session[1]
        channel.exec_command(cmd)

        try:
            for line in iter(lambda: channel.recv(65535).decode(), ""):
                if cmd.startswith("sudo "):
                    if line.startswith("[sudo] password ") or line.startswith("[sudo] пароль "):
                        channel.send(password + '\n')
                    elif ("is not in the sudoers file" in line) or ("отсутствует в файле sudoers" in line):
                        return "sudoers"
                self.append_console_string(line)
        except socket.timeout:
            return "timeout"

        channel.close()
        # добавляем пустую строку после результата каждой команды
        self.usignal.emit(self.id, "", True)
        return True

    @staticmethod
    def closeConnection(session):
        """
        Закрытие подключения.

        :param session: кортеж из объекта-клиента SSH и пароля пользователя
        """
        session[0].close()


def main():
    global datapath
    global logpath
    global path

    if isWindows():
        print("OS: Windows")
    else:
        print("OS: Linux")

    k = 0
    path = __file__
    for i in range(0, len(path)):
        if path[i] == "\\" or path[i] == "/":
            k = i
    path = path[:k + 1]
    print("PATH: " + path)

    if portable:
        datapath = path + "data/"
        logpath = path + "log/"
    else:
        if isWindows():
            datapath = os.getenv('APPDATA') + "\\LinuxRemoteMaster\\"
            logpath = datapath + "log\\"
        else:
            datapath = "~/LinuxRemoteMaster/"
            logpath = "/var/log/LinuxRemoteMaster/"

    if not os.path.exists(datapath):
        try:
            os.mkdir(datapath)
        except:
            messageBox("LinuxRemoteMaster", "Ошибка создания каталога: " + datapath)
    if not os.path.exists(logpath):
        try:
            os.mkdir(logpath)
        except:
            messageBox("LinuxRemoteMaster", "Ошибка создания каталога: " + logpath)

    print("LOGPATH: " + logpath)
    print("DATAPATH: " + datapath)

    if not os.path.exists(datapath + "hosts.txt"):
        f = open(datapath + "hosts.txt", "wt")
        f.write("host1=192.168.1.2|user|password\n")
        f.write("host2=192.168.1.3|user|password\n")
        f.write("host3=192.168.1.4|testuser|password\n")
        f.write("sekretar=192.168.1.5|user|password\n")
        f.write("host4=192.168.1.6|user|password\n")
        f.write("direktor=192.168.1.7|dir|password\n")
        f.write("@kabinet1=host1,host3\n")
        f.write("@priem=sekretar,direktor\n")
        f.close()

    app = QtWidgets.QApplication(sys.argv)
    window = LRMApp()
    window.show()

    app.exec_()


if __name__ == '__main__':
    main()
