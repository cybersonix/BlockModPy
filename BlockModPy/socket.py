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

from enum import Enum

from qtpy.QtCore import Qt, QXmlStreamReader, QXmlStreamWriter, QPointF


class Socket:
    """表示图形化块元素的连接点，管理连接点的几何属性和连接逻辑。

    Attributes：
        m_name: 插槽唯一标识符。
        m_pos: 相对于父块左上角的坐标位置（单位：像素）。示例：QPointF(0, 20)
        m_orientation: 连接线延伸方向类型枚举。
            Qt.Horizontal - 水平方向（左右延伸）
            Qt.Vertical   - 垂直方向（上下延伸）
        m_inlet: 连接点类型标识。
            True  - 输入型插槽（接收连接线接入）
            False - 输出型插槽（发起连接线）
    """

    class Direction(Enum):
        """插槽延伸方向枚举，定义连接点在块上的方位。

        Attributes：
            Left: 位于父块左侧边缘，水平向左延伸。
            Right: 位于父块右侧边缘，水平向右延伸。
            Top: 位于父块顶部边缘，垂直向上延伸。
            Bottom: 位于父块底部边缘，垂直向下延伸。
        """

        Left = 0
        Right = 1
        Top = 2
        Bottom = 3

    def __init__(self) -> None:
        self.m_name: str = ""  # 插槽名称
        self.m_pos: QPointF = QPointF(0, 0)  # 插槽位置
        self.m_orientation: Qt.Orientation = Qt.Horizontal  # 插槽方向
        self.m_inlet: bool = False  # 是否为输入插槽

    def direction(self) -> Direction:
        """根据位置和方向计算插槽指向方向。

        水平方向时返回左侧边缘，否则右侧边缘；垂直方向时：y=0返回顶部边缘，否则底部边缘。

        Returns:
            返回计算得到的方向枚举值。
        """
        if self.m_orientation == Qt.Horizontal:
            # 水平方向：左边缘为Left，右边缘为Right
            return (
                self.Direction.Left if (self.m_pos.x() == 0) else self.Direction.Right
            )
        else:
            # 垂直方向：上边缘为Top，下边缘为Bottom
            return (
                self.Direction.Top if (self.m_pos.y() == 0) else self.Direction.Bottom
            )

    def __eq__(self, other: object) -> bool:
        """重载相等运算符，支持多种比较方式。

        允许的对比类型：
        1. 与字符串对比：比对插槽名称（用于列表快速查找）。
        2. 与Socket实例对比：比对插槽名称（基于名称唯一性原则）。

        Args:
            other: 对比对象，支持 str 或 Socket 类型。

        Returns:
            返回比对结果。True表示名称匹配，False表示名称不匹配或类型不支持。

        Examples:
            socket = Socket()
            socket.m_name = "input_1"
            socket == "input_1"  # 返回True
            socket2 = Socket()
            socket2.m_name = "input_1"
            socket == socket2  # 返回True
        """
        if isinstance(other, str):
            return self.m_name == other
        elif isinstance(other, Socket):
            return self.m_name == other.m_name
        return NotImplemented

    def read_xml(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取插槽数据。

        Args:
            reader: XML 读取器对象。

        Raises:
            RuntimeError: 如果 XML 格式错误或包含未知元素。
        """
        if not reader.isStartElement():
            raise RuntimeError("Expected start element for Socket.")

        # 读取插槽属性
        self.m_name = str(reader.attributes().value("name"))

        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement():
                element_name = str(reader.name())
                if element_name == "Position":
                    pos_str = self._read_text_element(reader)
                    self.m_pos = self._decode_point(pos_str)
                elif element_name == "Orientation":
                    orient_str = self._read_text_element(reader)
                    if orient_str not in ["Horizontal", "Vertical"]:
                        raise ValueError(f"Invalid orientation value: {orient_str}")
                    self.m_orientation = (
                        Qt.Horizontal if orient_str == "Horizontal" else Qt.Vertical
                    )
                elif element_name == "Inlet":
                    inlet_str = self._read_text_element(reader)
                    if inlet_str not in ["true", "false"]:
                        raise ValueError(f"Invalid inlet value: {inlet_str}")
                    self.m_inlet = inlet_str == "true"
                else:
                    raise RuntimeError(
                        f"Found unknown element '{element_name}' in Socket tag."
                    )
            elif reader.isEndElement() and reader.name() == "Socket":
                break  # 结束读取

        if reader.hasError():
            raise RuntimeError(reader.errorString())

    def write_xml(self, writer: QXmlStreamWriter) -> None:
        """将插槽数据写入 XML。

        Args:
            writer: XML 写入器对象。
        """
        writer.writeStartElement("Socket")
        writer.writeAttribute("name", self.m_name)
        writer.writeTextElement("Position", self._encode_point(self.m_pos))
        writer.writeTextElement(
            "Orientation",
            "Horizontal" if self.m_orientation == Qt.Horizontal else "Vertical",
        )
        writer.writeTextElement("Inlet", "true" if self.m_inlet else "false")
        writer.writeEndElement()

    def _read_text_element(self, reader: QXmlStreamReader) -> str:
        """读取 XML 文本元素的内容。

        Args:
            reader: XML 读取器对象。

        Returns:
            文本元素的内容。

        Raises:
            RuntimeError: 如果元素不是文本元素。
        """
        if not reader.isStartElement():
            raise RuntimeError("Expected start element for text element.")

        text = reader.readElementText()
        if reader.hasError():
            raise RuntimeError(reader.errorString())
        return text

    def _encode_point(self, point: QPointF) -> str:
        """将 QPointF 编码为字符串。

        Args:
            point: 需要编码的点对象。

        Returns:
            编码后的字符串，格式为 "x,y"。
        """
        return f"{point.x()},{point.y()}"

    def _decode_point(self, point_str: str) -> QPointF:
        """将字符串解码为 QPointF。

        Args:
            point_str: 需要解码的字符串，格式为 "x,y"。

        Returns:
            解码后的 QPointF 对象。

        Raises:
            RuntimeError: 如果字符串格式无效。
        """
        try:
            x, y = map(float, point_str.split(","))
            return QPointF(x, y)
        except ValueError:
            raise RuntimeError(f"Invalid point format: {point_str}")
