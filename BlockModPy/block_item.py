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

from __future__ import annotations

from typing import List, Optional, Union

from qtpy.QtCore import QPointF, QRectF, QSizeF, Qt
from qtpy.QtGui import (
    QPainter,
    QLinearGradient,
    QPen,
    QColor,
    QBrush,
    QFontMetrics,
    QPixmap,
)
from qtpy.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from .block import Block
from .globals import Globals
from .socket_item import SocketItem


class BlockItem(QGraphicsRectItem):
    """BlockItem 类，表示图形场景中的块项，负责绘制块并管理其插槽项。"""

    def __init__(
        self, block: Block, parent: Optional[QGraphicsRectItem] = None
    ) -> None:
        """初始化 BlockItem 对象。

        Args:
            block: 关联的块对象。
            parent: 父项，默认为 None。
        """
        super().__init__(parent)
        self.m_block: Block = block
        self.m_socket_items: List[SocketItem] = []
        self.m_moved: bool = False

        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setZValue(10)

        self.create_socket_items()

    def inlet_socket_accepting_connection(
        self, scene_pos: QPointF
    ) -> Optional[SocketItem]:
        """查找接受连接的入口插槽项。

        Args:
            scene_pos: 场景坐标。

        Returns:
            如果找到接受连接的插槽项，返回该插槽项，否则返回 None。
        """
        for socket_item in self.m_socket_items:
            socket_scene_pos = socket_item.mapToScene(socket_item.socket().m_pos)
            socket_scene_pos -= scene_pos
            distance = socket_scene_pos.manhattanLength()
            if distance < Globals.GridSpacing / 2:
                return socket_item
        return None

    def is_invisible(self) -> bool:
        """检查块是否为不可见块。

        Returns:
            如果块为不可见块，返回 True，否则返回 False。
        """
        return self.m_block.m_name == Globals.InvisibleLabel

    def resize(self, new_width: int, new_height: int) -> None:
        """调整块的大小。

        Args:
            new_width: 新的宽度。
            new_height: 新的高度。
        """
        self.m_block.m_size = QSizeF(new_width, new_height)
        self.setRect(0, 0, new_width, new_height)

        for socket in self.m_block.m_sockets:
            if socket.m_orientation == Qt.Horizontal:
                if socket.m_pos.x() != 0.0:
                    socket.m_pos.setX(new_width)
            else:
                if socket.m_pos.y() != 0.0:
                    socket.m_pos.setY(new_height)

        for item in self.childItems():
            socket_item = item
            socket_item.update_socket_item()
            item.update()
        self.update()

    def boundingRect(self) -> QRectF:
        """获取块的边界矩形。

        Returns:
            块的边界矩形。
        """
        return super().boundingRect()

    def create_socket_items(self) -> None:
        """创建插槽项。"""
        self.m_socket_items.clear()

        for socket in self.m_block.m_sockets:
            socket_item = SocketItem(self, socket)
            if not socket.m_inlet:
                socket_item.setZValue(20)
            self.m_socket_items.append(socket_item)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """绘制块。

        Args:
            painter: 绘制器对象。
            option: 样式选项。
            widget: 绘制目标部件，默认为 None。
        """
        if self.is_invisible():
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        pixmap = self.m_block.m_properties.get("Pixmap")

        if self.m_block.m_properties.get("ShowPixmap", False) and isinstance(
            pixmap, QPixmap
        ):
            rect = self.rect()
            painter.setBrush(Qt.white)
            painter.fillRect(rect, QBrush(Qt.white))

            font_metrics = QFontMetrics(painter.font())
            rect.setTop(rect.top() + 4 + font_metrics.lineSpacing())
            painter.drawPixmap(rect, pixmap, pixmap.rect())
            painter.setPen(Qt.black)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect())

            rect = self.rect()
            rect.moveTop(4)
            painter.drawText(rect, Qt.AlignTop | Qt.AlignHCenter, self.m_block.m_name)
        else:
            grad = QLinearGradient(QPointF(0, 0), QPointF(self.rect().width(), 0))
            if option.state & QStyleOptionGraphicsItem.State_Selected:
                painter.setPen(QPen(QBrush(QColor(0, 128, 0)), 1.5))
                grad.setColorAt(0, QColor(230, 255, 230))
                grad.setColorAt(1, QColor(200, 240, 180))
            else:
                grad.setColorAt(0, QColor(196, 196, 255))
                grad.setColorAt(1, QColor(220, 220, 255))
            painter.setBrush(grad)
            painter.fillRect(self.rect(), grad)
            painter.setPen(Qt.black)
            painter.drawRect(self.rect())

            rect = self.rect()
            rect.moveTop(4)
            painter.drawText(rect, Qt.AlignTop | Qt.AlignHCenter, self.m_block.m_name)

        painter.restore()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标释放事件。

        Args:
            event: 鼠标事件对象。
        """
        if event.button() == Qt.LeftButton and (event.modifiers() & Qt.ControlModifier):
            self.setSelected(True)
            event.accept()
            return

        if event.button() == Qt.LeftButton and not self.m_moved:
            pass  # TODO: Signal block selection

        super().mouseReleaseEvent(event)
        self.m_moved = False

    def itemChange(
        self, change: QGraphicsRectItem.GraphicsItemChange, value: Union[QPointF, bool]
    ) -> Union[QPointF, bool]:
        """处理项属性变化事件。

        Args:
            change: 变化类型。
            value: 变化值。

        Returns:
            处理后的值。
        """
        if change == QGraphicsRectItem.ItemPositionChange:
            scene_manager = self.scene()

            # 类型安全处理，确保 value 是 QPointF 类型
            if not isinstance(value, QPointF):
                return super().itemChange(change, value)

            pos = value

            pos.setX(
                int((pos.x() + 0.5 * Globals.GridSpacing) / Globals.GridSpacing)
                * Globals.GridSpacing
            )
            pos.setY(
                int((pos.y() + 0.5 * Globals.GridSpacing) / Globals.GridSpacing)
                * Globals.GridSpacing
            )

            if self.m_block.m_pos != pos.toPoint():
                self.m_moved = True
                old_pos = self.m_block.m_pos
                self.m_block.m_pos = pos.toPoint()
                if scene_manager:
                    scene_manager.block_moved(self.m_block, old_pos)

            if scene_manager:
                scene_rect = scene_manager.sceneRect()
                if (
                    pos.x() < scene_rect.left()
                    or pos.y() < scene_rect.top()
                    or (pos.x() + self.rect().width()) > scene_rect.right()
                    or (pos.y() + self.rect().height()) > scene_rect.bottom()
                ):
                    scene_manager.setSceneRect(QRectF())

            return pos

        elif change == QGraphicsRectItem.ItemSelectedHasChanged:
            scene_manager = self.scene()
            if value:
                scene_manager.block_selected(self.m_block)

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标双击事件。

        Args:
            event: 鼠标事件对象。
        """
        scene_manager = self.scene()
        if scene_manager:
            scene_manager.block_double_clicked(self)
        super().mouseDoubleClickEvent(event)
