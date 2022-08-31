# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'aboutform.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(363, 178)
        AboutDialog.setMinimumSize(QtCore.QSize(363, 178))
        AboutDialog.setMaximumSize(QtCore.QSize(363, 178))
        AboutDialog.setWindowOpacity(1.0)
        self.buttonBox = QtWidgets.QDialogButtonBox(AboutDialog)
        self.buttonBox.setGeometry(QtCore.QRect(270, 10, 81, 141))
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(AboutDialog)
        self.label.setGeometry(QtCore.QRect(40, 140, 151, 16))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(AboutDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 10, 181, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.versionLabel = QtWidgets.QLabel(AboutDialog)
        self.versionLabel.setGeometry(QtCore.QRect(10, 30, 181, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.versionLabel.setFont(font)
        self.versionLabel.setObjectName("versionLabel")
        self.label_4 = QtWidgets.QLabel(AboutDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 70, 261, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.label_3 = QtWidgets.QLabel(AboutDialog)
        self.label_3.setGeometry(QtCore.QRect(250, 60, 101, 101))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap("images/linux-terminal-96.png"))
        self.label_3.setObjectName("label_3")

        self.retranslateUi(AboutDialog)
        self.buttonBox.accepted.connect(AboutDialog.accept)
        self.buttonBox.rejected.connect(AboutDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        _translate = QtCore.QCoreApplication.translate
        AboutDialog.setWindowTitle(_translate("AboutDialog", "Dialog"))
        self.label.setText(_translate("AboutDialog", "Icons by icons8.com"))
        self.label_2.setText(_translate("AboutDialog", "Linux Remote Master"))
        self.versionLabel.setText(_translate("AboutDialog", "Версия"))
        self.label_4.setText(_translate("AboutDialog", "Автор: Гладышев Дмитрий (2022)"))
