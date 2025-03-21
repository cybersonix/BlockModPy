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

from typing import Union, List, Dict, Set, Optional

from qtpy.QtCore import Qt, QPointF, QSize, QRectF, QLineF, QSizeF
from qtpy.QtCore import Signal
from qtpy.QtGui import QPixmap, QPainter
from qtpy.QtWidgets import (
    QGraphicsScene,
    QGraphicsItem,
    QApplication,
    QGraphicsSceneMouseEvent,
)

from .block import Block
from .block_item import BlockItem
from .connector import Connector
from .connector_segment_item import ConnectorSegmentItem
from .globals import Globals
from .network import Network
from .socket import Socket
from .socket_item import SocketItem


class SceneManager(QGraphicsScene):
    network_geometry_changed = Signal()
    new_block_selected = Signal(str)
    new_connection_added = Signal()
    selection_cleared = Signal()
    new_connector_selected = Signal(str, str)
    block_action_triggered = Signal(BlockItem)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.m_network: Network = Network()
        self.m_block_items: List[BlockItem] = []
        self.m_connector_segment_items: List[ConnectorSegmentItem] = []
        self.m_block_connector_map: Dict[Block, Set[Connector]] = {}
        self.m_currently_connecting: bool = False

    def __del__(self) -> None:
        del self.m_network

    def set_network(self, network: Network) -> None:
        """设置网络对象，并更新场景中的块和连接器。

        Args:
            network: 需要设置的网络对象。
        """
        self.m_network = network
        for item in self.m_block_items:
            self.removeItem(item)
        self.m_block_items.clear()
        for item in self.m_connector_segment_items:
            self.removeItem(item)
        self.m_connector_segment_items.clear()
        self.m_block_connector_map.clear()

        for block in self.m_network.m_blocks:
            item = self.create_block_item(block)
            self.addItem(item)
            self.m_block_items.append(item)

        for connector in self.m_network.m_connectors:
            new_conns = self.create_connector_items(connector)
            for item in new_conns:
                self.addItem(item)
                self.m_connector_segment_items.append(item)

        self.m_currently_connecting = False

    def network(self) -> Network:
        """获取当前网络对象。

        Returns:
            当前网络对象。
        """
        return self.m_network

    def generate_pixmap(self, target_size: QSize) -> QPixmap:
        """生成当前场景的缩略图。

        Args:
            target_size: 目标缩略图的大小。

        Returns:
            生成的缩略图。
        """
        r = self.itemsBoundingRect()
        eps = 1.01
        border_size = 10
        w = target_size.width()
        h = target_size.height()
        source_rect = QRectF()

        # 采用长度和宽度中较大者作为缩放比例的依据。
        if r.width() > r.height():
            m = r.width()
            target_size.setHeight(int(r.height() / r.width() * w + 2 * border_size))
            h = target_size.height() + 2 * border_size
            source_rect = QRectF(
                r.center().x() - 0.5 * m * eps,
                r.center().y() - 0.5 * r.height() * eps,
                eps * m,
                eps * r.height(),
            )
        else:
            m = r.height()
            source_rect = QRectF(
                r.center().x() - 0.5 * m * eps,
                r.center().y() - 0.5 * m * eps,
                eps * m,
                eps * m,
            )

        target_rect = QRectF(
            border_size, border_size, w - 2 * border_size, h - 2 * border_size
        )

        pm = QPixmap(target_size)
        pm.fill(Qt.white)
        painter = QPainter(pm)
        self.render(painter, target_rect, source_rect)
        painter.end()
        return pm

    def block_item_by_name(self, block_name: str) -> Optional[BlockItem]:
        """根据块名称查找对应的块项。

        Args:
            block_name: 块名称。

        Returns:
            如果找到则返回块项，否则返回 None。
        """
        for item in self.m_block_items:
            if item.m_block.m_name == block_name:
                return item
        return None

    def block_moved(self, block: Block) -> None:
        """处理块移动后的相关操作。

        当块发生移动时，此函数会被调用，用于更新与该块相关的连接器及其显示。

        Note:
            此函数通常从 BlockItem.itemChange() 事件处理程序中调用。
            在信号处理过程中（例如连接到 network_geometry_changed() 的槽函数中），切勿调用 set_network()，
            否则会导致现有块对象被删除并创建新的块对象，从而导致返回此函数时访问无效内存，引发崩溃。

        Args:
            block: 移动的块对象。
        """
        cons = self.m_block_connector_map.get(block, set())
        for con in cons:
            self.m_network.adjust_connector(con)
            self.update_connector_segment_items(con, None)
        self.network_geometry_changed.emit()

    def block_selected(self, block: Block) -> None:
        """当块被选中时，触发信号并发送块的名称。

        Args:
            block: 被选中的块对象。
        """
        self.new_block_selected.emit(block.m_name)

    def connector_segment_moved(self, current_item: ConnectorSegmentItem) -> None:
        """处理连接线段移动事件。

        当连接线段被移动时，更新与该线段相关的所有连接线段项，并发出网络几何变化的信号。

        Args:
            current_item: 当前被移动的连接线段项。
        """
        self.update_connector_segment_items(current_item.m_connector, current_item)
        self.network_geometry_changed.emit()

    def highlight_connector_segments(self, con: Connector, highlighted: bool) -> None:
        """高亮或取消高亮连接器中的所有线段。

        Args:
            con: 需要高亮的连接器对象。
            highlighted: 是否高亮，True 为高亮，False 为取消高亮。
        """
        for segment_item in self.m_connector_segment_items:
            if segment_item.m_connector == con:
                segment_item.m_is_highlighted = highlighted
                segment_item.update()
        self.update()

    def select_connector_segments(self, con: Connector) -> None:
        """选中连接器的所有线段。

        Args:
            con: 需要选中的连接器对象。
        """
        for segment_item in self.m_connector_segment_items:
            if segment_item.m_connector == con:
                if not segment_item.isSelected():
                    segment_item.setSelected(True)
                segment_item.update()
        self.update()

    def merge_connector_segments(self, con: Connector) -> None:
        """合并连接器的线段。

        Args:
            con: 需要合并线段的连接器对象。
        """
        segment_items: List[ConnectorSegmentItem] = []
        segment_items_dict = {}  # 临时存储索引到对象的映射

        for segment_item in self.m_connector_segment_items:
            if segment_item.m_connector == con:
                idx = segment_item.m_segment_idx
                if idx in {-1, -2}:
                    continue
                segment_items_dict[idx] = segment_item

        # 根据 con.m_segments 的长度构建有序列表，并验证所有索引存在
        expected_length = len(con.m_segments)
        for idx in range(expected_length):
            if idx not in segment_items_dict:
                raise ValueError(f"Missing segment item for index {idx}")
            segment_items.append(segment_items_dict[idx])

        update_segments: bool = False
        i = 0
        while i < len(segment_items):
            for i in range(len(segment_items)):
                seg_item = segment_items[i]
                seg = con.m_segments[i]
                if i > 0 and con.m_segments[i - 1].m_direction == seg.m_direction:
                    con.m_segments[i - 1].m_offset += seg.m_offset
                    seg.m_offset = 0
                    update_segments = True
                if Globals.near_zero(seg.m_offset):
                    break
            if i == len(segment_items):
                break

            if i == 0:
                con.m_segments.pop(0)
                seg_item = segment_items.pop(0)
                self.m_connector_segment_items.remove(seg_item)
                del seg_item
                for j in range(len(segment_items)):
                    segment_items[j].m_segment_idx -= 1
            elif i == len(segment_items) - 1:
                con.m_segments.pop()
                seg_item = segment_items.pop()
                if seg_item is not None:
                    self.m_connector_segment_items.remove(seg_item)
                    del seg_item
                i = 0
            else:
                con.m_segments.pop(i)
                seg_item = segment_items.pop(i)
                self.m_connector_segment_items.remove(seg_item)
                del seg_item
                for j in range(i, len(segment_items)):
                    segment_items[j].m_segment_idx -= 1
                if (
                        i > 0
                        and con.m_segments[i - 1].m_direction
                        == con.m_segments[i].m_direction
                ):
                    con.m_segments[i - 1].m_offset += con.m_segments[i].m_offset
                    con.m_segments.pop(i)
                    seg_item = segment_items.pop(i)
                    self.m_connector_segment_items.remove(seg_item)
                    del seg_item
                    for j in range(i, len(segment_items)):
                        segment_items[j].m_segment_idx -= 1
                    update_segments = True
                i = 0

        if update_segments:
            self.update_connector_segment_items(con, None)
        QApplication.restoreOverrideCursor()

    def is_connected_socket(self, b: Block, s: Socket) -> bool:
        """判断一个插槽是否已经连接。

        该函数用于检查给定块 b 是否通过连接器与给定插座 s 相连。

        Args:
            b: 块对象。
            s: 插槽对象。

        Returns:
            如果插槽已经连接则返回 True，否则返回 False。
        """
        # 查找Block对应的连接器集合
        connectors = self.block_connector_map.get(b)
        if not connectors:
            return False

        # 遍历所有关联的连接器
        for connector in connectors:
            # 检查源socket
            _, source_socket = self.m_network.lookup_block_and_socket(
                connector.source_socket
            )
            if s is source_socket:
                return True

            # 检查目标socket
            _, target_socket = self.m_network.lookup_block_and_socket(
                connector.target_socket
            )
            if s is target_socket:
                return True

        return False

    def start_socket_connection(
            self, outlet_socket_item: SocketItem, mouse_pos: QPointF
    ) -> None:
        """开始一个插槽连接。

        当用户点击一个出口插槽时，开始创建连接。创建一个虚拟块和虚拟插槽，
        并初始化连接器。

        Args:
            outlet_socket_item: 出口插槽项，表示用户点击的插槽。
            mouse_pos: 鼠标点击的位置，用于定位虚拟块。
        """
        assert not outlet_socket_item.socket().m_inlet

        # 取消所有块和连接线段的选中状态
        for block in self.m_block_items:
            block.setSelected(False)
        for segment_item in self.m_connector_segment_items:
            segment_item.setSelected(False)

        # 获取出口插槽的父块和插槽信息
        bitem = outlet_socket_item.parentItem()
        assert isinstance(bitem, BlockItem)
        source_block = bitem.block()
        source_socket = outlet_socket_item.socket()
        start_socket_name = f"{source_block.m_name}.{source_socket.m_name}"

        # 创建一个虚拟块，用于表示连接的起点
        dummy_block = Block()
        dummy_block.m_pos = mouse_pos
        dummy_block.m_size = QSizeF(20, 20)
        dummy_block.m_name = Globals.InvisibleLabel
        dummy_block.m_connection_helper_block = True

        # 创建一个虚拟插槽，用于表示连接的目标
        dummy_socket = Socket()
        dummy_socket.m_name = Globals.InvisibleLabel
        dummy_socket.m_inlet = True
        dummy_socket.m_orientation = Qt.Horizontal
        dummy_socket.m_pos = QPointF(0, 0)
        dummy_block.m_sockets.append(dummy_socket)

        # 将虚拟块添加到网络中
        self.m_network.m_blocks.append(dummy_block)

        # 生成虚拟插槽的名称
        target_socket_name = f"{dummy_block.m_name}.{dummy_socket.m_name}"

        # 创建一个连接器，表示从出口插槽到虚拟插槽的连接
        con = Connector()
        con.m_name = Globals.InvisibleLabel
        con.m_source_socket = start_socket_name
        con.m_target_socket = target_socket_name
        self.m_network.m_connectors.append(con)

        # 创建虚拟块的图形项，并添加到场景中
        bi = self.create_block_item(self.m_network.m_blocks[-1])  # type: ignore
        bi.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        bi.setPos(dummy_block.m_pos)
        bi.setPos(self.views()[0].mapToScene(mouse_pos))

        self.m_block_items.append(bi)
        self.addItem(bi)

        # 创建连接器的图形项，并添加到场景中
        new_conns = self.create_connector_items(self.m_network.m_connectors[-1])
        for item in new_conns:
            self.addItem(item)
            self.m_connector_segment_items.append(item)

        # 标记当前正在连接中
        self.m_currently_connecting = True

    def finish_connection(self) -> None:
        """完成连接操作。

        如果当前正在连接中，移除虚拟块并结束连接状态。
        """
        if self.m_network.m_blocks and self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel:  # type: ignore
            self.remove_block(len(self.m_network.m_blocks) - 1)
        self.m_currently_connecting = False

    def selected_blocks(self) -> List[Block]:
        """获取当前选中的块对象。

        Returns:
            当前选中的所有块对象列表。
        """
        selected = self.selectedItems()
        selected_blocks = []
        for item in selected:
            if isinstance(item, BlockItem):
                selected_blocks.append(item.block())
        return selected_blocks

    def selected_connector(self) -> Optional[Connector]:
        """获取当前选中的连接器对象。

        Returns:
            当前选中的连接器对象。如果未选中任何连接器，返回 None。
        """
        selected = self.selectedItems()
        for item in selected:
            if isinstance(item, ConnectorSegmentItem):
                return item.m_connector
        return None

    def add_block(self, block: Block) -> None:
        """向网络中添加一个新块。

        Args:
            block: 需要添加的块对象。
        """
        self.m_network.m_blocks.append(block)
        item = self.create_block_item(self.m_network.m_blocks[-1])
        self.addItem(item)
        self.m_block_items.append(item)

    def add_connector(self, con: Connector) -> None:
        """向网络中添加一个新连接器。

        Args:
            con: 需要添加的连接器对象。

        Raises:
            RuntimeError: 如果源插槽或目标插槽无效，或者目标插槽已经有连接。
        """
        try:
            b1, s1 = self.m_network.lookup_block_and_socket(con.m_source_socket)
        except Exception:
            raise RuntimeError(
                "[SceneManager::add_connector] Invalid source socket identifier."
            )
        try:
            b2, s2 = self.m_network.lookup_block_and_socket(con.m_target_socket)
        except Exception:
            raise RuntimeError(
                "[SceneManager::add_connector] Invalid target socket identifier."
            )
        if s1.m_inlet:
            raise RuntimeError(
                "[SceneManager::add_connector] Invalid source socket (must be an outlet socket)."
            )
        if not s2.m_inlet:
            raise RuntimeError(
                "[SceneManager::add_connector] Invalid target socket (must be an inlet socket)."
            )
        if self.is_connected_socket(b2, s2):
            raise RuntimeError(
                "[SceneManager::add_connector] Invalid target socket (has already an incoming connection)."
            )
        self.m_network.m_connectors.append(con)
        self.m_network.adjust_connector(self.m_network.m_connectors[-1])

    def remove_block(self, block: Union[Block, int]) -> None:
        """从网络中移除一个块及其相关连接。

        Args:
            block: 需要移除的块对象或其索引。

        Raises:
            RuntimeError: 如果块对象无效或不在网络中。
        """
        # 确定块索引
        if isinstance(block, int):
            block_index = block
            block_to_remove = self.m_network.m_blocks[block_index]
        else:
            # 遍历查找目标块
            for idx, b in enumerate(self.m_network.m_blocks):
                if b is block:  # 使用is进行对象身份比较
                    block_index = idx
                    block_to_remove = b
                    break
            else:
                raise RuntimeError("[SceneManager::remove_block] Block not in network")

        # 有效性检查
        assert 0 <= block_index < len(self.m_network.m_blocks)
        assert block_index < len(self.m_block_items)

        # 移除相关连接器
        related_connectors = self.m_block_connector_map.get(block_to_remove, set())
        for con in related_connectors:
            # 在连接器列表中查找并移除
            for i in reversed(range(len(self.m_network.m_connectors))):
                if self.m_network.m_connectors[i] is con:
                    del self.m_network.m_connectors[i]
                    break

        # 清理块关联数据
        # 只删除当前块的映射条目（关键修正点）
        if block_to_remove in self.m_block_connector_map:
            del self.m_block_connector_map[block_to_remove]

        # 移除图形项
        # 删除块图形项
        block_item = self.m_block_items.pop(block_index)
        self.removeItem(block_item)
        # 删除块数据
        del self.m_network.m_blocks[block_index]

        # 更新剩余连接器
        # 直接删除相关连接器图形项（优化点）
        connectors_to_keep = [
            con for con in self.m_network.m_connectors if con not in related_connectors
        ]
        # 清空并重建连接器
        for item in self.m_connector_segment_items:
            self.removeItem(item)
        self.m_connector_segment_items.clear()

        # 重建有效连接器的图形项
        for con in connectors_to_keep:
            new_items = self.create_connector_items(con)
            self.m_connector_segment_items.extend(new_items)
            for item in new_items:
                self.addItem(item)

    def remove_connector(self, con: Union[Connector, int]) -> None:
        """从网络中移除一个连接器。

        Args:
            con: 需要移除的连接器对象或其索引。

        Raises:
            RuntimeError: 如果连接器对象无效或不在网络中。
        """
        # 确定连接器索引
        if isinstance(con, int):
            connector_index = con
        else:
            # 使用对象身份比对
            for idx, c in enumerate(self.m_network.m_connectors):
                if c is con:  # 关键修正点1：使用is代替==
                    connector_index = idx
                    break
            else:
                raise RuntimeError("[SceneManager::remove_connector] Invalid pointer")

        # 有效性检查
        assert 0 <= connector_index < len(self.m_network.m_connectors)

        # 获取待删除连接器
        con_to_remove = self.m_network.m_connectors[connector_index]

        # 删除关联图形项 (修正循环逻辑)
        i = 0
        while i < len(self.m_connector_segment_items):
            if (
                    self.m_connector_segment_items[i].m_connector is con_to_remove
            ):  # 关键修正点2
                item = self.m_connector_segment_items.pop(i)
                self.removeItem(item)
                del item
            else:
                i += 1  # 仅当不删除时递增索引

        # 清理块-连接器映射表 (完整实现)
        for block in list(self.m_block_connector_map.keys()):  # 遍历副本避免修改问题
            cons = self.m_block_connector_map[block]
            if con_to_remove in cons:
                cons.remove(con_to_remove)
                if not cons:  # 清理空集合
                    del self.m_block_connector_map[block]

        # 删除连接器数据
        del self.m_network.m_connectors[connector_index]

    def mouse_press_event(self, mouse_event) -> None:
        """处理鼠标按下事件。

        如果当前正在连接中，捕获鼠标事件以继续连接操作。

        Args:
            mouse_event: 鼠标事件对象。
        """
        already_in_connection_process = (
                self.m_network.m_blocks
                and self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel
        )
        super().mousePressEvent(mouse_event)
        in_connection_process = (
                self.m_network.m_blocks
                and self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel
        )
        if not already_in_connection_process and in_connection_process:
            self.m_block_items[-1].grabMouse()

    def mouse_move_event(self, mouse_event) -> None:
        """处理鼠标移动事件。

        如果当前正在连接中，更新虚拟块的位置，并检查是否有可用的目标插槽。

        Args:
            mouse_event: 鼠标事件对象。
        """
        if self.m_currently_connecting:
            if (
                    self.m_block_items
                    and self.m_block_items[-1].block().m_name == Globals.InvisibleLabel
            ):
                p = self.m_block_items[-1].pos()
                for bi in self.m_block_items:
                    if bi.block().m_name == Globals.InvisibleLabel:
                        continue
                    # 重置所有插槽状态
                    for si in bi.m_socket_items:
                        si.m_hovered = False
                        si.update()
                    # 安全类型处理
                    socket_item: Optional[SocketItem] = (
                        bi.inlet_socket_accepting_connection(p)
                    )
                    if socket_item is not None:
                        if not self.is_connected_socket(
                                bi.block(), socket_item.socket()
                        ):
                            socket_item.m_hovered = True
                            socket_item.update()
        super().mouseMoveEvent(mouse_event)

    def mouse_release_event(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标释放事件。

        如果当前正在连接中，完成连接操作。

        Args:
            mouse_event: 鼠标事件对象。
        """
        super().mouseReleaseEvent(mouse_event)
        if mouse_event.button() & Qt.LeftButton:
            start_socket = ""
            target_socket = ""

            # 检查是否在连接模式下，并且是否将连接器放置到可连接的插槽上
            if self.m_currently_connecting:
                if (
                        self.m_block_items
                        and self.m_block_items[-1].block().m_name == Globals.InvisibleLabel
                ):
                    p = self.m_block_items[-1].pos()
                    for bi in self.m_block_items:
                        if bi.block().m_name == Globals.InvisibleLabel:
                            continue

                        # 查找可以连接的插槽
                        si = bi.inlet_socket_accepting_connection(p)
                        if si and not self.is_connected_socket(bi.block(), si.socket()):
                            # 找到目标插槽，记录起始插槽和目标插槽
                            start_socket = self.m_network.m_connectors[
                                -1
                            ].m_source_socket
                            target_socket = f"{bi.block().m_name}.{si.socket().m_name}"
                            break

            self.finish_connection()

            # 如果找到有效的起始和目标插槽，创建新的连接器
            if start_socket and target_socket:
                con = Connector()
                con.m_name = "New Connector"
                con.m_source_socket = start_socket
                con.m_target_socket = target_socket
                self.m_network.m_connectors.append(con)
                self.m_network.adjust_connector(self.m_network.m_connectors[-1])
                self.update_connector_segment_items(
                    self.m_network.m_connectors[-1], None
                )
                self.new_connection_added.emit()
            else:
                # 如果没有选择任何块或连接器，发出清除选择的信号
                block_or_connector_selected = False
                for item in self.m_block_items:
                    if item.isSelected():
                        block_or_connector_selected = True
                        break
                for item in self.m_connector_segment_items:
                    if item.isSelected():
                        block_or_connector_selected = True
                        break
                if not block_or_connector_selected:
                    self.selection_cleared.emit()

    def create_block_item(self, block: Block) -> BlockItem:
        """创建一个块图形项。

        Args:
            block: 需要创建图形项的块对象。

        Returns:
            创建的块图形项。
        """
        item = BlockItem(block)
        item.setRect(0, 0, block.m_size.width(), block.m_size.height())
        item.setPos(block.m_pos)
        return item

    def create_connector_item(self, con: Connector) -> ConnectorSegmentItem:
        """创建一个连接器线段图形项。

        Args:
            con: 需要创建图形项的连接器对象。

        Returns:
            创建的连接器线段图形项。
        """
        item = ConnectorSegmentItem(con)
        return item

    def create_connector_items(self, con: Connector) -> List[ConnectorSegmentItem]:
        """为连接器创建所有线段图形项。

        Args:
            con: 需要创建图形项的连接器对象。

        Returns:
            创建的连接器线段图形项列表。
        """
        new_conns: List[ConnectorSegmentItem] = []
        try:
            # 初始化默认值以避免未赋值引用
            start_line = QLineF()  # 默认空线段
            end_line = QLineF()  # 默认空线段

            # 查找源插槽和目标插槽
            block, socket = self.m_network.lookup_block_and_socket(con.m_source_socket)
            if block and socket:
                self.m_block_connector_map.setdefault(block, set()).add(con)
                start_line = block.socket_start_line(socket)  # 覆盖默认值

            block, socket = self.m_network.lookup_block_and_socket(con.m_target_socket)
            if block and socket:
                self.m_block_connector_map.setdefault(block, set()).add(con)
                end_line = block.socket_start_line(socket)  # 覆盖默认值

            if start_line.isNull():
                raise ValueError("Source socket not found or invalid")
            if end_line.isNull():
                raise ValueError("Target socket not found or invalid")

            # 创建起始和结束线段
            item = self.create_connector_item(con)
            item.setLine(start_line)
            item.setFlags(QGraphicsItem.ItemIsSelectable)
            item.m_segment_idx = -1  # 起始线段
            new_conns.append(item)

            item = self.create_connector_item(con)
            item.setLine(end_line)
            item.setFlags(QGraphicsItem.ItemIsSelectable)
            item.m_segment_idx = -2  # 结束线段
            new_conns.append(item)

            # 创建中间线段
            start = start_line.p2()
            for i, seg in enumerate(con.m_segments):
                item = self.create_connector_item(con)
                next_point = (
                    start + QPointF(seg.m_offset, 0)
                    if seg.m_direction == Qt.Horizontal
                    else start + QPointF(0, seg.m_offset)
                )
                item.setLine(QLineF(start, next_point))
                item.m_segment_idx = i  # 中间线段
                new_conns.append(item)
                start = next_point

        except Exception as e:
            print(f"Error creating connector items: {e}")
            for item in new_conns:
                item.deleteLater()
            new_conns.clear()

        return new_conns

    def on_selection_changed(self) -> None:
        """处理选择变化事件。

        如果选择了连接器线段，选中该连接器的所有线段，并发出信号。
        """
        items = self.selectedItems()
        if not items:
            self.selection_cleared.emit()
            return

        # 查找所有选中的连接器
        selected_connectors = set()
        for item in items:
            if isinstance(item, ConnectorSegmentItem):
                selected_connectors.add(item.m_connector)

        # 如果选中了连接器，选中该连接器的所有线段
        if selected_connectors:
            self.clearSelection()
            for item in self.m_connector_segment_items:
                if item.m_connector in selected_connectors:
                    item.setSelected(True)
            # 发出信号，表示选中了连接器
            self.new_connector_selected.emit(
                selected_connectors.pop().m_source_socket,
                selected_connectors.pop().m_target_socket,
            )

    def block_double_clicked(self, block_item: BlockItem) -> None:
        """处理块双击事件。

        Args:
            block_item: 被双击的块图形项。
        """
        self.block_action_triggered.emit(block_item)

    def update_connector_segment_items(
            self, con: Connector, current_item: Optional[ConnectorSegmentItem]
    ) -> None:
        """更新连接器的线段图形项。

        Args:
            con: 需要更新的连接器对象。
            current_item: 当前正在操作的线段图形项。
        """
        start_segment: Optional[ConnectorSegmentItem] = None
        end_segment: Optional[ConnectorSegmentItem] = None
        segment_items: List[ConnectorSegmentItem] = []

        # 查找所有与连接器相关的线段图形项
        for item in self.m_connector_segment_items:
            if item.m_connector == con:
                if item.m_segment_idx == -1:
                    start_segment = item
                elif item.m_segment_idx == -2:
                    end_segment = item
                else:
                    if current_item is None or item != current_item:
                        segment_items.append(item)

        # 如果找不到任何线段图形项，重新创建
        if start_segment is None and end_segment is None and not segment_items:
            new_conns = self.create_connector_items(con)
            for item in new_conns:
                self.addItem(item)
                self.m_connector_segment_items.append(item)
            return

        # 确保起始和结束线段存在
        assert start_segment is not None
        assert end_segment is not None

        # 移除多余的线段图形项
        items_needed = len(con.m_segments)
        if current_item is not None:
            items_needed -= 1

        while len(segment_items) > items_needed:
            item = segment_items.pop()
            self.m_connector_segment_items.remove(item)
            item.deleteLater()

        # 添加缺失的线段图形项
        for i in range(len(segment_items), items_needed):
            item = self.create_connector_item(con)
            item.m_is_highlighted = (
                current_item.m_is_highlighted if current_item else False
            )
            self.addItem(item)
            self.m_connector_segment_items.append(item)
            segment_items.append(item)

        # 插入当前线段图形项
        if current_item is not None:
            segment_items.insert(current_item.m_segment_idx, current_item)

        # 确保线段图形项数量与线段数量一致
        assert len(segment_items) == len(con.m_segments)

        # 更新所有线段图形项的几何信息
        try:
            # 分别查找源插槽和目标插槽
            source_block, source_socket = self.m_network.lookup_block_and_socket(
                con.m_source_socket
            )
            target_block, target_socket = self.m_network.lookup_block_and_socket(
                con.m_target_socket
            )

            # 更新起始线段（源插槽）
            if source_block and source_socket:
                start_line = source_block.socket_start_line(source_socket)
                start_segment.setLine(start_line)
            else:
                raise ValueError("Source socket not found")

            # 更新结束线段（目标插槽）
            if target_block and target_socket:
                end_line = target_block.socket_start_line(target_socket)
                end_segment.setLine(end_line)
            else:
                raise ValueError("Target socket not found")

            # 更新中间线段（保持与C++相同的逻辑）
            start = start_line.p2()
            for i, seg in enumerate(con.m_segments):
                item = segment_items[i]
                next_point = (
                    start + QPointF(seg.m_offset, 0)
                    if seg.m_direction == Qt.Horizontal
                    else start + QPointF(0, seg.m_offset)
                )
                item.setLine(QLineF(start, next_point))
                item.m_segment_idx = i
                start = next_point

        except Exception as e:
            print(f"Error updating connector segments: {e}")
