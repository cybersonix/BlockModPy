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

import math
from typing import List, Optional

from PySide2.QtWidgets import QApplication
from qtpy.QtCore import QPointF, QSize, QLineF, QEvent, Qt
from qtpy.QtGui import (
    QPainter,
    QColor,
    QTransform,
    QWheelEvent,
    QMouseEvent,
    QPaintEvent,
)
from qtpy.QtWidgets import QGraphicsView, QWidget

from BlockModPy.scene_manager import SceneManager

class ZoomMeshGraphicsView(QGraphicsView):
    """提供网格和缩放功能的 2D 图形视图类。"""

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化 ZoomMeshGraphicsView 对象。

        Args:
            parent: 父部件，默认为 None。
        """
        super().__init__(parent)
        self.m_resolution: float = 1000.0  # 分辨率，单位：像素/米
        self.m_grid_step: float = 0.1  # 网格间距，单位：米
        self.m_grid_enabled: bool = True  # 是否启用网格
        self.m_zoom_level: int = 0  # 缩放级别
        self.m_grid_color: QColor = QColor(175, 175, 255)  # 网格颜色
        self.m_pos: QPointF = QPointF()  # 当前鼠标位置
        self.m_major_grid: List[QLineF] = []  # 主网格线
        self.m_minor_grid: List[QLineF] = []  # 次网格线
        self.m_p_last: QPointF = QPointF()  # 上次网格更新的参考点
        self.m_grid_spacing_pix_last: float = 0.0  # 上次网格更新的网格间距
        self.m_window_size_last: QSize = QSize()  # 上次网格更新的窗口大小

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # 中键拖拽相关成员变量
        self.m_midButtonPressed = False
        self.m_dragStartPos = QPointF()

    # def zoom_level(self) -> int:
    #     """获取当前缩放级别。
    #
    #     Returns:
    #         当前缩放级别。
    #     """
    #     return self.m_zoom_level

    def set_grid_color(self, color: QColor) -> None:
        """设置网格颜色。

        Args:
            color: 网格颜色。
        """
        self.m_grid_color = color
        self.viewport().update()

    def set_grid_enabled(self, enabled: bool) -> None:
        """设置网格是否启用。

        Args:
            enabled: 是否启用网格。
        """
        self.m_grid_enabled = enabled
        self.viewport().update()

    def zoom_in(self) -> None:
        """放大视图。"""
        self.m_zoom_level = min(self.m_zoom_level + 1, 3000)
        factor = math.pow(10, self.m_zoom_level / 20.0)
        self.setTransform(QTransform(factor, 0, 0, factor, 0, 0))
        self.change_resolution_event()

    def zoom_out(self) -> None:
        """缩小视图。"""
        self.m_zoom_level = max(self.m_zoom_level - 1, -3000)
        factor = math.pow(10, self.m_zoom_level / 20.0)
        self.setTransform(QTransform(factor, 0, 0, factor, 0, 0))
        self.change_resolution_event()

    def set_zoom_level(self, zoom_level: int) -> None:
        """设置缩放级别。

        Args:
            zoom_level: 新的缩放级别。
        """
        self.m_zoom_level = max(min(zoom_level, 3000), -3000)
        factor = math.pow(10, self.m_zoom_level / 20.0)
        self.setTransform(QTransform(factor, 0, 0, factor, 0, 0))
        self.change_resolution_event()

    def reset_zoom(self) -> None:
        """重置缩放级别。"""
        self.m_zoom_level = 0
        self.resetTransform()

    def set_grid_step(self, grid_step: float) -> None:
        """设置网格间距。

        Args:
            grid_step: 新的网格间距，单位：米。
        """
        if grid_step <= 0:
            return
        self.m_grid_step = grid_step
        self.viewport().update()

    def set_resolution(self, res: float) -> None:
        """设置分辨率。

        Args:
            res: 新的分辨率，单位：像素/米。
        """
        if res <= 0:
            return
        self.m_resolution = res
        self.viewport().update()

    def enterEvent(self, event: QEvent) -> None:
        """处理鼠标进入事件。

        Args:
            event: 鼠标事件对象。
        """
        # super().enterEvent(event)
        assert event.type() == QEvent.Enter

        scene_manager = self.scene()
        if isinstance(scene_manager, SceneManager):
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

        super(ZoomMeshGraphicsView, self).enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """处理鼠标离开事件。

        Args:
            event: 鼠标事件对象。
        """
        # super().leaveEvent(event)
        scene_manager = self.scene()
        if isinstance(scene_manager, SceneManager):
            if scene_manager.is_currently_connecting:
                scene_manager.finish_connection()

        QApplication.restoreOverrideCursor()  # needed if we drag a segment out of the view
        super(ZoomMeshGraphicsView, self).leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self.m_midButtonPressed = True
            self.m_dragStartPos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """处理鼠标移动事件。

        Args:
            event: 鼠标事件对象。
        """
        if self.m_midButtonPressed:
            current_pos = event.pos()
            dx = self.m_dragStartPos.x() - current_pos.x()
            dy = self.m_dragStartPos.y() - current_pos.y()
            # 使用滚动条直接控制视口移动
            h_scroll = self.horizontalScrollBar()
            v_scroll = self.verticalScrollBar()
            h_scroll.setValue(int(h_scroll.value() + dx))
            v_scroll.setValue(int(v_scroll.value() + dy))
            self.m_dragStartPos = current_pos  # 更新初始位置
        else:
            super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self.m_midButtonPressed = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """处理鼠标滚轮事件。

        Args:
            event: 鼠标滚轮事件对象。
        """
        if event.angleDelta().y() < 0:
            self.zoom_out()
        else:
            self.zoom_in()
        event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制网格。

        Args:
            event: 绘制事件对象。
        """

        if self.m_grid_enabled:
            p = QPainter(self.viewport())
            p1 = self.mapFromScene(QPointF(0, 0))

            # 计算网格间距
            grid_spacing_pix = self.m_resolution * self.m_grid_step
            scale_factor = self.transform().m11()
            grid_spacing_pix *= scale_factor

            h = self.height()
            w = self.width()
            window_size = QSize(w, h)

            if (
                grid_spacing_pix != self.m_grid_spacing_pix_last
                or p1 != self.m_p_last
                or window_size != self.m_window_size_last
            ):

                self.m_p_last = p1
                self.m_grid_spacing_pix_last = grid_spacing_pix
                self.m_window_size_last = window_size

                # 主网格
                self.m_major_grid.clear()
                if grid_spacing_pix >= 5:
                    lines_x_till_view = math.floor(-p1.x() / grid_spacing_pix + 1)
                    offset_x = lines_x_till_view * grid_spacing_pix + p1.x()

                    lines_y_till_view = math.floor(-p1.y() / grid_spacing_pix + 1)
                    offset_y = lines_y_till_view * grid_spacing_pix + p1.y()

                    for x in [
                        offset_x + i * grid_spacing_pix
                        for i in range(int((w - offset_x) / grid_spacing_pix) + 1)
                    ]:
                        self.m_major_grid.append(QLineF(x, 0, x, h))
                    for y in [
                        offset_y + i * grid_spacing_pix
                        for i in range(int((h - offset_y) / grid_spacing_pix) + 1)
                    ]:
                        self.m_major_grid.append(QLineF(0, y, w, y))

                # 次网格
                grid_spacing_pix = self.m_resolution * self.m_grid_step * 0.1
                grid_spacing_pix *= scale_factor
                self.m_minor_grid.clear()
                if grid_spacing_pix >= 5:
                    lines_x_till_view = math.floor(-p1.x() / grid_spacing_pix + 1)
                    offset_x = lines_x_till_view * grid_spacing_pix + p1.x()

                    lines_y_till_view = math.floor(-p1.y() / grid_spacing_pix + 1)
                    offset_y = lines_y_till_view * grid_spacing_pix + p1.y()

                    for x in [
                        offset_x + i * grid_spacing_pix
                        for i in range(int((w - offset_x) / grid_spacing_pix) + 1)
                    ]:
                        self.m_minor_grid.append(QLineF(x, 0, x, h))
                    for y in [
                        offset_y + i * grid_spacing_pix
                        for i in range(int((h - offset_y) / grid_spacing_pix) + 1)
                    ]:
                        self.m_minor_grid.append(QLineF(0, y, w, y))

            # 绘制次网格
            p.setPen(QColor(220, 220, 255))
            p.drawLines(self.m_minor_grid)

            # 绘制主网格
            p.setPen(self.m_grid_color)
            p.drawLines(self.m_major_grid)

            # 绘制参考线用于调试
            p.setPen(QColor(255, 0, 0))
            p.drawLine(p1.x() - 5000, p1.y(), p1.x() + 5000, p1.y())  # 水平线
            p.drawLine(p1.x(), p1.y() - 5000, p1.x(), p1.y() + 5000)  # 垂直线

        super().paintEvent(event)

    def change_resolution_event(self) -> None:
        """处理分辨率变化事件。"""
        pass
