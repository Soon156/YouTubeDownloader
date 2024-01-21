import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog
from YouTubeUi import Ui_MainWindow
from DownloadVid import DownloadThread


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.select_path)
        self.pushButton_2.clicked.connect(self.start_download)
        self.checkBox.stateChanged.connect(self.checkbox_state_changed)
        self.progressBar.setValue(0)
        self.file_path = None
        self.dt = None
        self.show()

    def select_path(self):
        self.file_path = QFileDialog.getExistingDirectory(self, "Select Output Folder", '/')
        self.lineEdit_2.setText(self.file_path)

    def update_msg(self, msg):
        if msg:
            self.listWidget.addItem(msg)

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def update_btn(self, value):
        if value == 1:
            self.pushButton_2.setEnabled(True)
        else:
            self.pushButton_2.setEnabled(False)

    def checkbox_state_changed(self, state):
        if state:
            self.comboBox.setEnabled(False)
        else:
            self.comboBox.setEnabled(True)

    def start_download(self):
        self.listWidget.clear()
        self.progressBar.setValue(0)

        url = self.lineEdit.text()
        url_list = url.split(',')

        self.file_path = self.lineEdit_2.text()
        mp3 = self.checkBox.isChecked()
        index = self.comboBox.currentIndex()

        self.dt = DownloadThread(url_list, self.file_path, mp3, index)
        self.dt.finish.connect(self.update_btn)
        self.dt.msg.connect(self.update_msg)
        self.dt.progress.connect(self.update_progress)
        self.dt.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.setWindowTitle('YouTube Video Downloader')
    app.exec()
