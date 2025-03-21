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

import locale
import sys
import traceback

from qtpy.QtCore import QMessageLogContext, QtMsgType, qInstallMessageHandler

from BlockModPyDemo.debug_application import DebugApplication
from BlockModPyDemo.dialog_demo import DialogDemo


def q_debug_msg_handler(
    msg_type: QtMsgType, context: QMessageLogContext, msg: str
) -> None:
    """Qt消息处理函数，将消息输出到标准输出。

    Args:
        msg_type: 消息类型（调试/警告/错误等）
        context: 消息上下文信息
        msg: 消息内容
    """
    # 提取C++函数名（去除装饰符号）
    function = context.function.decode("utf-8") if context.function else "unknown"
    if function.startswith('"'):
        function = function[1:-1]
    print(f"[{function}] {msg}")


def main() -> int:
    """应用程序主入口函数。

    Returns:
        应用程序退出代码
    """
    # 初始化调试版应用程序
    app = DebugApplication(sys.argv)

    # 安装消息处理器
    qInstallMessageHandler(q_debug_msg_handler)

    # 区域设置配置
    if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        locale.setlocale(locale.LC_NUMERIC, "C")

    # 字体配置
    font = app.font()
    if sys.platform == "darwin":  # macOS
        font.setPointSize(10)
        app.setDesktopSettingsAware(False)
    elif sys.platform.startswith("linux"):  # Linux/Unix
        font.setPointSize(9)
        app.setDesktopSettingsAware(False)
    elif sys.platform == "win32":  # Windows
        font.setPointSize(8)
    app.setFont(font)

    # 主事件循环
    exit_code = 0
    try:
        # 创建并显示主对话框
        main_dialog = DialogDemo()

        # 窗口显示策略
        if sys.platform == "win32":
            main_dialog.showMaximized()
        else:
            main_dialog.show()

        # 运行事件循环
        exit_code = app.exec_()
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
