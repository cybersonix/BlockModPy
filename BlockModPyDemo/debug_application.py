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

import sys
import traceback

from qtpy.QtCore import QEvent, QObject
from qtpy.QtWidgets import QApplication


class DebugApplication(QApplication):
    """用于调试的 QApplication 子类，捕获事件循环中的所有异常。

    该类重写 QApplication 的 notify() 方法，在事件处理过程中捕获并打印异常信息，
    便于调试时追踪问题。

    Attributes:
        继承自 QApplication 的所有属性。

    Examples:
        app = BlockModDemoDebugApplication(sys.argv)
        sys.exit(app.exec_())

    """

    def __init__(self, argv: list) -> None:
        """初始化调试应用程序。

        Args:
            argv (list): 命令行参数列表，通常传递sys.argv。
        """
        super().__init__(argv)

    def notify(self, receiver: QObject, event: QEvent) -> bool:
        """重写事件通知方法以捕获所有异常。

        该方法包装了基类的 notify() 方法，在 try-except 块中执行事件处理，
        捕获并打印任何未处理的异常。

        Args:
            receiver: 接收事件的对象。
            event: 待处理的事件对象。

        Returns:
            bool: 事件处理结果，如果发生异常则返回False。

        Raises:
            不会主动抛出异常，但会捕获并打印所有异常信息。
        """
        try:
            return super().notify(receiver, event)
        except Exception as e:
            # 打印完整异常堆栈信息到标准错误
            traceback.print_exc(file=sys.stderr)
            return False
