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

from typing import List

from qtpy.QtCore import Qt, QXmlStreamReader, QXmlStreamWriter
from qtpy.QtGui import QColor


class Connector:
    """Connector 类，表示网络中的连接器，负责管理连接器的源插槽、目标插槽和线段信息。"""

    class Segment:
        """Segment 类，表示连接器的一个线段，包含方向和偏移量信息。"""

        def __init__(
            self, direction: Qt.Orientation = Qt.Horizontal, offset: float = 0.0
        ) -> None:
            """初始化 Segment 对象。

            Args:
                direction: 线段的方向，默认为水平方向。
                offset: 线段的偏移量，默认为 0.0。
            """
            self.m_direction: Qt.Orientation = direction
            self.m_offset: float = offset

        def read_xml(self, reader: QXmlStreamReader) -> None:
            """从 XML 读取线段数据。

            Args:
                reader: XML 读取器对象。

            Raises:
                RuntimeError: 如果 XML 格式错误或数据无效。
            """
            if not reader.isStartElement():
                raise RuntimeError("Expected start element.")

            while not reader.atEnd() and not reader.hasError():
                reader.readNext()
                if reader.isStartElement():
                    ename = reader.name()
                    if ename == "Orientation":
                        orient = reader.readElementText()
                        self.m_direction = (
                            Qt.Horizontal if orient == "Horizontal" else Qt.Vertical
                        )
                    elif ename == "Offset":
                        offset_str = reader.readElementText()
                        try:
                            self.m_offset = float(offset_str)
                        except ValueError:
                            reader.raiseError(
                                f"Invalid offset value '{offset_str}' in Segment element."
                            )
                            return
                    else:
                        reader.raiseError(
                            f"Found unknown element '{ename}' in Segment element."
                        )
                        return
                elif reader.isEndElement():
                    ename = reader.name()
                    if ename == "Segment":
                        break

        def write_xml(self, writer: QXmlStreamWriter) -> None:
            """将线段数据写入 XML。

            Args:
                writer: XML 写入器对象。
            """
            writer.writeStartElement("Segment")
            writer.writeTextElement(
                "Orientation",
                "Horizontal" if self.m_direction == Qt.Horizontal else "Vertical",
            )
            writer.writeTextElement("Offset", f"{self.m_offset}")
            writer.writeEndElement()

    def __init__(self) -> None:
        """初始化 Connector 对象。"""
        self.m_name: str = ""
        self.m_source_socket: str = ""
        self.m_target_socket: str = ""
        self.m_segments: List[Connector.Segment] = []
        self.m_text: str = ""
        self.m_linewidth: float = 0.8
        self.m_color: QColor = Qt.black

    def read_xml(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取连接器数据。

        Args:
            reader: XML 读取器对象。

        Raises:
            RuntimeError: 如果 XML 格式错误或数据无效。
        """
        if not reader.isStartElement():
            raise RuntimeError("Expected start element.")

        self.m_name = reader.attributes().value("name")

        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement():
                ename = reader.name()
                if ename == "Source":
                    self.m_source_socket = reader.readElementText()
                elif ename == "Target":
                    self.m_target_socket = reader.readElementText()
                elif ename == "Segments":
                    self._read_segments(reader)
                else:
                    reader.raiseError(
                        f"Found unknown element '{ename}' in Connector tag."
                    )
                    return
            elif reader.isEndElement():
                ename = reader.name()
                if ename == "Connector":
                    break

    def write_xml(self, writer: QXmlStreamWriter) -> None:
        """将连接器数据写入 XML。

        Args:
            writer: XML 写入器对象。
        """
        writer.writeStartElement("Connector")
        writer.writeAttribute("name", self.m_name)
        if self.m_source_socket:
            writer.writeTextElement("Source", self.m_source_socket)
        if self.m_target_socket:
            writer.writeTextElement("Target", self.m_target_socket)
        if self.m_segments:
            writer.writeComment("Connector segments (between start and end lines)")
            writer.writeStartElement("Segments")
            for segment in self.m_segments:
                segment.write_xml(writer)
            writer.writeEndElement()  # Segments
        writer.writeEndElement()

    def _read_segments(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取线段列表。

        Args:
            reader: XML 读取器对象。
        """
        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement() and reader.name() == "Segment":
                segment = Connector.Segment()
                segment.read_xml(reader)
                self.m_segments.append(segment)
            elif reader.isEndElement() and reader.name() == "Segments":
                break
