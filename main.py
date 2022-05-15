import os
import sys
import requests
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QInputDialog
import geo
from read_write_json import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.type = read_from_json("data.json")["type"]
        self.temp_marks = ''
        self.block_marks = list()
        self.setFixedSize(1256, 489)
        self.initUI()

    def initUI(self):
        uic.loadUi('data/uic/search.ui', self)
        self.s_line.setPlaceholderText('Введите адрес...')
        self.m_x, self.m_y = None, None
        self.cur_block = None
        self.block_name.setText('')
        self.setMouseTracking(True)
        self.btn_t_place_p.hide()
        self.btn_t_place_n.hide()
        self.t_place_info.setText('')
        self.setParams()
        self.btn.clicked.connect(self.getAdress)
        self.set_bt.clicked.connect(self.settings_window_open)
        self.add_block_btn.clicked.connect(self.create_block)
        self.update_blocks_list()
        self.delete_block_btn.clicked.connect(self.remove_block)
        self.rs_btn.clicked.connect(self.remove_all)
        self.btn_t_place_n.clicked.connect(self.n_action)
        self.blocks_list.clicked.connect(self.work_with_cur_block)
        self.btn_t_place_p.clicked.connect(self.add_to_block)
        self.addresses_list.clicked.connect(self.call_from_a_l)

    def setInfo(self, address):
        temp_place_geo = geo.geocode(address)
        full_address = temp_place_geo["metaDataProperty"]["GeocoderMetaData"]["text"]
        text = "ИНФОРМАЦИЯ ПО АДРЕСУ :\n\n"
        text += "Искомый адрес: " + address + '\n'
        text += "Точный адрес:\n" + full_address + '\n'
        self.t_place_info.setText(text)
        self.t_place_info.setWordWrap(True)

    def setParams(self, address="2-я Бауманская, д. 5, к. 1"):
        self.ll, self.sp = geo.get_ll_span(address)
        self.getImage()

    def getAdress(self):
        address = self.s_line.text()
        self.addresses_list.clearSelection()
        if address == '':
            self.temp_place()
            self.setParams()
        else:
            self.temp_place(address)
            self.setParams(address=address)
        self.s_line.setText('')
        self.s_line.setPlaceholderText('Введите адрес...')

    def temp_place(self, address=None):
        if address is None:
            self.temp_marks = ''
            self.t_place = ''
            self.btn_t_place_p.hide()
            self.btn_t_place_n.hide()
            self.t_place_info.setText('')
        else:
            self.btn_t_place_n.setText("Отмена")
            self.btn_t_place_p.show()
            self.btn_t_place_n.show()
            self.t_place = address
            self.setInfo(address)
            self.temp_marks = ','.join([str(x) for x in geo.get_coordinates(address)]) + ",pm2rdl"
            if self.cur_block is None:
                self.btn_t_place_p.setEnabled(False)
            else:
                self.btn_t_place_p.setEnabled(True)

    def getImage(self):
        map_request = "http://static-maps.yandex.ru/1.x/"
        self.type = read_from_json("data.json")["type"]
        line_of_marks = str()
        if self.temp_marks != '' and self.block_marks != []:
            line_of_marks = self.temp_marks + '~' + '~'.join(self.block_marks)
        elif self.block_marks == [] and self.temp_marks != '':
            line_of_marks = self.temp_marks
        elif self.temp_marks == '' and self.block_marks != []:
            line_of_marks = '~'.join(self.block_marks)

        params = {
            "ll": self.ll,
            "spn": self.sp,
            "l": self.type,
            "size": "650,450",
            "pt": line_of_marks
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

    def update_blocks_list(self):
        self.blocks_list.clear()
        self.blocks_list.clearSelection()
        self.block_marks = list()
        self.block_name.setText('')
        data = read_from_json("data.json")
        for elem in data["blocks"]:
            self.blocks_list.addItem(elem["name"])

    def update_addresses_list(self):
        self.addresses_list.clear()
        self.addresses_list.clearSelection()
        if self.cur_block is not None:
            data = read_from_json("data.json")
            blocks = data["blocks"]
            for elem in blocks:
                if elem["name"] == self.cur_block:
                    for place in elem["places"]:
                        self.addresses_list.addItem(place)

    def settings_window_open(self):
        self.settings = Settings()
        self.settings.show()

    def check_name(self, name):
        data = read_from_json("data.json")
        blocks = data["blocks"]
        f = 0
        for elem in blocks:
            if elem["name"] == name:
                name, ok_pressed = QInputDialog.getText(self, "Ошибка",
                                                        "Блок с таким именем уже существует, попробуйте еще раз:")
                if ok_pressed:
                    f = 1
                    break
                else:
                    name = None
        if f == 1:
            name = self.check_name(name)
        return name

    def create_block(self):
        name, ok_pressed = QInputDialog.getText(self, "Новый блок",
                                                "Введите название нового блока:")
        if ok_pressed:
            name = self.check_name(name)
            if name is not None:
                data = read_from_json("data.json")
                blocks = data["blocks"]
                block = dict()
                block["name"] = name
                block["places"] = list()
                blocks.append(block)
                write_to_json(data)
                self.cur_block = None
                self.btn_t_place_p.setEnabled(False)
                self.update_blocks_list()

    def remove_block(self):
        row = self.blocks_list.currentRow()
        item = self.blocks_list.item(row)
        self.t_place_info.setText('')
        if item is not None:
            item = item.text()
            data = read_from_json("data.json")
            lis = [x for x in data["blocks"] if x["name"] != item]
            data["blocks"] = lis.copy()
            write_to_json(data)
            self.cur_block = None
            self.update_blocks_list()
            self.block_marks = list()
            self.setMarks()

    def remove_all(self):
        data = read_from_json("data.json")
        data["blocks"] = list()
        write_to_json(data)
        self.cur_block = None
        self.update_blocks_list()
        self.update_addresses_list()
        self.t_place_info.setText('')
        self.block_marks = list()
        self.setMarks()
        self.setParams()

    def setMarks(self):
        self.block_marks = list()
        data = read_from_json("data.json")
        blocks = data["blocks"]
        for elem in blocks:
            if elem["name"] == self.cur_block:
                for address in elem["places"]:
                    ll, sp = geo.get_ll_span(address)
                    self.block_marks.append(ll + ',pm2dgm')
        if len(self.block_marks) > 1:
            max_lon, max_lat = 0, 0
            min_lon, min_lat = 10 ** 5, 10 ** 5
            data = read_from_json("data.json")
            blocks = data["blocks"]
            for elem in blocks:
                if elem["name"] == self.cur_block:
                    for address in elem["places"]:
                        envelope = geo.geocode(address)["boundedBy"]["Envelope"]
                        l, b = map(float, envelope["lowerCorner"].split(" "))
                        r, t = map(float, envelope["upperCorner"].split(" "))
                        max_lon = max(l, r, max_lon)
                        min_lon = min(l, r, min_lon)
                        max_lat = max(b, t, max_lat)
                        min_lat = min(b, t, min_lat)
            dx = abs(max_lon - min_lon) / 2.0
            dy = abs(max_lat - min_lat) / 2.0
            self.sp = f"{dx},{dy}"
            self.ll = f'{min_lon + dx},{min_lat + dy}'
        elif len(self.block_marks) == 1:
            data = read_from_json("data.json")
            blocks = data["blocks"]
            for elem in blocks:
                if elem["name"] == self.cur_block:
                    ll, sp = geo.get_ll_span(elem["places"][0])
                    self.ll = ll
                    self.sp = sp
        self.getImage()

    def work_with_cur_block(self):
        row = self.blocks_list.currentRow()
        item = self.blocks_list.item(row)
        if item is not None:
            item = item.text()
            self.block_name.setText(item)
            self.cur_block = item
            self.update_addresses_list()
            self.btn_t_place_p.setEnabled(True)
        self.setMarks()

    def add_to_block(self):
        data = read_from_json("data.json")
        blocks = data["blocks"]
        for elem in blocks:
            if elem["name"] == self.cur_block:
                elem["places"].append(self.t_place)
        data["blocks"] = blocks.copy()
        write_to_json(data)
        self.t_place_info.setText('')
        self.update_addresses_list()
        self.temp_place()
        self.setMarks()

    def call_from_a_l(self):
        row = self.addresses_list.currentRow()
        item = self.addresses_list.item(row)
        if item is not None:
            item = item.text()
            self.btn_t_place_p.hide()
            self.btn_t_place_n.setText("Удалить")
            self.btn_t_place_n.show()
            self.setInfo(item)
            self.setParams(item)

    def n_action(self):
        name_btn = self.btn_t_place_n.text()
        if name_btn == "Отмена":
            self.t_place = ''
            self.setParams()
        elif name_btn == "Удалить":
            self.delete_from_addresses_list()

    def delete_from_addresses_list(self):
        row = self.addresses_list.currentRow()
        item = self.addresses_list.item(row)
        if item is not None:
            item = item.text()
            data = read_from_json("data.json")
            blocks = data["blocks"]
            for elem in blocks:
                if elem["name"] == self.cur_block:
                    elem["places"].remove(item)
            self.t_place_info.setText('')
            write_to_json(data)
            self.update_addresses_list()
            self.setMarks()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if 310 <= event.x() <= 961 and 20 <= event.y() <= 470:
                self.m_x, self.m_y = event.x(), event.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_x, self.m_y = None, None

    def mouseMoveEvent(self, event):
        if self.m_x is not None and self.m_y is not None:
            self.temp_place()
            self.addresses_list.clearSelection()
            cur_x, cur_y = event.x(), event.y()
            lon, lat = map(float, self.ll.split(','))
            d1, d2 = map(float, self.sp.split(','))
            lon += (self.m_x - cur_x) / 256 * d1
            lat -= (self.m_y - cur_y) / 256 * d2
            self.ll = f'{lon},{lat}'
            self.m_x = cur_x
            self.m_y = cur_y
            self.getImage()

    def wheelEvent(self, event):
        d1, d2 = map(float, self.sp.split(','))
        if event.angleDelta().y() < 0:
            d1 *= 2
            d2 *= 2
            if d1 < 40 or d2 < 40:
                self.sp = f'{d1},{d2}'
        else:
            d1 /= 2
            d2 /= 2
            if d1 > 2 * 10 ** (-4) or d2 > 2 * 10 ** (-4):
                self.sp = f'{d1},{d2}'
        self.getImage()

    def closeEvent(self, event):
        os.remove(self.map_file)


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('data/uic/settings.ui', self)
        self.data = read_from_json("data.json")
        self.type = self.data["type"]
        self.window_closed = False
        if self.type == "map":
            self.r_map.setChecked(True)
        elif self.type == "sat":
            self.r_sat.setChecked(True)
        else:
            self.r_hyb.setChecked(True)
        self.r_map.toggled.connect(self.onClicked)
        self.r_sat.toggled.connect(self.onClicked)
        self.r_hyb.toggled.connect(self.onClicked)
        self.btn_cancel.clicked.connect(self.close)
        self.btn_accept.clicked.connect(self.accept)

    def onClicked(self):
        name = self.sender().text()
        if name == "Карта":
            self.type = "map"
        if name == "Спутник":
            self.type = "sat"
        if name == "Гибрид":
            self.type = "sat,skl"

    def accept(self):
        self.data["type"] = self.type
        write_to_json(self.data)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())

