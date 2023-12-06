import sys
from PyQt5.QtCore import Qt, QUrl, QTime, QTimer
from PyQt5.QtGui import QColor, QIcon, QFont, QFontDatabase
from PyQt5 import QtGui
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QSlider, QLabel, QListWidget, QListWidgetItem
import os

import ctypes

myappid = 'tsvirko.media.musicplayer.1.0' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

sys.path.append('src/fonts')

class CustomButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # self.normal_style = self.styleSheet()
        self.setStyleSheet("background-color: transparent")
        self.normal_style = self.styleSheet()

class MySlider(QSlider):
    def __init__(self, orientation, media_player):
        super().__init__(orientation)
        self.media_player = media_player

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            position = self.value()
            duration = self.media_player.duration()
            if duration != 0:
                self.media_player.setPosition(round(position * duration / 1000))
        super().mouseReleaseEvent(event)

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None, media_player=None, current_track_label=None, play_pause_button=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.track_mapping = {}
        self.media_player = media_player
        self.current_track_label = current_track_label
        self.play_pause_button = play_pause_button
        self.list_color = QColor(0,0,0)
        self.selected_color = QColor(0,0,0)
        self.prev_order = None

    def update_colors(self, list_color, selected_color):
        self.list_color = list_color
        self.selected_color = selected_color

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order = [self.track_mapping[self.item(i).text()] for i in range(self.count())]
        new_order_unique = []
        for item in new_order:
            if item not in new_order_unique:
                new_order_unique.append(item)
        self.update_playlist_order(new_order_unique)

    def set_track_mapping(self, track_mapping):
        self.track_mapping = track_mapping

    def update_playlist_order(self, new_order):
        if self.media_player is None:
            return
        new_playlist = QMediaPlaylist()
        for index in new_order:
            new_playlist.addMedia(self.media_player.playlist().media(index))

        # Очищаем текущий плейлист и добавляем элементы в новом порядке
        self.media_player.playlist().clear()
        self.play_pause_button.setText('\uec2b')

        for i in range(new_playlist.mediaCount()):
            self.media_player.playlist().addMedia(new_playlist.media(i))
        current_track = self.currentItem()
        
        for index in range(self.count()):
            self.item(index).setForeground(self.list_color)

        current_track.setForeground(self.selected_color)
        self.current_track_label.setText(current_track.text())
        if current_track is not None:
            track_index = self.row(current_track)
            self.media_player.playlist().setCurrentIndex(track_index)
        else:
            self.media_player.playlist().setCurrentIndex(0)

class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Загрузка шрифта для иконок
        font_path = "src/fonts/icons.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)

        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.icons_font = QFont(font_family)
        self.icons_font.setFamily("GolosIcons")  
        self.icons_font.setPointSize(16)

        self.setWindowTitle("Music player by Tsvirko")
        self.setGeometry(100, 100, 600, 400)

        self.current_theme = None

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.playlist = QMediaPlaylist()
        
        self.media_player = QMediaPlayer(self)
        self.media_player.setPlaylist(self.playlist)

        self.current_track_label = QLabel()
        
        self.play_pause_button = CustomButton("\uec2b")
        self.play_pause_button.setFont(self.icons_font)
        
        self.playlist_widget = DraggableListWidget(self, self.media_player, self.current_track_label, self.play_pause_button)
        self.playlist_widget.setStyleSheet("QListWidget { border: none; }")
        self.playlist_widget.setSelectionMode(QListWidget.SingleSelection)
        self.playlist_widget.setFocusPolicy(Qt.NoFocus)

        self.stop_button = CustomButton("\ueb5e")
        self.stop_button.setFont(self.icons_font)
        self.add_button = CustomButton("\uebc1")
        self.add_button.setFont(self.icons_font)
        self.next_button = CustomButton("\uea2d")
        self.next_button.setFont(self.icons_font)
        self.prev_button = CustomButton("\uea28")
        self.prev_button.setFont(self.icons_font)
        self.delete_button = CustomButton("\ueae4")
        self.delete_button.setFont(self.icons_font)

        self.position_slider = MySlider(Qt.Horizontal, self.media_player)
        self.position_slider.setRange(0, 1000)
        self.position_label = QLabel()

        # Создаем вертикальный макет для центрального виджета
        layout = QVBoxLayout(self.central_widget)
        
        self.menu_layout = QHBoxLayout()
        
        self.change_theme_button = CustomButton("\uebfb")
        self.change_theme_button.setFont(self.icons_font)
        
        self.blinded_version_layout = QHBoxLayout()

        self.change_to_blinded_version_button = CustomButton("\ueb2e")
        self.change_to_blinded_version_button.setFont(self.icons_font)

        self.blinded_version_layout.addWidget(self.change_to_blinded_version_button)

        self.menu_layout.addWidget(self.change_theme_button)
        self.menu_layout.addLayout(self.blinded_version_layout)

        layout.addLayout(self.menu_layout)
        
        # Добавляем playlist_widget в вертикальный макет
        layout.addWidget(self.playlist_widget)
        
        # Создаем горизонтальный макет для размещения кнопок
        self.button_layout = QHBoxLayout()
        
        # Добавляем кнопки в горизонтальный макет
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.play_pause_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.add_button)        
        
        # Создаем горизонтальный макет для размещения слайдера и меток
        self.slider_layout = QHBoxLayout()

        # Добавляем QLabel('Sample text') в горизонтальный макет
        self.slider_layout.addWidget(self.current_track_label)

        # Добавляем пространство-распорку в конец макета, чтобы "оттолкнуть" position_label вправо
        self.slider_layout.addStretch()

        # Добавляем position_label в горизонтальный макет
        self.slider_layout.addWidget(self.position_label)
        
        # Создаем вертикальный макет для размещения слайдера и горизонтального макета с метками
        self.position_layout = QVBoxLayout()
        
        # Добавляем слайдер и горизонтальный макет с метками в вертикальный макет
        self.position_layout.addLayout(self.slider_layout)
        self.position_layout.addWidget(self.position_slider)
        
        # Добавляем вертикальный макет с слайдером и метками в вертикальный макет основного окна
        layout.addLayout(self.position_layout)
        
        # Добавляем горизонтальный макет с кнопками в вертикальный макет
        layout.addLayout(self.button_layout)

        # Устанавливаем вертикальный макет как макет центрального виджета
        self.central_widget.setLayout(layout)

        self.play_pause_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.add_button.clicked.connect(self.add_track)
        self.next_button.clicked.connect(self.next_track)
        self.prev_button.clicked.connect(self.prev_track)
        self.delete_button.clicked.connect(self.delete_track)
        self.change_theme_button.clicked.connect(self.change_theme)
        self.change_to_blinded_version_button.clicked.connect(self.change_to_blinded_version)

        self.playlist_widget.itemClicked.connect(self.change_track)
        self.media_player.currentMediaChanged.connect(self.on_media_changed)
             
        self.position_timer = QTimer(self)
        self.position_timer.setInterval(1000)
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start()

        # self.recursively_install_hover_events(self.central_widget)

        self.set_default_theme()

    # def recursively_install_hover_events(self, widget):
    #     if isinstance(widget, CustomButton):
    #         widget.enterEvent = self.onEnterButton
    #         widget.leaveEvent = self.onLeaveButton
    #     if hasattr(widget, 'children'):
    #         for child in widget.children():
    #             self.recursively_install_hover_events(child)

    def on_media_changed(self):
        if self.playlist_widget.count() > 0:
            if self.playlist.currentIndex() < 0:
                self.play_pause_button.setText('\uec2b')
            next_item = self.playlist_widget.item(self.playlist.currentIndex())
            self.change_track(next_item)
                
    def play_pause(self):
        if self.playlist_widget.currentItem() is not None:
            if self.media_player.state() != 1:
                self.media_player.play()
                self.play_pause_button.setText('\uec16')
            else:
                self.play_pause_button.setText('\uec2b')
                self.media_player.pause()

    def stop(self):
        self.play_pause_button.setText('\uec2b')
        self.media_player.stop()

    def add_track(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        
        file_dialog = QFileDialog.getOpenFileNames(self, "Выберите аудиофайл", "", "Аудиофайлы (*.mp3 *.wav *.ogg)", options=options)
        if file_dialog[0]:
            for file in file_dialog[0]:
                media_content = QMediaContent(QUrl.fromLocalFile(file))
                self.playlist.addMedia(media_content)
                file_name = os.path.basename(file)
                self.playlist_widget.addItem(file_name[:file_name.rfind('.')])
            if self.playlist.currentIndex() == -1:
                self.playlist.setCurrentIndex(0)
            track_item = self.playlist_widget.item(self.playlist.currentIndex())
            self.change_track(track_item)
    
    def delete_track(self):
        current_item = self.playlist_widget.currentItem()
        if current_item:
            track_index = self.playlist_widget.row(current_item)
            if track_index != -1:
                self.playlist_widget.takeItem(track_index)
                self.playlist.removeMedia(track_index)
                track_item = self.playlist_widget.item(self.playlist.currentIndex())
                self.change_track(track_item)

    def change_track(self, item):
        if item is None:
            self.current_track_label.setText('')
            self.position_label.setText('')
            self.play_pause_button.setText('\uec2b')
        else:
            for index in range(self.playlist_widget.count()):
                self.playlist_widget.item(index).setForeground(self.list_color)
            self.current_track_label.setText(item.text())
            track_index = self.playlist_widget.row(item)
            self.playlist.setCurrentIndex(track_index)
            item.setForeground(self.selected_color)
            self.playlist_widget.setCurrentItem(item)

    def next_track(self):
        self.playlist.next()
        if self.playlist.currentIndex() != -1:
            next_item = self.playlist_widget.item(self.playlist.currentIndex())
            self.change_track(next_item)

    def prev_track(self):
        self.playlist.previous()
        if self.playlist.currentIndex() != -1:
            prev_item = self.playlist_widget.item(self.playlist.currentIndex())
            self.change_track(prev_item)

    def update_position(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        if duration != 0:
            slider_position = round(position / duration * 1000)
            self.position_slider.setValue(slider_position)
            self.position_label.setText(QTime.fromMSecsSinceStartOfDay(position).toString('mm:ss'))
        # Обновляем порядок треков в playlist_widget и в плейлисте
        self.update_track_mapping()

    def update_track_mapping(self):
        track_mapping = {self.playlist_widget.item(i).text(): i for i in range(self.playlist_widget.count())}
        self.playlist_widget.set_track_mapping(track_mapping)
        self.playlist_widget.media_player = self.media_player

    def change_color_in_layout(self, layout, color):
        for index in range(layout.count()):
            widget_item = layout.itemAt(index)
            if widget_item is not None:
                widget = widget_item.widget()
                if widget is not None:
                    widget.setStyleSheet("color: {}; background-color: transparent;".format(color))

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def change_theme(self):
        if self.current_theme == 'default':
            self.change_theme_button.setText('\ueade')
            self.set_dark_theme()
        elif self.current_theme == 'dark':
            self.change_theme_button.setText('\uebfb')
            self.set_default_theme()
        elif self.current_theme == 'blind default':
            self.change_theme_button.setText('\ueade')
            self.set_blind_dark_theme()
        elif self.current_theme == 'blind dark':
            self.change_theme_button.setText('\uebfb')
            self.set_blind_default_theme()

    def set_theme(self, content_color = "#000000",
                        button_layout_color = None, 
                        menu_layout_color = None, 
                        blinded_version_layout_color = None, 
                        slider_layout_color = None, 
                        bg = "#FFFFFF",
                        list_color = None,
                        selected_color = None):
        if button_layout_color is None:
            button_layout_color = content_color
        if menu_layout_color is None:
            menu_layout_color = content_color
        if blinded_version_layout_color is None:
            blinded_version_layout_color = content_color
        if slider_layout_color is None:
            slider_layout_color = content_color
        if list_color is None:
            list_color = content_color
        if selected_color is None:
            selected_color = content_color
        self.change_color_in_layout(self.button_layout, button_layout_color)
        self.change_color_in_layout(self.menu_layout, menu_layout_color)
        self.change_color_in_layout(self.blinded_version_layout, blinded_version_layout_color)
        self.change_color_in_layout(self.slider_layout, slider_layout_color)
        self.central_widget.setStyleSheet("background-color: {};".format(bg))
        self.playlist_widget.setStyleSheet("border: none;")
        self.list_color = QColor(*self.hex_to_rgb(list_color))
        self.selected_color = QColor(*self.hex_to_rgb(selected_color))
        self.playlist_widget.update_colors(self.list_color, self.selected_color)
        for index in range(self.playlist_widget.count()):
                self.playlist_widget.item(index).setForeground(self.list_color)
        track_item = self.playlist_widget.item(self.playlist.currentIndex())
        if track_item is not None:
            track_item.setForeground(self.selected_color)

    def set_default_theme(self):
        self.current_theme = 'default'
        self.set_theme(content_color='#525760',
                       slider_layout_color='#1D222A',
                       bg='#EAECF0',
                       list_color='#D4D5D9')
    
    def set_dark_theme(self):
        self.current_theme = 'dark'
        self.set_theme(content_color='#AAAEB6',
                       slider_layout_color='#EAECF0',
                       bg='#1D222A',
                       list_color='#525760')
    
    def set_blind_dark_theme(self):
        self.current_theme = 'blind dark'
        self.set_theme(content_color='#FFFFFF',
                       bg="#000000")
    
    def set_blind_default_theme(self):
        self.current_theme = 'blind default'
        self.set_theme()

    def change_font_size_recursive(self, widget, new_font):
        if hasattr(widget, 'setFont'):
            widget.setFont(new_font)
        if hasattr(widget, 'layout'):
            layout = widget.layout()
            if layout is not None:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item.widget() is not None:
                        self.change_font_size_recursive(item.widget(), new_font)
        if hasattr(widget, 'children'):
            for child in widget.children():
                self.change_font_size_recursive(child, new_font)
    
    def change_font_size(self, size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
    
    def change_font_size_16(self):
        new_font = self.font()
        new_font.setPointSize(16)
        self.change_font_size_recursive(self.central_widget, new_font)
        self.place_size_buttons()
        
    def change_font_size_20(self):
        new_font = self.font()
        new_font.setPointSize(20)
        self.change_font_size_recursive(self.central_widget, new_font)
        self.place_size_buttons()
        
    def change_font_size_32(self):
        new_font = self.font()
        new_font.setPointSize(32)
        self.change_font_size_recursive(self.central_widget, new_font)
        self.place_size_buttons()

    def delete_size_buttons(self):
        self.blinded_version_layout.removeWidget(self.size_button_16)
        self.size_button_16.deleteLater()
        self.blinded_version_layout.removeWidget(self.size_button_20)
        self.size_button_20.deleteLater()
        self.blinded_version_layout.removeWidget(self.size_button_32)
        self.size_button_32.deleteLater()
    
    def place_size_buttons(self):
        if self.current_theme == 'blind dark' or self.current_theme == 'blind default':
            self.delete_size_buttons()
        self.size_button_16 = CustomButton('\uea75')
        icons_font_16 = self.icons_font
        icons_font_16.setPointSize(16)
        self.size_button_16.setFont(icons_font_16)
        self.size_button_16.setStyleSheet("background-color: transparent;")
        self.size_button_20 = CustomButton('\uea76')
        icons_font_20 = self.icons_font
        icons_font_20.setPointSize(20)
        self.size_button_20.setFont(icons_font_20)
        self.size_button_20.setStyleSheet("background-color: transparent; font-size: 20;")
        self.size_button_32 = CustomButton('\uea77')
        icons_font_32 = self.icons_font
        icons_font_32.setPointSize(32)
        self.size_button_32.setFont(icons_font_32)
        self.size_button_32.setStyleSheet("background-color: transparent; font-size: 32;")
        self.blinded_version_layout.addWidget(self.size_button_16)
        self.blinded_version_layout.addWidget(self.size_button_20)
        self.blinded_version_layout.addWidget(self.size_button_32)
        self.size_button_16.clicked.connect(self.change_font_size_16)
        self.size_button_20.clicked.connect(self.change_font_size_20)
        self.size_button_32.clicked.connect(self.change_font_size_32)

    def change_to_blinded_version(self):
        if self.current_theme == 'blind default' or self.current_theme == 'blind dark':
            self.delete_size_buttons()
            new_font = self.font()
            new_font.setPointSize(16)
            self.change_font_size_recursive(self.central_widget, new_font)
            self.current_theme = 'dark'
            self.change_theme()
        else:
            self.set_theme()
            self.place_size_buttons()
            self.current_theme = 'blind default'

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font_path = "src/fonts/golos.ttf"
    font_id = QFontDatabase.addApplicationFont(font_path)

    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    custom_font = QFont(font_family)
    custom_font.setFamily("Golos")  
    custom_font.setPointSize(16)

    QApplication.setFont(custom_font)
    
    window = MediaPlayer()
    window.show()

    app.setWindowIcon(QtGui.QIcon('src/fonts/music.ico'))
    window.setWindowIcon(QtGui.QIcon('src/fonts/music.ico'))

    sys.exit(app.exec_())