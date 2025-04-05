# Имя бота в Telegram Weather_Bot

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
import aiohttp
import logging
# Файл config с ключами необходимо создавать дополнительно
from config import TOKEN, API_KEY_WEATHER

# Создаем объекты классов Bot (отвечает за взаимодействие с Telegram bot API) и Dispatcher (управляет обработкой входящих сообщений и команд)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Создаем класс Form, наследуемый от StatesGroup. Все состояния, которые мы будем собирать, будут группироваться
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    city_weather = State()

# Создаем базу данных, в которую будет сохраняться информация от пользователя
def init_db():
    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
	    CREATE TABLE IF NOT EXISTS users (
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    name TEXT NOT NULL,
	    age INTEGER NOT NULL,
	    city TEXT NOT NULL)
	    ''')
    conn.commit()
    conn.close()

# Инициализируем БД
init_db()

# Обработка команды /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Я бот выдающий прогноз погоды в любом городе!\nКоманды моего управления можно посмотреть в меню.\nКак тебя зовут?")
    await state.set_state(Form.name)

# Обработка команды /help
@dp.message(Command('help'))
async def help(message: Message):
    await message.answer("Этот бот умеет выполнять команды:\n/start - приветствие\n/help - список команд\n/weather - прогноз погоды")

# Обработка команды /weather
@dp.message(Command('weather'))
async def weather(message: Message, state: FSMContext):
    await message.answer("Введи город, в котором хочешь узнать погоду:")
    await state.set_state(Form.city_weather)

# Сохраняем информацию об имени пользователя и запрашиваем информацию о возрасте
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Сохраняем информацию о возрасте пользователя и спрашиваем из какого он города
@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Из какого ты города?")
    await state.set_state(Form.city)

# Сохраняем собранную информацию о пользователе в БД
@dp.message(Form.city)
async def city(message: Message, state:FSMContext):
    await state.update_data(city=message.text)
    # Сохраняем все данные в виде словаря в переменной user_data, которые были сохранены в контексте состояния
    user_data = await state.get_data()
    # Добавляем информацию в базу данных
    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
       INSERT INTO users (name, age, city) VALUES (?, ?, ?)''',
                (user_data['name'], user_data['age'], user_data['city']))
    conn.commit()
    conn.close()
    # Предлагаем узнать погоду в любом городе мира
    await message.answer(f"{user_data['name']}, спасибо за регистрацию.\nДля получения прогноза погоды введи команду /weather или выбери её в меню")

# Запрашиваем погоду с сайта и выводим в чат-бот
@dp.message(Form.city_weather)
async def city_weather(message: Message, state:FSMContext):
    await state.update_data(city_weather=message.text)
    city = message.text
    # Создаем асинхронную HTTP-сессию клиента (позволяет выполнять несколько запросов одновременно, сохраняя определенные параметры, такие как заголовки, файлы и параметры подключения)
    async with aiohttp.ClientSession() as session:
        # Выполняем HTTP-запрос с помощью метода get
        async with session.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY_WEATHER}&units=metric") as response:
            # Если запрос выполнен удачно, выводим информацию в чат
            if response.status == 200:
                weather_data = await response.json()
                main = weather_data['main']
                weather = weather_data['weather'][0]

                temperature = main['temp']
                humidity = main['humidity']
                description = weather['description']

                weather_report = (f"Город - {city}\n"
                                  f"Температура - {temperature}С\n"
                                  f"Влажность воздуха - {humidity}%\n"
                                  f"Описание погоды - {description}")
                await message.answer(weather_report)
            else:
                await message.answer("Не удалось получить данные о погоде")

    # В конце подключения к сессии очищаем состояния
    await state.clear()

# Создаем асинхронную функцию main, которая будет запускать наш бот
async def main():
    await dp.start_polling(bot)

# Запускаем асинхронную функцию main
if __name__ == "__main__":
    asyncio.run(main())