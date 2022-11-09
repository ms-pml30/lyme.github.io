import datetime
import json
import telebot
import sqlite3

db = sqlite3.connect("notes.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS main (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id    BIGINT,
    notes    TEXT,
    schedule TEXT
);""")
db.commit()

TOKEN = "5694397764:AAF2OKaPo_i3IFdcsG7lvojWm0gt5_VhK2Y"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start", "help", "settings"])
def start(message: telebot.types.Message):
    cur.execute("SELECT * FROM main WHERE tg_id = ?;", (message.chat.id,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO main(tg_id) VALUES (?);", (message.chat.id,))
        db.commit()

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("Заметки", "Расписание")

    bot.send_message(message.chat.id, "Нажмите на кнопку:", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def main(message: telebot.types.Message):
    __DAYS = {"1": "Понедельник", "2": "Вторник", "3": "Среда", "4": "Четверг", "5": "Пятница", '6': "Суббота",
              "0": "Воскресенье"}

    match message.text:
        case "Заметки":
            send_message = bot.send_message(message.chat.id, "Загрузка",
                                           reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.delete_message(send_message.chat.id, send_message.message_id)

            cur.execute("SELECT notes FROM main WHERE tg_id = ?;", (message.chat.id,))
            notes = cur.fetchone()[0]

            if notes:
                notes = json.loads(notes)

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(*[telebot.types.InlineKeyboardButton(note[:15] if len(note) >= 16 else note[:], callback_data=f"note_{i}") for i, note in enumerate(notes)], telebot.types.InlineKeyboardButton("Добавить запись", callback_data='addnote_NULL'),
                           telebot.types.InlineKeyboardButton("Назад", callback_data="back_NULL"))

                bot.send_message(message.chat.id, "Выберите запись:", reply_markup=markup)
            else:
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(telebot.types.InlineKeyboardButton("Добавить запись", callback_data='addnote_NULL'),
                           telebot.types.InlineKeyboardButton("Назад", callback_data="back_NULL"))

                bot.send_message(message.chat.id, "Нет записей", reply_markup=markup)
        case "Расписание":
            send_message = bot.send_message(message.chat.id, "Загрузка",
                                            reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.delete_message(send_message.chat.id, send_message.message_id)

            cur.execute("SELECT schedule FROM main WHERE tg_id = ?;", (message.chat.id,))
            schedule = cur.fetchone()[0]

            if schedule:
                schedule = json.loads(schedule)

                today_schedule = schedule[datetime.datetime.now().strftime("%w")]
                if today_schedule is None:
                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(telebot.types.InlineKeyboardButton("Добавить расписание", callback_data="schedule_NULL"),
                               telebot.types.InlineKeyboardButton("Назад", callback_data="back_NULL"))

                    bot.send_message(message.chat.id, f"Нет расписания на сегодня ({__DAYS[datetime.datetime.now().strftime('%w')]})", reply_markup=markup)
                else:
                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(telebot.types.InlineKeyboardButton("Изменить расписание", callback_data="schedule_NULL"),
                               telebot.types.InlineKeyboardButton("Назад", callback_data="back_NULL"))

                    bot.send_message(message.chat.id, f"Расписание на сегодня ({__DAYS[datetime.datetime.now().strftime('%w')]}):\n\n{today_schedule}", reply_markup=markup)
            else:
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(telebot.types.InlineKeyboardButton("Добавить расписание", callback_data="schedule_NULL"), telebot.types.InlineKeyboardButton("Назад", callback_data="back_NULL"))

                bot.send_message(message.chat.id, "Нет расписания", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(callback: telebot.types.CallbackQuery):
    __DAYS = {"1": "Понедельник", "2": "Вторник", "3": "Среда", "4": "Четверг", "5": "Пятница", '6': "Суббота", "0": "Воскресенье"}

    data1, data2, *data3 = callback.data.split("_")

    match data1:
        case "back":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            start(callback.message)
        case "backtonotes":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            callback.message.text = "Заметки"
            main(callback.message)
        case "backtoschedule":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            callback.message.text = "Расписание"
            main(callback.message)
        case "backtodetailshedule":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            Schedule(callback.message)
        case "addnote":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            MakeNote(callback.message)
        case "addschedule":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            Schedule().make_schedule(callback.message, data2)
        case "schedule":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)

            Schedule(callback.message)
        case "detailshedule":
            cur.execute("SELECT schedule FROM main WHERE tg_id = ?;", (callback.message.chat.id,))
            schedule = cur.fetchone()[0]

            if schedule:
                schedule = json.loads(schedule)

                schedule = schedule.get(data2)

                if schedule:
                    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
                    markup.add(telebot.types.InlineKeyboardButton("Изменить", callback_data=f"edit_{data2}_schedule"),
                               telebot.types.InlineKeyboardButton("Удалить", callback_data=f"del_{data2}_schedule"))
                    markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data="backtodetailshedule_NULL"), row_width=1)
                else:
                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(telebot.types.InlineKeyboardButton("Добавить", callback_data=f"addschedule_{data2}"), telebot.types.InlineKeyboardButton("Назад", callback_data="backtodetailshedule_NULL"))
            else:
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(telebot.types.InlineKeyboardButton("Добавить", callback_data=f"addschedule_{data2}"),
                           telebot.types.InlineKeyboardButton("Назад", callback_data="backtodetailshedule_NULL"))

            bot.edit_message_text(chat_id=callback.message.chat.id, text=f"Расписание на {__DAYS[data2]}:\n\n{schedule}" if schedule else f"Нет расписания на {__DAYS[data2]}", message_id=callback.message.message_id,
                                  reply_markup=markup)
        case "note":
            cur.execute("SELECT notes FROM main WHERE tg_id = ?;", (callback.message.chat.id,))
            notes = json.loads(cur.fetchone()[0])

            note = notes[int(data2)]

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            markup.add(telebot.types.InlineKeyboardButton("Изменить", callback_data=f"edit_{data2}_note"), telebot.types.InlineKeyboardButton("Удалить", callback_data=f"del_{data2}_note"))
            markup.add(telebot.types.InlineKeyboardButton("Назад", callback_data="backtonotes_NULL"), row_width=1)

            bot.edit_message_text(chat_id=callback.message.chat.id, text=note, message_id=callback.message.message_id, reply_markup=markup)
        case "del":
            match data3[0]:
                case "note":
                    cur.execute("SELECT notes FROM main WHERE tg_id = ?;", (callback.message.chat.id,))
                    notes = cur.fetchone()[0]

                    notes = json.loads(notes)

                    del notes[int(data2)]

                    if notes:
                        cur.execute('UPDATE main SET notes = ? WHERE tg_id = ?', (json.dumps(notes), callback.message.chat.id))
                    else:
                        cur.execute('UPDATE main SET notes = ? WHERE tg_id = ?', (None, callback.message.chat.id))

                    db.commit()

                    bot.delete_message(callback.message.chat.id, callback.message.message_id)

                    callback.message.text = "Заметки"
                    main(callback.message)
                case "schedule":
                    bot.delete_message(callback.message.chat.id, callback.message.message_id)

                    Schedule().del_schedule(callback.message, data2)

        case "edit":
            match data3[0]:
                case "note":
                    bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)

                    EditNote(callback.message, data2)
                case "schedule":
                    bot.delete_message(callback.message.chat.id, callback.message.message_id)

                    Schedule().make_schedule(callback.message, data2)


class Schedule:
    __DAYS = ["Понедельник", "Вторник", "Среду", "Четверг", "Пятницу", "Субботу", "Воскресенье"]

    def __init__(self, message: telebot.types.Message = None):
        if not message is None:
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(*[telebot.types.InlineKeyboardButton(day, callback_data=f"detailshedule_{i if i != 7 else 0}") for i, day in enumerate(self.__DAYS, 1)], telebot.types.InlineKeyboardButton("Назад", callback_data="backtoschedule_NULL"), telebot.types.InlineKeyboardButton("Назад в меню", callback_data="back_NULL"))

            bot.send_message(message.chat.id, "Выберите день недели:", reply_markup=markup)

    def make_schedule(self, message: telebot.types.Message, id):
        self.id = id

        send_message = bot.send_message(message.chat.id, "Отправьте расписание:")

        bot.register_next_step_handler(send_message, self.get_text)

    def get_text(self, message: telebot.types.Message):
        cur.execute("SELECT schedule FROM main WHERE tg_id = ?;", (message.chat.id,))
        schedule = cur.fetchone()[0]

        if schedule:
            schedule = json.loads(schedule)
        else:
            schedule = {"1": None, "2": None, "3": None, "4": None, "5": None, '6': None, "0": None}

        schedule[self.id] = message.text

        cur.execute('UPDATE main SET schedule = ? WHERE tg_id = ?', (json.dumps(schedule), message.chat.id))
        db.commit()

        self.__init__(message)

    def del_schedule(self, message: telebot.types.Message, id):
        cur.execute("SELECT schedule FROM main WHERE tg_id = ?;", (message.chat.id,))
        schedule = cur.fetchone()[0]

        schedule = json.loads(schedule)

        schedule[id] = None

        if schedule == {"1": None, "2": None, "3": None, "4": None, "5": None, '6': None, "0": None}:
            schedule = None

        cur.execute('UPDATE main SET schedule = ? WHERE tg_id = ?', (json.dumps(schedule) if schedule else schedule, message.chat.id))
        db.commit()

        self.__init__(message)

class MakeNote:
    def __init__(self, message: telebot.types.Message):
        send_message = bot.send_message(message.chat.id, "Отправьте заметку:")

        bot.register_next_step_handler(send_message, self.get_text)

    def get_text(self, message: telebot.types.Message):
        cur.execute("SELECT notes FROM main WHERE tg_id = ?;", (message.chat.id,))
        notes = cur.fetchone()[0]

        if notes:
            notes = json.loads(notes)
        else:
            notes = []

        notes.append(message.text)
        cur.execute('UPDATE main SET notes = ? WHERE tg_id = ?', (json.dumps(notes), message.chat.id))
        db.commit()

        message.text = "Заметки"
        main(message)

class EditNote:
    def __init__(self, message: telebot.types.Message, id):
        self.id = int(id)

        send_message = bot.send_message(message.chat.id, "Отправьте новый текст: ")
        bot.register_next_step_handler(send_message, self.get_text)

    def get_text(self, message: telebot.types.Message):
        cur.execute("SELECT notes FROM main WHERE tg_id = ?;", (message.chat.id,))
        notes = cur.fetchone()[0]

        notes = json.loads(notes)

        notes[self.id] = message.text

        cur.execute('UPDATE main SET notes = ? WHERE tg_id = ?', (json.dumps(notes), message.chat.id))

        db.commit()

        message.text = "Заметки"
        main(message)

bot.polling()

cur.close()
db.close()
