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

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .block_item import BlockItem

from qtpy.QtCore import Qt, QRectF, QPointF
from qtpy.QtGui import (
    QPen,
    QPainter,
    QPainterPath,
    QFont,
    QFontMetrics,
    QColor,
    QBrush,
)
from qtpy.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QApplication,
)

from .block import Block
from .globals import Globals
from .socket import Socket


class SocketItem(QGraphicsItem):
    """SocketItem 类，表示图形场景中的插槽项，负责绘制插槽并处理相关事件。"""

    def __init__(self, parent: BlockItem, socket: Socket) -> None:
        """初始化 SocketItem 对象。

        Args:
            parent: 父项，通常是 BlockItem。
            socket: 关联的插槽对象。
        """
        super().__init__(parent)
        self.m_block: Block = parent.m_block
        self.m_socket: Socket = socket
        self.m_hovered: bool = False
        self.m_symbol_rect: QRectF = QRectF()

        self.update_socket_item()
        self.setZValue(12)
        self.setAcceptHoverEvents(True)

    @property
    def socket(self) -> Socket:
        return self.m_socket

    def update_socket_item(self) -> None:
        """更新插槽项的位置和大小。"""
        if self.m_socket.m_inlet:
            if self.m_socket.direction() == Socket.Direction.Left:
                self.m_symbol_rect = QRectF(-4, self.m_socket.m_pos.y() - 4, 8, 8)
            elif self.m_socket.direction() == Socket.Direction.Right:
                self.m_symbol_rect = QRectF(
                    self.m_socket.m_pos.x() - 4, self.m_socket.m_pos.y() - 4, 8, 8
                )
            elif self.m_socket.direction() == Socket.Direction.Top:
                self.m_symbol_rect = QRectF(self.m_socket.m_pos.x() - 4, -4, 8, 8)
            elif self.m_socket.direction() == Socket.Direction.Bottom:
                self.m_symbol_rect = QRectF(
                    self.m_socket.m_pos.x() - 4, self.m_socket.m_pos.y() - 4, 8, 8
                )
        else:
            if self.m_socket.direction() == Socket.Direction.Left:
                self.m_symbol_rect = QRectF(-8, self.m_socket.m_pos.y() - 4, 8, 8)
            elif self.m_socket.direction() == Socket.Direction.Right:
                self.m_symbol_rect = QRectF(
                    self.m_socket.m_pos.x(), self.m_socket.m_pos.y() - 4, 8, 8
                )
            elif self.m_socket.direction() == Socket.Direction.Top:
                self.m_symbol_rect = QRectF(self.m_socket.m_pos.x() - 4, -8, 8, 8)
            elif self.m_socket.direction() == Socket.Direction.Bottom:
                self.m_symbol_rect = QRectF(
                    self.m_socket.m_pos.x() - 4, self.m_socket.m_pos.y(), 8, 8
                )

    def boundingRect(self) -> QRectF:
        """获取插槽项的边界矩形。

        Returns:
            插槽项的边界矩形。
        """
        rect = self.m_symbol_rect
        font = QFont()
        font.setPointSizeF(Globals.LabelFontSize)
        metrics = QFontMetrics(font)
        text_bounding_rect = metrics.boundingRect(self.m_socket.m_name)
        text_bounding_rect.setWidth(text_bounding_rect.width() + 6)

        # if self.m_socket.direction() == Socket.Direction.Left:
        #     rect.moveLeft(rect.left() - text_bounding_rect.width() - 6)
        # elif self.m_socket.direction() == Socket.Direction.Right:
        #     rect.setWidth(rect.width() + text_bounding_rect.width() + 6)
        # elif self.m_socket.direction() == Socket.Direction.Top:
        #     rect.moveTop(rect.top() - text_bounding_rect.width() - 6)
        # elif self.m_socket.direction() == Socket.Direction.Bottom:
        #     rect.setHeight(rect.height() + text_bounding_rect.width() + 6)

        return rect

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """处理鼠标悬停进入事件。

        Notes:
            对于输出插槽，允许悬停的条件是：
            - 场景当前不在连接模式

            对于输入插槽，仅允许在以下条件满足时允许悬停：
            - 场景处于连接模式
            - 插槽未被占用

        Args:
            event: 鼠标悬停事件对象。
        """
        from .scene_manager import SceneManager

        scene_manager = self.scene()
        if isinstance(scene_manager, SceneManager):
            if (
                not self.m_socket.m_inlet and not scene_manager.is_currently_connecting
            ) or (
                self.m_socket.m_inlet
                and scene_manager.is_currently_connecting
                and not scene_manager.is_connected_socket(self.m_block, self.m_socket)
            ):
                if QApplication.overrideCursor() is None:
                    QApplication.setOverrideCursor(Qt.CrossCursor)
                self.m_hovered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """处理鼠标悬停离开事件。

        Args:
            event: 鼠标悬停事件对象。
        """
        if self.m_hovered:
            QApplication.restoreOverrideCursor()
        self.m_hovered = False
        super().hoverLeaveEvent(event)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """绘制插槽项。

        Args:
            painter: 绘制器对象。
            option: 样式选项。
            widget: 绘制目标部件，默认为 None。
        """
        if (
            self.parentItem()
            and self.parentItem().m_block.m_name == Globals.InvisibleLabel
        ):
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.m_symbol_rect

        if self.m_socket.m_inlet:
            painter.setBrush(Qt.white)
            if self.m_socket.direction() == Socket.Direction.Left:
                painter.setPen(Qt.white)
                painter.drawPie(rect, 90 * 16, -180 * 16)
                painter.setPen(Qt.black)
                painter.drawArc(rect, 90 * 16, -180 * 16)
            elif self.m_socket.direction() == Socket.Direction.Right:
                painter.setPen(Qt.white)
                painter.drawPie(rect, 90 * 16, 180 * 16)
                painter.setPen(Qt.black)
                painter.drawArc(rect, 90 * 16, 180 * 16)
            elif self.m_socket.direction() == Socket.Direction.Top:
                painter.setPen(Qt.white)
                painter.drawPie(rect, 0 * 16, -180 * 16)
                painter.setPen(Qt.black)
                painter.drawArc(rect, 0 * 16, -180 * 16)
            elif self.m_socket.direction() == Socket.Direction.Bottom:
                painter.setPen(Qt.white)
                painter.drawPie(rect, 0 * 16, 180 * 16)
                painter.setPen(Qt.black)
                painter.drawArc(rect, 0 * 16, 180 * 16)

            from .scene_manager import SceneManager

            scene_manager = self.scene()
            if isinstance(
                scene_manager, SceneManager
            ) and scene_manager.is_connected_socket(self.m_block, self.m_socket):
                painter.save()
                painter.setPen(Qt.NoPen)
                painter.setBrush(Qt.black)
                rect2 = QRectF(
                    rect.x() + 2, rect.y() + 2, rect.width() - 4, rect.height() - 4
                )
                painter.drawEllipse(rect2)
                painter.restore()

            if self.m_hovered:
                painter.save()
                pen = QPen(QColor(192, 0, 0), 0.8)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(96, 0, 0)))
                rect2 = QRectF(
                    rect.x() - 1, rect.y() - 1, rect.width() + 2, rect.height() + 2
                )
                painter.drawEllipse(rect2)
                painter.restore()
        else:
            path = QPainterPath()
            if self.m_socket.direction() == Socket.Direction.Left:
                path.moveTo(rect.right(), rect.y())
                path.lineTo(rect.left(), 0.5 * (rect.top() + rect.bottom()))
                path.lineTo(rect.right(), rect.bottom())
            elif self.m_socket.direction() == Socket.Direction.Right:
                path.moveTo(rect.left(), rect.y())
                path.lineTo(rect.right(), 0.5 * (rect.top() + rect.bottom()))
                path.lineTo(rect.left(), rect.bottom())
            elif self.m_socket.direction() == Socket.Direction.Top:
                path.moveTo(rect.left(), rect.bottom())
                path.lineTo(0.5 * (rect.left() + rect.right()), rect.top())
                path.lineTo(rect.right(), rect.bottom())
            elif self.m_socket.direction() == Socket.Direction.Bottom:
                path.moveTo(rect.left(), rect.top())
                path.lineTo(0.5 * (rect.left() + rect.right()), rect.bottom())
                path.lineTo(rect.right(), rect.top())

            pen = QPen(Qt.black)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            if self.m_hovered:
                painter.fillPath(path, Qt.white)
            else:
                painter.setBrush(QColor(0, 0, 196))
            painter.drawPath(path)

        font = QFont(painter.font())
        font.setPointSizeF(Globals.LabelFontSize)
        metrics = QFontMetrics(font)
        painter.setFont(font)
        text_bounding_rect = QRectF(metrics.boundingRect(self.m_socket.m_name))
        text_bounding_rect.setWidth(text_bounding_rect.width() + 6)

        if self.m_socket.direction() == Socket.Direction.Left:
            text_bounding_rect.moveTo(
                QPointF(
                    rect.left() - text_bounding_rect.width(),
                    rect.top() - text_bounding_rect.height() + 3,
                )
            )
            painter.drawText(
                text_bounding_rect, Qt.AlignRight | Qt.AlignTop, self.m_socket.m_name
            )
        elif self.m_socket.direction() == Socket.Direction.Right:
            text_bounding_rect.moveTo(
                QPointF(rect.right(), rect.top() - text_bounding_rect.height() + 3)
            )
            painter.drawText(
                text_bounding_rect, Qt.AlignLeft | Qt.AlignTop, self.m_socket.m_name
            )
        elif self.m_socket.direction() == Socket.Direction.Top:
            painter.translate(rect.left(), rect.top())
            painter.rotate(-90)
            text_bounding_rect.moveTo(0, -text_bounding_rect.height())
            painter.drawText(
                text_bounding_rect, Qt.AlignLeft | Qt.AlignTop, self.m_socket.m_name
            )
        elif self.m_socket.direction() == Socket.Direction.Bottom:
            painter.translate(rect.left(), rect.bottom())
            painter.rotate(-90)
            text_bounding_rect.moveTo(
                -text_bounding_rect.width(), -text_bounding_rect.height()
            )
            painter.drawText(
                text_bounding_rect, Qt.AlignRight | Qt.AlignTop, self.m_socket.m_name
            )

        painter.restore()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标按下事件。

        Args:
            event: 鼠标事件对象。
        """
        if (
            not self.m_socket.m_inlet
            and event.button() == Qt.LeftButton
            and event.modifiers() == Qt.NoModifier
        ):
            from .scene_manager import SceneManager

            scene_manager = self.scene()
            if isinstance(scene_manager, SceneManager):
                pos = event.pos()
                pos = self.mapToScene(pos)
                scene_manager.start_socket_connection(self, pos)
                event.accept()
        super().mousePressEvent(event)
