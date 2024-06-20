import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QLabel, QWidget, QVBoxLayout, QAction
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from globals import data_queue
from dlp import lyric_lang, getlyric
import queue

class TrayApp(QMainWindow):
    update_label_signal = pyqtSignal(str)
    update_menu_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.initUI()

        # 用來更新GUI線程
        self.gui_thread = QThread()
        self.gui_worker = GuiWorker()
        self.gui_worker.moveToThread(self.gui_thread)
        self.gui_worker.update_label_signal.connect(self.update_label)
        self.gui_worker.update_menu_signal.connect(self.update_menu)
        self.gui_thread.started.connect(self.gui_worker.update_gui)
        self.gui_thread.start()

    def initUI(self):
        self.setWindowTitle('YouTube 字幕程式')

        screen_width = QApplication.primaryScreen().size().width()
        screen_height = QApplication.primaryScreen().size().height()
        window_width = screen_width // 4
        window_height = screen_height // 6
        self.setWindowIcon(QIcon('youtube.png'))
        self.setGeometry(0, screen_height - window_height, window_width, window_height)
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.6)  # 設置透明度，0.0 完全透明，1.0 完全不透明

        # 不設置固定大小，允許窗口大小調整
        # self.setFixedSize(window_width, window_height)  # 如果你需要固定大小，可以設置這行為固定大小

        # 設置中心小部件
        central_widget = QWidget()
        layout = QVBoxLayout()

        # 自定義 QLabel
        self.lyric_text = QLabel('請開啟Youtube', self)
        self.lyric_text.setAlignment(Qt.AlignCenter)
        self.lyric_text.setFont(QFont('Helvetica', 20))
        self.lyric_text.setStyleSheet('background-color: black; color: white;')

        layout.addWidget(self.lyric_text)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 創建系統托盤圖標
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('youtube.png'))  # 將 'icon.png' 替換為你的圖標路徑

        # 創建上下文菜單
        self.tray_menu = QMenu(self)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # 最小化到托盤
        self.tray_icon.activated.connect(self.icon_activated)
        
        # Add Exit App action
        exit_action = QAction("離開App(請勿點擊)", self)
        exit_action.triggered.connect(self.close)  # or you can use sys.exit() if self.close() is not defined
        self.tray_menu.addAction(exit_action)

        # version
        help = QAction("版本 V1.0.1", self)
        help.setEnabled(False)
        self.tray_menu.addAction(help)

        # 啟用窗口拖動
        self._startPos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._startPos = event.pos()

    def mouseMoveEvent(self, event):
        if self._startPos is not None:
            self.move(self.pos() + event.pos() - self._startPos)

    def mouseReleaseEvent(self, event):
        self._startPos = None

    def icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def update_label(self, text):
        self.lyric_text.setText(text)

    def update_menu(self, lyric_lang_list):
        self.tray_menu.clear()
        if lyric_lang_list is not None:
            sub_menu = self.tray_menu.addMenu("選擇語言")
            for lang, sub_url in lyric_lang_list.items():
                action = QAction(lang, self)
                action.triggered.connect(lambda _, l=lang: self.gui_worker.set_language(l))
                sub_menu.addAction(action)
            self.tray_menu.addMenu(sub_menu)
        else:
            print("沒有可用的語言")
    
        # Add Exit App action
        exit_action = QAction("離開App(請勿點擊)", self)
        exit_action.triggered.connect(self.close)  # or you can use sys.exit() if self.close() is not defined
        self.tray_menu.addAction(exit_action)

        # version
        help = QAction("版本 V1.0.1", self)
        help.setEnabled(False)
        self.tray_menu.addAction(help)


class GuiWorker(QObject):
    update_label_signal = pyqtSignal(str)
    update_menu_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__()
        self.select_lang = "ko"  # 初始設置為韓文字幕

    def set_language(self, lang):
        self.select_lang = lang

    def print_subtitle(self, events, time_in_seconds):
        # 遍歷每個事件塊，檢查秒數是否落在事件的時間範圍內
        for event in events:
            start_seconds = event['tStartMs'] / 1000
            end_seconds = (event['tStartMs'] + event['dDurationMs']) / 1000
            if start_seconds <= time_in_seconds + 1.5 <= end_seconds:
                subtitle = event['segs'][0]['utf8']
                return subtitle
        return ''

    def update_gui(self):
        current_url = None
        lyric_content = {}
        lyric_now = []
        update_counter = True
        now_lang = self.select_lang  # Initialize now_lang with the selected language

        while True:
            try:
                current_time, video_id = data_queue.get(timeout=1)
                new_url = video_id

                # 重新獲取字幕列表
                if new_url != current_url:
                    self.update_label_signal.emit("無可用字幕")
                    current_url = new_url
                    lyric_lang_list = lyric_lang(current_url)
                    if lyric_lang_list is not None:
                        self.update_menu_signal.emit(lyric_lang_list)
                        if self.select_lang not in lyric_lang_list.keys():
                            self.select_lang = next(iter(lyric_lang_list))
                        now_lang = self.select_lang  # Update now_lang if select_lang changes
                        sub_url = lyric_lang_list[now_lang]
                        lyric_content = getlyric(sub_url)
                
                # 更新字幕部分
                if lyric_lang_list is not None:
                    # Check if selected language has changed
                    if self.select_lang != now_lang:
                        now_lang = self.select_lang
                        sub_url = lyric_lang_list[now_lang]
                        lyric_content = getlyric(sub_url)

                    lyric = self.print_subtitle(lyric_content, current_time)
                    if lyric not in lyric_now:
                        if len(lyric_now) < 2:
                            lyric_now.append(lyric)
                        else:
                            if update_counter:
                                lyric_now[0] = lyric
                                update_counter = False
                            else:
                                lyric_now[1] = lyric
                                update_counter = True
                        if len(lyric_now) == 1:
                            subtitle_text = lyric_now[0]
                        else:
                            subtitle_text = lyric_now[0] + "\n" + lyric_now[1]
                        self.update_label_signal.emit(subtitle_text)
                else:
                    self.update_label_signal.emit("無可用字幕")

            except queue.Empty:
                continue


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TrayApp()
    ex.show()  # 確保主窗口顯示
    sys.exit(app.exec_())
