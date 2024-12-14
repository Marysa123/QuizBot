import aiosqlite
import main
from question import quiz_data
import question

async def create_results_table():
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (user_id INTEGER, result TEXT)''')
        await db.commit()

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (user_id INTEGER, result TEXT)''')  # Новая таблица для результатов
        # Сохраняем изменения
        await db.commit()

async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()
        
async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect('quiz_bot.db') as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0                

async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = main.generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def get_question(message, user_id):
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = question.quiz_data[current_question_index]['correct_option']
    opts = question.quiz_data[current_question_index]['options']
    kb = main.generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{question.quiz_data[current_question_index]['question']}", reply_markup=kb)

async def save_user_answer(user_id, answer):
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute('INSERT INTO quiz_results (user_id, result) VALUES (?, ?)', (user_id, answer))
        await db.commit()

async def get_user_results(user_id):
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT result FROM quiz_results WHERE user_id = ?', (user_id,)) as cursor:
            results = await cursor.fetchall()
            return "\n".join([result[0] for result in results]) if results else "Нет результатов."


async def clear_user_answers(user_id):
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute('DELETE FROM quiz_results WHERE user_id = ?', (user_id,))
        await db.commit()
