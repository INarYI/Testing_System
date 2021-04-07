import csv
import hashlib
import random
import sqlite3
import sys
from sqlite3.dbapi2 import Connection

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication


class Main(QMainWindow):
    user_answ_points = {}

    def __init__(self):
        super().__init__()
        QMessageBox.about(self, "Введение", "Здравствуйте, сейчас вашему вниманию будет представлен тест. "
                                            "Тест можно пройти 2 раза, лучший результат будет сохранен в БД. "
                                            "Следующим окном будет открыто окнов входа. "
                                            "Если у вас уже есть учетная запись - войдите в неё. "
                                            "В ином случае нажмите на кнопку регистрация и пройдите регистрацию. "
                                            "\nУдачи.")
        uic.loadUi('Enter.ui', self)
        self.EnterBut.clicked.connect(self.login)
        self.RegisterBut.clicked.connect(self.open_reg)
        self.con = sqlite3.connect('STDB.db')

    def login(self):
        self.upassword = self.Passwordedit.text()
        self.ulogin = self.Loginedit.text()
        hashpassw = hashlib.md5(self.upassword.encode()).hexdigest()
        cur = self.con.cursor()
        passwfbd = cur.execute("""SELECT Password FROM Users WHERE Login = '""" + self.ulogin + "'")
        flag = False
        for elem in passwfbd:
            if hashpassw == elem[0]:
                flag = True
            break
        if flag:
            t = (cur.execute("""SELECT Type FROM Users WHERE Login = '""" + str(self.ulogin) + "'")).fetchall()
            ty = None
            for i in range(len(t)):
                ty = (t[i][0])
                break
            if ty == 0:
                self.read_user_info(self.ulogin)
                self.open_test_form()
                self.close()
            else:
                self.read_user_info(self.ulogin)
                self.open_teacher_form()
                self.close()

        else:
            QMessageBox.critical(self, "Ошибка", "При попытке входа произошла ошибка, попробуйте "
                                                 "снова")

    def open_test_form(self):
        self.test_form = QuestForm()
        self.test_form.show()

    def open_teacher_form(self):
        self.teacher_form = Teacher_Form()
        self.teacher_form.show()

    def read_user_info(self, ulogin):
        cur = ex.con.cursor()
        user_info = cur.execute("""SELECT Name, Surname, Variant, Try_number, Max_result FROM Users WHERE Login = '""" +
                                ulogin + "'")
        for elem in user_info:
            self.name = elem[0]
            self.surname = elem[1]
            self.variant = elem[2]
            self.try_num = elem[3]
            self.total_sum = elem[4]
            self.current_question_num = 1
            self.current_sum = 0
            break
        if self.try_num >= 2:
            QMessageBox.critical(self, "Попытки", "Ваши попытки закончились, ваш наибольший результат "
                                 + str(self.total_sum))
            sys.exit(app.exec_())

    def open_reg(self):
        self.RegForm = Registration()
        self.RegForm.show()

    def __del__(self):
        self.con.close()


class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('RegistrationForm.ui', self)
        self.RegEnd.clicked.connect(self.register)

    def register(self):
        cur = ex.con.cursor()
        uname = self.namedit.text()
        usurname = self.surnamedit.text()
        ulogin = self.login.text()
        upassword = self.password.text()
        passhash = str(hashlib.md5(upassword.encode()).hexdigest())
        cb = self.Teacher.isChecked()
        c = self.Class.value()
        let = str(self.Letter.text()).upper()
        cl = str(c) + let
        all_logins = (cur.execute("""SELECT Login FROM Users""")).fetchall()
        if uname != '' and usurname != '' and ulogin != '' and upassword != '':
            flag = True
            for i in range(len(all_logins)):
                if "('" + str(ulogin) + "',)" == str(all_logins[i]):
                    flag = False
            if flag:
                var = random.choice([1, 2])
                cur = ex.con.cursor()
                if cb:
                    a = 1
                    cur.execute(
                        """INSERT INTO Users(Name, Surname, Login, Password, Type, Variant) VALUES {0}""".format(
                            str((uname, usurname, ulogin, passhash, a, var))))
                    self.close()
                    ex.con.commit()
                    QMessageBox.about(self, "Регистрация успешна", "Поздравляю, вы успешно зарегистрировались. " +
                                      "Теперь используйте свой логин и пароль для входа")
                else:
                    if 0 < c <= 11:
                        cur.execute(
                            """INSERT INTO Users(Name, Surname, Login, Password, Variant, Class) VALUES {0}""".format(
                                str((uname, usurname, ulogin, passhash, var, cl))))
                        self.close()
                        ex.con.commit()
                        QMessageBox.about(self, "Регистрация успешна", "Поздравляю, вы успешно зарегистрировались. \n" +
                                          "Теперь используйте свой логин и пароль для входа")
                    else:
                        QMessageBox.critical(self, 'Ошибка', 'Проверьте пожалуйста номер класса')
            else:
                QMessageBox.critical(self, "Ошибка", "Данный логин уже занят, пожалуста используйте другой")
        else:
            QMessageBox.critical(self, "Ошибка", "При регистрации произошла ошибка, попробуйте снова")


class QuestForm(QMainWindow):
    questions = {}
    answers = {}
    points = {}

    def __init__(self):
        super().__init__()
        uic.loadUi('TestForm.ui', self)
        self.Answer1.clicked.connect(self.check_answer)
        self.Answer2.clicked.connect(self.check_answer)
        self.Answer3.clicked.connect(self.check_answer)
        self.Answer4.clicked.connect(self.check_answer)
        self.read_questions()
        self.fill_form()

    def read_questions(self):
        self.questions.clear()
        self.answers.clear()
        self.points.clear()
        ex.user_answ_points.clear()
        ex.current_sum = 0
        ex.current_question_num = 1
        cur = ex.con.cursor()
        quest_cur = cur.execute(
            """SELECT Question_number, Question_text, Answer_1, Answer_2, Answer_3, Answer_4, Answer_num, Points"""
            + """ FROM Questions"""
            + """ WHERE Variant = """ + str(ex.variant))
        for elem in quest_cur:
            self.questions[elem[0]] = (elem[1], elem[2], elem[3], elem[4], elem[5])
            self.answers[elem[0]] = elem[6]
            self.points[elem[0]] = elem[7]

    def fill_form(self):
        if ex.current_question_num <= len(self.questions):
            self.textBrowser.setText(self.questions[ex.current_question_num][0])
            self.Answer1.setText(str(self.questions[ex.current_question_num][1]))
            self.Answer2.setText(str(self.questions[ex.current_question_num][2]))
            self.Answer3.setText(str(self.questions[ex.current_question_num][3]))
            self.Answer4.setText(str(self.questions[ex.current_question_num][4]))
        else:
            max_sum = max(ex.current_sum, ex.total_sum)
            QMessageBox.about(self, "Результат", "Тест пройден, Ваш результат "
                              + str(ex.current_sum) + ", Ваш лучший результат " + str(max_sum))
            QMessageBox.about(self, "Запись ваших результатов в файл", "Далее вам нужно будет выполнить "
                                                                       "сохранение ваших результатов в файл."
                                                                       "Для этого вам нужно лишь ввести название"
                                                                       " файла, в который вы хотите записать ваши"
                                                                       " результаты."
                                                                       "Пожалуйста используйте название файлов, "
                                                                       "в которых будет использоваться какая-либо"
                                                                       " опознавательная информация.")
            if ex.variant == 1:
                new_variant = 2
            else:
                new_variant = 1
            ex.try_num += 1
            cur = ex.con.cursor()
            cur.execute("UPDATE Users SET Max_result = " + str(max_sum) + " WHERE Login = '" + ex.ulogin + "'")
            cur.execute("UPDATE Users SET Variant = " + str(new_variant) + ", Try_number = " + str(ex.try_num) +
                        " WHERE Login = '" + ex.ulogin + "'")
            ex.con.commit()
            file_name = QFileDialog.getSaveFileName(self, "Выберите csv-файл для сохранения результатов", "", "*.csv")[
                0]
            with open(file_name, "w", newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                write_list = [ex.ulogin, ex.name, ex.surname, "Результаты теста"]
                writer.writerow(write_list)
                for i in range(1, ex.current_question_num):
                    if ex.user_answ_points[i][1] == 0:
                        res_str = "Неправильно"
                    else:
                        res_str = "Правильно"
                    answer_num = ex.user_answ_points[i][0]
                    write_list = [self.questions[i][0], self.questions[i][answer_num], res_str,
                                  str(ex.user_answ_points[i][1])]
                    writer.writerow(write_list)
                write_list = ["Итоговый балл", "", "", str(ex.current_sum)]
                writer.writerow(write_list)
            sys.exit(app.exec_())

    def check_answer(self):
        curr_answer = 0
        if self.sender() == self.Answer1:
            curr_answer = 1
        elif self.sender() == self.Answer2:
            curr_answer = 2
        elif self.sender() == self.Answer3:
            curr_answer = 3
        elif self.sender() == self.Answer4:
            curr_answer = 4
        if curr_answer == self.answers[ex.current_question_num]:
            ex.current_sum += self.points[ex.current_question_num]
            ex.user_answ_points[ex.current_question_num] = (curr_answer, self.points[ex.current_question_num])
        else:
            ex.user_answ_points[ex.current_question_num] = (curr_answer, 0)
        ex.current_question_num += 1
        self.fill_form()


class Teacher_Form(QMainWindow):

    def __init__(self):
        super().__init__()
        uic.loadUi('Teacher.ui', self)
        self.SaveResults.clicked.connect(self.save_results)
        self.MakeTest.clicked.connect(self.test)

    def save_results(self):
        cl = self.Class.value()
        let = self.Letter.text()
        cll = str(cl) + str(let).upper()
        cur = ex.con.cursor()
        ans = cur.execute("""SELECT Name, Surname, Max_result FROM Users WHERE Class = '""" + cll + "'")
        lans = ans.fetchall()
        file_name = QFileDialog.getSaveFileName(self, "Выберите csv-файл для сохранения результатов", "", "*.csv")[
            0]
        with open(file_name, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            write_list = ["Результаты теста", 'Класс ' + cll]
            writer.writerow(write_list)
            for i in range(len(lans)):
                x = lans[i]
                name = x[0]
                surname = x[1]
                max_result = x[2]
                writer = csv.writer(csv_file, delimiter=';')
                write_list = [surname, name, max_result]
                writer.writerow(write_list)
        sys.exit(app.exec_())

    def test(self):
        file_name = QFileDialog.getOpenFileName(self, "Выберите csv-файл для загрузки теста", "", "*.csv")[0]
        if file_name == '':
            self.close()
        else:
            with open(file_name, newline='') as TEST:
                reader = csv.reader(TEST, delimiter=';')
                for i in reader:
                    cl = str(i[0])
                    var = i[1]
                    qn = i[2]
                    qt = i[3]
                    an1 = i[4]
                    an2 = i[5]
                    an3 = i[6]
                    an4 = i[7]
                    ann = i[8]
                    po = i[9]
                    cur = ex.con.cursor()
                    cur.execute(
                        """INSERT OR REPLACE INTO Questions (Class, Variant, Question_number, Question_text, Answer_1, 
                        Answer_2, Answer_3, Answer_4, Answer_num, Points)
                        VALUES ({0}""".format("'"
                                              + str(cl) + "', " + str(var) + ", " + str(qn) + ", '"
                                              + str(qt) + "', '" + str(an1) + "', '" + str(an2) + "', '"
                                              + str(an3) + "', '" + str(an4) + "', " + str(ann) + ", "
                                              + str(po))
                        + ")")
        ex.con.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec_())
print('exit')
