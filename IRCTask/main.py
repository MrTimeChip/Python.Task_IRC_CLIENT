from main_widget import MainWidget
import sys
from PyQt5.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    main_widget = MainWidget()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
