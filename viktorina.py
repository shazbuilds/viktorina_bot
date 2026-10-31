
from config import TOKEN
from telebot import TeleBot
from telebot import custom_filters
from telebot import types
from telebot.handler_backends import State
from telebot.handler_backends import StatesGroup
from telebot.storage import StateMemoryStorage



BTN_START = "🎮 Start"
BTN_HELP = "ℹ️ Help"

QUESTIONS = [
    ["Which brackets are used for a list in Python?", ["( )", "[ ]", "{ }"], 1],
    ["What is 2 ** 3?", ["6", "8", "9"], 1],
    ["Who gives you a bot token?", ["@BotFather", "@Python", "Google"], 0],
]

storage = StateMemoryStorage()
bot = TeleBot(TOKEN, state_storage=storage)

class Quiz(StatesGroup):
    name = State()
    question = State()


def menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(BTN_START, BTN_HELP)
    return keyboard


def answer_buttons(question_index):
    keyboard = types.InlineKeyboardMarkup()
    answers = QUESTIONS[question_index][1]

    for number in range(len(answers)):
        button = types.InlineKeyboardButton(
            text=answers[number],
            callback_data="answer_" + str(number),
        )
        keyboard.add(button)

    return keyboard


def send_question(chat_id, question_index):
    number = question_index + 1
    text = "❓ Question " + str(number) + ": " + QUESTIONS[question_index][0]
    bot.send_message(chat_id, text, reply_markup=answer_buttons(question_index))


@bot.message_handler(commands=["start"], state="*")
def start(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Hello! 🧠 Welcome to the Mini Quiz.",
        reply_markup=menu(),
    )


@bot.message_handler(commands=["test"], state="*")
def test(message):
    send_question(message.chat.id, 0)


@bot.message_handler(commands=["cancel"], state="*")
def cancel(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "❌ Stopped", reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == BTN_HELP)
def help_message(message):
    text = (
        "🎮 Start - 3 questions. Press the answer buttons.\n"
        "/cancel - stop the quiz"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == BTN_START)
def begin_quiz(message):
    bot.set_state(message.from_user.id, Quiz.name, message.chat.id)
    bot.send_message(
        message.chat.id,
        "Your name?",
        reply_markup=types.ReplyKeyboardRemove(),
    )

@bot.message_handler(state=Quiz.name)
def get_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    bot.set_state(user_id, Quiz.question, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data["name"] = message.text
        data["index"] = 0
        data["score"] = 0

    send_question(chat_id, 0)

@bot.message_handler(state=Quiz.question)
def text_during_question(message):
    bot.send_message(message.chat.id, "Press one of the buttons 👆 (or /cancel)")

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("answer_"),
    state=Quiz.question,
)
def get_answer(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    chosen = int(call.data.split("_")[1])

    with bot.retrieve_data(user_id, chat_id) as data:
        index = data["index"]
        correct = QUESTIONS[index][2]

        if chosen == correct:
            data["score"] = data["score"] + 1
            mark = "✅ Correct!"
        else:
            right_text = QUESTIONS[index][1][correct]
            mark = "❌ Wrong. Correct answer: " + right_text

        data["index"] = index + 1

        name = data["name"]
        score = data["score"]
        next_index = data["index"]

    old_text = "❓ Question " + str(index + 1) + ": " + QUESTIONS[index][0]
    bot.edit_message_text(
        old_text + "\n" + mark,
        chat_id,
        call.message.message_id,
    )
    bot.answer_callback_query(call.id)

    if next_index < len(QUESTIONS):
        send_question(chat_id, next_index)
    else:
        bot.delete_state(user_id, chat_id)
        result = name + ", your result: " + str(score) + "/" + str(len(QUESTIONS))
        bot.send_message(chat_id, "🏁 " + result, reply_markup=menu())


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def old_button(call):
    bot.answer_callback_query(
        call.id,
        "The game is over. Press 🎮 Start",
        show_alert=True,
    )

@bot.message_handler(func=lambda m: True)
def other(message):
    bot.send_message(
        message.chat.id,
        "I did not understand 🤔 Please use the buttons below.",
        reply_markup=menu(),
    )

bot.add_custom_filter(custom_filters.StateFilter(bot))

print("Bot is running...")
bot.infinity_polling()
