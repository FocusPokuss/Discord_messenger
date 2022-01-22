from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QMenu, QAction,
                             QSystemTrayIcon, QStyle, QGridLayout, QLabel, QLineEdit, QListWidgetItem, QTextEdit,
                             QMessageBox)
from PyQt5.QtCore import QEvent, QRect
from PyQt5.QtGui import QFont
from worker import send_message, futures, loop
from data_api import load_data, tokens_data, save_data

import asyncio
import sys

WIDTH = 800
HEIGHT = 500


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        load_data()
        self.setFixedWidth(WIDTH)
        self.setFixedHeight(HEIGHT)
        self.setWindowOpacity(1)
        self.setStyleSheet("background-color: rgb(108, 122, 137)")
        self.token_label = QLabel('token:', self)
        self.delay_label = QLabel('delay:', self)
        self.chat_id_label = QLabel('chat_id:', self)
        self.proxy_label = QLabel('proxy:', self)
        self.pos_b4_minimize = self.pos()
        self.start_btn = self.create_start_button()
        self.add_token_window = AddTokenWindow(self)
        self.tray_menu = self.create_tray()
        self.edit_global_messages_window = EditGlobalMessagesWindow(self)
        self.edit_explicit_messages_window = EditExplicitMessagesWindow(self)
        self.active_tokens_list = self.create_info_about_token()
        self.add_tokens_btn = self.create_add_tokens_btn()
        self.load_tokens()

    def load_tokens(self):
        for alias in tokens_data:
            if alias == '!global_messages!':
                continue
            item = QListWidgetItem(alias)
            item.setCheckState(2)
            self.active_tokens_list.addItem(item)

    def create_add_tokens_btn(self):
        btn = QPushButton('add tokens', self)
        btn.move(WIDTH//2+100, 75)
        btn.clicked.connect(self.add_token_window.show_window)
        return btn

    def create_start_button(self):
        button = QPushButton('Start', self)
        button.setCheckable(True)
        button.move(WIDTH // 2 - 200, HEIGHT - 50)
        button.setStyleSheet('background-color: gold')
        button.clicked.connect(self.start)
        return button

    def create_tray(self):
        tray_menu = QSystemTrayIcon(self)
        tray_menu.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        exit_ = QAction('Exit', self)
        exit_.triggered.connect(self.close)
        menu = QMenu()
        menu.addAction(exit_)
        tray_menu.activated.connect(self.release_from_tray)
        tray_menu.setContextMenu(menu)
        tray_menu.show()
        return tray_menu

    def create_info_about_token(self):
        grid = QGridLayout()
        btn_grid = QGridLayout()
        label_grid = QGridLayout()

        list_widget = QListWidget(self)
        list_widget.setFont(QFont('Comic Sans Ms', 10))
        list_widget.itemPressed.connect(lambda e: self.update_token_labels(e.text()))

        label_grid.addWidget(self.token_label, 0, 0)
        label_grid.addWidget(self.chat_id_label, 1, 0)
        label_grid.addWidget(self.proxy_label, 2, 0)
        label_grid.addWidget(self.delay_label, 3, 0)

        stop_btn = QPushButton('stop', self)
        run_btn = QPushButton('run', self)
        edit_btn = QPushButton('edit', self)
        delete_btn = QPushButton('delete', self)
        edit_explicit_messages_btn = QPushButton('explicit messages', self)
        edit_global_messages_btn = QPushButton('global messages', self)
        delete_btn.clicked.connect(self.delete_alias)
        edit_btn.clicked.connect(self.edit_alias)
        edit_global_messages_btn.clicked.connect(self.edit_global_messages_window.show_window)
        edit_explicit_messages_btn.clicked.connect(self.edit_explicit_messages_window.show_window)

        btn_grid.addWidget(stop_btn, 1, 1)
        btn_grid.addWidget(run_btn, 1, 0)
        btn_grid.addWidget(edit_btn, 2, 0)
        btn_grid.addWidget(delete_btn, 2, 1)
        btn_grid.addWidget(edit_explicit_messages_btn, 3, 0)
        btn_grid.addWidget(edit_global_messages_btn, 3, 1)

        grid.addWidget(list_widget)
        grid.addLayout(btn_grid, 1, 0)
        grid.addLayout(label_grid, 2, 0)
        grid.setGeometry(QRect(WIDTH - 300, HEIGHT - 400, 300, 370))
        return list_widget

    def release_from_tray(self, event):
        if event == 3:
            self.move(0, 0)
            self.showMaximized()
            self.activateWindow()

    def delete_alias(self):
        item: QListWidgetItem = self.active_tokens_list.selectedItems()
        if item:
            alias = self.active_tokens_list.takeItem(self.active_tokens_list.row(item[0])).text()
            del tokens_data[alias]

    def edit_alias(self):
        item: QListWidgetItem = self.active_tokens_list.selectedItems()
        if item:
            data = tokens_data[item[0].text()]
            self.add_token_window.alias_line.setText(item[0].text())
            self.add_token_window.token_line.setText(data['token'])
            self.add_token_window.chat_id_line.setText(data['chat_id'])
            self.add_token_window.proxy_line.setText(data['proxy'])
            self.add_token_window.delay_line.setText(data['delay'])
            self.add_token_window.show_window(True)

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.pos_b4_minimize = self.pos()
                self.hide()
            else:
                self.move(self.pos_b4_minimize)

    def closeEvent(self, event):
        print('exit')
        save_data()

    def start(self, state):
        if state:
            self.start_btn.setText('Stop')
            self.active_tokens_list.clearSelection()
            self.active_tokens_list.setDisabled(True)
            for i in range(self.active_tokens_list.count()):
                item = self.active_tokens_list.item(i)
                if item.checkState():
                    item_text = item.text()
                    messages = tokens_data[item_text].get('messages') or self.global_messages
                    futures.setdefault(item_text, asyncio.run_coroutine_threadsafe(send_message(
                        token=tokens_data[item_text]['token'],
                        chat_id=tokens_data[item_text]['chat_id'],
                        delay=tokens_data[item_text]['delay'],
                        proxy=tokens_data[item_text]['proxy'],
                        message_pool=messages
                    ), loop))

        else:
            self.start_btn.setText('Start')
            self.active_tokens_list.setDisabled(False)
            for fut in futures.copy():
                futures.pop(fut).cancel()

    def update_token_labels(self, alias):
        self.token_label.setText(f"token: {tokens_data[alias]['token']}")
        self.chat_id_label.setText(f"chat_id: {tokens_data[alias]['chat_id']}")
        self.proxy_label.setText(f"proxy: {tokens_data[alias]['proxy']}")
        self.delay_label.setText(f"delay: {tokens_data[alias]['delay']}")


class AddTokenWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setFixedWidth(450)
        self.setFixedHeight(200)

        self.alias_line = QLineEdit('', self)
        self.token_line = QLineEdit('', self)
        self.chat_id_line = QLineEdit('', self)
        self.proxy_line = QLineEdit('', self)
        self.delay_line = QLineEdit('', self)

        self.add_btn = QPushButton('add', self)

        self.grid = self.create_grid()
        self.main_window = main_window

    def create_grid(self):
        grid = QGridLayout()
        btn_grid = QGridLayout()

        alias_label = QLabel('alias:', self)
        token_label = QLabel('token:', self)
        chat_id_label = QLabel('chat_id:', self)
        proxy_label = QLabel('proxy:', self)
        delay_label = QLabel('delay:', self)

        save_btn = QPushButton('save', self)

        self.add_btn.pressed.connect(lambda: self.add_token(self.alias_line,
                                                            self.token_line,
                                                            self.chat_id_line,
                                                            self.delay_line,
                                                            self.proxy_line))

        btn_grid.addWidget(self.add_btn, 5, 0)
        btn_grid.addWidget(save_btn, 5, 1)

        grid.addWidget(alias_label, 0, 0)
        grid.addWidget(token_label, 1, 0)
        grid.addWidget(chat_id_label, 2, 0)
        grid.addWidget(proxy_label, 3, 0)
        grid.addWidget(delay_label, 4, 0)
        grid.addWidget(self.alias_line, 0, 1)
        grid.addWidget(self.token_line, 1, 1)
        grid.addWidget(self.chat_id_line, 2, 1)
        grid.addWidget(self.proxy_line, 3, 1)
        grid.addWidget(self.delay_line, 4, 1)

        grid.setGeometry(QRect(0, 0, 500, 500))
        grid.addLayout(btn_grid, 5, 1)
        self.setLayout(grid)
        return grid

    def show_window(self, update=False):
        self.main_window.active_tokens_list.setDisabled(True)
        if update:
            self.add_btn.setText('update')
        else:
            self.add_btn.setText('add')
        self.show()

    def closeEvent(self, event):
        self.main_window.active_tokens_list.setDisabled(False)

    def add_token(self, *args):
        prev_alias = None
        is_update = self.add_btn.text() == 'update'
        if is_update:
            prev_alias = self.main_window.active_tokens_list.selectedItems()
            if prev_alias:
                prev_alias = prev_alias[0].text()
            self.close()
        else:
            self.add_btn.setText('add')

        for arg in args[:4]:
            if not arg.text():
                arg.setStyleSheet('background-color: red')
                break
            else:
                arg.setStyleSheet('background-color: white')
        else:
            data = [arg.text() for arg in args]
            alias, token, chat_id, delay, *proxy = data
            proxy = proxy[0]
            messages = []

            if prev_alias:
                messages = tokens_data[prev_alias]['messages']

            new_token = {'token': token, 'chat_id': chat_id, 'delay': delay, 'proxy': proxy, 'messages': messages}

            for arg in args:
                arg.setText('')

            if is_update:
                selected: QListWidgetItem = self.main_window.active_tokens_list.selectedItems()[0]
                del tokens_data[selected.text()]
                tokens_data.update({alias: new_token})
                selected.setText(alias)
            else:
                qwerty = tokens_data.get(alias)
                if qwerty:
                    warn = QMessageBox()
                    warn.setIcon(QMessageBox.Critical)
                    warn.setGeometry(QRect(self.pos().x()+50, self.pos().y(), 100, 50))
                    warn.setWindowTitle('Wrong alias')
                    warn.setInformativeText(f"'{alias}' is already exists!")
                    warn.exec_()
                    return
                tokens_data[alias] = new_token
                item = QListWidgetItem()
                item.setCheckState(2)
                item.setText(alias)
                self.main_window.active_tokens_list.addItem(item)

            self.main_window.update_token_labels(alias)


class EditGlobalMessagesWindow(QWidget):
    def __init__(self, window):
        super().__init__()
        self.main_window = window
        self.setFixedWidth(600)
        self.setFixedHeight(600)
        self.grid = QGridLayout(self)
        self.m_box = self.create_messages_box()
        self.message_list = self.create_message_list()

    def create_messages_box(self):
        btn_grid = QGridLayout(self)
        m_box = QTextEdit(self)

        add_btn = QPushButton('add', self)
        delete_btn = QPushButton('delete', self)

        add_btn.pressed.connect(self.add_message)
        delete_btn.pressed.connect(self.delete_message)

        btn_grid.addWidget(add_btn, 1, 0)
        btn_grid.addWidget(delete_btn, 1, 1)
        self.grid.addWidget(m_box, 2, 0, 2, 0)
        self.grid.addLayout(btn_grid, 1, 0)
        return m_box

    def create_message_list(self):
        list_widget = QListWidget(self)
        global_messages = tokens_data.get('!global_messages!')
        if global_messages:
            list_widget.addItems(global_messages)
        self.grid.addWidget(list_widget, 0, 0)
        return list_widget

    def show_window(self):
        self.main_window.active_tokens_list.setDisabled(True)
        self.show()

    def closeEvent(self, event):
        self.main_window.active_tokens_list.setDisabled(False)

    def add_message(self):
        text = self.m_box.toPlainText()
        self.message_list.addItem(text)
        tokens_data['!global_messages!'].append(text)
        self.m_box.clear()

    def delete_message(self):
        selected = self.message_list.selectedItems()
        if selected:
            index = self.message_list.row(selected[0])
            del tokens_data['!global_messages!'][index]
            self.message_list.takeItem(index)


class EditExplicitMessagesWindow(EditGlobalMessagesWindow):
    def __init__(self, window):
        super().__init__(window)
        self.message_list = self.create_dynamic_message_list()

    def create_message_list(self):
        pass

    def create_dynamic_message_list(self):
        list_widget = QListWidget(self)
        self.grid.addWidget(list_widget, 0, 0)
        return list_widget

    def show_window(self):
        raw = self.main_window.active_tokens_list.selectedItems()
        if raw:
            self.main_window.active_tokens_list.setDisabled(True)
            data = tokens_data[raw[0].text()].get('messages')
            if data:
                self.message_list.addItems(data)
        self.show()

    def closeEvent(self, event):
        self.main_window.active_tokens_list.setDisabled(False)
        self.message_list.clear()

    def add_message(self):
        alias = self.main_window.active_tokens_list.selectedItems()[0].text()
        text = self.m_box.toPlainText()
        self.message_list.addItem(text)
        messages = tokens_data[alias].get('messages')
        if not messages:
            tokens_data[alias]['messages'] = []
        tokens_data[alias]['messages'].append(text)
        self.m_box.clear()

    def delete_message(self):
        selected = self.message_list.selectedItems()
        if selected:
            index = self.message_list.row(selected[0])
            del tokens_data[self.main_window.active_tokens_list.selectedItems()[0].text()]['messages'][index]
            self.message_list.takeItem(index)


def create_app():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

