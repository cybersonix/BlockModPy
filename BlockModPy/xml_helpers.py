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

from typing import Optional, Tuple

from qtpy.QtCore import QPointF, QXmlStreamReader


class XMLHelpers:
    """提供 XML 文件读取和写入的辅助函数。"""

    @staticmethod
    def read_unknown_element(reader: QXmlStreamReader) -> None:
        """递归读取未知的 XML 元素。

        Args:
            reader: XML 读取器对象。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return
        assert reader.isStartElement()

        while not reader.atEnd():
            reader.readNext()
            if reader.isEndElement():
                break
            if reader.isStartElement():
                XMLHelpers.read_unknown_element(reader)

    @staticmethod
    def read_until_end_element(reader: QXmlStreamReader) -> None:
        """读取直到遇到结束元素。

        Args:
            reader: XML 读取器对象。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return
        while not reader.atEnd():
            reader.readNext()
            if reader.isEndElement():
                break
            if reader.isStartElement():
                XMLHelpers.read_unknown_element(reader)

    @staticmethod
    def read_double_attribute(
        reader: QXmlStreamReader, name: str, optional: bool = False
    ) -> Optional[float]:
        """读取 XML 元素中的 double 类型属性。

        Args:
            reader: XML 读取器对象。
            name: 属性名称。
            optional: 是否为可选属性，默认为 False。

        Returns:
            解析后的 double 值，如果解析失败且属性为可选，则返回 None。

        Raises:
            ValueError: 如果解析失败且属性为必选。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return None
        value_str = str(reader.attributes().value(name))
        try:
            return float(value_str)
        except ValueError:
            if not optional:
                reader.raiseError(f"Invalid value for attribute '{name}'.")
            return None

    @staticmethod
    def read_int_attribute(
        reader: QXmlStreamReader, name: str, optional: bool = False
    ) -> Optional[int]:
        """读取 XML 元素中的 int 类型属性。

        Args:
            reader: XML 读取器对象。
            name: 属性名称。
            optional: 是否为可选属性，默认为 False。

        Returns:
            解析后的 int 值，如果解析失败且属性为可选，则返回 None。

        Raises:
            ValueError: 如果解析失败且属性为必选。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return None
        value_str = str(reader.attributes().value(name))
        try:
            return int(value_str)
        except ValueError:
            if not optional:
                reader.raiseError(f"Invalid value for attribute '{name}'.")
            return None

    @staticmethod
    def read_bool_attribute(
        reader: QXmlStreamReader, name: str, optional: bool = False
    ) -> Optional[bool]:
        """读取 XML 元素中的 bool 类型属性。

        Args:
            reader: XML 读取器对象。
            name: 属性名称。
            optional: 是否为可选属性，默认为 False。

        Returns:
            解析后的 bool 值，如果解析失败且属性为可选，则返回 None。

        Raises:
            ValueError: 如果解析失败且属性为必选。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return None
        value_str = str(reader.attributes().value(name))
        try:
            return bool(int(value_str))
        except ValueError:
            if not optional:
                reader.raiseError(f"Invalid value for attribute '{name}'.")
            return None

    @staticmethod
    def read_text_element(reader: QXmlStreamReader) -> str:
        """读取 XML 元素中的文本内容。

        Args:
            reader: XML 读取器对象。

        Returns:
            元素中的文本内容，如果读取失败则返回空字符串。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return ""
        assert reader.isStartElement()
        return reader.readElementText()

    @staticmethod
    def read_named_double(reader: QXmlStreamReader) -> Tuple[str, float]:
        """读取带有 'name' 属性的 double 类型元素。

        Args:
            reader: XML 读取器对象。

        Returns:
            包含元素名称和 double 值的元组。

        Raises:
            ValueError: 如果解析失败。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return "", 0.0
        name = str(reader.attributes().value("name"))
        data = reader.readElementText()
        try:
            return name, float(data)
        except ValueError:
            reader.raiseError(f"Invalid value '{data}' for Double element '{name}'.")
            return "", 0.0

    @staticmethod
    def read_named_integer(reader: QXmlStreamReader) -> Tuple[str, int]:
        """读取带有 'name' 属性的 int 类型元素。

        Args:
            reader: XML 读取器对象。

        Returns:
            包含元素名称和 int 值的元组。

        Raises:
            ValueError: 如果解析失败。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return "", 0
        name = str(reader.attributes().value("name"))
        data = reader.readElementText()
        try:
            return name, int(data)
        except ValueError:
            reader.raiseError(f"Invalid value '{data}' for Integer element '{name}'.")
            return "", 0

    @staticmethod
    def read_named_string(reader: QXmlStreamReader) -> Tuple[str, str]:
        """读取带有 'name' 属性的 string 类型元素。

        Args:
            reader: XML 读取器对象。

        Returns:
            包含元素名称和 string 值的元组。
        """
        if reader.error() != QXmlStreamReader.NoError:
            return "", ""
        name = str(reader.attributes().value("name"))
        value = reader.readElementText()
        return name, value

    @staticmethod
    def encode_point(point: QPointF) -> str:
        """将 QPointF 对象编码为字符串。

        Args:
            point: 需要编码的 QPointF 对象。

        Returns:
            编码后的字符串。
        """
        return f"{point.x()}, {point.y()}"

    @staticmethod
    def decode_point(point_str: str) -> QPointF:
        """将字符串解码为 QPointF 对象。

        Args:
            point_str: 需要解码的字符串。

        Returns:
            解码后的 QPointF 对象。

        Raises:
            ValueError: 如果字符串格式无效。
        """
        parts = point_str.split(",")
        if len(parts) != 2:
            raise ValueError("Invalid format of encoded point.")
        return QPointF(float(parts[0].strip()), float(parts[1].strip()))
