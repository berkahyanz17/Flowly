# app.py
import sys
from PySide6.QtWidgets import QApplication
from src.db import init_db
from src.ui_main import MainWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
