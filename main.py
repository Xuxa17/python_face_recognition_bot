import config
import telebot
from telebot import types
from BD import BD
from enum import Enum

bot = telebot.TeleBot(config.token)

bd = BD("bot_bd")
user_name = "Unknown"

class State(Enum):
    FACE_RECOGNITION = 1
    ADD_USER_PHOTO = 2
    USER_NAME_INPUT = 3
    NOTHING_TO_DO = 4

state = State.NOTHING_TO_DO

@bot.message_handler(commands=['menu'])
def print_menu(message):
    global state
    state = State.NOTHING_TO_DO
    one_markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton("Распознать лицо", callback_data='recognize')
    item2 = types.InlineKeyboardButton("Сохранить лицо", callback_data='add')
    item3 = types.InlineKeyboardButton("Получить данные о пользователях", callback_data='get')

    one_markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Меню бота: ", parse_mode='html', reply_markup=one_markup)

@bot.message_handler(commands=['start'])  # Обработка команды для старта
def welcome(message):
    global state
    sti = open('hello.webm', 'rb')
    bot.send_sticker(message.chat.id, sti)

    one_markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton("Распознать лицо", callback_data='recognize')
    item2 = types.InlineKeyboardButton("Сохранить лицо", callback_data='add')
    item3 = types.InlineKeyboardButton("Получить данные о пользователях", callback_data='get')

    one_markup.add(item1, item2, item3)

    bot.send_message(message.chat.id,
                     "Добро пожаловать, {0.first_name}!\n\nЯ - <b>{1.first_name}</b>, бот команды Комрады в СПбПУ, "
                     "создан для того, "
                     "чтобы производить распознавание людей на фото и увеличивать счётчик распознаваний в БД."
                     "\n\n"
                     "<i>Have a nice time</i>".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=one_markup)


@bot.callback_query_handler(func=lambda call: call.data in ['recognize', 'add', 'get'])
def callback_inline_one(call):
    global state
    try:
        if call.message:
            if call.data == 'recognize':
                bot.send_message(call.message.chat.id, "Отправьте изображение", parse_mode="html")
                state = State.FACE_RECOGNITION
            elif call.data == 'add':
                bot.send_message(call.message.chat.id, "Введите имя пользователя", parse_mode="html")
                state = State.USER_NAME_INPUT
            else:
                bd.form_bd()
                bot.send_document(call.message.chat.id, open('bd.txt', 'rb'))
    except:
        print("Ошибка нажатия на кнопку")


@bot.message_handler(content_types=['text'])
def text_handler(message):
    global state, user_name
    if state == State.USER_NAME_INPUT:
        user_name = message.text
        bot.send_message(message.chat.id, "Отправьте фото пользователя", parse_mode="html")
        state = State.ADD_USER_PHOTO
    else:
        bot.send_message(message.chat.id, "Выберите в меню желаемое действие. \nМеню можно вызвать следующей командой: /menu", parse_mode="html")


@bot.message_handler(content_types=['photo'])
def photo(message):
    global state
    if state == State.FACE_RECOGNITION:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        response = bd.user_recognize(downloaded_file)
        if len(response) == 0:
            bot.send_message(message.chat.id, "Не удалось распознать человека на изображении", parse_mode="html")
        else:
            bot.send_message(message.chat.id, f"На изображении есть {', '.join(response)}", parse_mode="html")
        state = State.NOTHING_TO_DO

    elif state == State.ADD_USER_PHOTO:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        response = bd.add_user(user_name, file_info.file_path, downloaded_file)
        if response is None:
            bot.send_message(message.chat.id, "На фото не распознаётся лицо, попробуйте другое", parse_mode="html")
            return
        if len(response) != 0:
            bot.send_message(message.chat.id, "Пользователь с таким лицом уже есть в базе данных", parse_mode="html")
            bot.send_message(message.chat.id, f"Имя пользователя: {', '.join(response)}", parse_mode="html")
        else:
            bot.send_message(message.chat.id, "Пользователь сохранён", parse_mode="html")
        state = State.NOTHING_TO_DO
    else:
        bot.send_message(message.chat.id, "Выберите в меню желаемое действие. \nМеню можно вызвать следующей командой: /menu", parse_mode="html")


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except ConnectionError as e:
        print('Ошибка соединения: ', e)
    except Exception as r:
        print("Непридвиденная ошибка: ", r)
    finally:
        print("Здесь всё закончилось")