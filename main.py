import sys
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialog
import datetime as dt

HEADER_1 = ['Название', "Год", "Страна", "Тираж", "Цена", "Дата", "Кол-во", "Описание"]
HEADER_2 = ["Название", "Год", "Дата", "Количество", "Описание"]


class Base:
    def open_main_window(self):
        """Открытие начального экрана"""
        self.w = Main()
        self.w.show()
        self.hide()

    def open_collect_window(self):
        """Открытие окна коллекции"""
        self.w = CollectionWindow(self.id, self.form)
        self.w.show()
        self.hide()


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        uic.loadUi('start_window.ui', self)
        self.initUI()
        self.load_collections()

    def initUI(self):
        self.setWindowTitle('Коллекционеры')

        self.setStyleSheet("""QWidget{background: #DFF6FF;}
        QListWidget{background: #CBFFFF;}""")

        self.add_collection_button.setIcon(QIcon('plus.jpg'))
        self.add_collection_button.setIconSize(QSize(75, 75))

        self.add_collection_button.clicked.connect(self.choice_collection)
        self.list_collections.itemActivated.connect(self.open_collection)

    def load_collections(self):
        self.list_collections: QListWidget
        res = CUR.execute("""SELECT name FROM name_collect""").fetchall()
        for item in res:
            self.list_collections.addItem(*item)

    def open_collection(self, item):
        self.list_collections: QListWidget
        name = item.text()
        id = CUR.execute("""SELECT id, form FROM name_collect WHERE name = ?""", (name,)).fetchone()
        self.w = CollectionWindow(id[0], id[1])
        self.w.show()
        self.hide()

    def choice_collection(self):
        """Выбор шаблона коллекции"""
        self.w = ChoiceForm()
        self.w.show()
        self.hide()

    def add_collection(self):
        id = CUR.execute("""SELECT MAX(id) FROM name_collect""").fetchone()[0]
        if not id:
            id = 0
        id += 1

        self.h = CreateNewCollection(id)
        self.h.show()
        self.hide()


class CreateNewCollection(QWidget, Base):
    def __init__(self, id, form):
        super(CreateNewCollection, self).__init__()
        uic.loadUi('new_collection.ui', self)
        self.id = id
        self.form = form
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Создание новой коллекции')

        self.set_style_sheet()

        self.saveButton.clicked.connect(self.check_data)
        self.backButton.clicked.connect(self.open_main_window)

    def set_style_sheet(self):
        self.setStyleSheet("""QWidget{background: #DFF6FF; }
                QPushButton{background: #ABFFFF;
                border-style: outset;
                border-width: 1px;
                border-radius: 10px;
                border-color: black;}
                QLineEdit{background: #F0FFFF;}
                QTextEdit{background: #F0FFFF;}""")

    def check_data(self):
        """Проверка названия коллекции"""
        self.name: QLineEdit
        self.description: QTextEdit
        collection_name = self.name.text().strip()
        if len(CUR.execute("""SELECT * FROM name_collect WHERE name = ?""",
                           (collection_name,)).fetchall()) != 0:
            self.message.setText('Коллекция с таким названием уже \n'
                                 'существует! Выберите другое название!')
            return
        if collection_name == '':
            self.message.setText('Введите корректное название коллекции!')
            return
        CUR.execute("""INSERT INTO name_collect values(?, ?, ?, ? )""",
                    (self.id, collection_name, self.description.toPlainText(), self.form))
        CON.commit()
        self.open_collect_window()


class CollectionWindow(QWidget, Base):
    def __init__(self, id, form):
        super(CollectionWindow, self).__init__()
        uic.loadUi('collection_window.ui', self)
        self.id = id
        self.form = form
        self.collection_name, self.comment = CUR.execute(
            f"""SELECT name, comment FROM name_collect WHERE id = {self.id}""").fetchall()[0]
        self.initUi()

    def initUi(self):
        self.description: QTextEdit
        self.delete_collect_button: QPushButton
        self.table: QTableWidget
        self.sort_by: QComboBox

        self.set_style_sheet()

        self.set_box_items()

        self.setWindowTitle(f'{self.collection_name} - коллекция')
        self.description.setText(self.comment)
        self.name_label.setText(self.collection_name)
        self.table.setFixedSize(1000, 620)

        self.add_el.clicked.connect(self.open_new_elem_form)
        self.exit_button.clicked.connect(self.check)
        self.delete_collect_button.clicked.connect(self.delete_collection)
        self.sort_by.currentTextChanged.connect(self.combobox_changed)
        self.clearButton.clicked.connect(self.clear_collection)

        self.load_table(self.prepare_data())

    def set_box_items(self):
        if self.form == 1:
            self.sort_by.addItems(
                ['Без сортировки', 'По возрастанию цены', 'По убыванию цены', 'По дате добавления',
                 'Алфавитный порядок'])
            self.order = {'По возрастанию цены': lambda x: x[4] if x[4] != '' else 0,
                          'По убыванию цены': lambda x: -x[4] if x[4] != '' else 0,
                          'По дате добавления': lambda x: x[5],
                          'Алфавитный порядок': lambda x: str(x[0])}

        else:
            self.sort_by.addItems(
                ['Без сортировки', 'По дате добавления', 'Алфавитный порядок'])
            self.order = {'По дате добавления': lambda x: x[2],
                          'Алфавитный порядок': lambda x: str(x[0])}

    def set_style_sheet(self):
        p = QPalette()
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0.0, QColor(176, 255, 255))
        gradient.setColorAt(1.0, QColor(232, 255, 255))
        p.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(p)

        self.setStyleSheet("""QPushButton{background: #ABFFFF;
                border-style: outset;
                border-width: 1px;
                border-radius: 10px;
                border-color: black;}
                QComboBox{background: #ABFFFF;
                border-style: outset;
                border-width: 1px;
                border-color: black;}
                QTextEdit{background: #F0FFFF;}
                QTableWidget{background: #F0FFFF;}""")

    def change_text(self):
        """Сохраниение измененного текста описания"""
        text = self.description.toPlainText()
        CUR.execute("""UPDATE name_collect 
        SET comment = ? 
        WHERE id = ?""", (text, self.id,))
        CON.commit()

    def clear_collection(self):
        self.window = ClearCollection(self.id, self.form)
        self.window.show()
        self.hide()

    def delete_collection(self):
        self.window = DeleteCollection(self.id, self.form)
        self.window.show()
        self.hide()

    def check(self):
        """Проверка при выходе на главный экран"""
        self.change_text()
        self.open_main_window()

    def prepare_data(self):
        """Данные из БД для занесения в таблицу"""
        if self.form == 1:
            return CUR.execute(
                f"""SELECT  name,  year, country, edition, price, date, count, description
                FROM sample_1 WHERE id = {self.id}""").fetchall()
        return CUR.execute(
            f"""SELECT  name,  year, date, count, description
                        FROM sample_2 WHERE id = {self.id}""").fetchall()

    def combobox_changed(self, value):
        """Сортировка данных"""
        self.sort_by: QComboBox

        res = self.prepare_data()
        if value != 'Без сортировки':
            res.sort(key=self.order[value])
        self.load_table(res)

    def load_table(self, res):
        """Загрузка данных в таблицу"""
        self.table: QTableWidget
        if self.form == 1:
            header = HEADER_1
        else:
            header = HEADER_2

        self.table.setColumnCount(len(header))
        self.table.setHorizontalHeaderLabels(header)
        self.table.setRowCount(0)
        for row, el1 in enumerate(res):
            self.table.setRowCount(
                self.table.rowCount() + 1)
            for col, el2 in enumerate(el1):
                self.table.setItem(row, col, QTableWidgetItem(str(el2)))

        self.table.resizeColumnsToContents()
        k = 0
        for i in range(len(header) - 1):
            k += int(self.table.columnWidth(i))
        self.table.resizeRowsToContents()
        self.table.setColumnWidth(len(header) - 1, 979 - k)

    def open_new_elem_form(self):
        if self.form == 1:
            self.w = NewElemForm1(self.id)
        else:
            self.w = NewElemForm2(self.id)
        self.w.show()
        self.hide()


class NewElemForm1(QMainWindow, Base):
    def __init__(self, id):
        super(NewElemForm1, self).__init__()
        uic.loadUi('new_elem_1.ui', self)
        self.id = id
        self.form = 1
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Добавить новый элемент')

        self.year: QSpinBox
        self.date: QDateEdit
        self.set_style_sheet()
        date = dt.date.today()
        self.year.setValue(2005)
        self.date.setDate(date)
        self.add_button.clicked.connect(self.add_elem)
        self.backButton.clicked.connect(self.cancel)

    def set_style_sheet(self):
        self.setStyleSheet("""QWidget{background: #DFF6FF; }
        QLineEdit{background: #F0FFFF;}
        QSpinBox{background: #F0FFFF;}
        QDateEdit{background: #F0FFFF;}
        QTextEdit{background: #F0FFFF;}
        QPushButton{background: #ABFFFF;
        border-style: outset;
        border-width: 1px;
        border-radius: 10px;
        border-color: black;}
        QLabel{font: italic}""")

    def cancel(self):
        self.w = CollectionWindow(self.id, 1)
        self.w.show()
        self.hide()

    def add_elem(self):
        """Добавление элемента в коллекцию"""

        def is_int(a: str):
            """Проверка строка --> цисло"""
            if a.strip().isdigit():
                return int(a)
            if a.strip() == '':
                return ''
            return False

        name = self.name.text()
        year = is_int(self.year.text())
        country = self.country.text()
        edition = is_int(self.edition.text())
        price = is_int(self.price.text())
        count_one = is_int(self.count_one.text())
        date = self.date.text()
        description = self.description.toPlainText()
        if edition is False or price is False or count_one is False or year is False:
            self.verdict.setText('Введите корректные данные!')
            return

        CUR.execute("""INSERT INTO sample_1 values(?, ?, ?, ?, ?, ?, ?, ?, ? )""",
                    (self.id, name, description, year, country, edition, price, date, count_one,))
        CON.commit()
        self.verdict.setText('')

        self.open_collect_window()


class NewElemForm2(QMainWindow, Base):
    def __init__(self, id):
        super(NewElemForm2, self).__init__()
        uic.loadUi('new_elem_2.ui', self)
        self.id = id
        self.form = 2
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Добавить новый элемент')

        self.year: QSpinBox
        self.date: QDateEdit
        self.set_style_sheet()
        date = dt.date.today()
        self.year.setValue(2005)
        self.date.setDate(date)
        self.add_button.clicked.connect(self.add_elem)
        self.backButton.clicked.connect(self.cancel)

    def set_style_sheet(self):
        self.setStyleSheet("""QWidget{background: #DFF6FF; }
        QLineEdit{background: #F0FFFF;}
        QSpinBox{background: #F0FFFF;}
        QDateEdit{background: #F0FFFF;}
        QTextEdit{background: #F0FFFF;}
        QPushButton{background: #ABFFFF;
        border-style: outset;
        border-width: 1px;
        border-radius: 10px;
        border-color: black;}
        QLabel{font: italic}""")

    def cancel(self):
        self.w = CollectionWindow(self.id, 2)
        self.w.show()
        self.hide()

    def add_elem(self):
        """Добавление элемента в коллекцию"""

        def is_int(a: str):
            """Проверка строка --> цисло"""
            if a.strip().isdigit():
                return int(a)
            if a.strip() == '':
                return ''
            return False

        name = self.name.text()
        year = is_int(self.year.text())
        count_one = is_int(self.count_one.text())
        date = self.date.text()
        description = self.description.toPlainText()
        if count_one is False or year is False:
            self.verdict.setText('Введите корректные данные!')
            return

        CUR.execute("""INSERT INTO sample_2 values(?, ?, ?, ?, ?, ? )""",
                    (self.id, name, year, date, count_one, description,))
        CON.commit()
        self.verdict.setText('')
        self.open_collect_window()


class DeleteCollection(QDialog, Base):
    def __init__(self, id, form):
        super(DeleteCollection, self).__init__()
        self.setWindowTitle('Удаление?!?!??')
        self.setGeometry(700, 400, 300, 125)

        self.id = id
        self.form = form

        self.bt_cancel = QPushButton('Назад', self)
        self.bt_del = QPushButton('Удалить', self)
        self.label = QLabel('Вы точно хотите удалить коллекцию?\n'
                            'Восстановить будет невозможно!', self)

        self.bt_cancel.resize(100, 30)
        self.bt_del.resize(100, 30)
        self.label.move(50, 25)
        self.bt_del.move(45, 75)
        self.bt_cancel.move(155, 75)

        self.bt_del.clicked.connect(self.delete_collection)
        self.bt_cancel.clicked.connect(self.open_collect_window)
        self.set_style_sheet()

    def set_style_sheet(self):
        self.setStyleSheet("""QDialog{background: #DFF6FF; }
        QPushButton{background: #ABFFFF;
        border-style: outset;
        border-width: 1px;
        border-radius: 10px;
        border-color: black;
        font: italic; font: bold;}
        QLabel{font: italic}""")

    def delete_collection(self):
        """Удаление коллекции"""
        CUR.execute("""DELETE FROM name_collect WHERE id = ?""", (self.id,))
        CON.commit()
        if self.form == 1:
            CUR.execute("""DELETE FROM sample_1 WHERE id = ?""", (self.id,))
            CON.commit()
        else:
            CUR.execute("""DELETE FROM sample_2 WHERE id = ?""", (self.id,))
            CON.commit()
        self.w = Main()
        self.w.show()
        self.hide()


class ClearCollection(QDialog, Base):
    def __init__(self, id, form):
        super(ClearCollection, self).__init__()
        self.id = id
        self.form = form
        self.setWindowTitle('Очистить?!?!??')
        self.setGeometry(700, 400, 300, 125)

        self.bt_cancel = QPushButton('Назад', self)
        self.bt_del = QPushButton('Очистить', self)
        self.label = QLabel('Вы точно хотите очистить коллекцию?\n'
                            'Восстановить будет невозможно!', self)

        self.bt_cancel.resize(100, 30)
        self.bt_del.resize(100, 30)
        self.label.move(50, 25)
        self.bt_del.move(45, 75)
        self.bt_cancel.move(155, 75)

        self.bt_del.clicked.connect(self.clear)
        self.bt_cancel.clicked.connect(self.open_collect_window)
        self.set_style_sheet()

    def set_style_sheet(self):
        self.setStyleSheet("""QDialog{background: #DFF6FF; }
        QPushButton{background: #ABFFFF;
        border-style: outset;
        border-width: 1px;
        border-radius: 10px;
        border-color: black;
        font: italic; font: bold;}
        QLabel{font: italic}""")

    def clear(self):
        """Удаление всех элементов из коллекции"""
        if self.form == 1:
            CUR.execute("""DELETE FROM sample_1 WHERE id = ?""", (self.id,))
            CON.commit()
        else:
            CUR.execute("""DELETE FROM sample_2 WHERE id = ?""", (self.id,))
            CON.commit()
        self.open_collect_window()


class ChoiceForm(QWidget, Base):
    def __init__(self):
        super(ChoiceForm, self).__init__()
        uic.loadUi('choice_form.ui', self)
        self.initUi()

    def initUi(self):
        self.form_1: QRadioButton
        self.form_2: QRadioButton
        self.choiceButton: QPushButton
        self.layout_1: QHBoxLayout
        self.layout_2: QHBoxLayout

        self.setStyleSheet("""QWidget{background: #DFF6FF; }
                    QPushButton{background: #ABFFFF;
                    border-style: outset;
                    border-width: 1px;
                    border-radius: 10px;
                    border-color: black;
                    font: italic; font: bold;}""")

        label_1 = QLabel(self)
        label_2 = QLabel(self)
        label_1.setPixmap(QPixmap('first_form.png'))
        label_2.setPixmap(QPixmap('second_form.png'))

        self.layout_1.addWidget(label_1)
        self.layout_2.addWidget(label_2)
        self.form_1.setChecked(True)
        self.choiceButton.clicked.connect(self.choice_form)
        self.exitButton.clicked.connect(self.open_main_window)

    def choice_form(self):
        self.form_1: QRadioButton
        self.form_2: QRadioButton
        self.choiceButton: QPushButton
        if self.form_1.isChecked():
            form = 1
        else:
            form = 2

        id = CUR.execute("""SELECT MAX(id) FROM name_collect""").fetchone()[0]
        if not id:
            id = 0
        id += 1
        self.w = CreateNewCollection(id, form)
        self.w.show()
        self.hide()


CON = sqlite3.connect('collect_db.sqlite')
CUR = CON.cursor()

app_1 = QApplication(sys.argv)
ex_main = Main()
ex_main.show()
sys.exit(app_1.exec_())
