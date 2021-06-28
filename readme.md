# Telegram super resolution bot

## Стек
- **SRGAN** [repo](https://github.com/sgrvinod/a-PyTorch-Tutorial-to-Super-Resolution), [paper](https://arxiv.org/abs/1609.04802) - Метод улучшения качества изображения
- **pyTelegramBotAPI** [repo](https://github.com/eternnoir/pyTelegramBotAPI) - библиотека для работы с telegram bot API 
- **Flask** - движок для бота
- **MySQL** - БД для отслеживания пользователей


## Запуск бота

Для запуска бота - необходимо создать файл constants.py

```python
# Bot token
API_TOKEN = '<BOT_TOKEN>'
# Url to recieve webhooks
URL = '<BOT_URL>'

# MySQL database credentials
DB_USER = 'root'
DB_PASS = '12345678'
DB_HOST = 'localhost'
DB_NAME = 'DB'
```

Затем вызвать команду
```sh
python app.py
```