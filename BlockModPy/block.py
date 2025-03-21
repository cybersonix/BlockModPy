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

from typing import List, Dict, Tuple, Any

from qtpy.QtCore import QPointF, QLineF, QSizeF, QXmlStreamReader, QXmlStreamWriter
from qtpy.QtCore import Qt

from .globals import Globals
from .socket import Socket


class Block:
    """Block 类，表示网络中的一个块，包含块的名称、位置、大小、插槽等属性。"""

    def __init__(self, name: str = "", x: float = 0.0, y: float = 0.0) -> None:
        """初始化 Block 对象。

        Args:
            name: 块的名称。
            x: 块的 X 坐标。
            y: 块的 Y 坐标。
        """

        self.m_name: str = name
        self.m_pos: QPointF = QPointF(x, y)
        self.m_size: QSizeF = QSizeF()
        self.m_sockets: List[Socket] = []
        self.m_properties: Dict[str, Any] = {}
        self.m_connection_helper_block: bool = False

    def read_xml(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取块数据。

        Args:
            reader: XML 读取器对象。

        Raises:
            RuntimeError: 如果 XML 格式错误。
        """
        if not reader.isStartElement():
            raise RuntimeError("Expected start element.")

        # 读取 Block 元素的属性
        self.m_name = reader.attributes().value("name")

        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement():
                ename = reader.name()
                if ename == "Position":
                    pos = self._read_text_element(reader)
                    self.m_pos = self._decode_point(pos)
                elif ename == "Size":
                    size_str = self._read_text_element(reader)
                    pos = self._decode_point(size_str)
                    self.m_size.setWidth(pos.x())
                    self.m_size.setHeight(pos.y())
                elif ename == "Sockets":
                    self._read_list(reader, self.m_sockets)
                elif ename == "Properties":
                    while not reader.atEnd() and not reader.hasError():
                        reader.readNext()
                        if reader.isStartElement():
                            ename = reader.name()
                            if ename == "ShowPixmap":
                                val = self._read_text_element(reader)
                                self.m_properties["ShowPixmap"] = val == "true"
                        elif reader.isEndElement():
                            ename = reader.name()
                            if ename == "Properties":
                                break
                else:
                    reader.raiseError(f"Found unknown element '{ename}' in Block tag.")
                    return
            elif reader.isEndElement():
                ename = reader.name()
                if ename == "Block":
                    break

    def write_xml(self, writer: QXmlStreamWriter) -> None:
        """将块数据写入 XML。

        Args:
            writer: XML 写入器对象。
        """
        writer.writeStartElement("Block")
        writer.writeAttribute("name", self.m_name)
        writer.writeTextElement("Position", self._encode_point(self.m_pos))
        writer.writeTextElement(
            "Size",
            self._encode_point(QPointF(self.m_size.width(), self.m_size.height())),
        )
        if self.m_sockets:
            writer.writeComment("Sockets")
            writer.writeStartElement("Sockets")
            for socket in self.m_sockets:
                socket.write_xml(writer)
            writer.writeEndElement()  # Sockets
        if "ShowPixmap" in self.m_properties:
            writer.writeStartElement("Properties")
            writer.writeTextElement(
                "ShowPixmap", "true" if self.m_properties["ShowPixmap"] else "false"
            )
            writer.writeEndElement()  # Properties
        writer.writeEndElement()

    def socket_start_line(self, socket: Socket) -> QLineF:
        """获取插槽的起始线。

        Args:
            socket: 插槽对象。

        Returns:
            插槽的起始线。
        """
        if self.m_name == Globals.InvisibleLabel:
            start_point = QPointF(socket.m_pos) + self.m_pos
            return QLineF(start_point, start_point)

        other_point = socket.m_pos
        direction = socket.direction()

        offset = {
            Socket.Direction.Left: QPointF(-2 * Globals.GridSpacing, 0),
            Socket.Direction.Right: QPointF(2 * Globals.GridSpacing, 0),
            Socket.Direction.Top: QPointF(0, -2 * Globals.GridSpacing),
            Socket.Direction.Bottom: QPointF(0, 2 * Globals.GridSpacing),
        }.get(direction, QPointF())

        start_point = QPointF(socket.m_pos) + self.m_pos
        other_point = other_point + self.m_pos + offset
        return QLineF(start_point, other_point)

    def find_socket_insert_position(self, inlet_socket: bool) -> Tuple[int, int]:
        """查找插槽的插入坐标 (x, y)。

        Args:
            inlet_socket: 是否为入口插槽。

        Returns:
            插槽的 X、Y 坐标。
        """
        row_count = int(self.m_size.height() / Globals.GridSpacing + 0.5)
        col_count = int(self.m_size.width() / Globals.GridSpacing + 0.5)

        vertical_sockets = [0] * (row_count - 1)
        horizontal_sockets = [0] * (col_count - 1)

        target_sockets = self.filter_sockets(inlet_socket)

        for socket in target_sockets:
            if socket.m_pos.y() == 0.0:
                colrow_idx = int(socket.m_pos.x() / Globals.GridSpacing + 0.5)
                if 0 <= colrow_idx < col_count - 1:
                    horizontal_sockets[colrow_idx] = 1
            else:
                row_idx = int(socket.m_pos.y() / Globals.GridSpacing + 0.5)
                if 0 < row_idx < row_count - 1:
                    vertical_sockets[row_idx] = 1

        for i, val in enumerate(vertical_sockets):
            if val == 0:
                x, y = 0, i
                return x, y

        for i, val in enumerate(horizontal_sockets):
            if val == 0:
                x, y = i, 0
                return x, y

        return col_count - 1, 0

    def unused_socket_spots(self) -> Tuple[List[int], List[int], List[int], List[int]]:
        """获取未使用的插槽位置。

        Returns:
            包含左侧、顶部、右侧和底部未使用插槽位置的元组。
        """
        row_count = int(self.m_size.height() / Globals.GridSpacing + 0.5)
        col_count = int(self.m_size.width() / Globals.GridSpacing + 0.5)

        left_sockets = [0] * row_count
        right_sockets = [0] * row_count
        top_sockets = [0] * col_count
        bottom_sockets = [0] * col_count

        for socket in self.m_sockets:
            col_idx = int(socket.m_pos.x() / Globals.GridSpacing + 0.5)
            row_idx = int(socket.m_pos.y() / Globals.GridSpacing + 0.5)

            if int(socket.m_pos.x()) == 0 and 0 < row_idx < row_count:
                left_sockets[row_idx] += 1
            elif (
                int(socket.m_pos.x()) == int(self.m_size.width())
                and 0 < row_idx < row_count
            ):
                right_sockets[row_idx] += 1
            elif int(socket.m_pos.y()) == 0 and 0 < col_idx < col_count:
                top_sockets[col_idx] += 1
            elif (
                int(socket.m_pos.y()) == int(self.m_size.height())
                and 0 < col_idx < col_count
            ):
                bottom_sockets[col_idx] += 1

        return left_sockets, top_sockets, right_sockets, bottom_sockets

    def auto_update_sockets(
        self, inlet_sockets: List[str], outlet_sockets: List[str]
    ) -> None:
        """自动更新插槽。

        Args:
            inlet_sockets: 入口插槽列表。
            outlet_sockets: 出口插槽列表。
        """
        remaining_sockets = []
        for socket in self.m_sockets:
            if socket.m_inlet and socket.m_name in inlet_sockets:
                remaining_sockets.append(socket)
            elif not socket.m_inlet and socket.m_name in outlet_sockets:
                remaining_sockets.append(socket)
        self.m_sockets = remaining_sockets

        left_sockets, top_sockets, right_sockets, bottom_sockets = (
            self.unused_socket_spots()
        )

        all_sockets = inlet_sockets + outlet_sockets
        for s in all_sockets:
            if any(socket.m_name == s for socket in self.m_sockets):
                continue

            new_socket = Socket()
            new_socket.m_name = s
            new_socket.m_inlet = s in inlet_sockets

            found = False
            for i, val in enumerate(left_sockets):
                if new_socket.m_inlet and val == 0:
                    left_sockets[i] = 1
                    new_socket.m_pos = QPointF(0, i * Globals.GridSpacing)
                    found = True
                    break
                elif not new_socket.m_inlet and right_sockets[i] == 0:
                    right_sockets[i] = 1
                    new_socket.m_pos = QPointF(
                        self.m_size.width(), i * Globals.GridSpacing
                    )
                    found = True
                    break

            if not found:
                for i, val in enumerate(top_sockets):
                    if new_socket.m_inlet and val == 0:
                        top_sockets[i] = 1
                        new_socket.m_orientation = Qt.Vertical
                        new_socket.m_pos = QPointF(i * Globals.GridSpacing, 0)
                        found = True
                        break
                    elif not new_socket.m_inlet and bottom_sockets[i] == 0:
                        bottom_sockets[i] = 1
                        new_socket.m_orientation = Qt.Vertical
                        new_socket.m_pos = QPointF(
                            i * Globals.GridSpacing, self.m_size.height()
                        )
                        found = True
                        break

            if not found:
                if new_socket.m_inlet:
                    new_socket.m_pos = QPointF(
                        self.m_size.width() - Globals.GridSpacing, 0
                    )
                else:
                    new_socket.m_pos = QPointF(
                        self.m_size.width() - Globals.GridSpacing, self.m_size.height()
                    )

            self.m_sockets.append(new_socket)

    def filter_sockets(self, inlet_socket: bool) -> List[Socket]:
        """过滤插槽。

        Args:
            inlet_socket: 是否为入口插槽。

        Returns:
            符合条件的插槽列表。
        """
        return [socket for socket in self.m_sockets if socket.m_inlet == inlet_socket]

    @staticmethod
    def _read_text_element(reader: QXmlStreamReader) -> str:
        """读取 XML 文本元素。

        Args:
            reader: XML 读取器对象。

        Returns:
            文本内容。
        """
        if not reader.isStartElement():
            raise RuntimeError("Expected start element")
        text = reader.readElementText()
        if reader.hasError():
            raise RuntimeError(reader.errorString())
        return text

    @staticmethod
    def _decode_point(pos: str) -> QPointF:
        """解码点坐标。

        Args:
            pos: 点坐标字符串。

        Returns:
            解码后的点坐标。
        """
        x, y = map(float, pos.split(","))
        return QPointF(x, y)

    @staticmethod
    def _encode_point(point: QPointF) -> str:
        """编码点坐标。

        Args:
            point: 点坐标。

        Returns:
            编码后的点坐标字符串。
        """
        return f"{point.x()},{point.y()}"

    @staticmethod
    def _read_list(reader: QXmlStreamReader, sockets: List[Socket]) -> None:
        """读取插槽列表。

        Args:
            reader: XML 读取器对象。
            sockets: 插槽列表。
        """
        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement() and reader.name() == "Socket":
                socket = Socket()
                socket.read_xml(reader)
                sockets.append(socket)
            elif reader.isEndElement() and reader.name() == "Sockets":
                break
