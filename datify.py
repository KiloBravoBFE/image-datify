import sys
import os
import re
import datetime
import platform

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QCoreApplication

IS_WINDOWS = platform.system() == "Windows"
if (IS_WINDOWS): # good luck, I don't have a Windows machine I want to test this on o7
    try:
        import win32file
        import win32con
    except ImportError:
        IS_WINDOWS = False

FILENAME_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})"), "%Y-%m-%d at %H.%M.%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2} at \d{2}-\d{2}-\d{2})"), "%Y-%m-%d at %H-%M-%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}-\d{2}\d{2}\d{2})"), "%Y-%m-%d-%H%M%S"),

    (re.compile(r"(\d{8})_(\d{6})"), "%Y%m%d%H%M%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})"), "%Y-%m-%d%H-%M-%S"),
    (re.compile(r"IMG_(\d{8})_(\d{6})"), "%Y%m%d%H%M%S"),
]

def extract_datetime(filename):
    # Try to parse knoqn patterns
    for pattern, fmt in FILENAME_PATTERNS:
        m = pattern.search(filename)
        if (not m):
            continue
        try:
            if (m.lastindex == 2):
                s = f"{m.group(1)}{m.group(2)}"
            else:
                s = m.group(1)
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Timestamp Editor")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Image Timestamp Editor")
        header.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(header)

        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select image folder…")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Image", "Extracted Date", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.modify_checkbox = QCheckBox("Change Modified & Accessed time")
        self.modify_checkbox.setChecked(True)
        self.created_checkbox = QCheckBox("Change Created time (Windows only)")
        self.created_checkbox.setEnabled(IS_WINDOWS)
        layout.addWidget(self.modify_checkbox)
        layout.addWidget(self.created_checkbox)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.apply_btn = QPushButton("Apply Timestamp Changes")
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.clicked.connect(self.apply_changes)
        layout.addWidget(self.apply_btn)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if (folder):
            if ("/gvfs/mtp:" in folder):
                QMessageBox.warning(
                    self,
                    "MTP Device Detected",
                    "Android devices do not support changing timestamps directly.\n"
                    "Please copy the images to your computer first."
                )
                return
            self.folder_edit.setText(folder)
            self.load_images(folder)

    def load_images(self, folder):
        self.table.setRowCount(0)
        for filename in sorted(os.listdir(folder)):
            if (not filename.lower().endswith((".jpg", ".jpeg", ".png", ".jxl", ".cr2"))):
                continue

            dt = extract_datetime(filename)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(filename))

            if (dt is None):
                self.table.setItem(row, 1, QTableWidgetItem("—"))
                status_item = QTableWidgetItem("Invalid")
                status_item.setForeground(Qt.red)
            else:
                self.table.setItem(row, 1, QTableWidgetItem(dt.strftime("%Y-%m-%d %H:%M:%S")))

                path = os.path.join(folder, filename)
                try:
                    # Compare current modified time with filename date
                    current_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    if (current_mtime.replace(microsecond=0)) == dt:
                        status_item = QTableWidgetItem("OK")
                        status_item.setForeground(Qt.green)
                    else:
                        status_item = QTableWidgetItem("Change")
                        status_item.setForeground(Qt.yellow)
                except Exception:
                    status_item = QTableWidgetItem("Change")
                    status_item.setForeground(Qt.yellow)

            self.table.setItem(row, 2, status_item)

    def apply_changes(self):
        folder = self.folder_edit.text()
        if (not os.path.isdir(folder)):
            QMessageBox.warning(self, "Error", "Invalid folder.")
            return
        if ("/gvfs/mtp:" in folder):
            QMessageBox.warning(
                self,
                "MTP Device Detected",
                "Cannot change timestamps on Android devices directly.\n"
                "Please copy the images to a local folder first."
            )
            return

        rows_to_update = [row for row in range(self.table.rowCount())
                          if (self.table.item(row, 2).text() == "Change")]

        if (not rows_to_update):
            QMessageBox.information(self, "Info", "No files need updating.")
            return

        self.progress.setMaximum(len(rows_to_update))
        self.progress.setValue(0)
        self.progress.show()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        updated = 0
        for i, row in enumerate(rows_to_update, start=1):
            filename = self.table.item(row, 0).text()
            date_text = self.table.item(row, 1).text()
            dt = datetime.datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
            ts = dt.timestamp()
            path = os.path.join(folder, filename)

            try:
                if (self.modify_checkbox.isChecked()):
                    os.utime(path, (ts, ts))

                if (self.created_checkbox.isChecked() and IS_WINDOWS):
                    handle = win32file.CreateFile(
                        path,
                        win32con.GENERIC_WRITE,
                        0,
                        None,
                        win32con.OPEN_EXISTING,
                        0,
                        None,
                    )
                    win_time = win32file.FILETIME.from_datetime(dt)
                    win32file.SetFileTime(handle, win_time, None, None)
                    handle.close()

                # set upd
                self.table.setItem(row, 2, QTableWidgetItem("OK"))
                self.table.item(row, 2).setForeground(Qt.green)
                updated += 1
            except Exception as e:
                self.table.setItem(row, 2, QTableWidgetItem("Failed"))
                self.table.item(row, 2).setForeground(Qt.red)

            self.progress.setValue(i)
            QApplication.processEvents()

        QApplication.restoreOverrideCursor()
        self.progress.hide()
        QMessageBox.information(self, "Done", f"Timestamps updated for {updated} files.")

def main():
    QCoreApplication.setAttribute(Qt.AA_DontUseNativeDialogs, False)
    app = QApplication(sys.argv)

    # totally did not copy this from my other project, so hope this doesn't look completely janky
    dark_qss = """
    QWidget { background-color: #282C34; color: #ECEFF4; font-size: 14px; }
    QLineEdit { background-color: #3B3F45; border: none; border-radius: 8px; padding: 8px; min-height: 36px; }
    QPushButton { background-color: #4C566A; color: #ECEFF4; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 600; }
    QPushButton:hover { background-color: #5E6680; }
    QPushButton:pressed { background-color: #3B4252; }
    QTableWidget { background-color: #21252B; gridline-color: transparent; border: none; alternate-background-color: #2C2F36; }
    QHeaderView::section { background-color: transparent; border: none; font-weight: 600; color: #ECEFF4; padding: 6px; }
    QTableWidget::item { border: none; }
    QTableWidget::item:selected { background-color: #729FCF33; }
    QCheckBox { spacing: 8px; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    QProgressBar { background-color: #3B3F45; border-radius: 4px; height: 6px; text-align: none; }
    QProgressBar::chunk { background-color: #88C0D0; border-radius: 4px; }
    """
    app.setStyleSheet(dark_qss)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
