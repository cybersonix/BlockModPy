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

from typing import Optional, Any, TYPE_CHECKING

from qtpy.QtCore import Qt, QPoint, QLineF, QRectF
from qtpy.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush
from qtpy.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsItem,
    QApplication,
)

from .connector import Connector
from .globals import Globals

if TYPE_CHECKING:
    from .scene_manager import SceneManager


class ConnectorSegmentItem(QGraphicsLineItem):
    """表示连接器的一个线段项，负责绘制线段并处理相关事件。"""

    def __init__(self, connector: Connector) -> None:
        """初始化 ConnectorSegmentItem 对象。

        Args:
            connector: 关联的连接器对象。
        """
        super().__init__()
        self.m_connector: Connector = connector
        self.m_segment_idx: int = -1
        self.m_is_highlighted: bool = False
        self.m_moved: bool = False
        self.m_last_pos: QPoint = QPoint()

        self.setFlags(
            QGraphicsLineItem.ItemIsMovable
            | QGraphicsLineItem.ItemIsSelectable
            | QGraphicsLineItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(5)  # Below block

    def set_line(self, line: QLineF) -> None:
        """设置线段并初始化最后位置。

        Args:
            line: 线段对象。
        """
        self.m_last_pos = self.pos().toPoint()
        super().setLine(line)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        """绘制线段项。

        Args:
            painter: 绘制器对象。
            option: 样式选项。
            widget: 绘制目标部件，默认为 None。
        """
        line = self.line()
        if Globals.near_zero(line.length()):
            return

        painter.save()
        if self.m_is_highlighted:
            pen = QPen()
            pen.setWidthF(1.5 * self.m_connector.m_linewidth)
            pen.setStyle(Qt.SolidLine)
            pen.setColor(QColor(0, 0, 110))
            if self.isSelected():
                pen.setColor(QColor(192, 0, 0))
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(line)
        else:
            pen = QPen()
            pen.setWidthF(self.m_connector.m_linewidth)
            pen.setColor(self.m_connector.m_color)
            pen.setStyle(Qt.SolidLine)
            if self.isSelected():
                pen.setWidthF(1.5 * self.m_connector.m_linewidth)
                pen.setColor(QColor(192, 0, 0))
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(line)

        # Draw text if this is the central segment
        if (
            self.m_connector.m_text
            and self.m_segment_idx == self._calculate_central_segment_index()
        ):
            x = line.p1().x() + line.dx() / 2
            y = line.p1().y() + line.dy() / 2
            br = painter.boundingRect(
                int(x), int(y), 150, 30, 0, self.m_connector.m_text
            )
            width = 1.2 * br.width()
            height = 1.2 * br.height()
            rect = QRectF(x - width / 2, y - height / 2, width, height)
            pen = QPen()
            pen.setWidthF(1)
            pen.setColor(self.m_connector.m_color)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.white))
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignCenter, self.m_connector.m_text)

        painter.restore()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """处理鼠标悬停进入事件。

        Args:
            event: 鼠标悬停事件对象。
        """
        super().hoverEnterEvent(event)
        scene_manager = self.scene()
        if (
            isinstance(scene_manager, SceneManager)
            and scene_manager.is_currently_connecting()
        ):
            return

        if self.m_segment_idx >= 0:
            if self.line().dx() == 0.0:
                QApplication.setOverrideCursor(Qt.SplitHCursor)
            else:
                QApplication.setOverrideCursor(Qt.SplitVCursor)

        if isinstance(scene_manager, SceneManager):
            scene_manager.highlight_connector_segments(self.m_connector, True)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """处理鼠标悬停离开事件。

        Args:
            event: 鼠标悬停事件对象。
        """
        super().hoverLeaveEvent(event)
        scene_manager = self.scene()
        if (
            isinstance(scene_manager, SceneManager)
            and scene_manager.is_currently_connecting()
        ):
            return

        QApplication.restoreOverrideCursor()
        if isinstance(scene_manager, SceneManager):
            scene_manager.highlight_connector_segments(self.m_connector, False)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标按下事件。

        Args:
            event: 鼠标事件对象。
        """
        scene_manager = self.scene()
        if isinstance(scene_manager, SceneManager):
            scene_manager.clear_selection()
        self.setSelected(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标释放事件。

        Args:
            event: 鼠标事件对象。
        """
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.setSelected(True)
            event.accept()
            scene_manager = self.scene()
            if isinstance(scene_manager, SceneManager):
                scene_manager.on_selection_changed()
            return

        if event.button() == Qt.LeftButton and not self.m_moved:
            super().mouseReleaseEvent(event)
            self.setSelected(True)
            event.accept()
            scene_manager = self.scene()
            if isinstance(scene_manager, SceneManager):
                scene_manager.on_selection_changed()
            self.update()
            return

        super().mouseReleaseEvent(event)
        self.m_moved = False
        scene_manager = self.scene()
        if isinstance(scene_manager, SceneManager):
            scene_manager.merge_connector_segments(self.m_connector)
            scene_manager.on_selection_changed()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """处理图形项属性变更事件。

        Args:
            change: 变更类型。
            value: 变更值。

        Returns:
            变更后的值。
        """
        if change == QGraphicsItem.ItemPositionChange and self.m_segment_idx >= 0:
            pos_f = value.toPointF()
            pos_f.setX(int(pos_f.x() / Globals.GridSpacing) * Globals.GridSpacing)
            pos_f.setY(int(pos_f.y() / Globals.GridSpacing) * Globals.GridSpacing)
            pos = pos_f.toPoint()

            if self.m_last_pos != pos:
                self.m_moved = True
                move_dist = pos - self.m_last_pos

                # Update connector segments
                self._update_segments(move_dist)

                # Manually correct the line's coordinates
                scene_manager = self.scene()
                if isinstance(scene_manager, SceneManager):
                    scene_manager.connector_segment_moved(self)

                line = self.line()
                p1 = line.p1() - move_dist
                p2 = line.p2() - move_dist
                self.setLine(QLineF(p1, p2))

                self.m_last_pos = pos

            return pos_f

        return super().itemChange(change, value)

    def shape(self) -> QPainterPath:
        """获取线段项的形状。

        Returns:
            线段项的形状路径。
        """
        path = QPainterPath()
        line = self.line()
        x = line.p1().x() - 10
        y = line.p1().y() - 10
        dx = line.dx() + 20
        dy = line.dy() + 20
        rect = QRectF(x, y, dx, dy)
        path.addRect(rect)
        return path

    def _calculate_central_segment_index(self) -> int:
        """计算中心线段的索引。

        Returns:
            中心线段的索引。
        """
        if len(self.m_connector.m_segments) <= 2:
            return 0
        return (len(self.m_connector.m_segments) - 2) // 2 + 1

    def _update_segments(self, move_dist: QPoint) -> None:
        """更新连接器线段的偏移量。

        Args:
            move_dist: 移动距离。
        """
        dx = move_dist.x()
        dy = move_dist.y()
        seg_idx = self.m_segment_idx

        # Update segments to the left
        while (seg_idx := seg_idx - 1) >= 0 and (
            not Globals.near_zero(dx) or not Globals.near_zero(dy)
        ):
            seg = self.m_connector.m_segments[seg_idx]
            if not Globals.near_zero(dx) and seg.m_direction == Qt.Horizontal:
                seg.m_offset += dx
                dx = 0
            if not Globals.near_zero(dy) and seg.m_direction == Qt.Vertical:
                seg.m_offset += dy
                dy = 0

        seg_idx = self.m_segment_idx

        # Insert new segment if needed
        if not Globals.near_zero(dx):
            seg = self.m_connector.m_segments[seg_idx]
            if seg.m_direction == Qt.Horizontal:
                seg.m_offset += dx
            else:
                new_seg = Connector.Segment(Qt.Horizontal, dx)
                self.m_connector.m_segments.insert(0, new_seg)
                seg_idx += 1
                self.m_segment_idx = seg_idx

        if not Globals.near_zero(dy):
            seg = self.m_connector.m_segments[seg_idx]
            if seg.m_direction == Qt.Vertical:
                seg.m_offset += dy
            else:
                new_seg = Connector.Segment(Qt.Vertical, dy)
                self.m_connector.m_segments.insert(0, new_seg)
                seg_idx += 1
                self.m_segment_idx = seg_idx

        # Update segments to the right
        dx = move_dist.x()
        dy = move_dist.y()
        seg_idx = self.m_segment_idx

        while (seg_idx := seg_idx + 1) < len(self.m_connector.m_segments) and (
            not Globals.near_zero(dx) or not Globals.near_zero(dy)
        ):
            seg = self.m_connector.m_segments[seg_idx]
            if not Globals.near_zero(dx) and seg.m_direction == Qt.Horizontal:
                seg.m_offset -= dx
                dx = 0
            if not Globals.near_zero(dy) and seg.m_direction == Qt.Vertical:
                seg.m_offset -= dy
                dy = 0

        # Insert new segment if needed
        if not Globals.near_zero(dx):
            new_seg = Connector.Segment(Qt.Horizontal, -dx)
            self.m_connector.m_segments.append(new_seg)

        if not Globals.near_zero(dy):
            new_seg = Connector.Segment(Qt.Vertical, -dy)
            self.m_connector.m_segments.append(new_seg)
