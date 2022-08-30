#!/usr/bin/python3

'''
* Author:         Gladyshev Dmitriy (2020-2022)
*
* Design Name:    Linux Remote Master
* Description:    Программа для удалённого администрирования Linux систем
'''

import os
import queue
import sys  # sys нужен для передачи argv в QApplication
from datetime import datetime
import time
import json
import paramiko
from playsound import playsound
from threading import Thread, Lock
import re
from queue import Queue

# Qt
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QLabel, QInputDialog, QComboBox, QMdiSubWindow
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject
from PyQt5.Qt import pyqtSignal
# design
import mainform
import mdiform

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
    Отображение диалогового окна с сообщением

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
    Логирование

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
    """Проверяет, под какой ОС запущено приложение. True, если Windows."""
    if os.name == "nt":
        return True
    else:
        return False


def saveSettings():
    """Сохранение настроек в файл"""
    logger("Сохранение настроек.")
    try:
        with open(datapath + 'settings.json', 'w') as f:
            json.dump(settings, f)
    except:
        logger("ОШИБКА: Не удалось сохранить настройки.")
        messageBox("Критическая ошибка", "Ошибка сохранения файла настроек. Возможно нет прав доступа на запись.")


def loadSettings():
    """Загрузка настроек из файла"""
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

    # Устанавливаем значения по-умолчанию, если их нет в настройках
    #if "NotifyFile1" not in settings:
    #    settings["NotifyFile1"] = path + "sounds/male-1min.mp3"

startPosition = True
consolebuf = ""


class LRMApp(QtWidgets.QMainWindow, mainform.Ui_MainWindow):
    """Класс главного окна приложения"""
    def __init__(self):
        super().__init__()

        # Очередь хостов
        host_queue = Queue()

        # Список MDI форм с консолью
        self.mdi_console = []
        # Список подформ (необходимо для правильного отображения формочек в mdiArea)
        self.mdi_console_sub_form = []

        loadSettings()
        self.loadHostsDB()

        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        for i in range(0, THREADS_COUNT):
            self.mdi_console.append(MDIForm())
            self.mdi_console_sub_form.append(QMdiSubWindow())
            self.mdi_console_sub_form[i].setWidget(self.mdi_console[i])
            self.mdiArea.addSubWindow(self.mdi_console_sub_form[i])
            self.mdi_console_sub_form[i].resize(self.mdi_console[i].size())
            self.mdi_console_sub_form[i].show()

        self.loadCommandsButton.clicked.connect(self.loadListCommands)
        self.loadTaskHostsButton.clicked.connect(self.loadListTaskHosts)
        self.commandLinkButton.clicked.connect(self.executeClick)
        self.loadCommandsAction.triggered.connect(self.loadListCommands)
        self.saveCommandsAction.triggered.connect(self.saveListCommands)
        self.clearCommandsAction.triggered.connect(self.clearListCommands)
        self.loadTaskHostsAction.triggered.connect(self.loadListTaskHosts)

        # В файле mainform.py не учитывается возможность несовпадения каталога программы с рабочим каталогом.
        # Такое происходит, например, при автостарте программы. И в этом случае изображения не подгружаются.
        # Данные строки исправляют эту ошибку и повторно загружают ресурсы, но уже с учётом пути.
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap(path + "images/alarm_32px.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #self.setWindowIcon(icon)

    @staticmethod
    def loadHostsDB():
        '''
        Загрузка списка всех хостов
        '''
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
        '''
        Загрузка списка команд из файла.
        '''
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
        '''
        Сохранение списка команд в файл.
        '''
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
        '''
        Очистка списка команд.
        '''
        self.listCommands.clear()

    def loadListTaskHosts(self):
        '''
        Загрузка списка хостов из файла для задания.
        '''
        fname = QFileDialog.getOpenFileName(self, 'Выбор файла', path, "Текстовые файлы (*.txt);;Все файлы (*.*)")[0]
        if fname != "":

            f = open(fname, "rt")
            self.hostsTable.clear()
            self.hostsTable.setRowCount(0)
            self.hostsTable.setHorizontalHeaderLabels(["Хост", "IP"])
            row = 0
            for item in f:
                item = item.strip()
                if item in list_hosts:
                    ip = list_hosts[item]["ip"]
                    self.hostsTable.setRowCount(row + 1)
                    self.hostsTable.setItem(row, 0, QTableWidgetItem(item.strip()))
                    self.hostsTable.setItem(row, 1, QTableWidgetItem(ip))
                    row = row + 1
            f.close()
            #self.hostsTable.setVerticalHeaderLabels(vh)
            self.hostsTable.resizeColumnsToContents()


    def executeClick(self):
        global thrn
        global list_commands

        list_commands = []
        for i in range(0, self.listCommands.count()):
            s = self.listCommands.item(i).text()
            list_commands.append(s)

        thrn = processWork()
        thrn.usignal.connect(self.on_data_ready)
        thrn.start()

    def on_data_ready(self, id: int, data: str, newline: bool):
        """ Обработка данных поступивших из потоков

        :param id: ID потока
        :param data: данные
        :param newline: перенос на новую строку
        """
        if self.mdi_console[0].listWidget.count() == 0:
            self.mdi_console[0].listWidget.addItem("")
        self.mdi_console[0].listWidget.item(self.mdi_console[0].listWidget.count() - 1).setText(data)
        if newline:
            self.mdi_console[0].listWidget.addItem("")

class MDIForm(QtWidgets.QMainWindow, mdiform.Ui_MDIWindow):
    """Класс MDI окон консолей"""
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class processWork(QtCore.QThread):
    """Поток выполнения команд"""
    usignal = pyqtSignal(object, object, object)

    def __init__(self):
        QtCore.QThread.__init__(self)


    def append_log(self, text):
        global startPosition
        global consolebuf

        text = repr(text)

        if text != "''":
            text = text[1:-1]  # избавляемся от кавычек в начале и конце
            while '\\r\\n' in text:
                text = text.replace('\\r\\n', '\\n')
            text = re.sub(r'\\x1b\[\d+m', "",
                          text)  # регулярка для удаления escape последовательностей вида \x1b[33m

            skipNext = False
            for i in range(0, len(text)):
                if skipNext:
                    skipNext = False
                    continue
                if text[i] == "\\" and text[i + 1] == "r":
                    startPosition = True
                    skipNext = True
                    self.usignal.emit(0, consolebuf, False)
                    continue
                if text[i] == "\\" and text[i + 1] == "n":
                    startPosition = True
                    skipNext = True
                    self.usignal.emit(0, consolebuf, True)
                    consolebuf = ""
                    continue
                if startPosition:
                    consolebuf = text[i]
                    startPosition = False
                else:
                    consolebuf = consolebuf + text[i]
            self.usignal.emit(0, consolebuf, False)

    def run(self):
        sess = self.connectToHost("", "", "", 22)
        for item in list_commands:
            print(item)
            s = self.executeLine(sess, item)
        self.closeConnection(sess)

    def connectToHost(self, hostname, username, password, port=22):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=hostname, username=username, password=password, port=port)

        return client, password

    def executeLine(self, session, cmd):
        self.usignal.emit(0, "# " + cmd, True)

        channel = session[0].get_transport().open_session()
        channel.get_pty()
        channel.settimeout(30)
        password = session[1]
        channel.exec_command(cmd)

        for line in iter(lambda: channel.recv(65535).decode(), ""):
            if cmd.startswith("sudo "):
                if line.startswith("[sudo] password "):
                    channel.send(password + '\n')
                elif ("is not in the sudoers file" in line) or ("отсутствует в файле sudoers" in line):
                    return False
            #line = repr(line)
            self.append_log(line)
            #print(repr(line))

            '''if "\n" in line:
                self.textEdit.append(line)'''
        channel.close()
        self.usignal.emit(0, "", True)
        return True

    def closeConnection(self, session):
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
