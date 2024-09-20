import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QPushButton,
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint
import datetime
import os


class CustomLabel(QLabel):
    def __init__(self, parent=None):
        super(CustomLabel, self).__init__(parent)
        self.selection_rect = QRect()
        self.dragging = False
        self.resizing = False
        self.resize_borders = [0, 0, 0, 0]  # 上下左右边框大小
        self.selecting = False
        self.selecting_start = QPoint()
        self.moving = False
        self.moving_offset = QPoint()
        self.setCursor(Qt.CrossCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.selection_rect.isNull() and self.selection_rect.contains(
                event.pos()
            ):
                border_size = 5
                if (
                    event.pos().x() >= self.selection_rect.right() - border_size
                    and event.pos().x() <= self.selection_rect.right() + border_size
                ):
                    self.resize_borders[1] = 1  # 右边框
                    self.setCursor(Qt.SizeHorCursor)
                    self.resizing = True
                elif event.pos().x() <= self.selection_rect.left() + border_size:
                    self.resize_borders[3] = 1  # 左边框
                    self.setCursor(Qt.SizeHorCursor)
                    self.resizing = True
                elif event.pos().y() >= self.selection_rect.bottom() - border_size:
                    self.resize_borders[2] = 1  # 下边框
                    self.setCursor(Qt.SizeVerCursor)
                    self.resizing = True
                elif event.pos().y() <= self.selection_rect.top() + border_size:
                    self.resize_borders[0] = 1  # 上边框
                    self.setCursor(Qt.SizeVerCursor)
                    self.resizing = True
                else:
                    self.moving = True
                    self.moving_offset = event.pos() - self.selection_rect.topLeft()
            else:
                self.selecting = True
                self.selection_rect = QRect(
                    event.pos(), event.pos()
                )  # 初始化起点为鼠标位置
                self.selecting_start = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting and event.buttons() & Qt.LeftButton:
            self.selection_rect.setBottomRight(event.pos())
            self.update()
        elif self.resizing and event.buttons() & Qt.LeftButton:
            if self.resize_borders[0]:  # 上边框
                self.selection_rect.setTop(event.pos().y())
            if self.resize_borders[1]:  # 右边框
                self.selection_rect.setRight(event.pos().x())
            if self.resize_borders[2]:  # 下边框
                self.selection_rect.setBottom(event.pos().y())
            if self.resize_borders[3]:  # 左边框
                self.selection_rect.setLeft(event.pos().x())
            self.update()
        elif self.moving and event.buttons() & Qt.LeftButton:
            self.selection_rect.moveTo(event.pos() - self.moving_offset)
            self.update()
        scroll_margin = 20
        cursor_pos = event.pos()
        area = self.parent().parent().viewport().rect()

        # 向右滚动
        if cursor_pos.x() > area.width() - scroll_margin:
            self.parent().parent().horizontalScrollBar().setValue(
                self.parent().parent().horizontalScrollBar().value() + scroll_margin
            )

        # 向下滚动
        elif cursor_pos.y() > area.height() - scroll_margin:
            self.parent().parent().verticalScrollBar().setValue(
                self.parent().parent().verticalScrollBar().value() + scroll_margin
            )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.selecting:
                self.selecting = False
            if self.resizing:
                self.resizing = False
            if self.moving:
                self.moving = False
            self.update()

    def paintEvent(self, event):
        super(CustomLabel, self).paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
        painter.drawRect(self.selection_rect)

        if not self.selection_rect.isNull():
            center = self.selection_rect.center()
            x, y = center.x(), center.y()
            painter.drawLine(
                QPoint(x, self.selection_rect.top()),
                QPoint(x, self.selection_rect.bottom()),
            )
            painter.drawLine(
                QPoint(self.selection_rect.left(), y),
                QPoint(self.selection_rect.right(), y),
            )

            # 绘制调整大小的标记
            border_size = 5
            painter.fillRect(
                self.selection_rect.right() - border_size,
                self.selection_rect.top(),
                border_size,
                self.selection_rect.height(),
                Qt.red,
            )
            painter.fillRect(
                self.selection_rect.left(),
                self.selection_rect.top(),
                border_size,
                self.selection_rect.height(),
                Qt.red,
            )
            painter.fillRect(
                self.selection_rect.left(),
                self.selection_rect.bottom() - border_size,
                self.selection_rect.width(),
                border_size,
                Qt.red,
            )
            painter.fillRect(
                self.selection_rect.left(),
                self.selection_rect.top(),
                self.selection_rect.width(),
                border_size,
                Qt.red,
            )

    def save_template_image(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"template_image_{timestamp}.bmp"
        pixmap = self.pixmap()
        if pixmap and not self.selection_rect.isNull():
            x = self.selection_rect.x()
            y = self.selection_rect.y()
            width = self.selection_rect.width()
            height = self.selection_rect.height()

            # 从pixmap中裁剪选择区域
            cropped_pixmap = pixmap.copy(x, y, width, height)

            # 将裁剪后的QPixmap保存为临时文件
            temp_file_path = os.path.join(os.getcwd(), "temp.bmp")
            cropped_pixmap.save(temp_file_path)

            # 读取临时文件
            cropped_image_cv = cv2.imread(temp_file_path)

            if cropped_image_cv is not None:
                # 使用时间戳作为文件名的一部分
                cv2.imwrite(filename, cropped_image_cv)

            os.remove(temp_file_path)


class ImageViewer(QMainWindow):
    def __init__(self, img):
        super(ImageViewer, self).__init__()

        self.img = img

        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.image_label = CustomLabel()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        self.save_button = QPushButton("保存图片")
        self.save_button.clicked.connect(self.image_label.save_template_image)

        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.save_button)
        self.setCentralWidget(self.central_widget)

        self.set_image(self.img)

    def set_image(self, img):
        height, width, channel = img.shape
        qImg = QImage(img.data, width, height, width * channel, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qImg)

        scroll_area_size = self.scroll_area.viewport().size()

        if width > scroll_area_size.width() or height > scroll_area_size.height():
            self.image_label.setPixmap(pixmap)
            self.image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        else:
            scale_factor = 2  # 放大的比例因子
            scaled_pixmap = pixmap.scaled(
                width * scale_factor,
                height * scale_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled_pixmap)

        # 确保图片居中显示
        self.image_label.setAlignment(Qt.AlignCenter)


if __name__ == "__main__":
    img_path = r"941.bmp"
    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)

    app = QApplication([])
    viewer = ImageViewer(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    viewer.show()
    app.exec_()
