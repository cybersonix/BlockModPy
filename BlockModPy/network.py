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

import os
from typing import List, Set, Tuple

from qtpy.QtCore import (
    QFile,
    QIODevice,
    Qt,
    QXmlStreamReader,
    QXmlStreamWriter,
)

from .block import Block
from .connector import Connector
from .globals import Globals
from .socket import Socket


class Network:
    """网络类，负责管理块和连接器，并提供相关操作。"""

    def __init__(self) -> None:
        """初始化网络对象。"""
        self.m_blocks: List[Block] = []
        self.m_connectors: List[Connector] = []

    def swap(self, other: Network) -> None:
        """交换两个网络对象的内容。

        Args:
            other: 另一个网络对象。
        """
        self.m_blocks, other.m_blocks = other.m_blocks, self.m_blocks
        self.m_connectors, other.m_connectors = other.m_connectors, self.m_connectors

    def read_xml(self, fname: str) -> None:
        """从 XML 文件中读取网络数据。

        Args:
            fname: XML 文件的路径。

        Raises:
            RuntimeError: 如果文件无法读取或 XML 格式错误。
        """
        if not os.path.exists(fname):
            raise RuntimeError(f"Cannot read file: {fname} does not exist.")

        file = QFile(fname)
        if not file.open(QIODevice.ReadOnly | QFile.Text):
            raise RuntimeError("Cannot open file for reading.")

        reader = QXmlStreamReader(file)

        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement():
                if reader.name() == "BlockMod":
                    while not reader.atEnd() and not reader.hasError():
                        reader.readNext()
                        if reader.isStartElement():
                            section_name = reader.name()
                            if section_name == "Blocks":
                                self._read_blocks(reader)
                            elif section_name == "Connectors":
                                self._read_connectors(reader)
                            else:
                                reader.raiseError(f"Unknown tag '{section_name}'.")
                        elif reader.isEndElement() and reader.name() == "BlockMod":
                            break
                else:
                    reader.raiseError("Expected BlockMod XML tag.")
                    break

        if reader.hasError():
            raise RuntimeError(reader.errorString())

        file.close()

    def write_xml(self, fname: str) -> None:
        """将网络数据写入 XML 文件。

        Args:
            fname: XML 文件的路径。

        Raises:
            RuntimeError: 如果文件无法创建或写入。
        """
        file = QFile(fname)
        if not file.open(QIODevice.WriteOnly | QFile.Truncate | QFile.Text):
            raise RuntimeError("Cannot create output file.")

        writer = QXmlStreamWriter(file)
        writer.setAutoFormatting(True)
        writer.setAutoFormattingIndent(-1)
        writer.writeStartDocument()

        writer.writeStartElement("BlockMod")

        if self.m_blocks:
            writer.writeComment("Blocks")
            writer.writeStartElement("Blocks")
            for block in self.m_blocks:
                block.write_xml(writer)
            writer.writeEndElement()  # Blocks

        if self.m_connectors:
            writer.writeComment("Connectors")
            writer.writeStartElement("Connectors")
            for connector in self.m_connectors:
                connector.write_xml(writer)
            writer.writeEndElement()  # Connectors

        writer.writeEndElement()  # BlockMod
        writer.writeEndDocument()
        file.close()

    def check_names(self, print_names: bool = False) -> None:
        """检查块和插槽的名称是否有效。

        Args:
            print_names: 是否打印块和插槽的名称。

        Raises:
            RuntimeError: 如果名称无效或重复。
        """
        block_names: Set[str] = set()
        for block in self.m_blocks:
            if "." in block.m_name:
                raise RuntimeError(f"Invalid Block ID name '{block.m_name}'")
            if block.m_name in block_names:
                raise RuntimeError(f"Duplicate Block ID name '{block.m_name}'")
            block_names.add(block.m_name)
            if print_names:
                print(block.m_name)

            socket_names: Set[str] = set()
            for socket in block.m_sockets:
                if socket.m_name in socket_names:
                    raise RuntimeError(
                        f"Duplicate Socket ID name '{socket.m_name}' within block '{block.m_name}'"
                    )
                socket_names.add(socket.m_name)
                if print_names:
                    print(socket.m_name)

        connected_sockets: Set[str] = set()
        for connector in self.m_connectors:
            try:
                source_block, source_socket = self.lookup_block_and_socket(
                    connector.m_source_socket
                )
                target_block, target_socket = self.lookup_block_and_socket(
                    connector.m_target_socket
                )
            except RuntimeError as e:
                raise RuntimeError(str(e))

            if source_socket.m_inlet:
                raise RuntimeError(
                    f"Invalid source socket '{connector.m_source_socket}' (must be an outlet socket)."
                )
            if not target_socket.m_inlet:
                raise RuntimeError(
                    f"Invalid target socket '{connector.m_target_socket}' (must be an inlet socket)."
                )
            if connector.m_target_socket in connected_sockets:
                raise RuntimeError(
                    f"Target socket '{connector.m_target_socket}' connected twice!"
                )
            connected_sockets.add(connector.m_target_socket)

    def have_socket(self, socket_variable_name: str, inlet_socket: bool) -> bool:
        """检查是否存在指定名称的插槽。

        Args:
            socket_variable_name: 插槽的完整名称（格式为 "block.socket"）。
            inlet_socket: 是否为入口插槽。

        Returns:
            如果存在指定名称的插槽，返回 True，否则返回 False。
        """
        block_name, socket_name = self._split_flat_name(socket_variable_name)
        for block in self.m_blocks:
            if block.m_name == block_name:
                for socket in block.m_sockets:
                    if socket.m_name == socket_name and socket.m_inlet == inlet_socket:
                        return True
        return False

    def adjust_connectors(self) -> None:
        """调整所有连接器的几何信息。

        Raises:
            RuntimeError: 如果调整过程中发生错误。
        """
        for connector in self.m_connectors:
            try:
                self.adjust_connector(connector)
            except RuntimeError as e:
                print(f"Error adjusting connector {connector.m_name}: {e}")
                raise

    def adjust_connector(self, connector: Connector) -> None:
        """调整单个连接器的几何信息。

        Args:
            connector: 需要调整的连接器对象。

        Raises:
            RuntimeError: 如果连接器的插槽无效。
        """
        source_block, source_socket = self.lookup_block_and_socket(
            connector.m_source_socket
        )
        target_block, target_socket = self.lookup_block_and_socket(
            connector.m_target_socket
        )

        start_line = source_block.socket_start_line(source_socket)
        end_line = target_block.socket_start_line(target_socket)

        dx = end_line.p2().x() - start_line.p2().x()
        dy = end_line.p2().y() - start_line.p2().y()

        for segment in connector.m_segments:
            if segment.m_direction == Qt.Horizontal:
                dx -= segment.m_offset
            else:
                dy -= segment.m_offset

        if not Globals.near_zero(dy):
            for segment in connector.m_segments:
                if segment.m_direction == Qt.Vertical:
                    segment.m_offset += dy
                    break
            else:
                connector.m_segments.append(Connector.Segment(Qt.Vertical, dy))

        if not Globals.near_zero(dx):
            for segment in connector.m_segments:
                if segment.m_direction == Qt.Horizontal:
                    segment.m_offset += dx
                    break
            else:
                connector.m_segments.append(Connector.Segment(Qt.Horizontal, dx))

    def lookup_block_and_socket(self, flat_name: str) -> Tuple[Block, Socket]:
        """根据完整名称查找块和插槽。

        Args:
            flat_name: 完整名称（格式为 "block.socket"）。

        Returns:
            包含块和插槽的元组。

        Raises:
            RuntimeError: 如果名称无效。
        """
        block_name, socket_name = self._split_flat_name(flat_name)

        # 搜索 Block 对象
        block = next((b for b in self.m_blocks if b.m_name == block_name), None)
        if block is None:
            raise RuntimeError("Invalid flat name.")

        # 搜索 Socket 对象
        socket = next((s for s in block.m_sockets if s.m_name == socket_name), None)
        if socket is None:
            raise RuntimeError("Invalid flat name.")

        return block, socket

    def remove_block(self, block_idx: int) -> None:
        """移除指定索引的块及其相关连接器。

        Args:
            block_idx: 块的索引。

        Raises:
            IndexError: 如果索引无效。
        """
        if block_idx >= len(self.m_blocks):
            raise IndexError("Block index out of range.")

        block = self.m_blocks[block_idx]
        block_name = block.m_name

        # Remove connectors related to this block
        self.m_connectors = [
            connector
            for connector in self.m_connectors
            if not (
                connector.m_source_socket.startswith(block_name + ".")
                or connector.m_target_socket.startswith(block_name + ".")
            )
        ]

        # Remove the block
        self.m_blocks.pop(block_idx)

    def rename_block(self, block_idx: int, new_name: str) -> None:
        """重命名指定索引的块，并更新相关连接器。

        Args:
            block_idx: 块的索引。
            new_name: 新的块名称。

        Raises:
            IndexError: 如果索引无效。
        """
        if block_idx >= len(self.m_blocks):
            raise IndexError("Block index out of range.")

        block = self.m_blocks[block_idx]
        old_name = block.m_name
        block.m_name = new_name

        # Update connectors
        for connector in self.m_connectors:
            if connector.m_source_socket.startswith(old_name + "."):
                connector.m_source_socket = (
                    new_name + connector.m_source_socket[len(old_name) :]
                )
            if connector.m_target_socket.startswith(old_name + "."):
                connector.m_target_socket = (
                    new_name + connector.m_target_socket[len(old_name) :]
                )

    @staticmethod
    def _split_flat_name(flat_name: str) -> Tuple[str, str]:
        """将完整名称拆分为块名称和插槽名称。

        Args:
            flat_name: 完整名称（格式为 "block.socket"）。

        Returns:
            包含块名称和插槽名称的元组。

        Raises:
            RuntimeError: 如果名称格式无效。
        """
        if "." not in flat_name:
            raise RuntimeError(
                f"Bad flat name '{flat_name}', expected 'block.socket' format."
            )
        dot_index = flat_name.index(".")
        return flat_name[:dot_index].strip(), flat_name[dot_index + 1 :].strip()

    def _read_blocks(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取块数据。

        Args:
            reader: XML 读取器对象。
        """
        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement() and reader.name() == "Block":
                block = Block()
                block.read_xml(reader)
                self.m_blocks.append(block)
            elif reader.isEndElement() and reader.name() == "Blocks":
                break

    def _read_connectors(self, reader: QXmlStreamReader) -> None:
        """从 XML 读取连接器数据。

        Args:
            reader: XML 读取器对象。
        """
        while not reader.atEnd() and not reader.hasError():
            reader.readNext()
            if reader.isStartElement() and reader.name() == "Connector":
                connector = Connector()
                connector.read_xml(reader)
                self.m_connectors.append(connector)
            elif reader.isEndElement() and reader.name() == "Connectors":
                break
