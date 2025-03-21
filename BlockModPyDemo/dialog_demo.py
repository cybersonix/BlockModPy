#  BSD 3-Clause License
#
#  This file is part of the BlockModPy Library (Python port).
#
#  Original C++ implementation:
#  	Copyright (c) 2019, Andreas Nicolai (BSD-3-Clause)
#
#  Python port:
#  	Copyright (c) 2025, Sun Hao
#
#  Redistribution and use in source and binary forms, with or without modification,
#  are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#  3. Neither the name of the original copyright holder (Andreas Nicolai),
#     the BlockMod Library, nor the names of its contributors may be used to endorse
#     or promote products derived from this software without specific prior written
#     permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
#  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
#  OF THE POSSIBILITY OF SUCH DAMAGE.

import random
from typing import Optional

from qtpy.QtCore import Qt, QSizeF, QPointF
from qtpy.QtWidgets import QDialog, QFileDialog, QMessageBox

from BlockModPy.block import Block
from BlockModPy.globals import Globals
from BlockModPy.network import Network
from BlockModPy.scene_manager import SceneManager
from BlockModPy.socket import Socket
from ui.dialog import Ui_BlockModPyDemoDialog  # 导入自动生成的UI类


class DialogDemo(QDialog, Ui_BlockModPyDemoDialog):
    """主演示对话框，提供完整的BlockMod网络编辑功能。

    Attributes:
        m_sceneManager (SceneManager): 场景管理对象，负责维护网络模型和视图交互
    """

    def __init__(self, parent: Optional[QDialog] = None) -> None:
        """初始化对话框并设置UI布局。

        Args:
            parent: 父级窗口，默认为None
        """
        super().__init__(
            parent, Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )
        self.setupUi(self)  # 初始化自动生成的UI

        # 初始化场景管理器
        self.m_sceneManager = SceneManager(self)
        self.graphicsView.setScene(self.m_sceneManager)
        self.graphicsView.set_resolution(1)  # 1像素/米
        self.graphicsView.set_grid_step(80)  # 主网格80像素/米

        # 连接信号槽
        self.toolButtonNew.clicked.connect(self.on_toolButtonNew_clicked)
        self.toolButtonOpen.clicked.connect(self.on_toolButtonOpen_clicked)
        self.toolButtonSave.clicked.connect(self.on_toolButtonSave_clicked)
        self.pushButtonRemoveBlock.clicked.connect(
            self.on_pushButtonRemoveBlock_clicked
        )
        self.pushButtonRemoveConnection.clicked.connect(
            self.on_pushButtonRemoveConnection_clicked
        )
        self.pushButtonAddBlock.clicked.connect(self.on_pushButtonAddBlock_clicked)

        # 加载示例网络
        # self.load_network("demo.bm")

        # 暂时隐藏块编辑器
        self.groupBox_2.setVisible(False)

    def on_toolButtonNew_clicked(self) -> None:
        """处理新建网络按钮点击事件，创建空网络。"""
        new_network = Network()
        self.m_sceneManager.set_network(new_network)

    def on_toolButtonOpen_clicked(self) -> None:
        """处理打开文件按钮点击事件，弹出文件选择对话框。"""
        fname, _ = QFileDialog.getOpenFileName(
            self, "选择BlockMod文件", "", "BlockMod文件 (*.bm)"
        )
        if fname:
            self.load_network(fname)

    def on_toolButtonSave_clicked(self) -> None:
        """处理保存文件按钮点击事件，弹出文件保存对话框。"""
        fname, _ = QFileDialog.getSaveFileName(
            self, "保存BlockMod文件", "", "BlockMod文件 (*.bm)"
        )
        if fname:
            try:
                self.m_sceneManager.network().write_xml(fname)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"文件保存失败：{str(e)}")

    def on_pushButtonRemoveBlock_clicked(self) -> None:
        """处理移除块按钮点击事件，删除选中块。"""
        selected_blocks = self.m_sceneManager.selected_blocks()
        for block in selected_blocks:
            self.m_sceneManager.remove_block(block)

    def on_pushButtonRemoveConnection_clicked(self) -> None:
        """处理移除连接按钮点击事件，删除选中连接线。"""
        selected_connector = self.m_sceneManager.selected_connector()
        if selected_connector:
            self.m_sceneManager.remove_connector(selected_connector)

    def on_pushButtonAddBlock_clicked(self) -> None:
        """处理添加块按钮点击事件，生成随机块并添加到场景。"""
        new_block = self._generate_random_block()
        self.m_sceneManager.add_block(new_block)

    def load_network(self, filename: str) -> None:
        """加载指定网络文件到场景。

        Args:
            filename: 要加载的.bm文件路径

        Raises:
            RuntimeError: 当文件格式错误或读取失败时抛出
        """
        network = Network()
        try:
            network.read_xml(filename)
            network.check_names()

            # 验证并调整连接器
            valid_connectors = []
            for con in network.m_connectors:
                try:
                    network.adjust_connector(con)
                    valid_connectors.append(con)
                except Exception:
                    continue
            network.m_connectors = valid_connectors
            self.m_sceneManager.set_network(network)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载网络文件：{str(e)}")
            raise RuntimeError(f"网络加载失败: {str(e)}") from e

    def _generate_random_block(self) -> Block:
        """生成随机几何属性和插槽配置的块。

        Returns:
            生成的Block对象，包含随机名称、尺寸和插槽配置
        """
        block = Block()

        # 生成随机名称（4-8个字母）
        name_length = 4 + random.randint(0, 4)
        block.m_name = "".join(
            [chr(97 + random.randint(0, 25)) for _ in range(name_length)]
        )

        # 生成随机尺寸（基于网格间距）
        grid_x = name_length + 4 + random.randint(0, 8)
        grid_y = 3 + random.randint(0, 8)
        block.m_size = QSizeF(
            grid_x * Globals.GridSpacing, grid_y * Globals.GridSpacing
        )

        # 随机位置（0-30格）
        block.m_pos = QPointF(
            random.randint(0, 30) * Globals.GridSpacing,
            random.randint(0, 30) * Globals.GridSpacing,
        )

        # 生成随机插槽
        for i in range(grid_x - 2):
            # 顶部边缘插槽
            if random.random() < 1 / 6:
                self._add_random_socket(block, i, True)
            # 底部边缘插槽
            if random.random() < 1 / 6:
                self._add_random_socket(block, i, False)

        return block

    def _add_random_socket(self, block: Block, index: int, is_top: bool) -> None:
        """为块添加随机配置的插槽。

        Args:
            block: 目标块对象
            index: X轴网格索引
            is_top: 是否位于顶部边缘
        """
        socket = Socket()
        socket.m_inlet = random.random() < 0.5
        name_length = random.randint(1, 6)
        socket.m_name = "".join(
            [chr(97 + random.randint(0, 25)) for _ in range(name_length)]
        )
        socket.m_orientation = Qt.Vertical
        y_pos = 0.0 if is_top else block.m_size.height()
        socket.m_pos = QPointF((index + 1) * Globals.GridSpacing, y_pos)
        block.m_sockets.append(socket)
