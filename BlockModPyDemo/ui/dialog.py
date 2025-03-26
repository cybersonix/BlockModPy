# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from BlockModPy.zoom_mesh_graphics_view import ZoomMeshGraphicsView
from BlockModPyDemo.resources import BlockModDemoPy_rc  # noqa


class Ui_BlockModPyDemoDialog(object):
    def setupUi(self, BlockModPyDemoDialog):
        if not BlockModPyDemoDialog.objectName():
            BlockModPyDemoDialog.setObjectName("BlockModPyDemoDialog")
        BlockModPyDemoDialog.resize(1273, 663)
        self.gridLayout_2 = QGridLayout(BlockModPyDemoDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.widget_2 = QWidget(BlockModPyDemoDialog)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.toolButtonNew = QToolButton(self.widget_2)
        self.toolButtonNew.setObjectName("toolButtonNew")
        icon = QIcon()
        icon.addFile(":/gfx/filenew_32x32.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonNew.setIcon(icon)
        self.toolButtonNew.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.toolButtonNew)

        self.toolButtonOpen = QToolButton(self.widget_2)
        self.toolButtonOpen.setObjectName("toolButtonOpen")
        icon1 = QIcon()
        icon1.addFile(":/gfx/fileopen_32x32.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonOpen.setIcon(icon1)
        self.toolButtonOpen.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.toolButtonOpen)

        self.toolButtonSave = QToolButton(self.widget_2)
        self.toolButtonSave.setObjectName("toolButtonSave")
        icon2 = QIcon()
        icon2.addFile(":/gfx/filesave_32x32.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonSave.setIcon(icon2)
        self.toolButtonSave.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.toolButtonSave)

        self.horizontalSpacer_2 = QSpacerItem(
            20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.toolButtonInfo = QToolButton(self.widget_2)
        self.toolButtonInfo.setObjectName("toolButtonInfo")
        icon3 = QIcon()
        icon3.addFile(":/gfx/info_32x32.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonInfo.setIcon(icon3)
        self.toolButtonInfo.setIconSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.toolButtonInfo)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.gridLayout_2.addWidget(self.widget_2, 0, 0, 1, 1)

        self.groupBox = QGroupBox(BlockModPyDemoDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = ZoomMeshGraphicsView(self.groupBox)
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setEnabled(True)

        self.verticalLayout.addWidget(self.graphicsView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButtonRemoveConnection = QPushButton(self.groupBox)
        self.pushButtonRemoveConnection.setObjectName("pushButtonRemoveConnection")

        self.horizontalLayout_2.addWidget(self.pushButtonRemoveConnection)

        self.pushButtonRemoveBlock = QPushButton(self.groupBox)
        self.pushButtonRemoveBlock.setObjectName("pushButtonRemoveBlock")

        self.horizontalLayout_2.addWidget(self.pushButtonRemoveBlock)

        self.pushButtonAddBlock = QPushButton(self.groupBox)
        self.pushButtonAddBlock.setObjectName("pushButtonAddBlock")

        self.horizontalLayout_2.addWidget(self.pushButtonAddBlock)

        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.gridLayout_2.addWidget(self.groupBox, 1, 0, 1, 1)

        self.groupBox_2 = QGroupBox(BlockModPyDemoDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.blockEditorView = ZoomMeshGraphicsView(self.groupBox_2)
        self.blockEditorView.setObjectName("blockEditorView")

        self.gridLayout.addWidget(self.blockEditorView, 0, 0, 3, 1)

        self.toolButtonAddSocket = QToolButton(self.groupBox_2)
        self.toolButtonAddSocket.setObjectName("toolButtonAddSocket")
        icon4 = QIcon()
        icon4.addFile(":/gfx/plus.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonAddSocket.setIcon(icon4)
        self.toolButtonAddSocket.setIconSize(QSize(24, 24))

        self.gridLayout.addWidget(self.toolButtonAddSocket, 0, 1, 1, 1)

        self.toolButtonRemoveSocket = QToolButton(self.groupBox_2)
        self.toolButtonRemoveSocket.setObjectName("toolButtonRemoveSocket")
        icon5 = QIcon()
        icon5.addFile(":/gfx/minus.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolButtonRemoveSocket.setIcon(icon5)
        self.toolButtonRemoveSocket.setIconSize(QSize(24, 24))

        self.gridLayout.addWidget(self.toolButtonRemoveSocket, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(
            20, 261, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout.addItem(self.verticalSpacer, 2, 1, 1, 1)

        self.checkBoxSocketIsInlet = QCheckBox(self.groupBox_2)
        self.checkBoxSocketIsInlet.setObjectName("checkBoxSocketIsInlet")

        self.gridLayout.addWidget(self.checkBoxSocketIsInlet, 3, 0, 1, 1)

        self.gridLayout_2.addWidget(self.groupBox_2, 1, 1, 1, 1)

        self.retranslateUi(BlockModPyDemoDialog)

        QMetaObject.connectSlotsByName(BlockModPyDemoDialog)

    # setupUi

    def retranslateUi(self, BlockModPyDemoDialog):
        BlockModPyDemoDialog.setWindowTitle(
            QCoreApplication.translate("BlockModPyDemoDialog", "BlockModPy Demo", None)
        )
        self.groupBox.setTitle(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u7f51\u683c\u6a21\u578b", None
            )
        )
        self.pushButtonRemoveConnection.setText(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u79fb\u9664\u8fde\u63a5", None
            )
        )
        self.pushButtonRemoveBlock.setText(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u79fb\u9664\u5757", None
            )
        )
        self.pushButtonAddBlock.setText(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u6dfb\u52a0\u5757", None
            )
        )
        self.groupBox_2.setTitle(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u5757\u7f16\u8f91\u5668", None
            )
        )
        self.checkBoxSocketIsInlet.setText(
            QCoreApplication.translate(
                "BlockModPyDemoDialog", "\u8f93\u5165\u63d2\u69fd", None
            )
        )

    # retranslateUi
