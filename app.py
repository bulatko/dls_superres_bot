from enum import unique
from flask import Flask, request
import flask
import logging
import requests
import numpy as np
import torch
import os
import json
from time import sleep
from constants import *
import pymysql
pymysql.install_as_MySQLdb()
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from utils import get_model, main_menu, super_res_image


logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

app = flask.Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_NAME)
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    last_message = db.Column(db.Text)
    images_num = db.Column(db.Integer)

    def __init__(self, id, first_name, last_name, last_message=''):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.last_message = last_message
        self.images_num = 0

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        db.session.commit()

    def __repr__(self):
        return json.dumps({'id': self.id, 'first_name': self.first_name, 'last_name': self.last_name, 'last_message': self.last_name, 'images_num': self.images_num})



def get_db_user(data, change_last_message=True):
    user = data.from_user
    res : User = User.query.filter_by(id=user.id).first()
    
    if res is None:
        bot.send_message(user.id, "Регистрация")
        res = User(user.id, user.first_name, user.last_name)
        db.session.add(res)
        db.session.commit()

    if res.first_name != user.first_name \
        or res.last_name != user.last_name:
        res.first_name = user.first_name
        res.last_name = user.last_name

    if type(data) == telebot.types.Message and change_last_message:
        res.last_message = data.text

    return res




# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'Bot is working'


# Process webhook calls
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)



# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):

    db_user = get_db_user(message)
    keyboard = main_menu()

    bot.reply_to(message,
                 ("Добро пожаловать в бот для смены стилей с помщью нейросетей. Доступные функции указаны в меню ниже"), reply_markup=keyboard)

    

@bot.message_handler(regexp='^Привет$')
def send_welcome(message):
    db_user = get_db_user(message)
    bot.reply_to(message,
                 ("И тебе привет, {}".format(db_user.first_name)))

@bot.message_handler(content_types=['document'])
def proccess_image(message: telebot.types.Message):
    photo: telebot.types.Document = message.document
    if photo.file_size > 500 * 1024:
        bot.reply_to(message, "Максимальный размер изображения - 500КБ")
        return

    filename = photo.file_name
    extension = filename[filename.rfind('.') + 1:].lower()
    good_extensions = ['jpg', 'png', 'jpeg']
    if extension not in good_extensions:
        bot.reply_to(message, "Неподходящий формат. Выберите один из следующих: {}".format(', '.join(good_extensions)))
        return
    db_user = get_db_user(message)
    file_url = bot.get_file_url(photo.file_id)
    #filename = '{}.jpg'.format(db_user.id)
    bot.send_message(db_user.id, 'Изображение обрабатывается')
    with open(filename, 'wb') as f:
        f.write(requests.get(file_url).content)
    try:
        super_res_image(filename, net)
        bot.send_document(db_user.id, open('interpolated_' + filename, 'rb'), caption='Билинейная интерполяция')
        sleep(0.1)
        bot.send_document(db_user.id, open(filename, 'rb'), caption='Картинка, обработанная GAN\'ом')
        db_user.images_num = db_user.images_num + 1

    except Exception as e:
        bot.reply_to(message, "Ошибка обработки\n{}".format(str(e)))

    #os.unlink(filename)
    #os.unlink('interpolated_' + filename)


@bot.message_handler(content_types=['photo'])
def proccess_image(message: telebot.types.Message):
    bot.reply_to(message, "Отправь изображение как файл")



@bot.callback_query_handler(func=lambda callback: True)
def echo_message(callback: telebot.types.CallbackQuery):
    db_user = get_db_user(callback)
    user: telebot.types.User = callback.from_user
    bot.answer_callback_query(callback.id, user.id)

    bot.send_message(user.id, ("{} {} ({}) - {}".format(user.first_name, user.last_name, user.username, user.id)))

# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def procces_message(message):
    db_user = get_db_user(message)
    if message.text == 'Улучшить изображение':
        bot.send_message(db_user.id, "Отправь боту изображение как файл " +
            "(максимальный размер - 500КБ). " + 
            "Тебе придёт 2 изобрашения: улучшенное SRGAN'ом и билинейной интерполяцией.")
        
    elif message.text == 'Статистика':
        text = ("Количество людей в боте: {}\n" + \
            "Всего обработанно изображений: {}\n" + \
            "Обработано твоих изображений: {}").format(
                len(User.query.all()),
                sum([a.images_num for a in User.query.all()]),
                db_user.images_num
            )
        bot.reply_to(message, text)


if __name__ == '__main__':
    global net
    net = get_model()
    try:
        bot.set_webhook(URL)
    except Exception:
        pass
    db.create_all()
    app.run(port=1234,
            debug=True)