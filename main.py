import os


TOKEN = os.environ['drmbl_token']
chat_id = os.environ['test_chat_id']
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.handler import CancelHandler
import asyncio
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Union
import requests


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
store_file_id = list()

button_hi = InlineKeyboardButton(text='Рассказать историю', callback_data='story')
button_profile = InlineKeyboardButton(text='Анкета знакомств', callback_data='personal_profile')
button_pic_of_dics = InlineKeyboardButton(text='Отправить фотографии', callback_data='send_dudes')

button_menu = KeyboardButton(text = '/menu')

greet_kb = InlineKeyboardMarkup()
greet_kb.add(button_hi)
greet_kb.add(button_pic_of_dics)
greet_kb.add(button_profile)
menu_kb = ReplyKeyboardMarkup(resize_keyboard = True)
menu_kb.add(button_menu)


@dp.callback_query_handler(text=['send_dudes', 'personal_profile', 'story'])
async def random_value(call: types.CallbackQuery):
    if call.data == 'send_dudes':
        await call.message.answer(text='Пожалуйста, отправьте вашу фотографию/фотографии одним сообщением.')
    with open('send_dudes.txt', 'r', encoding = 'utf-8') as msg_txt:
      if call.data == 'personal_profile':
          await call.message.answer(
              text= msg_txt.read())
    if call.data == 'story':
        await call.message.answer(text='Пожалуйста, напишите вашу историю в одном сообщении.\n\nЕсли желаете ДОБАВИТЬ ФОТОГРАФИЮ к вашему рассказу:\n- Либо прикрепите вашу историю к фото\n- Либо, если не хватает знаков, чтобы прикрепить текст к фото, то отправьте их несколькими сообщениями, НО ОТМЕТЬТЕ вашу историю и фотографию.Например, поставьте одинаковый смайл (🌚,👾,💋,🔥 и т.д) перед историей и такой же прикрепите к вашей фотографии.', reply_markup = menu_kb)
    await call.answer()


@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет!\n \n Я чат-бот, созданный для того, чтобы отправлять ваши истории, анкеты знакомств и фотографии "
        "анонимно админам \"Под радужным пледом\".\n \nПожалуйста, выбери нужную кнопку, если желаешь рассказать нам свою "
        "историю❤",
        reply_markup=greet_kb)

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer('Ваша история скоро будет опубликована', reply_markup =  menu_kb)
    messag = message.text.replace("#", "%23")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={messag}"
    print(requests.get(url).json())
    print(message.text)


class AlbumMiddleware(BaseMiddleware):

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler() 
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"]=self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]


@dp.message_handler(is_media_group=True, content_types=types.ContentType.PHOTO)
async def handle_albums(message: types.Message, album: List[types.Message]):
    media_group = types.MediaGroup()
    txt = message.caption
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id

        try:
          
            media_group.attach({"media": file_id, "type": obj.content_type, "caption" : txt })
        except ValueError:
            return await message.answer('Можно отправлять только фото')

    await bot.send_media_group(chat_id, media = media_group)
    await message.answer('Ваши фотографии скоро будут опубликованы!')
  



@dp.message_handler(content_types=["photo"])
async def get_photo(message):
    file_id = message.photo[-1].file_id
    await bot.send_photo(chat_id, file_id, caption = message.caption)
    await message.answer('Ваша фотография скоро будет опубликована!')



if __name__ == '__main__':
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, skip_updates=True)

