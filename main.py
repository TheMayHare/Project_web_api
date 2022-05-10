import os
import sys

import requests
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from geo import get_coordinates, get_ll_span


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.type = "map"
        self.initUI()

    def setParams(self, adress="2-я Бауманская, д. 5, к. 1"):
        self.ll, self.sp = get_ll_span(adress)
        self.or_ll = self.ll
        self.getImage()

    def getImage(self):
        map_request = "http://static-maps.yandex.ru/1.x/"
        params = {
            "ll": self.ll,
            "spn": self.sp,
            "l": self.type,
            "size": "650,450",
            "pt": f"{self.or_ll},pm2dom"
        }
        response = requests.get(map_request, params=params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)
        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)
        self.pixmap = QPixmap(self.map_file)
        self.im_l.setPixmap(self.pixmap)

    def initUI(self):
        uic.loadUi('search.ui', self)
        self.s_line.setPlaceholderText('Введите адрес...')
        self.setParams()
        self.btn.clicked.connect(self.getAdress)
        self.rs_btn.clicked.connect(self.reset)
        self.r_map.setChecked(True)
        self.r_map.toggled.connect(self.onClicked)
        self.r_sat.toggled.connect(self.onClicked)
        self.r_hyb.toggled.connect(self.onClicked)

    def onClicked(self):
        name = self.sender().text()
        if name == "Карта":
            self.type = "map"
        if name == "Спутник":
            self.type = "sat"
        if name == "Гибрид":
            self.type = "sat,skl"
        self.getImage()

    def reset(self):
        self.setParams()
        self.s_line.setText('')
        self.s_line.setPlaceholderText('Введите адрес...')

    def getAdress(self):
        adress = self.s_line.text()
        if adress == '':
            self.setParams()
        else:
            self.setParams(adress=adress)
        self.s_line.setText('')
        self.s_line.setPlaceholderText('Введите адрес...')

    def closeEvent(self, event):
        os.remove(self.map_file)


class Search(Example):
    def keyPressEvent(self, event):
        d1, d2 = map(float, self.sp.split(','))
        lon, lat = map(float, self.ll.split(','))
        if event.key() + 1 == Qt.Key_Enter:
            self.getAdress()
        if event.key() == Qt.Key_PageUp:
            d1 *= 2
            d2 *= 2
            if d1 < 40 or d2 < 40:
                self.sp = f'{d1},{d2}'
            self.getImage()
        if event.key() == Qt.Key_PageDown:
            d1 /= 2
            d2 /= 2
            if d1 > 2 * 10 ** (-4) or d2 > 2 * 10 ** (-4):
                self.sp = f'{d1},{d2}'
            self.getImage()
        if event.key() == Qt.Key_Left:
            lon -= 0.025 * d1
            self.ll = f'{lon},{lat}'
            self.getImage()
        if event.key() == Qt.Key_Right:
            lon += 0.025 * d1
            self.ll = f'{lon},{lat}'
            self.getImage()
        if event.key() == Qt.Key_Up:
            lat += 0.025 * d2
            self.ll = f'{lon},{lat}'
            self.getImage()
        if event.key() == Qt.Key_Down:
            lat -= 0.025 * d2
            self.ll = f'{lon},{lat}'
            self.getImage()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Search()
    ex.show()
    sys.exit(app.exec())

