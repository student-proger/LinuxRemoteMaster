# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mdiform.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MDIWindow(object):
    def setupUi(self, MDIWindow):
        MDIWindow.setObjectName("MDIWindow")
        MDIWindow.resize(446, 277)
        self.centralwidget = QtWidgets.QWidget(MDIWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        MDIWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MDIWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 446, 21))
        self.menubar.setObjectName("menubar")
        MDIWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MDIWindow)
        self.statusbar.setObjectName("statusbar")
        MDIWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MDIWindow)
        QtCore.QMetaObject.connectSlotsByName(MDIWindow)

    def retranslateUi(self, MDIWindow):
        _translate = QtCore.QCoreApplication.translate
        MDIWindow.setWindowTitle(_translate("MDIWindow", "MainWindow"))
