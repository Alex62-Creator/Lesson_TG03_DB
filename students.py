import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import logging
# Файл config с ключами необходимо создавать дополнительно
from config import TOKEN

# Создаем объекты классов Bot (отвечает за взаимодействие с Telegram bot API) и Dispatcher (управляет обработкой входящих сообщений и команд)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Создаем класс Form, наследуемый от StatesGroup. Все состояния, которые мы будем собирать, будут группироваться
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()

# Создаем базу данных, в которую будет сохраняться информация от пользователя
def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
	    CREATE TABLE IF NOT EXISTS students (
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    name TEXT NOT NULL,
	    age INTEGER NOT NULL,
	    grade TEXT NOT NULL)
	    ''')
    conn.commit()
    conn.close()

# Инициализируем БД
init_db()

# Обработка команды /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Я бот собирающий данные о студентах\nВведи свое имя:")
    await state.set_state(Form.name)

# Обработка команды /help
@dp.message(Command('help'))
async def help(message: Message):
    await message.answer("Этот бот умеет выполнять команды:\n/start - приветствие\n/help - список команд\n/list - список студентов")

# Обработка команды /list
@dp.message(Command('list'))
async def list(message: Message):
    # Извлекаем информацию из базы данных
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM students''')
    # Получаем все строки
    rows = cur.fetchall()
    # Перебираем все строки и выводим информацию в чат
    for row in rows:
        text = f"Студент: {row[1]} Возраст: {row[2]} Факультет: {row[3]}\n"
        await bot.send_message(message.chat.id, text)
    conn.close()

# Сохраняем имя студента и запрашиваем информацию о его возрасте
@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Сохраняем информацию о возрасте студента и спрашиваем на каком факультете он учится
@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("На каком факультете ты учишься?")
    await state.set_state(Form.grade)

# Сохраняем собранную информацию о студенте в БД
@dp.message(Form.grade)
async def grade(message: Message, state:FSMContext):
    await state.update_data(grade=message.text)
    # Сохраняем все данные в виде словаря в переменной user_data, которые были сохранены в контексте состояния
    user_data = await state.get_data()
    # Добавляем информацию в базу данных
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
       INSERT INTO students (name, age, grade) VALUES (?, ?, ?)''',
                (user_data['name'], user_data['age'], user_data['grade']))
    conn.commit()
    conn.close()

    await message.answer(f"{user_data['name']}, спасибо за регистрацию.")

# Создаем асинхронную функцию main, которая будет запускать наш бот
async def main():
    await dp.start_polling(bot)

# Запускаем асинхронную функцию main
if __name__ == "__main__":
    asyncio.run(main())