from typing import Union, List, Dict, Set, Optional

from qtpy.QtCore import Qt, QPointF, QSize, QRectF, QLineF
from qtpy.QtCore import Signal
from qtpy.QtGui import QPixmap, QPainter
from qtpy.QtWidgets import QGraphicsScene, QGraphicsItem, QApplication, QGraphicsSceneMouseEvent


# 假设这些类已经在其他地方定义
class Network:
    def __init__(self):
        self.m_blocks = []
        self.m_connectors = []

    def adjustConnector(self, connector):
        pass

    def lookupBlockAndSocket(self, socket_name, block, socket):
        pass


class Block:
    def __init__(self):
        self.m_name = ""
        self.m_pos = QPointF()
        self.m_size = QSize()
        self.m_sockets = []

    def socketStartLine(self, socket):
        return QLineF()


class Socket:
    def __init__(self):
        self.m_name = ""
        self.m_inlet = False
        self.m_orientation = Qt.Horizontal
        self.m_pos = QPointF()

class SocketItem(QGraphicsItem):
    def __init__(self, socket):
        super().__init__()
        self.m_socket = socket
        self.m_isHighlighted = False


class BlockItem(QGraphicsItem):
    def __init__(self, block):
        super().__init__()
        self.m_block = block

    def block(self):
        return self.m_block


class Connector:
    def __init__(self):
        self.m_name = ""
        self.m_sourceSocket = ""
        self.m_targetSocket = ""
        self.m_segments = []


class ConnectorSegmentItem(QGraphicsItem):
    def __init__(self, connector):
        super().__init__()
        self.m_connector = connector
        self.m_segmentIdx = 0
        self.m_isHighlighted = False

    def line(self):
        return QLineF()


class Globals:
    InvisibleLabel = "InvisibleLabel"

    @staticmethod
    def nearZero(value):
        return abs(value) < 1e-6


class SceneManager(QGraphicsScene):
    networkGeometryChanged = Signal()
    newBlockSelected = Signal(str)
    newConnectionAdded = Signal()
    selectionCleared = Signal()
    newConnectorSelected = Signal(str, str)
    blockActionTriggered = Signal(BlockItem)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.m_network: Network = Network()
        self.m_blockItems: List[BlockItem] = []
        self.m_connectorSegmentItems: List[ConnectorSegmentItem] = []
        self.m_blockConnectorMap: Dict[Block, Set[Connector]] = {}
        self.m_currentlyConnecting: bool = False

    def __del__(self) -> None:
        del self.m_network

    def setNetwork(self, network: Network) -> None:
        """设置网络对象，并更新场景中的块和连接器。

        Args:
            network: 需要设置的网络对象。
        """
        self.m_network = network
        for item in self.m_blockItems:
            self.removeItem(item)
        self.m_blockItems.clear()
        for item in self.m_connectorSegmentItems:
            self.removeItem(item)
        self.m_connectorSegmentItems.clear()
        self.m_blockConnectorMap.clear()

        for block in self.m_network.m_blocks:
            item = self.createBlockItem(block)
            self.addItem(item)
            self.m_blockItems.append(item)

        for connector in self.m_network.m_connectors:
            new_conns = self.createConnectorItems(connector)
            for item in new_conns:
                self.addItem(item)
                self.m_connectorSegmentItems.append(item)

        self.m_currentlyConnecting = False

    def network(self) -> Network:
        """获取当前网络对象。

        Returns:
            当前网络对象。
        """
        return self.m_network

    def generatePixmap(self, targetSize: QSize) -> QPixmap:
        """生成当前场景的缩略图。

        Args:
            targetSize: 目标缩略图的大小。

        Returns:
            生成的缩略图。
        """
        r = self.itemsBoundingRect()
        eps = 1.01
        borderSize = 10
        w = targetSize.width()
        h = targetSize.height()
        sourceRect = QRectF()

        if r.width() > r.height():
            m = r.width()
            targetSize.setHeight(r.height() / r.width() * w + 2 * borderSize)
            h = targetSize.height() + 2 * borderSize
            sourceRect = QRectF(r.center().x() - 0.5 * m * eps,
                                r.center().y() - 0.5 * r.height() * eps,
                                eps * m, eps * r.height())
        else:
            m = r.height()
            sourceRect = QRectF(r.center().x() - 0.5 * m * eps,
                                r.center().y() - 0.5 * m * eps,
                                eps * m, eps * m)

        targetRect = QRectF(borderSize, borderSize,
                            w - 2 * borderSize, h - 2 * borderSize)

        pm = QPixmap(targetSize)
        pm.fill(Qt.white)
        painter = QPainter(pm)
        self.render(painter, targetRect, sourceRect)
        painter.end()
        return pm

    def blockItemByName(self, blockName: str) -> Optional[BlockItem]:
        """根据块名称查找对应的块项。

        Args:
            blockName: 块名称。

        Returns:
            如果找到则返回块项，否则返回 None。
        """
        for item in self.m_blockItems:
            if item.m_block.m_name == blockName:
                return item
        return None

    def blockMoved(self, block: Block) -> None:
        """处理块移动后的相关操作。

        当块发生移动时，此函数会被调用，用于更新与该块相关的连接器及其显示。

        Note:
            此函数通常从 BlockItem.itemChange() 事件处理程序中调用。
            在信号处理过程中（例如连接到 networkGeometryChanged() 的槽函数中），切勿调用 setNetwork()，
            否则会导致现有块对象被删除并创建新的块对象，从而导致返回此函数时访问无效内存，引发崩溃。

        Args:
            block: 移动的块对象。
        """
        cons = self.m_blockConnectorMap.get(block, set())
        for con in cons:
            self.m_network.adjustConnector(con)
            self.updateConnectorSegmentItems(con, None)
        self.networkGeometryChanged.emit()

    def blockSelected(self, block: Block) -> None:
        """当块被选中时，触发信号并发送块的名称。

        Args:
            block: 被选中的块对象。
        """
        self.newBlockSelected.emit(block.m_name)

    def connectorSegmentMoved(self, currentItem: ConnectorSegmentItem) -> None:
        """处理连接线段移动事件。

        当连接线段被移动时，更新与该线段相关的所有连接线段项，并发出网络几何变化的信号。

        Args:
            currentItem: 当前被移动的连接线段项。
        """
        self.updateConnectorSegmentItems(currentItem.m_connector, currentItem)
        self.networkGeometryChanged.emit()

    def highlightConnectorSegments(self, con: Connector, highlighted: bool) -> None:
        """高亮或取消高亮连接器中的所有线段。

        Args:
            con: 需要高亮的连接器对象。
            highlighted: 是否高亮，True 为高亮，False 为取消高亮。
        """
        for segmentItem in self.m_connectorSegmentItems:
            if segmentItem.m_connector == con:
                segmentItem.m_isHighlighted = highlighted
                segmentItem.update()
        self.update()

    def selectConnectorSegments(self, con: Connector) -> None:
        """选中连接器的所有线段。

        Args:
            con: 需要选中的连接器对象。
        """
        for segmentItem in self.m_connectorSegmentItems:
            if segmentItem.m_connector == con:
                if not segmentItem.isSelected():
                    segmentItem.setSelected(True)
                segmentItem.update()
        self.update()

    def mergeConnectorSegments(self, con: Connector) -> None:
        """合并连接器的线段。

        Args:
            con: 需要合并线段的连接器对象。
        """
        segmentItems: List[Optional[ConnectorSegmentItem]] = [None] * len(con.m_segments)
        for segmentItem in self.m_connectorSegmentItems:
            if segmentItem.m_connector == con:
                if segmentItem.m_segmentIdx in [-1, -2]:
                    continue
                segmentItems[segmentItem.m_segmentIdx] = segmentItem

        updateSegments: bool = False
        i = 0
        while i < len(segmentItems):
            for i in range(len(segmentItems)):
                segItem = segmentItems[i]
                seg = con.m_segments[i]
                if i > 0 and con.m_segments[i - 1].m_direction == seg.m_direction:
                    con.m_segments[i - 1].m_offset += seg.m_offset
                    seg.m_offset = 0
                    updateSegments = True
                if Globals.nearZero(seg.m_offset):
                    break
            if i == len(segmentItems):
                break

            if i == 0:
                con.m_segments.pop(0)
                segItem = segmentItems.pop(0)
                self.m_connectorSegmentItems.remove(segItem)
                del segItem
                for j in range(len(segmentItems)):
                    segmentItems[j].m_segmentIdx -= 1
            elif i == len(segmentItems) - 1:
                con.m_segments.pop()
                segItem = segmentItems.pop()
                self.m_connectorSegmentItems.remove(segItem)
                del segItem
                i = 0
            else:
                con.m_segments.pop(i)
                segItem = segmentItems.pop(i)
                self.m_connectorSegmentItems.remove(segItem)
                del segItem
                for j in range(i, len(segmentItems)):
                    segmentItems[j].m_segmentIdx -= 1
                if i > 0 and con.m_segments[i - 1].m_direction == con.m_segments[i].m_direction:
                    con.m_segments[i - 1].m_offset += con.m_segments[i].m_offset
                    con.m_segments.pop(i)
                    segItem = segmentItems.pop(i)
                    self.m_connectorSegmentItems.remove(segItem)
                    del segItem
                    for j in range(i, len(segmentItems)):
                        segmentItems[j].m_segmentIdx -= 1
                    updateSegments = True
                i = 0

        if updateSegments:
            self.updateConnectorSegmentItems(con, None)
        QApplication.restoreOverrideCursor()


    def isConnectedSocket(self, b: Block, s: Socket) -> bool:
        """判断一个插槽是否已经连接。

        Args:
            b: 块对象。
            s: 插槽对象。

        Returns:
            如果插槽已经连接则返回 True，否则返回 False。
        """
        conns = self.m_blockConnectorMap.get(b, set())
        for c in conns:
            block, socket = None, None
            self.m_network.lookupBlockAndSocket(c.m_sourceSocket, block, socket)
            if s == socket:
                return True
            self.m_network.lookupBlockAndSocket(c.m_targetSocket, block, socket)
            if s == socket:
                return True
        return False

    def startSocketConnection(self, outletSocketItem: SocketItem, mousePos: QPointF) -> None:
        """开始一个插槽连接。

        当用户点击一个出口插槽时，开始创建连接。创建一个虚拟块和虚拟插槽，
        并初始化连接器。

        Args:
            outletSocketItem: 出口插槽项，表示用户点击的插槽。
            mousePos: 鼠标点击的位置，用于定位虚拟块。
        """
        assert not outletSocketItem.socket().m_inlet

        # 取消所有块和连接线段的选中状态
        for block in self.m_blockItems:
            block.setSelected(False)
        for segmentItem in self.m_connectorSegmentItems:
            segmentItem.setSelected(False)

        # 获取出口插槽的父块和插槽信息
        bitem = outletSocketItem.parentItem()
        assert isinstance(bitem, BlockItem)
        sourceBlock = bitem.block()
        sourceSocket = outletSocketItem.socket()
        startSocketName = f"{sourceBlock.m_name}.{sourceSocket.m_name}"

        # 创建一个虚拟块，用于表示连接的起点
        dummyBlock = Block()
        dummyBlock.m_pos = mousePos
        dummyBlock.m_size = QSizeF(20, 20)
        dummyBlock.m_name = Globals.InvisibleLabel
        dummyBlock.m_connectionHelperBlock = True

        # 创建一个虚拟插槽，用于表示连接的目标
        dummySocket = Socket()
        dummySocket.m_name = Globals.InvisibleLabel
        dummySocket.m_inlet = True
        dummySocket.m_orientation = Qt.Horizontal
        dummySocket.m_pos = QPointF(0, 0)
        dummyBlock.m_sockets.append(dummySocket)

        # 将虚拟块添加到网络中
        self.m_network.m_blocks.append(dummyBlock)

        # 生成虚拟插槽的名称
        targetSocketName = f"{dummyBlock.m_name}.{dummySocket.m_name}"

        # 创建一个连接器，表示从出口插槽到虚拟插槽的连接
        con = Connector()
        con.m_name = Globals.InvisibleLabel
        con.m_sourceSocket = startSocketName
        con.m_targetSocket = targetSocketName
        self.m_network.m_connectors.append(con)

        # 创建虚拟块的图形项，并添加到场景中
        bi = self.createBlockItem(self.m_network.m_blocks[-1])
        bi.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        bi.setPos(dummyBlock.m_pos)
        self.m_blockItems.append(bi)
        self.addItem(bi)

        # 创建连接器的图形项，并添加到场景中
        newConns = self.createConnectorItems(self.m_network.m_connectors[-1])
        for item in newConns:
            self.addItem(item)
            self.m_connectorSegmentItems.append(item)

        # 标记当前正在连接中
        self.m_currentlyConnecting = True

    def finishConnection(self) -> None:
        """完成连接操作。

        如果当前正在连接中，移除虚拟块并结束连接状态。
        """
        if self.m_network.m_blocks and self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel:
            self.removeBlock(len(self.m_network.m_blocks) - 1)
        self.m_currentlyConnecting = False

    def selectedBlocks(self) -> List[Block]:
        """获取当前选中的块对象。

        Returns:
            当前选中的所有块对象列表。
        """
        selected = self.selectedItems()
        selectedBlocks = []
        for item in selected:
            if isinstance(item, BlockItem):
                selectedBlocks.append(item.block())
        return selectedBlocks

    def selectedConnector(self) -> Optional[Connector]:
        """获取当前选中的连接器对象。

        Returns:
            当前选中的连接器对象。如果未选中任何连接器，返回 None。
        """
        selected = self.selectedItems()
        for item in selected:
            if isinstance(item, ConnectorSegmentItem):
                return item.m_connector
        return None

    def addBlock(self, block: Block) -> None:
        """向网络中添加一个新块。

        Args:
            block: 需要添加的块对象。
        """
        self.m_network.m_blocks.append(block)
        item = self.createBlockItem(self.m_network.m_blocks[-1])
        self.addItem(item)
        self.m_blockItems.append(item)

    def addConnector(self, con: Connector) -> None:
        """向网络中添加一个新连接器。

        Args:
            con: 需要添加的连接器对象。

        Raises:
            RuntimeError: 如果源插槽或目标插槽无效，或者目标插槽已经有连接。
        """
        try:
            b1, s1 = None, None
            self.m_network.lookupBlockAndSocket(con.m_sourceSocket, b1, s1)
        except Exception:
            raise RuntimeError("[SceneManager::addConnector] Invalid source socket identifier.")
        try:
            b2, s2 = None, None
            self.m_network.lookupBlockAndSocket(con.m_targetSocket, b2, s2)
        except Exception:
            raise RuntimeError("[SceneManager::addConnector] Invalid target socket identifier.")
        if s1.m_inlet:
            raise RuntimeError("[SceneManager::addConnector] Invalid source socket (must be an outlet socket).")
        if not s2.m_inlet:
            raise RuntimeError("[SceneManager::addConnector] Invalid target socket (must be an inlet socket).")
        if self.isConnectedSocket(b2, s2):
            raise RuntimeError(
                "[SceneManager::addConnector] Invalid target socket (has already an incoming connection).")
        self.m_network.m_connectors.append(con)
        self.m_network.adjustConnector(self.m_network.m_connectors[-1])

    def removeBlock(self, block: Union[Block, int]) -> None:
        """从网络中移除一个块。

        Args:
            block: 需要移除的块对象或其索引。

        Raises:
            RuntimeError: 如果块对象无效或不在网络中。
        """
        if isinstance(block, int):
            blockIndex = block
        else:
            for idx, b in enumerate(self.m_network.m_blocks):
                if b == block:
                    blockIndex = idx
                    break
            else:
                raise RuntimeError("[SceneManager::removeBlock] Invalid pointer (not in managed network)")

        assert len(self.m_network.m_blocks) > blockIndex
        assert len(self.m_blockItems) > blockIndex

        blockToBeRemoved = self.m_network.m_blocks[blockIndex]
        connectors = self.m_blockConnectorMap.get(blockToBeRemoved, set())
        for con in connectors:
            for idx, c in enumerate(self.m_network.m_connectors):
                if c == con:
                    self.m_network.m_connectors.pop(idx)
                    break

        bi = self.m_blockItems[blockIndex]
        self.m_blockItems.pop(blockIndex)
        del bi

        self.m_network.m_blocks.pop(blockIndex)

        for item in self.m_connectorSegmentItems:
            self.removeItem(item)
        self.m_connectorSegmentItems.clear()
        self.m_blockConnectorMap.clear()
        for con in self.m_network.m_connectors:
            self.updateConnectorSegmentItems(con, None)

    def removeConnector(self, con: Union[Connector, int]) -> None:
        """从网络中移除一个连接器。

        Args:
            con: 需要移除的连接器对象或其索引。

        Raises:
            RuntimeError: 如果连接器对象无效或不在网络中。
        """
        if isinstance(con, int):
            connectorIndex = con
        else:
            for idx, c in enumerate(self.m_network.m_connectors):
                if c == con:
                    connectorIndex = idx
                    break
            else:
                raise RuntimeError("[SceneManager::removeConnector] Invalid pointer (not in managed network)")

        assert len(self.m_network.m_connectors) > connectorIndex

        conToBeRemoved = self.m_network.m_connectors[connectorIndex]

        i = 0
        while i < len(self.m_connectorSegmentItems):
            if self.m_connectorSegmentItems[i].m_connector == conToBeRemoved:
                del self.m_connectorSegmentItems[i]
                continue
            i += 1

        for block, conList in self.m_blockConnectorMap.items():
            conList.discard(conToBeRemoved)

        self.m_network.m_connectors.pop(connectorIndex)

    def mousePressEvent(self, mouseEvent) -> None:
        """处理鼠标按下事件。

        如果当前正在连接中，捕获鼠标事件以继续连接操作。

        Args:
            mouseEvent: 鼠标事件对象。
        """
        alreadyInConnectionProcess = (self.m_network.m_blocks and
                                      self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel)
        super().mousePressEvent(mouseEvent)
        inConnectionProcess = (self.m_network.m_blocks and
                               self.m_network.m_blocks[-1].m_name == Globals.InvisibleLabel)
        if not alreadyInConnectionProcess and inConnectionProcess:
            self.m_blockItems[-1].grabMouse()

    def mouseMoveEvent(self, mouseEvent) -> None:
        """处理鼠标移动事件。

        如果当前正在连接中，更新虚拟块的位置，并检查是否有可用的目标插槽。

        Args:
            mouseEvent: 鼠标事件对象。
        """
        if self.m_currentlyConnecting:
            if self.m_blockItems and self.m_blockItems[-1].block().m_name == Globals.InvisibleLabel:
                p = self.m_blockItems[-1].pos()
                for bi in self.m_blockItems:
                    if bi.block().m_name == Globals.InvisibleLabel:
                        continue
                    for si in bi.m_socketItems:
                        si.m_hovered = False
                        si.update()
                    si = bi.inletSocketAcceptingConnection(p)
                    if si and not self.isConnectedSocket(bi.block(), si.socket()):
                        si.m_hovered = True
                        si.update()
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """处理鼠标释放事件。

        如果当前正在连接中，完成连接操作。

        Args:
            mouseEvent: 鼠标事件对象。
        """
        super().mouseReleaseEvent(mouseEvent)
        if mouseEvent.button() & Qt.LeftButton:
            startSocket = ""
            targetSocket = ""

            # 检查是否在连接模式下，并且是否将连接器放置到可连接的插槽上
            if self.m_currentlyConnecting:
                if self.m_blockItems and self.m_blockItems[-1].block().m_name == Globals.InvisibleLabel:
                    p = self.m_blockItems[-1].pos()
                    for bi in self.m_blockItems:
                        if bi.block().m_name == Globals.InvisibleLabel:
                            continue

                        # 查找可以连接的插槽
                        si = bi.inletSocketAcceptingConnection(p)
                        if si and not self.isConnectedSocket(bi.block(), si.socket()):
                            # 找到目标插槽，记录起始插槽和目标插槽
                            startSocket = self.m_network.m_connectors[-1].m_sourceSocket
                            targetSocket = f"{bi.block().m_name}.{si.socket().m_name}"
                            break

            self.finishConnection()

            # 如果找到有效的起始和目标插槽，创建新的连接器
            if startSocket and targetSocket:
                con = Connector()
                con.m_name = "New Connector"
                con.m_sourceSocket = startSocket
                con.m_targetSocket = targetSocket
                self.m_network.m_connectors.append(con)
                self.m_network.adjustConnector(self.m_network.m_connectors[-1])
                self.updateConnectorSegmentItems(self.m_network.m_connectors[-1], None)
                self.newConnectionAdded.emit()
            else:
                # 如果没有选择任何块或连接器，发出清除选择的信号
                block_or_connector_selected = False
                for item in self.m_blockItems:
                    if item.isSelected():
                        block_or_connector_selected = True
                        break
                for item in self.m_connectorSegmentItems:
                    if item.isSelected():
                        block_or_connector_selected = True
                        break
                if not block_or_connector_selected:
                    self.selectionCleared.emit()

    def createBlockItem(self, block: Block) -> BlockItem:
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

    def createConnectorItem(self, con: Connector) -> ConnectorSegmentItem:
        """创建一个连接器线段图形项。

        Args:
            con: 需要创建图形项的连接器对象。

        Returns:
            创建的连接器线段图形项。
        """
        item = ConnectorSegmentItem(con)
        return item

    def createConnectorItems(self, con: Connector) -> List[ConnectorSegmentItem]:
        """为连接器创建所有线段图形项。

        Args:
            con: 需要创建图形项的连接器对象。

        Returns:
            创建的连接器线段图形项列表。
        """
        new_conns: List[ConnectorSegmentItem] = []
        try:
            # 查找源插槽和目标插槽
            socket: Optional[Socket] = None
            block: Optional[Block] = None
            self.m_network.lookupBlockAndSocket(con.m_sourceSocket, block, socket)
            if block and socket:
                self.m_blockConnectorMap.setdefault(block, set()).add(con)
                start_line = block.socketStartLine(socket)

            self.m_network.lookupBlockAndSocket(con.m_targetSocket, block, socket)
            if block and socket:
                self.m_blockConnectorMap.setdefault(block, set()).add(con)
                end_line = block.socketStartLine(socket)

            # 创建起始和结束线段
            item = self.createConnectorItem(con)
            item.setLine(start_line)
            item.setFlags(QGraphicsItem.ItemIsSelectable)
            item.m_segmentIdx = -1  # 起始线段
            new_conns.append(item)

            item = self.createConnectorItem(con)
            item.setLine(end_line)
            item.setFlags(QGraphicsItem.ItemIsSelectable)
            item.m_segmentIdx = -2  # 结束线段
            new_conns.append(item)

            # 创建中间线段
            start = start_line.p2()
            for i, seg in enumerate(con.m_segments):
                item = self.createConnectorItem(con)
                next_point = start + QPointF(seg.m_offset, 0) if seg.m_direction == Qt.Horizontal else start + QPointF(
                    0, seg.m_offset)
                item.setLine(QLineF(start, next_point))
                item.m_segmentIdx = i  # 中间线段
                new_conns.append(item)
                start = next_point

        except Exception as e:
            print(f"Error creating connector items: {e}")
            for item in new_conns:
                item.deleteLater()
            new_conns.clear()

        return new_conns

    def onSelectionChanged(self) -> None:
        """处理选择变化事件。

        如果选择了连接器线段，选中该连接器的所有线段，并发出信号。
        """
        items = self.selectedItems()
        if not items:
            self.selectionCleared.emit()
            return

        # 查找所有选中的连接器
        selected_connectors = set()
        for item in items:
            if isinstance(item, ConnectorSegmentItem):
                selected_connectors.add(item.m_connector)

        # 如果选中了连接器，选中该连接器的所有线段
        if selected_connectors:
            self.clearSelection()
            for item in self.m_connectorSegmentItems:
                if item.m_connector in selected_connectors:
                    item.setSelected(True)
            # 发出信号，表示选中了连接器
            self.newConnectorSelected.emit(
                selected_connectors.pop().m_sourceSocket,
                selected_connectors.pop().m_targetSocket
            )

    def blockDoubleClicked(self, block_item: BlockItem) -> None:
        """处理块双击事件。

        Args:
            block_item: 被双击的块图形项。
        """
        self.blockActionTriggered.emit(block_item)

    def updateConnectorSegmentItems(self, con: Connector, current_item: Optional[ConnectorSegmentItem]) -> None:
        """更新连接器的线段图形项。

        Args:
            con: 需要更新的连接器对象。
            current_item: 当前正在操作的线段图形项。
        """
        start_segment: Optional[ConnectorSegmentItem] = None
        end_segment: Optional[ConnectorSegmentItem] = None
        segment_items: List[ConnectorSegmentItem] = []

        # 查找所有与连接器相关的线段图形项
        for item in self.m_connectorSegmentItems:
            if item.m_connector == con:
                if item.m_segmentIdx == -1:
                    start_segment = item
                elif item.m_segmentIdx == -2:
                    end_segment = item
                else:
                    if current_item is None or item != current_item:
                        segment_items.append(item)

        # 如果找不到任何线段图形项，重新创建
        if start_segment is None and end_segment is None and not segment_items:
            new_conns = self.createConnectorItems(con)
            for item in new_conns:
                self.addItem(item)
                self.m_connectorSegmentItems.append(item)
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
            self.m_connectorSegmentItems.remove(item)
            item.deleteLater()

        # 添加缺失的线段图形项
        for i in range(len(segment_items), items_needed):
            item = self.createConnectorItem(con)
            item.m_isHighlighted = current_item.m_isHighlighted if current_item else False
            self.addItem(item)
            self.m_connectorSegmentItems.append(item)
            segment_items.append(item)

        # 插入当前线段图形项
        if current_item is not None:
            segment_items.insert(current_item.m_segmentIdx, current_item)

        # 确保线段图形项数量与线段数量一致
        assert len(segment_items) == len(con.m_segments)

        # 更新所有线段图形项的几何信息
        try:
            # 更新起始和结束线段
            socket: Optional[Socket] = None
            block: Optional[Block] = None
            self.m_network.lookupBlockAndSocket(con.m_sourceSocket, block, socket)
            if block and socket:
                start_line = block.socketStartLine(socket)
                start_segment.setLine(start_line)

            self.m_network.lookupBlockAndSocket(con.m_targetSocket, block, socket)
            if block and socket:
                end_line = block.socketStartLine(socket)
                end_segment.setLine(end_line)

            # 更新中间线段
            start = start_line.p2()
            for i, seg in enumerate(con.m_segments):
                item = segment_items[i]
                next_point = start + QPointF(seg.m_offset, 0) if seg.m_direction == Qt.Horizontal else start + QPointF(
                    0, seg.m_offset)
                item.setLine(QLineF(start, next_point))
                item.m_segmentIdx = i
                start = next_point

        except Exception as e:
            print(f"Error updating connector segments: {e}")