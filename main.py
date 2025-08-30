import logging
import os
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler, CallbackQueryHandler, CallbackContext
)
from config import BOT_TOKEN, ADMIN_ID
import sqlite_db as db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Определяем состояния для анкеты
FULL_NAME, PHONE, EXPERIENCE = range(3)

# Путь к папке с изображениями
IMAGES_DIR = 'images'

# Тексты для разделов (ЗАПОЛНИТЕ СВОИМИ ДАННЫМИ!)
CLUB_INFO = """
🎒 Добро пожаловать в турклуб Восхождение!

Ты хочешь ходить в походы, путешествовать по родному Башкортостану и за его пределами? Участвовать в соревнованиях: бегать по лесам, преодолевать препятствия и зарабатывать медали? Тогда тебе точно к нам!
"""

SPORT_ACHIEVEMENTS = """
🏆 Наши спортивные достижения:
• 3 место на Всероссийских соревнованиях по спортивному туризму "Весенний призыв" (2025)
• 2 место на Всероссийских студенческих соревнованиях по спортивному туризму (2023, 2024)
• Участники Всероссийской универсиады по спортивному ориентированию (2024)
• А также множество других всероссийских и региональных соревнований по спортивному туризму, ориентированию и рогейну
"""

GRANT_ACHIEVEMENTS = """
🏅 Наши гранты и проекты:
• Выиграли грантов на сумму более 5 миллионов рублей
• Наши проекты это: "Открой Урал", "Чистые горы", Фестиваль спортивного туризма "Рекорд"
• А ещё организовываем множество других соревнований в регионе!
"""

ACTIVITIES = """
🌄 Наша активность: 
• Тренировки по спортивному туризму и ориентированию
• Соревнования по пешеходному, горному, водному видам туризма от межвузовского до всероссийского уровня
• Соревнования по спортивному ориентированию, рогейну и трейлраннингу
• Походы по Башкирии и России
• Много новых знакомств, хорошие друзья на всю жизнь
• Участие в совместных проектах, в том числе и в грантовых
"""

CURRENT_MEMBERS = """
🧗‍♂️ Актив клуба:
• Семенова Софья Андреевна (Руководитель) - @Sonya_Sem
• Кильбахтина Анастасия Маратовна (Заместитель руководителя) - @Ana_astassi
• Кулешов Семен Евгеньевич (Тренер по спортивному ориентированию) - @Smyon_K
• А также: Афанасьева Полина, Галлямов Ильназ, Саяпов Радмир, Сухарев Павел, Яковлев Артур и другие...
"""

PLANS = """
📅 Планы на предстоящий сезон:
• Сентябрь: День открытых дверей для первокурсников, Уфимский международный марафон, Первенство РБ, соревнования по спортивному ориентированию
• Октябрь: Всероссийские соревнования по спортивному туризму "Кубок памяти К.П. Хомякова", Кольцо-24
• Ноябрь: Кубок РБ по горному туризму, соревнования по ночному спортивному ориентированию "Под звездами" и "Сова"
• Декабрь: Новый год в турклубе, "Новогодняя гонка" в городе Челябинск
"""

TRAINING_SCHEDULE = """
🏋️ График тренировок:

Понедельник:
• 16:00-18:00

Вторник:
• 16:00-18:00

Четверг:
• 16:00-18:00

Более подробный график обсуждается в беседах клуба.
"""

# Клавиатура главного меню
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("О турклубе ℹ️", callback_data='menu_about')],
        [InlineKeyboardButton("Наш актив 👥", callback_data='menu_members')],
        [InlineKeyboardButton("Планы на сезон 📅", callback_data='menu_plans')],
        [InlineKeyboardButton("График тренировок 🕐", callback_data='training_schedule')],
        [InlineKeyboardButton("Записаться в клуб 🎒", callback_data='menu_join')],
        [
            InlineKeyboardButton("Наши соцсети 📸", callback_data='menu_contact'),
            InlineKeyboardButton("Отправить вопрос 💬", url='https://t.me/+yCKiBmrS2I5jNjMy')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для подменю "О турклубе"
def about_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Достижения (спорт) 🏆", callback_data='about_sport')],
        [InlineKeyboardButton("Достижения (гранты) 🏅", callback_data='about_grants')],
        [InlineKeyboardButton("Наши активности 🌄", callback_data='about_activities')],
        [InlineKeyboardButton("← Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура для выбора опыта
def experience_keyboard():
    keyboard = [
        [InlineKeyboardButton("Нет опыта в этих сферах", callback_data='exp_none')],
        [InlineKeyboardButton("Спортивный туризм", callback_data='exp_tourism')],
        [InlineKeyboardButton("Легкая атлетика", callback_data='exp_climbing')],
        [InlineKeyboardButton("Спортивное ориентирование", callback_data='exp_mountain')],
        [InlineKeyboardButton("Беговые лыжи", callback_data='exp_other')],
    ]
    return InlineKeyboardMarkup(keyboard)


# Клавиатура админ-меню
def admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Просмотреть новые заявки", callback_data='admin_new_apps')],
        [InlineKeyboardButton("Просмотреть все заявки", callback_data='admin_all_apps')],
        [InlineKeyboardButton("← Назад", callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(keyboard)


def send_photo_with_caption(update, context, image_name, caption):
    """Отправка фото с подписью с поддержкой разных форматов"""
    supported_formats = ['.jpg', '.jpeg', '.png']

    for format in supported_formats:
        image_path = os.path.join(IMAGES_DIR, f"{image_name}{format}")
        if os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as photo:
                    context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=caption,
                        reply_markup=main_menu_keyboard()
                    )
                return True
            except Exception as e:
                print(f"Ошибка отправки фото {image_path}: {e}")
                return False

    # Если фото не найдено, отправляем только текст
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=caption,
        reply_markup=main_menu_keyboard()
    )
    return True


# ========== ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ ==========

# Команда /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    welcome_text = f"Привет, {user.first_name}! " + CLUB_INFO
    # Если запустил админ - покажем ему спец. меню
    if update.effective_user.id == ADMIN_ID:
        update.message.reply_text(
            "Добро пожаловать в панель администратора!",
            reply_markup=admin_menu_keyboard()
        )
    else:
        update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())


# Команда /admin
def admin_command(update: Update, context: CallbackContext):
    """Команда /admin - доступ только для администратора"""
    if update.effective_user.id == ADMIN_ID:
        update.message.reply_text(
            "Панель администратора:",
            reply_markup=admin_menu_keyboard()
        )
    else:
        update.message.reply_text("⛔ У вас нет доступа к этой команде.")


# Команда /export
def export_command(update: Update, context: CallbackContext):
    """Команда /export - выгрузка базы данных"""
    if update.effective_user.id == ADMIN_ID:
        update.message.reply_text("📦 Отправляю файл базы данных...")
        if db.send_db_to_admin(context, ADMIN_ID):
            update.message.reply_text("✅ Файл отправлен!")
        else:
            update.message.reply_text("❌ Ошибка отправки файла")
    else:
        update.message.reply_text("⛔ Нет доступа к этой команде")


# Обработчик нажатий на инлайн-кнопки
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Если это URL-кнопка, просто выходим - Telegram сам откроет ссылку
    if query.data.startswith('http'):
        return

    data = query.data

    # Главное меню
    if data == 'menu_about':
        # Вместо редактирования сообщения, отправляем новое
        query.message.reply_text(
            text="Что тебя интересует?",
            reply_markup=about_menu_keyboard()
        )

    elif data == 'training_schedule':
        try:
            query.delete_message()
        except:
            pass

        # Просто отправляем текстовое сообщение
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TRAINING_SCHEDULE,
            reply_markup=main_menu_keyboard(),
            parse_mode='Markdown'  # Если хотите использовать форматирование
        )

    elif data == 'menu_members':
        # Удаляем сообщение с кнопками только если это текстовое сообщение
        try:
            query.delete_message()
        except:
            pass  # Если не получается удалить (например, это фото), просто продолжаем
        send_photo_with_caption(
            update, context,
            'nash_aktiv',
            CURRENT_MEMBERS
        )

    elif data == 'menu_plans':
        try:
            query.delete_message()
        except:
            pass
        send_photo_with_caption(
            update, context,
            'plany_sezon',
            PLANS
        )

    elif data == 'menu_contact':
        try:
            query.delete_message()
        except:
            pass
        send_photo_with_caption(
            update, context,
            'svyaz_rukovodstvo',
            "Узнай о нас больше в группе ВК https://vk.com/tkvsh?from=groups"
        )

    elif data == 'menu_join':
        # Для текстовых сообщений используем edit_message_text
        try:
            query.edit_message_text(
                text="Отлично! Для записи заполни, пожалуйста, небольшую анкету. Как тебя зовут (ФИО)?")
        except:
            # Если это фото, отправляем новое сообщение
            query.message.reply_text("Отлично! Для записи заполни, пожалуйста, небольшую анкету. Как тебя зовут (ФИО)?")
        return FULL_NAME

    # Подменю "О турклубе"
    elif data == 'about_sport':
        try:
            query.delete_message()
        except:
            pass
        send_photo_with_caption(
            update, context,
            'dostizheniya_sport',
            SPORT_ACHIEVEMENTS
        )

    elif data == 'about_grants':
        try:
            query.delete_message()
        except:
            pass
        send_photo_with_caption(
            update, context,
            'dostizheniya_grants',
            GRANT_ACHIEVEMENTS
        )

    elif data == 'about_activities':
        try:
            query.delete_message()
        except:
            pass
        send_photo_with_caption(
            update, context,
            'nashi_aktivnosti',
            ACTIVITIES
        )

    elif data == 'back_to_main':
        # Для возврата в главное меню тоже нужно обработать оба случая
        try:
            query.edit_message_text(text="Главное меню:", reply_markup=main_menu_keyboard())
        except:
            query.message.reply_text("Главное меню:", reply_markup=main_menu_keyboard())

    # Обработка выбора опыта (из анкеты)
    elif data.startswith('exp_'):
        # Сохраняем выбор опыта
        experience_map = {
            'exp_none': 'Нет опыта в этих сферах',
            'exp_tourism': 'Спортивный туризм',
            'exp_climbing': 'Легкая атлетика',
            'exp_mountain': 'Спортивное ориентирование',
            'exp_other': 'Беговые лыжи'
        }
        context.user_data['experience'] = experience_map[data]

        # Собираем все данные из user_data
        user_data = context.user_data
        full_name = user_data['full_name']
        phone = user_data['phone']
        experience = user_data['experience']
        username = f"@{update.effective_user.username}" if update.effective_user.username else "Не указан"

        # Сохраняем анкету в базу данных
        success = db.add_application_sqlite(
            user_id=update.effective_user.id,
            username=username,
            full_name=full_name,
            phone=phone,
            experience=experience
        )

        # Формируем сообщение для админа
        app_text = (
            "📝 Новая заявка в турклуб!\n"
            f"👤 ФИО: {full_name}\n"
            f"📞 Телефон: {phone}\n"
            f"🔗 TG: {username}\n"
            f"🎯 Опыт: {experience}\n"
            f"🆔 User ID: {update.effective_user.id}\n"
            f"💾 Сохранено: {'✅ В базу данных' if success else '❌ Ошибка сохранения'}"
        )

        # Отправляем анкету админу
        context.bot.send_message(chat_id=ADMIN_ID, text=app_text)

        # Отправляем подтверждение пользователю
        try:
            query.edit_message_text(
                text="Спасибо! Твоя заявка отправлена! 🎉\nС тобой свяжутся в ближайшее время.\nОстались вопросы? Перходи по ссылке 👉 https://t.me/+yCKiBmrS2I5jNjMy",
                reply_markup=main_menu_keyboard()
            )
        except:
            query.message.reply_text(
                text="Спасибо! Твоя заявка отправлена! 🎉\nС тобой свяжутся в ближайшее время.\nОстались вопросы? Перходи по ссылке 👉 https://t.me/+yCKiBmrS2I5jNjMy",
                reply_markup=main_menu_keyboard()
            )

        # Очищаем данные пользователя
        context.user_data.clear()
        return ConversationHandler.END

    # Админ-меню
    elif data == 'admin_new_apps':
        applications = db.get_new_applications_from_db()
        if not applications:
            text = "🟢 Новых заявок нет."
        else:
            text = f"📋 Новые заявки ({len(applications)}):\n\n"
            for app in applications:
                # app[0]=id, [1]=user_id, [2]=username, [3]=full_name, [4]=phone, [5]=experience, [6]=status, [7]=created_at
                text += (
                    f"📍 Заявка #{app[0]}\n"
                    f"👤 {app[3]}\n"
                    f"📞 {app[4]}\n"
                    f"🎯 {app[5]}\n"
                    f"🔗 {app[2]}\n"
                    f"🕐 {app[7]}\n\n"
                )
        try:
            query.edit_message_text(text=text, reply_markup=admin_menu_keyboard())
        except:
            query.message.reply_text(text=text, reply_markup=admin_menu_keyboard())

    elif data == 'admin_all_apps':
        applications = db.get_applications_from_db()
        if not applications:
            text = "📭 Заявок нет."
        else:
            text = f"📋 Все заявки ({len(applications)}):\n\n"
            for app in applications:
                text += (
                    f"📍 #{app[0]} | {app[6]}\n"
                    f"👤 {app[3]}\n"
                    f"📞 {app[4]}\n"
                    f"🎯 {app[5]}\n"
                    f"🕐 {app[7]}\n\n"
                )
        try:
            query.edit_message_text(text=text, reply_markup=admin_menu_keyboard())
        except:
            query.message.reply_text(text=text, reply_markup=admin_menu_keyboard())


# Обработчик для этапов анкеты
def get_full_name(update: Update, context: CallbackContext):
    full_name = update.message.text
    context.user_data['full_name'] = full_name
    update.message.reply_text("Отлично! Теперь укажи свой номер телефона для связи:")
    return PHONE


def get_phone(update: Update, context: CallbackContext):
    phone = update.message.text
    context.user_data['phone'] = phone
    update.message.reply_text(
        "Супер! Занимался(-ась) ли ты ранее чем-то из ниже перечисленного (Отметь свой выбор)?",
        reply_markup=experience_keyboard()
    )
    return EXPERIENCE


# Обработчик для отмены диалога
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Заполнение анкеты отменено.', reply_markup=main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END


# ========== ЗАПУСК БОТА ==========
def main():
    # Создаем updater и передаем ему токен
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обработчик команды /start
    dp.add_handler(CommandHandler("start", start))

    # Обработчик команды /admin
    dp.add_handler(CommandHandler("admin", admin_command))

    # Обработчик команды /export
    dp.add_handler(CommandHandler("export", export_command))

    # Обработчик для обычных инлайн-кнопок
    dp.add_handler(CallbackQueryHandler(button_handler,
                                        pattern='^(menu_about|menu_members|menu_plans|training_schedule|menu_contact|about_|back_to_main|admin_)'))
    # Обработчик диалога (анкеты)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^menu_join$')],
        states={
            FULL_NAME: [MessageHandler(Filters.text & ~Filters.command, get_full_name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            EXPERIENCE: [CallbackQueryHandler(button_handler, pattern='^exp_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_handler)

    # Запускаем бота
    print("Бот запущен...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()