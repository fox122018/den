import requests
import unittest
import string
import random
import datetime

def generate_str(length):   # Генерация случайной строки заданной длины
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_milestone(url_milestones, head): # Создание новой milestone
    new_milestone = {
        "title": "v1.0 " + str(datetime.datetime.now()),
        "description": "Tracking milestone for version 1.0"
    }
    res = requests.post(url_milestones, json=new_milestone, headers=head).json()
    numbers_milestones = [res["number"]]
    return numbers_milestones

def get_milestones(res_milestones):   # Получение списка номеров всех существующих milestones
    numbers_milestones = []
    for m in res_milestones:
        numbers_milestones.append(m["number"])
    numbers_milestones.sort()
    return numbers_milestones

class My_test(unittest.TestCase):
    @classmethod
    def setUpClass(self):  # Подготовка к тестированию
        self.login_owner = "fox122018"
        self.repos_owner = "den"
        self.login_collaborator = "RussianTestUser"
        self.tokens = {
            "owner": "token c7e824c5b8f4efe8bef514c1d6f1d7a2bf53703c",  # владелец fox122018
            "guest": "token 01c070c430ad42b6c0267c810daa7464fde7e0ee"   # гость ProkofevaAlina
        }
        self.head = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": self.tokens["owner"]  # по умолчанию авторизация от имени владельца
        }
        self.base_url = "https://api.github.com/repos/" + self.login_owner + "/" + self.repos_owner + "/issues"
        new_issue = {
            "title": "Title of new issue. " + str(datetime.datetime.now()),
            "body": "Hello world"
        }
        res = requests.post(self.base_url, json=new_issue, headers=self.head)  # создание новой issue от имени owner
        if (res.status_code == 201):
            self.number_of_issue = res.json()["number"]
            self.req_url = self.base_url + "/" + str(self.number_of_issue)
            print("Создана issue с номером", self.number_of_issue)
            print(self.req_url)
        else:
            print("Issue не создана!")

        self.url_milestones = "https://api.github.com/repos/" + self.login_owner + "/" + self.repos_owner + "/milestones"
        res_milestones = requests.get(self.url_milestones, headers=self.head).json()  # получение списка milestones
        if (len(res_milestones) == 0):  # milestones отсутствуют
            self.numbers_milestones = create_milestone(self.url_milestones, self.head)
        else:
            self.numbers_milestones = get_milestones(res_milestones)
        print("Номера milestones:", self.numbers_milestones)

    def change_user(self, user):    # Установка авторизации от имени owner/guest
        self.head["Authorization"] = self.tokens[user]
        # print("Выбран пользователь ", user, self.head["Authorization"])

    def tearDown(self):     # Обновление issue от имени owner после каждого теста
        self.change_user("owner")
        data = {
            "title": "Текущий заголовок " + str(datetime.datetime.now()),
            "body": "Здесь написан какой-то текст",
            "state": "open",
            "milestone": None,
            "labels": ["question"],
            "assignees": [self.login_owner]
        }
        requests.patch(self.req_url, json=data, headers=self.head)

    def check(self, name_param, params, type_test):  # Осуществление проверки
        if (type_test == "positive"):
            for p in params:
                with self.subTest(i=p):
                    response = requests.patch(self.req_url, json=p, headers=self.head)
                    self.assertEqual(response.status_code, 200)  # Успешный запрос
                    d = response.json()
                    if (name_param in ["title", "body", "state"]):
                        self.assertEqual(d[name_param], p[name_param])
                    if (name_param == "milestone"):
                        if (p[name_param] is None):
                            self.assertEqual(d[name_param], None)
                        else:
                            self.assertEqual(d[name_param]["number"], p[name_param])
                    if (name_param == "labels"):
                        for j in range(len(p[name_param])):
                            self.assertEqual(d[name_param][j]["name"], p[name_param][j])
                    if (name_param == "assignees"):
                        for j in range(len(p[name_param])):
                            self.assertEqual(d[name_param][j]["login"], p[name_param][j])
        if (type_test == "negative"):
            for p in params:
                with self.subTest(i=p):
                    response = requests.patch(self.req_url, json=p, headers=self.head)
                    self.assertGreaterEqual(response.status_code, 400)  # Ошибка клиента
                    self.assertLess(response.status_code, 500)  # 400 <= status_code < 500

    def test_title(self):   # Тестирование параметра "title"
        name_param = "title"
        print("Тестирование параметра", name_param)
        titles_pos = [
            {name_param: "Заголовок этой задачи содержит около пятидесяти (50) символов"},
            {name_param: "Я"},
            {name_param: "МЫ"},
            {name_param: generate_str(1000)},
            {name_param: "@#$%^&;.?,>|\/№\"!()_{}[<~"}
        ]
        titles_neg = [
            {name_param: ""},   # пустая строка
            {name_param: 13}    # неверный тип
        ]
        self.check(name_param, titles_pos, "positive")
        self.check(name_param, titles_neg, "negative")

    def test_body(self):  # Тестирование параметра "body"
        name_param = "body"
        print("Тестирование параметра", name_param)
        bodies_pos = [
            {name_param: "Здесь написан какой-то текст issue, длиной около 50 символов"},
            {name_param: ""},   # пустая строка
            {name_param: generate_str(10000)},
            {name_param: "@#$%^&;.?,>|\/№\"!()_{}[<~"}
        ]
        bodies_neg = [
            {name_param: ["hello", "world"]}    # неверный тип
        ]
        self.check(name_param, bodies_pos, "positive")
        self.check(name_param, bodies_neg, "negative")

    def test_state_by_owner(self):  # Тестирование параметра "state" от имени owner
        name_param = "state"
        print("Тестирование параметра", name_param, "от имени owner")
        states_pos = [
            {name_param: "closed"},
            {name_param: "open"}
        ]
        states_neg = [
            {name_param: "cLOsEd"},  # смешанный регистр
            {name_param: "OPEN"},   # верхний регистр
            {name_param: "new state, oops"},    # несуществующее состояние
            {name_param: 4.12}  # неверный тип
        ]
        self.check(name_param, states_pos, "positive")
        self.check(name_param, states_neg, "negative")

    def test_close_issue_by_guest(self):  # Закрытие issue от имени guest, который не является ее автором
        print("Закрытие issue от имени guest, который не является ее автором")
        name_param = "state"
        states = [
            {name_param: "closed"},
        ]
        self.change_user("guest")   # смена пользователя
        self.check(name_param, states, "negative")

    def test_reopen_issue_by_guest(self):  # Переоткрытие issue от имени guest, который не является ее автором
        print("Переоткрытие issue от имени guest, который не является ее автором")
        name_param = "state"
        requests.patch(self.req_url, json=[{"state": "closed"}], headers=self.head)   # закрытие issue от имени owner
        self.change_user("guest")   # смена пользователя
        states = [
            {name_param: "open"},
        ]
        self.check(name_param, states, "negative")

    def test_milestone_by_owner(self):  # Тестирование параметра "milestone" от имени owner
        name_param = "milestone"
        print("Тестирование параметра", name_param, "от имени owner")
        milestones_pos = [
            {name_param: self.numbers_milestones[0]},  # существующий номер
            {name_param: None}    # null
        ]
        milestones_neg = [
            {name_param: 0},
            {name_param: -1},
            {name_param: 2**31},
            {name_param: "str"}  # неверный тип
        ]
        self.check(name_param, milestones_pos, "positive")
        self.check(name_param, milestones_neg, "negative")

    def test_milestone_by_guest(self):  # Тестирование параметра "milestone" от имени guest
        name_param = "milestone"
        print("Тестирование параметра", name_param, "от имени guest")
        self.change_user("guest")  # смена пользователя
        milestones = [
            {name_param: self.numbers_milestones[0]},
        ]
        self.check(name_param, milestones, "negative")

    def test_labels_by_owner(self):  # Тестирование параметра "labels" от имени owner
        name_param = "labels"
        print("Тестирование параметра", name_param, "от имени owner")
        labels_pos = [
            {name_param: ["bug09"]},
            {name_param: ["баг", "QUESTion"]},
            {name_param: []}    # null
        ]
        labels_neg = [
            {name_param: "@#$%^&;.?,>|\/№\"!()_{}[<~"},
            {name_param: ["bug", 888, 0.5]}  # неверный тип
        ]
        self.check(name_param, labels_pos, "positive")
        self.check(name_param, labels_neg, "negative")

    def test_labels_by_guest(self):  # Тестирование параметра "labels" от имени guest
        name_param = "labels"
        print("Тестирование параметра", name_param, "от имени guest")
        self.change_user("guest")  # смена пользователя
        labels = [
            {name_param: ["bug"]},
        ]
        self.check(name_param, labels, "negative")

    def test_assignees_by_owner(self):  # Тестирование параметра "assignees" от имени owner
        name_param = "assignees"
        print("Тестирование параметра", name_param, "от имени owner")
        assignees_pos = [
            {name_param: [self.login_owner]},
            {name_param: [self.login_owner, self.login_collaborator]},
            {name_param: []}  # null
        ]
        assignees_neg = [
            {name_param: ["@#$%^&;.?,>|\/№\"!()_{}[<~"]},   # несуществующий пользователь
            {name_param: [self.login_owner, 888, 0.5]}  # неверный тип
        ]
        self.check(name_param, assignees_pos, "positive")
        self.check(name_param, assignees_neg, "negative")

    def test_assignees_by_guest(self):  # Тестирование параметра "assignees" от имени guest
        name_param = "assignees"
        print("Тестирование параметра", name_param, "от имени guest")
        self.change_user("guest")  # смена пользователя
        assignees = [
            {name_param: [self.login_owner]},
        ]
        self.check(name_param, assignees, "negative")

    def test_edit_issue_by_guest_creater(self):  # Редактированиие issue от имени  ее автора, который является guest
        print("Редактированиие issue от имени  ее автора, который является guest")
        self.change_user("guest")  # смена пользователя
        data_v1 = {
            "title": "Эта issue создана guest v1 " + str(datetime.datetime.now()),
            "body": "Первоначальный текст",
            "state": "open",
            "milestone": self.numbers_milestones[0],
            "labels": ["bug"],
            "assignees": [self.login_owner]
        }
        old_res = requests.post(self.base_url, json=data_v1, headers=self.head)  # создание новой issue от имени guest
        old_issue = old_res.json()

        data_v2 = {
            "title": "Эта issue отредактирована guest v2 " + str(datetime.datetime.now()),
            "body": "Исправленный текст",
            "state": "open",
            "milestone": None,
            "labels": ["question"],
            "assignees": [self.login_owner, self.login_collaborator]
        }
        new_res = requests.patch(old_issue["url"], json=data_v2, headers=self.head)  # обновление issue от имени ее автора
        self.assertEqual(new_res.status_code, 200)  # Успешный запрос
        new_issue = new_res.json()
        for param in ["title", "body", "state"]:  # измененные параметры
            self.assertEqual(new_issue[param], data_v2[param])
        for param in ["milestone", "labels", "assignees"]:  # НЕизмененные параметры
            self.assertEqual(old_issue[param], new_issue[param])

    def test_incorrect_url(self):   # Тестирование при некорректном url
        print("Тестирование при некорректном url")
        incorrect_url = "https://api.github.com/repos/" + self.login_owner + "/" + self.repos_owner + "/issues///"
        data = {
            "title": "Title of new issue. " + str(datetime.datetime.now())
        }
        response = requests.patch(incorrect_url, json=data, headers=self.head)
        self.assertGreaterEqual(response.status_code, 400)  # Ошибка клиента
        self.assertLess(response.status_code, 500)  # 400 <= status_code < 500


if __name__ == '__main__':
    unittest.main()