from telebot import *
from PIL import Image, ImageOps
import io
from telebot import types

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TOKEN = os.getenv('TOKEN_API')

bot = telebot.TeleBot(TOKEN)

user_states = {}  # тут будем хранить информацию о действиях пользователя

# набор символов из которых составляем изображение
ASCII_CHARS = '@%#*+=-:. '

JOKES = [
    '"Крошка-картошка" — организация, запрещённая в Республике Беларусь',
    'Я не конфетка, что всем по вкусу! Я — орешек, что не всем по зубам!',
    'Это Лена. Она такая спокойная, что из себя её вывести может только мышь. Мёртвая',
    'Лучшее средство для самоочищения и искупления в муках - молоко с огурцом',
    'Порядочные люди не гремят бутылками когда выкидывают мусор',
    'Вампиры-гопники вместо семок грызут насосавшихся комаров',
    'Чем сильнее охреневаешь от происходящего, тем точнее улавливаешь суть.',
    'Одиночество - это когда вместо кота я глажу свою волосатую ногу. Таня, 18 лет',
    'Однажды меня немножко испортили деньги, но долги быстро починили',
    'Велик жесткий диск, а поиграть не во что...',
]


def resize_image(image, new_width=100):
    """
    Изменяет размер изображения
    """
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))


def grayify(image):
    """Преобразует изображение в черно-белое"""
    return image.convert("L")


def image_to_ascii(image_stream, new_width=40):
    """
    Преобразует изображение в ASCII-арт
    """
    # Переводим в оттенки серого
    image = Image.open(image_stream).convert('L')

    # меняем размер сохраняя отношение сторон
    width, height = image.size
    aspect_ratio = height / float(width)
    new_height = int(
        aspect_ratio * new_width * 0.55)  # 0,55 так как буквы выше чем шире
    img_resized = image.resize((new_width, new_height))

    img_str = pixels_to_ascii(img_resized)
    img_width = img_resized.width

    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)

    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"

    return ascii_art


def pixels_to_ascii(image):
    """
    Функция перевода изображения в набор символов
    """
    pixels = image.getdata()
    characters = ""
    for pixel in pixels:
        characters += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return characters


def pixelate_image(image, pixel_size):
    """
    Функция огрубления изображения
    """
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Отправка приветствия"""
    bot.reply_to(message, "Send me an image, and I'll provide options for you!")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Обработка фото"""
    bot.reply_to(message, "I got your photo! Please choose what you'd like to do with it.") #, reply_markup=get_options_keyboard())
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id}
    bot.send_message(message.chat.id, "Хотите изменить набор символов?(yes/да или no/нет)")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    Обработка текста
    """
    global ASCII_CHARS

    if message.text.lower() == "да" or message.text.lower() == "yes":
        bot.send_message(message.chat.id,"Введите набор символов")

        user_states[message.chat.id]['ascii_chars'] = True

    elif message.text.lower() == "нет" or message.text.lower() == "no":
        ASCII_CHARS = '@%#*+=-:. '
        bot.reply_to(message, "I got your photo! Please choose what you'd like to do with it.",
                     reply_markup=get_options_keyboard())
    elif message.text.lower() == "random joke":
        bot.send_message(message.chat.id, get_random_joke())
    elif user_states[message.chat.id]['ascii_chars']:
        ASCII_CHARS = message.text
        bot.reply_to(message, "I got your photo! Please choose what you'd like to do with it.",
                     reply_markup=get_options_keyboard())
    else:
        bot.send_message(message.chat.id, "Не понимаю")


def get_random_joke():
    """
    Получение случайной шутки
    """
    return random.choice(JOKES)


def get_options_keyboard():
    """
    Кнопки для выбора действия
    """
    keyboard = types.InlineKeyboardMarkup()
    pixelate_btn = types.InlineKeyboardButton("Pixelate", callback_data="pixelate")
    ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")
    invert_btn = types.InlineKeyboardButton("Invert", callback_data="invert")
    mirror_btn = types.InlineKeyboardButton("Mirror", callback_data="mirror")
    colorrizer_btn = types.InlineKeyboardButton("Colorrizer", callback_data="colorrizer")
    resizer_btn = types.InlineKeyboardButton("Resize", callback_data="resize")

    keyboard.add(pixelate_btn, ascii_btn, invert_btn, mirror_btn, colorrizer_btn, resizer_btn)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обработка нажатия на кнопки
    """
    if call.data == "pixelate":
        bot.answer_callback_query(call.id, "Pixelating your image...")
        pixelate_and_send(call.message)
    elif call.data == "ascii":
        bot.answer_callback_query(call.id, "Converting your image to ASCII art...")
        ascii_and_send(call.message)
    elif call.data == "invert":
        bot.answer_callback_query(call.id, "Inverting your image...")
        invert_colors(call.message)
    elif call.data == "mirror":
        bot.answer_callback_query(call.id, "Mirroring your image...")
        mirror_image(call.message)
    elif call.data == "colorrizer":
        bot.answer_callback_query(call.id, "Colorrizing your image...")
        convert_to_heatmap(call.message)
    elif call.data == "resize":
        bot.answer_callback_query(call.id, "Resizing your image...")
        resize_for_sticker (call.message)
    elif call.data == "joke":
        bot.answer_callback_query(call.id, "I'm not funny.")

    else:
        bot.answer_callback_query(call.id, "I don't understand your request.")


def pixelate_and_send(message):
    """
    Огрубление изображения
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    pixelated = pixelate_image(image, 20)

    output_stream = io.BytesIO()
    pixelated.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def ascii_and_send(message):
    """
    Преобразование изображения в ASCII-арт
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    ascii_art = image_to_ascii(image_stream)
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")


def invert_colors(message):
    """
    Инвертирование цветов
    """
    file_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)

    image = Image.open(image_stream)
    inverted = ImageOps.invert(image)
    output_stream = io.BytesIO()
    inverted.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def mirror_image(message):
    """
    Отражение изображения слева направо
    """
    file_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    mirrored = image.transpose(Image.FLIP_LEFT_RIGHT)
    output_stream = io.BytesIO()
    mirrored.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def convert_to_heatmap(message):
    """
    Преобразование изображения в тепловую карту
    """
    file_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    heatmap = ImageOps.colorize(grayify(image),(0, 0, 0), (255, 255, 255))
    output_stream = io.BytesIO()
    heatmap.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def  resize_for_sticker (message):
    """
    Ресайз изображения для стикера
    """
    size = (128, 128)
    file_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    width, height = image.size
    if width > height:
        ratio = width / size[0]
        new_height = int(height / ratio)
        new_size = (size[0], new_height)
    else:
        ratio = height / size[1]
        new_width = int(width / ratio)
        new_size = (new_width, size[1])
    resized = image.resize(new_size)
    output_stream = io.BytesIO()
    resized.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_sticker(message.chat.id, output_stream)


bot.polling(none_stop=True)
