import sys
import os
import random
from PyQt5.QtCore import Qt, QPoint, QTimer, QRectF
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction

def get_resource_path(relative_path):
    """ 获取文件的绝对路径（兼容 PyInstaller 打包后的临时目录） """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

DIALOGUES = [
    "汪！今天也要开心哦！",
    "不要一直摸人家啦~",
    "你在偷懒对不对？",
    "需要我陪你加班吗？",
    "饿了，想吃小骨头！",
    "晃得我头好晕呀~",
    "干贴贴！快带我出去玩！",
    "你是在拖拽我去哪里？"
]

class SpeechBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.text = ""
        self.hide()
        
    def set_text(self, text):
        self.text = text
        self.adjustSize()
        self.update()

    def paintEvent(self, event):
        if not self.text:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(5, 5, self.width() - 10, self.height() - 15)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        arrow_bottom = self.height() - 5
        arrow_top = self.height() - 15
        center_x = self.width() / 2
        path.moveTo(center_x - 6, arrow_top)
        path.lineTo(center_x, arrow_bottom)
        path.lineTo(center_x + 6, arrow_top)

        painter.setBrush(QColor(255, 255, 255, 230))
        painter.setPen(QPen(QColor(100, 100, 100, 200), 1.5))
        painter.drawPath(path)

        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(rect, Qt.AlignCenter, self.text)

class DesktopPet(QWidget):
    def __init__(self, image_name="pet.png"):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 使用兼容路径加载图片
        image_path = get_resource_path(image_name)
        self.original_pixmap = QPixmap(image_path)
        
        if self.original_pixmap.isNull():
            # 备用方案：尝试在同级目录下寻找图片
            self.original_pixmap = QPixmap(image_name)
            if self.original_pixmap.isNull():
                sys.exit(1)

        self.scale_factor = 0.25
        self.is_topmost = True

        self.is_dragging = False
        self.drag_position = QPoint()
        self.action_index = 0
        self.animation_step = 0
        self.drag_step = 0
        self.current_action = "jump"

        self.squash_factor = 1.0
        self.offset_y = 0
        self.offset_x = 0
        self.rotation = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(30)

        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.hide_speech_bubble)

        self.bubble = SpeechBubble()
        self.update_pet_size()

    def update_pet_size(self):
        w = int(self.original_pixmap.width() * self.scale_factor)
        h = int(self.original_pixmap.height() * self.scale_factor)
        self.setFixedSize(w + 40, h + 40)
        self.update()
        self.update_bubble_position()

    def update_bubble_position(self):
        if self.bubble.isVisible():
            pet_pos = self.pos()
            bubble_x = pet_pos.x() + (self.width() - self.bubble.width()) // 2
            bubble_y = pet_pos.y() - self.bubble.height() + 5
            self.bubble.move(bubble_x, bubble_y)

    def show_speech_bubble(self, text=None):
        if not text:
            text = random.choice(DIALOGUES)
        self.bubble.set_text(text)
        self.bubble.resize(max(120, len(text) * 14), 45)
        self.update_bubble_position()
        self.bubble.show()
        self.bubble_timer.start(3000)

    def hide_speech_bubble(self):
        self.bubble.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.original_pixmap.width() * self.scale_factor
        h = self.original_pixmap.height() * self.scale_factor

        painter.save()
        center_x = self.width() / 2 + self.offset_x
        center_y = self.height() / 2 + self.offset_y
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation)

        scaled_w = w * (2.0 - self.squash_factor)
        scaled_h = h * self.squash_factor
        
        target_rect = QRectF(-scaled_w / 2, -scaled_h / 2, scaled_w, scaled_h)
        painter.drawPixmap(target_rect, self.original_pixmap, QRectF(self.original_pixmap.rect()))
        painter.restore()

    def update_animation(self):
        if self.is_dragging:
            self.drag_step += 1
            self.rotation = (self.drag_step % 6 - 3) * 3
            self.offset_y = (self.drag_step % 4 - 2) * 2
            self.update()
            self.update_bubble_position()
            return

        if self.animation_step > 0:
            self.animation_step -= 1

            if self.current_action == "jump":
                progress = (30 - self.animation_step) / 30.0
                if progress < 0.5:
                    self.offset_y = -40 * (progress * 2)
                else:
                    self.offset_y = -40 * ((1 - progress) * 2)

            elif self.current_action == "squash":
                if self.animation_step > 15:
                    self.squash_factor = 0.6 + (30 - self.animation_step) * 0.02
                else:
                    self.squash_factor = 0.9 + (15 - self.animation_step) * 0.01

            elif self.current_action == "shake":
                self.rotation = (self.animation_step % 4 - 2) * 4

            self.update()
        else:
            self.offset_x = 0
            self.offset_y = 0
            self.squash_factor = 1.0
            self.rotation = 0
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            self.update_bubble_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_dragging and (event.globalPos() - self.drag_position - self.pos()).manhattanLength() < 5:
                self.trigger_next_interaction()
            
            self.is_dragging = False
            self.rotation = 0
            self.update()
            event.accept()

    def trigger_next_interaction(self):
        actions = ["jump", "squash", "shake"]
        self.current_action = actions[self.action_index]
        self.action_index = (self.action_index + 1) % len(actions)
        self.animation_step = 30
        self.show_speech_bubble()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor = min(self.scale_factor * 1.1, 1.0)
        else:
            self.scale_factor = max(self.scale_factor * 0.9, 0.1)
        self.update_pet_size()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        resize_menu = menu.addMenu("📏 调整大小")
        size_large = QAction("大 (150%)", self)
        size_medium = QAction("中 (100%)", self)
        size_small = QAction("小 (50%)", self)

        size_large.triggered.connect(lambda: self.set_preset_scale(0.35))
        size_medium.triggered.connect(lambda: self.set_preset_scale(0.25))
        size_small.triggered.connect(lambda: self.set_preset_scale(0.15))

        resize_menu.addAction(size_large)
        resize_menu.addAction(size_medium)
        resize_menu.addAction(size_small)

        topmost_action = QAction("📌 窗口置顶", self, checkable=True)
        topmost_action.setChecked(self.is_topmost)
        topmost_action.triggered.connect(self.toggle_topmost)
        menu.addAction(topmost_action)

        menu.addSeparator()

        exit_action = QAction("❌ 退出程序", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)

        menu.exec_(event.globalPos())

    def set_preset_scale(self, scale):
        self.scale_factor = scale
        self.update_pet_size()

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.is_topmost)
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet("pet.png")
    pet.show()
    sys.exit(app.exec_())
