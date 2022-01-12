from random import randrange
from sqlite3 import IntegrityError
from vk import search_partners, photo_request
import data_base
from settings import token, group_token, version
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

vk = vk_api.VkApi(token=token)
user_api = vk.get_api()


def message(user_id, message, attachment=''):
    vk_group.method('messages.send',
                    {'user_id': user_id,
                     'message': message,
                     'random_id': randrange(10 ** 7),
                     'attachment': attachment})


vk_group = vk_api.VkApi(token=group_token)
api = vk_group.get_api()
longpoll = VkLongPoll(vk_group)


class Bot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = data_base.User
        self.first_name = ''
        self.last_name = ''
        self.city = 0
        self.age_from = 0
        self.age_to = 0
        self.sex = ''
        self.offset = 0
        self.match_id = 0
        self.top_photos = ''
        self.match_name = ''
        self.match_lastname = ''

    def get_info(self):
        response = requests.get(
            'https://api.vk.com/method/users.get',
            {'user_ids': self.user_id, 'access_token': token, 'v': version})
        for user_info in response.json()['response']:
            self.first_name = user_info['first_name']
            self.last_name = user_info['last_name']
        return self.first_name + ' ' + self.last_name

    def get_city(self, city):
        result = vk.method('database.getCities', {'country_id': 1, 'count': 1, 'q': city})
        if not result['items']:
            self.city = 0
            return self.city
        else:
            for city_ in result['items']:
                self.city = city_['id']
                return self.city

    def get_age_from(self):
        message(self.user_id, 'Введите минимальный возраст партнера')
        for age_event in longpoll.listen():
            if age_event.type == VkEventType.MESSAGE_NEW:
                if age_event.to_me:
                    try:
                        if int(age_event.text) >= 16:
                            self.age_from = age_event.text
                            return self.age_from
                        else:
                            message(self.user_id, 'Маленький возраст!Повторите ввод')
                    except:
                        message(self.user_id, 'Минимальный возраст 16 лет!')

    def get_age_to(self):
        message(self.user_id, 'Введите максимальный возраст партнера')
        for age_event in longpoll.listen():
            if age_event.type == VkEventType.MESSAGE_NEW:
                if age_event.to_me:
                    try:
                        if int(age_event.text) < 90:
                            self.age_to = age_event.text
                            return self.age_to
                        else:
                            message(self.user_id, 'Максимальный возраст 90 лет! Повторите ввод')
                    except:
                        message(self.user_id, 'Максимальный возраст 90 лет! Повторите ввод')

    def gender(self):
        message(self.user_id, 'Введите пол партнера(1-если женский,2-если мужской,3- не важно)')
        for gender_event in longpoll.listen():
            if gender_event.type == VkEventType.MESSAGE_NEW:
                if gender_event.to_me:
                    res = gender_event.text
                    if res == "1" or res == "2" or res == "3":
                        self.sex = gender_event.message
                        return self.sex
                    else:
                        self.sex = 0
                        return self.sex

    def registration(self):
        message(self.user_id, "Регистрация прошла успешно,"
                              "чтобы начать поиск ,напишите START ")
        self.get_info()
        data_base.create_tables()
        data_base.register_user(self.user_id)

    def search_pair(self):
        message(self.user_id, f"В каком городе будем искать партнера?")
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if self.get_city(event.message) == 0:
                        message(self.user_id, f"Такого города нет")
                    else:
                        self.gender()
                        self.get_age_from()
                        self.get_age_to()
                        if self.age_from > self.age_to:
                            message(self.user_id, f"Неверный  возраст")
                            self.search_pair()
                        res = search_partners(self.age_from, self.age_to, self.sex, self.city, self.offset)
                        self.match_id = res['id']
                        self.match_name = res['first_name']
                        self.match_lastname = res['last_name']
                        self.top_photos = photo_request(self.match_id)
                        profile_link = f'https://vk.com/id{self.match_id}'
                        message(self.user_id, f'Имя: {self.match_name}\n'
                                              f'Фамилия: {self.match_lastname}\nlink: {profile_link}',
                                self.top_photos)
                        return self.search_pair_()

    def search_pair_(self):
        message(self.user_id, f"Как Вам? Хотите добавить в избранное?"
                              f"Напишите ЛАЙК ,чтобы добавить в избранное, ЧС - чтобы добавить в черный список, "
                              f"ДАЛЕЕ ,чтобы продолжить")
        while True:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        profile_link = f'https://vk.com/id{self.match_id}'
                        if event.message == 'лайк' or event.message == 'ЛАЙК' or event.message == 'Лайк':
                            try:
                                data_base.add_match(id_vk=self.match_id, first_name=self.match_name,
                                                    last_name=self.match_lastname,
                                                    link=profile_link, id_user=self.user_id)
                                message(self.user_id, 'Пользователь добавлен в избранное,ищем дальше(да/нет)?')
                            except IntegrityError:
                                message(self.user_id, 'Пользователь уже в избранном,ищем дальше(да/нет),'
                                                      'чтобы посмотреть список избранных напишите +?')
                        elif event.message == '+':
                            people = data_base.check(self.user_id)
                            for numbers, users in enumerate(people):
                                message(self.user_id, f'{users.first_name} " " {users.last_name}, {users.link}')
                            message(self.user_id, 'ищем дальше(да/нет)??')
                        elif event.message == 'ДАЛЕЕ' or event.message == 'далее' or event.message == 'Далее' or \
                                event.message == 'Да' or event.message == 'да' or event.message == 'ДА':
                            message(self.user_id, 'Ищем дальше')
                            self.offset += 1
                            res = search_partners(self.age_from, self.age_to, self.sex, self.city, self.offset)
                            self.match_id = res['id']
                            self.match_name = res['first_name']
                            self.match_lastname = res['last_name']
                            self.top_photos = photo_request(self.match_id)
                            message(self.user_id, f'Имя: {self.match_name}\n'
                                                  f'Фамилия: {self.match_lastname}\nСсылка: {profile_link}',
                                    self.top_photos)
                            return self.search_pair_()
                        elif event.message == 'нет' or event.message == 'НЕТ' or event.message == 'Нет':
                            message(self.user_id, 'Чтобы продолжить поиск ,напишите ДАЛЕЕ,'
                                                  'чтобы начать поиск с новыми параметрами СТАРТ,'
                                                  'чтобы закончить СТОП')
                        elif event.message == 'стоп' or event.message == 'СТОП' or event.message == 'Стоп':
                            pass
                        elif event.message == "СТАРТ" or event.message == "старт" or event.message == "Старт":
                            bot.search_pair()
                        elif event.message == 'Чс' or event.message == 'ЧС' or event.message == 'чс':
                            data_base.add_to_black_list(id_vk=self.match_id, first_name=self.match_name,
                                                        last_name=self.match_lastname,
                                                        link=profile_link)
                            message(self.user_id, 'Пользователь добавлен в черный список,ищем дальше(да/нет)?')
                        else:
                            message(self.user_id, 'Ищем дальше')
                            self.offset += 1
                            res = search_partners(self.age_from, self.age_to, self.sex, self.city, self.offset)
                            self.match_id = res['id']
                            self.match_name = res['first_name']
                            self.match_lastname = res['last_name']
                            self.top_photos = photo_request(self.match_id)
                            message(self.user_id, f'Имя: {self.match_name}\n'
                                                  f'Фамилия: {self.match_lastname}\nСсылка: {profile_link}',
                                    self.top_photos)
                            return self.search_pair_()


if __name__ == '__main__':
    for new_event in longpoll.listen():
        if new_event.type == VkEventType.MESSAGE_NEW:
            if new_event.to_me:
                bot = Bot(new_event.user_id)
                request = new_event.text
                if request == "привет" or request == "Привет":
                    bot.get_info()
                    message(new_event.user_id, f"Привет, {bot.first_name}, "
                                               f"хочешь найти партнера? Для начала нужно пройти "
                                               f"регистрацию, напиши РЕГИСТРАЦИЯ ")
                elif request == "регистрация" or request == "РЕГИСТРАЦИЯ" or request == "Регистрация":
                    bot.registration()
                elif request == "СТАРТ" or request == "старт" or request == "Старт":
                    bot.search_pair()
                elif request == "Стоп" or request == "стоп" or request == "СТОП":
                    pass
                elif request == "пока" or request == "Пока":
                    message(new_event.user_id, "До свидания")
                else:
                    message(new_event.user_id, "Не понял вашего ответа...Напишите ПРИВЕТ, чтобы начать")
