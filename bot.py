#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QoraCoders SMM Panel - JSON fayl asosida (MySQL kerak emas)
Faqat BOT_TOKEN va ADMIN_ID kerak.
"""

import os
import json
import base64
import hashlib
import random
import string
import requests
import datetime
from flask import Flask, request, jsonify

# ===========================================================================
# SOZLAMALAR - Railway Variables orqali olinadi
# ===========================================================================

TELEGRAM_API_KEY = os.getenv("BOT_TOKEN", "")
ADMIN_ID         = os.getenv("ADMIN_ID", "")
BOT_USERNAME     = os.getenv("BOT_USERNAME", "")

SIM_KEY  = os.getenv("SIM_KEY", "c9947f74188921527252c1cb9b14816f")
SIM_FOIZ = int(os.getenv("SIM_FOIZ", "50"))   # Ustama foiz (%)
VALYUTA  = "so'm"
SALESEEN_URL = "https://saleseen.uz/api/sms"

# ===========================================================================
# JSON FAYL MA'LUMOTLAR BAZASI
# ===========================================================================

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("user", exist_ok=True)
os.makedirs("set", exist_ok=True)

def _load(name):
    path = f"{DATA_DIR}/{name}.json"
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(name, data):
    path = f"{DATA_DIR}/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_list(name):
    path = f"{DATA_DIR}/{name}.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_list(name, data):
    path = f"{DATA_DIR}/{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Foydalanuvchilar ---

def get_user(uid):
    users = _load("users")
    return users.get(str(uid))

def save_user(uid, user):
    users = _load("users")
    users[str(uid)] = user
    _save("users", users)

def all_users():
    return list(_load("users").values())

def count_users():
    return len(_load("users"))

# --- Buyurtmalar ---

def get_orders():
    return _load_list("orders")

def save_orders(orders):
    _save_list("orders", orders)

def add_order(order):
    orders = get_orders()
    orders.append(order)
    save_orders(orders)
    return len(orders)

def get_user_orders(uid):
    return [o for o in get_orders() if str(o.get("user_id")) == str(uid)]

# --- Xizmatlar ---

def get_services():
    return _load_list("services")

def get_service(sid):
    for s in get_services():
        if str(s.get("service_id")) == str(sid):
            return s
    return None

# --- Kategoriyalar ---

def get_categories():
    return _load_list("categories")

def get_subcategories(cat_id):
    return [c for c in _load_list("subcategories") if str(c.get("category_id")) == str(cat_id)]

# --- Provayderlar ---

def get_providers():
    return _load_list("providers")

def get_provider(pid):
    for p in get_providers():
        if str(p.get("id")) == str(pid):
            return p
    return None

# --- Sozlamalar ---

def get_settings():
    s = _load("settings")
    if not s:
        s = {
            "start":      "Salom {name}! Botga xush kelibsiz.\nBalansingiz: {balance} so'm",
            "referal":    "1000",
            "ref_status": "on",
            "bonus":      "500",
            "status":     "active",
            "percent":    "40"
        }
        _save("settings", s)
    return s

# ===========================================================================
# YORDAMCHI FUNKSIYALAR
# ===========================================================================

def enc(mode, value):
    if mode == "encode":
        return base64.b64encode(str(value).encode()).decode()
    elif mode == "decode":
        try:
            return base64.b64decode(str(value)).decode("utf-8", errors="ignore")
        except Exception:
            return value
    return value

def generate_code(length=7):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

def _write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(content))

def _read_step(uid):
    return _read_file(f"user/{uid}.step") or ""

def _write_step(uid, step):
    _write_file(f"user/{uid}.step", step)

def _del_step(uid):
    try:
        os.unlink(f"user/{uid}.step")
    except Exception:
        pass

def _get_currency_rate(currency):
    rate_map = {"UZS": 1, "USD": 12500, "RUB": 130, "INR": 150, "TRY": 400}
    return rate_map.get(str(currency).upper(), 1)

# ===========================================================================
# TELEGRAM BOT API
# ===========================================================================

def bot_call(method, data=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/{method}"
    try:
        resp = requests.post(url, json=data or {}, timeout=15)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sms(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": f"<b>{text}</b>",
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return bot_call("sendMessage", payload)

def edit_msg(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": f"<b>{text}</b>",
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return bot_call("editMessageText", payload)

def del_msg(chat_id, message_id):
    return bot_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def keyboard(buttons):
    return json.dumps({"inline_keyboard": buttons})

# ===========================================================================
# MENYULAR
# ===========================================================================

def main_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [
            [{"text": "🛍 Buyurtma berish"}, {"text": "📞 Nomer olish"}],
            [{"text": "🔐 Mening hisobim"}, {"text": "💰 Hisobni to'ldirish"}],
            [{"text": "🛒 Buyurtma holati"}, {"text": "🚀 Referal yig'ish"}],
            [{"text": "☎️ Administrator"},   {"text": "🤝 Hamkorlik (API)"}],
        ]
    })

def admin_panel_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [
            [{"text": "⚙️ Asosiy sozlamalar"}, {"text": "📊 Statistika"}],
            [{"text": "🔔 Xabar yuborish"},    {"text": "🛍 Chegirmalar"}],
            [{"text": "👤 Foydalanuvchini boshqarish"}],
            [{"text": "⏰ Cron sozlamasi"},    {"text": "📞 Nomer API balans"}],
            [{"text": "🤖 Bot holati"},         {"text": "🎮 Donat sozlamalari"}],
            [{"text": "⏪ Orqaga"}],
        ]
    })

def back_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [[{"text": "➡️ Orqaga"}]]
    })

# ===========================================================================
# FOYDALANUVCHI QO'SHISH
# ===========================================================================

def add_user(uid):
    existing = get_user(uid)
    if not existing:
        api_key = hashlib.md5(os.urandom(16)).hexdigest()
        referal = generate_code()
        new_user = {
            "id":       str(uid),
            "user_id":  count_users() + 1,
            "status":   "active",
            "balance":  "0",
            "outing":   "0",
            "api_key":  api_key,
            "referal":  referal
        }
        save_user(uid, new_user)

def join_check(uid):
    channel_data = _read_file("set/channel")
    if not channel_data:
        return True
    channels = [c for c in channel_data.split("\n") if c.strip()]
    for ch in channels:
        resp = bot_call("getChatMember", {"chat_id": ch, "user_id": uid})
        status = resp.get("result", {}).get("status", "")
        if status not in ("creator", "administrator", "member"):
            return False
    return True

# ===========================================================================
# WEBHOOK HANDLER
# ===========================================================================

def handle_update(update: dict):
    global BOT_USERNAME

    message  = update.get("message", {})
    callback = update.get("callback_query", {})

    cid2 = callback.get("message", {}).get("chat", {}).get("id")
    mid2 = callback.get("message", {}).get("message_id")
    data = callback.get("data", "")
    qid  = callback.get("id")

    cid     = message.get("chat", {}).get("id")
    mid     = message.get("message_id")
    text    = message.get("text", "")
    name    = message.get("from", {}).get("first_name", "")
    chat_id = cid2 or cid

    settings = get_settings()
    m        = main_menu()

    # Bot bloklandi
    bot_del = update.get("my_chat_member", {})
    if bot_del:
        botdel_status = bot_del.get("new_chat_member", {}).get("status")
        botdel_id     = bot_del.get("from", {}).get("id")
        if botdel_status == "kicked":
            u = get_user(botdel_id)
            if u:
                u["status"] = "deactive"
                save_user(botdel_id, u)

    if chat_id:
        u = get_user(chat_id)
        if u and u.get("status") == "deactive":
            return

    step = _read_step(cid or chat_id or 0)

    # /start
    if text == "/start" and join_check(cid):
        add_user(cid)
        user       = get_user(cid)
        start_text = settings.get("start", "Xush kelibsiz!")
        start_text = start_text.replace("{name}", str(name))
        start_text = start_text.replace("{balance}", str(user["balance"]) if user else "0")
        start_text = start_text.replace("{time}", datetime.datetime.now().strftime("%H:%M"))
        sms(cid, start_text, m)
        return

    # /start user<ID> — referal
    if text and text.startswith("/start user"):
        ref_uid = text.replace("/start user", "").strip()
        ref_user = get_user(ref_uid)
        if ref_user and str(ref_user["id"]) != str(cid):
            existing = get_user(cid)
            if not existing:
                if join_check(cid):
                    bonus = float(settings.get("referal", "0"))
                    ref_user["balance"] = str(float(ref_user["balance"]) + bonus)
                    save_user(ref_uid, ref_user)
                else:
                    _write_file(f"user/{cid}.id", str(ref_uid))
                bot_call("sendMessage", {
                    "chat_id": ref_user["id"],
                    "text": f"<b>📳 Sizda yangi <a href='tg://user?id={cid}'>taklif</a> mavjud!</b>",
                    "parse_mode": "HTML"
                })
        add_user(cid)
        sms(cid, "🖥 Asosiy menyudasiz", m)
        return

    # Orqaga
    if text in ("➡️ Orqaga", "⏪ Orqaga"):
        _del_step(cid)
        sms(cid, "🖥️ Asosiy menyudasiz", m)
        return

    # Admin panel
    if text == "🗄️ Boshqaruv" and str(cid) == str(ADMIN_ID):
        _del_step(cid)
        sms(cid, "🖥️ Boshqaruv paneli", admin_panel_menu())
        return

    # Statistika
    if text == "📊 Statistika" and str(cid) == str(ADMIN_ID):
        users_list   = all_users()
        orders_list  = get_orders()
        active_users = len([u for u in users_list if u.get("status") == "active"])
        completed    = len([o for o in orders_list if o.get("status") == "Completed"])
        pending      = len([o for o in orders_list if o.get("status") == "Pending"])
        in_progress  = len([o for o in orders_list if o.get("status") == "In progress"])
        canceled     = len([o for o in orders_list if o.get("status") == "Canceled"])
        sms(cid,
            f"📊 Statistika\n"
            f"• Jami foydalanuvchilar: {len(users_list)} ta\n"
            f"• Aktiv: {active_users} ta\n"
            f"• O'chirilgan: {len(users_list) - active_users} ta\n\n"
            f"📊 Buyurtmalar\n"
            f"• Jami: {len(orders_list)} ta\n"
            f"• Bajarilgan: {completed} ta\n"
            f"• Kutilayotgan: {pending} ta\n"
            f"• Jarayonda: {in_progress} ta\n"
            f"• Bekor qilingan: {canceled} ta\n\n"
            f"📊 Xizmatlar: {len(get_services())} ta",
            admin_panel_menu()
        )
        _del_step(cid)
        return

    # Mening hisobim
    if text == "🔐 Mening hisobim" and join_check(cid):
        user = get_user(cid)
        if not user:
            sms(cid, "Foydalanuvchi topilmadi.", m)
            return
        user_orders = get_user_orders(cid)
        sms(cid,
            f"👤 Sizning ID raqamingiz: {cid}\n\n"
            f"♻️ Holatingiz: {user['status']}\n"
            f"💵 Balansingiz: {user['balance']} so'm\n"
            f"📊 Buyurtmalaringiz: {len(user_orders)} ta\n"
            f"💰 Kiritilgan summa: {user['outing']} so'm",
            keyboard([
                [{"text": "💰 Hisobni to'ldirish", "callback_data": "menu=tolov"},
                 {"text": "🚀 Referal",             "callback_data": "pul_ishla"}],
                [{"text": "🎟 Promokod",             "callback_data": "kodpromo"},
                 {"text": "⭐️ Premium",              "callback_data": "preimium"}],
            ])
        )
        return

    # Referal
    if text == "🚀 Referal yig'ish" and join_check(cid):
        user = get_user(cid)
        if user:
            if not BOT_USERNAME:
                info = bot_call("getMe")
                BOT_USERNAME = info.get("result", {}).get("username", "bot")
            bonus = settings.get("referal", "0")
            sms(cid,
                f"Sizning referal havolangiz:\n\nhttps://t.me/{BOT_USERNAME}?start=user{user['id']}\n\n"
                f"Har bir taklif uchun {bonus} so'm beriladi.\n\n"
                f"👤 ID raqam: {user['id']}",
                keyboard([[{"text": "💎 Konkurs (🏆 TOP 10)", "callback_data": "konkurs"}]])
            )
        return

    # Buyurtma berish
    if text == "🛍 Buyurtma berish" and join_check(cid):
        categories = get_categories()
        if not categories:
            sms(cid, "⚠️ Tarmoqlar topilmadi.", None)
            return
        btns = [[{"text": enc("decode", c["category_name"]),
                  "callback_data": f"tanla1={c['category_id']}"}]
                for c in categories]
        btns.append([{"text": "🔥 Eng yaxshi xizmatlar ⚡️", "url": "https://t.me"}])
        sms(cid, "✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Ijtimoiy tarmoqni tanlang.",
            keyboard(btns))
        return

    # Administrator
    if text == "☎️ Administrator" and join_check(cid):
        sms(cid, "⭐ Bizga savollaringiz bormi?\n\n📑 Murojaat matnini yozib yuboring.", back_menu())
        _write_step(cid, "murojaat")
        return

    if step == "murojaat":
        sms(cid, "✅ Murojaatingiz qabul qilindi", m)
        bot_call("copyMessage", {
            "chat_id": ADMIN_ID,
            "from_chat_id": cid,
            "message_id": mid,
            "reply_markup": keyboard([
                [{"text": "👁️ Ko'rish",      "url": f"tg://user?id={cid}"}],
                [{"text": "📑 Javob yozish", "callback_data": f"javob={cid}"}],
            ])
        })
        _write_step(cid, "")
        return

    # API kalit
    if text == "🤝 Hamkorlik (API)" and join_check(cid):
        user = get_user(cid)
        if user:
            sms(cid,
                f"⭐ Sizning API kalitingiz:\n<code>{user['api_key']}</code>\n\n"
                f"💵 API hisobi: {user['balance']} so'm",
                keyboard([[{"text": "🔄 APIni yangilash", "callback_data": "apidetail=newkey"}]])
            )
        return

    # Link kiritish jarayoni
    if step.startswith("link="):
        params_raw = step.replace("link=", "")
        _write_file(f"user/{cid}.link", text.strip())
        _write_file(f"user/{cid}.params", params_raw)
        _write_step(cid, "order=default=sp1")
        sms(cid, "⬇️ Kerakli buyurtma miqdorini kiriting:", back_menu())
        return

    # Miqdor kiritish jarayoni
    if step.startswith("order="):
        params_raw = _read_file(f"user/{cid}.params") or ""
        link_file  = _read_file(f"user/{cid}.link") or ""
        if not params_raw:
            sms(cid, "Xatolik: parametrlar topilmadi.", m)
            _del_step(cid)
            return
        parts = params_raw.split("=")
        if len(parts) < 6:
            sms(cid, "Xatolik: parametrlar noto'g'ri.", m)
            _del_step(cid)
            return
        oid, omin, omax, orate, prov, serv = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        try:
            qty = int(text.strip())
        except ValueError:
            sms(cid, "⚠️ Iltimos, faqat raqam kiriting.", back_menu())
            return
        if qty < int(omin):
            sms(cid, f"⚠️ Minimal miqdor: {omin} ta", back_menu())
            return
        if qty > int(omax):
            sms(cid, f"⚠️ Maksimal miqdor: {omax} ta", back_menu())
            return
        user = get_user(cid)
        if not user:
            sms(cid, "Foydalanuvchi topilmadi.", m)
            return
        narxi = float(orate) / 1000 * qty
        if float(user["balance"]) < narxi:
            sms(cid, f"❌ Balansingiz yetarli emas!\n\nKerakli: {narxi:.0f} so'm\nBalans: {user['balance']} so'm", m)
            _del_step(cid)
            return
        provider = get_provider(prov)
        if not provider:
            sms(cid, "❌ Provayder topilmadi.", m)
            _del_step(cid)
            return
        try:
            resp = requests.get(
                f"{provider['api_url']}?key={provider['api_key']}&action=add"
                f"&service={oid}&link={link_file}&quantity={qty}",
                timeout=15, verify=False
            )
            j = resp.json()
        except Exception:
            sms(cid, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.", m)
            _del_step(cid)
            return
        jid = j.get("order")
        if not jid:
            sms(cid, "❌ Buyurtma qabul qilinmadi.", m)
            _del_step(cid)
            return
        ball = float(user["balance"]) - narxi
        user["balance"] = str(round(ball, 2))
        save_user(cid, user)
        order_id = add_order({
            "order_id":    len(get_orders()) + 1,
            "user_id":     str(cid),
            "api_order":   str(jid),
            "service":     serv,
            "quantity":    qty,
            "link":        link_file,
            "retail":      str(round(narxi, 2)),
            "status":      "Pending",
            "provider":    prov,
            "order_create": datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        })
        try:
            os.unlink(f"user/{cid}.link")
        except Exception:
            pass
        _del_step(cid)
        sms(cid,
            f"✅ Buyurtma qabul qilindi!\n\n"
            f"🆔 Buyurtma ID: {order_id}\n"
            f"📦 Miqdor: {qty} ta\n"
            f"💵 Narxi: {narxi:.0f} so'm\n"
            f"💰 Qolgan balans: {ball:.0f} so'm",
            m
        )
        return

    # 📞 Nomer olish
    if text == "📞 Nomer olish" and join_check(cid):
        sms(cid,
            "📞 Nomer olish bo'limi\n\n"
            "⚡️ SaleSeen orqali tayyor Telegram akkauntlar:\n\n"
            "✅ Oldindan faollashtirilgan\n"
            "✅ 2FA (2-bosqichli tekshiruv) yo'q\n"
            "✅ Kod darhol beriladi\n"
            "✅ Bir nechta mamlakat mavjud\n\n"
            "❗️ Shartlar:\n"
            "- Nomer sotib olingandan so'm pul qaytarilmaydi\n"
            "- Balans yetarli bo'lishi shart\n"
            "- Nomer bir martalik foydalanish uchun",
            keyboard([
                [{"text": "✅ Roziman, davom etish", "callback_data": "hop"}],
                [{"text": "❌ Bekor qilish", "callback_data": "main"}],
            ])
        )
        return

    # 💰 Hisobni to'ldirish
    if text == "💰 Hisobni to'ldirish" and join_check(cid):
        tolov_text = (
            "💳 Hisobni to'ldirish\n\n"
            "To'lov usulini tanlang yoki admin bilan bog'laning:\n\n"
            "💡 Admin orqali to'ldirish uchun:\n"
            "1. To'lov miqdorini yozing\n"
            "2. Chek/screenshot yuboring\n"
            "3. Admin tasdiqlaydi"
        )
        sms(cid, tolov_text, keyboard([
            [{"text": "📲 Admin orqali to'ldirish", "callback_data": "menu=tolov"}],
            [{"text": "🔙 Orqaga", "callback_data": "main"}],
        ]))
        return

    # 🛒 Buyurtma holati
    if text == "🛒 Buyurtma holati" and join_check(cid):
        user = get_user(cid)
        if not user:
            sms(cid, "Foydalanuvchi topilmadi.", m)
            return
        orders = get_user_orders(cid)
        if not orders:
            sms(cid, "❌ Sizda hozircha buyurtmalar yo'q.", m)
            return
        last5 = orders[-5:]
        txt = "🛒 So'nggi buyurtmalaringiz:\n\n"
        for o in reversed(last5):
            txt += (f"🆔 #{o.get('order_id')} | {o.get('status')}\n"
                    f"📦 {o.get('quantity')} ta | 💵 {o.get('retail')} so'm\n"
                    f"📅 {o.get('order_create','')}\n\n")
        sms(cid, txt, m)
        return

    # 📞 Nomer API balans (admin)
    if text == "📞 Nomer API balans" and str(cid) == str(ADMIN_ID):
        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=getBalance&apiKey={SIM_KEY}",
                timeout=10, verify=False
            )
            j = resp.json()
            if j.get("success"):
                bal = j["result"]["balance"]
                cur = j["result"].get("currency", "UZS")
                h = f"{bal} {cur}"
            else:
                h = j.get("message", "Xatolik")
        except Exception:
            h = "Xatolik"
        sms(cid,
            f"📄 API ma'lumotlari:\n"
            f"➖➖➖➖➖➖➖➖➖➖➖\n"
            f"Ulangan sayt:\n<code>saleseen.uz</code>\n\n"
            f"API kalit:\n<code>{SIM_KEY}</code>\n\n"
            f"API hisob: {h}\n"
            f"➖➖➖➖➖➖➖➖➖➖➖",
            admin_panel_menu()
        )
        _del_step(cid)
        return

    # 🤖 Bot holati (admin)
    if text == "🤖 Bot holati" and str(cid) == str(ADMIN_ID):
        settings2 = get_settings()
        holat = settings2.get("status", "active")
        sms(cid,
            f"🤖 Botning hozirgi holati: <b>{'✅ Aktiv' if holat == 'active' else '❌ Nofaol'}</b>",
            keyboard([
                [{"text": "✅ Yoqish", "callback_data": "holat-active"},
                 {"text": "❌ O'chirish", "callback_data": "holat-deactive"}],
                [{"text": "🔙 Yopish", "callback_data": "yopish"}],
            ])
        )
        return

    # 🔔 Xabar yuborish (admin)
    if text == "🔔 Xabar yuborish" and str(cid) == str(ADMIN_ID):
        sms(cid,
            "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n\n"
            "⚠️ Xabar yuborilgandan keyin barcha foydalanuvchilarga jo'natiladi.",
            back_menu()
        )
        _write_step(cid, "send")
        return

    if step == "send" and str(cid) == str(ADMIN_ID):
        users_list = all_users()
        ok = 0
        fail = 0
        for u in users_list:
            try:
                bot_call("copyMessage", {
                    "chat_id": u["id"],
                    "from_chat_id": cid,
                    "message_id": mid,
                })
                ok += 1
            except Exception:
                fail += 1
        sms(cid, f"✅ Xabar yuborildi!\n\n✅ Muvaffaqiyatli: {ok} ta\n❌ Xatolik: {fail} ta",
            admin_panel_menu())
        _del_step(cid)
        return

    # 👤 Foydalanuvchini boshqarish (admin)
    if text == "👤 Foydalanuvchini boshqarish" and str(cid) == str(ADMIN_ID):
        sms(cid,
            "👤 Foydalanuvchini boshqarish\n\nFoydalanuvchi ID sini kiriting:",
            back_menu()
        )
        _write_step(cid, "user_manage")
        return

    if step == "user_manage" and str(cid) == str(ADMIN_ID):
        target_uid = text.strip()
        target_user = get_user(target_uid)
        if not target_user:
            sms(cid, "❌ Foydalanuvchi topilmadi.", admin_panel_menu())
            _del_step(cid)
            return
        u_orders = get_user_orders(target_uid)
        sms(cid,
            f"👤 Foydalanuvchi: {target_uid}\n"
            f"♻️ Holat: {target_user.get('status','active')}\n"
            f"💵 Balans: {target_user.get('balance','0')} so'm\n"
            f"📊 Buyurtmalar: {len(u_orders)} ta\n"
            f"💰 Kiritilgan: {target_user.get('outing','0')} so'm",
            keyboard([
                [{"text": "➕ Balans qo'shish", "callback_data": f"uadd={target_uid}"},
                 {"text": "➖ Balans ayirish", "callback_data": f"usub={target_uid}"}],
                [{"text": "✅ Faollashtirish", "callback_data": f"uact={target_uid}"},
                 {"text": "❌ Bloklash", "callback_data": f"ublock={target_uid}"}],
                [{"text": "🔙 Orqaga", "callback_data": "yopish"}],
            ])
        )
        _del_step(cid)
        return

    # Foydalanuvchi balansiga qo'shish/ayirish miqdori kiritish
    if step.startswith("uadd_amount=") and str(cid) == str(ADMIN_ID):
        target_uid = step.replace("uadd_amount=", "")
        try:
            amount = float(text.strip())
        except ValueError:
            sms(cid, "⚠️ Faqat raqam kiriting.", back_menu())
            return
        target_user = get_user(target_uid)
        if target_user:
            target_user["balance"] = str(round(float(target_user["balance"]) + amount, 2))
            save_user(target_uid, target_user)
            sms(cid, f"✅ {target_uid} ga {amount} so'm qo'shildi.\nYangi balans: {target_user['balance']} so'm",
                admin_panel_menu())
            try:
                sms(int(target_uid), f"💰 Hisobingizga {amount} so'm qo'shildi!\n\nBalans: {target_user['balance']} so'm", None)
            except Exception:
                pass
        _del_step(cid)
        return

    if step.startswith("usub_amount=") and str(cid) == str(ADMIN_ID):
        target_uid = step.replace("usub_amount=", "")
        try:
            amount = float(text.strip())
        except ValueError:
            sms(cid, "⚠️ Faqat raqam kiriting.", back_menu())
            return
        target_user = get_user(target_uid)
        if target_user:
            new_bal = max(0, float(target_user["balance"]) - amount)
            target_user["balance"] = str(round(new_bal, 2))
            save_user(target_uid, target_user)
            sms(cid, f"✅ {target_uid} dan {amount} so'm ayirildi.\nYangi balans: {target_user['balance']} so'm",
                admin_panel_menu())
        _del_step(cid)
        return

    # Tolov so'rovi (foydalanuvchi)
    if step.startswith("tolovqldm="):
        pay_type = step.replace("tolovqldm=", "")
        amount_text = text.strip()
        try:
            amount = float(amount_text)
        except ValueError:
            sms(cid, "⚠️ Faqat raqam kiriting.", back_menu())
            return
        user = get_user(cid)
        sms(cid, f"✅ To'lov so'rovingiz qabul qilindi!\n\n💰 Miqdor: {amount} so'm\n\nAdmin tez orada tasdiqlaydi.", m)
        sms(int(ADMIN_ID),
            f"💰 Yangi to'lov so'rovi!\n\n"
            f"👤 Foydalanuvchi ID: {cid}\n"
            f"💵 Miqdor: {amount} so'm\n"
            f"📲 To'lov turi: {pay_type}",
            keyboard([
                [{"text": "✅ Tasdiqlash", "callback_data": f"payadd={cid}={amount}"},
                 {"text": "❌ Bekor qilish", "callback_data": f"paydel={cid}={amount}"}],
            ])
        )
        _del_step(cid)
        return

    # Admin javob yozish
    if step.startswith("javob_yoz="):
        target_uid = step.replace("javob_yoz=", "")
        try:
            bot_call("copyMessage", {
                "chat_id": int(target_uid),
                "from_chat_id": cid,
                "message_id": mid,
            })
            sms(cid, "✅ Javob yuborildi.", admin_panel_menu())
        except Exception:
            sms(cid, "❌ Xatolik yuz berdi.", admin_panel_menu())
        _del_step(cid)
        return

    # Callback query'lar
    if callback:
        _handle_callback(data=data, chat_id=chat_id, cid2=cid2, mid2=mid2,
                         qid=qid, settings=settings, m=m)
        return

    if message:
        add_user(cid)

# ===========================================================================
# CALLBACK HANDLER
# ===========================================================================

def _handle_callback(data, chat_id, cid2, mid2, qid, settings, m):

    # Kategoriya tanlash
    if data and data.startswith("tanla1="):
        n = data.split("=")[1]
        subcats = get_subcategories(n)
        if not subcats:
            bot_call("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "⚠️ Xizmat turlari topilmadi!",
                "show_alert": True
            })
            return
        seen = []
        btns = []
        for c in subcats:
            name = enc("decode", c["name"])
            if name not in seen:
                seen.append(name)
                btns.append([{"text": name, "callback_data": f"tanla2={c['cate_id']}"}])
        btns.append([{"text": "⏪ Orqaga", "callback_data": "absd"}])
        edit_msg(chat_id, mid2, "⬇️ Kerakli xizmat turini tanlang:", keyboard(btns))

    elif data and data.startswith("tanla2="):
        n        = data.split("=")[1]
        services = [s for s in get_services()
                    if str(s.get("category_id")) == str(n) and s.get("service_status") == "on"]
        if not services:
            bot_call("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "⚠️ Xizmatlar topilmadi!",
                "show_alert": True
            })
            return
        btns = []
        for s in services:
            name = enc("decode", s["service_name"])
            btns.append([{
                "text":          f"{name} {s['service_price']} - so'm",
                "callback_data": f"ordered={s['service_id']}={n}"
            }])
        btns.append([{"text": "⏪ Orqaga", "callback_data": "absd"}])
        edit_msg(chat_id, mid2, "💎 Xizmatlardan birini tanlang!\n💴 Narxlar 1000 tasi uchun:", keyboard(btns))

    elif data and data.startswith("ordered="):
        parts = data.split("=")
        sid   = parts[1]
        n2    = parts[2] if len(parts) > 2 else ""
        svc   = get_service(sid)
        if not svc:
            return
        name = enc("decode", svc["service_name"])
        desc = enc("decode", svc.get("service_desc", ""))
        info = (
            f"🔑 Xizmat IDsi: <code>{svc['service_id']}</code>\n"
            f"💵 Narxi (1000 ta) - {svc['service_price']} so'm\n"
            f"🔽 Minimal: {svc['service_min']} ta\n"
            f"🔼 Maksimal: {svc['service_max']} ta\n\n{desc}"
        )
        edit_msg(chat_id, mid2, f"<b>{name}</b>\n\n{info}",
            keyboard([
                [{"text": "✅ Tanlash",
                  "callback_data": f"order={svc['service_api']}={svc['service_min']}={svc['service_max']}={svc['service_price']}={svc['service_type']}={svc['api_service']}={svc['service_id']}"}],
                [{"text": "⏪ Orqaga", "callback_data": f"tanla2={n2}"}],
            ])
        )

    elif data and data.startswith("order="):
        parts = data.split("=")
        if len(parts) < 8:
            return
        oid, omin, omax, orate, otype, prov, serv = parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]
        del_msg(chat_id, mid2)
        sms(chat_id, "⬇️ Havola (link) kiriting:", back_menu())
        _write_step(chat_id, f"link={oid}={omin}={omax}={orate}={prov}={serv}")

    elif data == "apidetail=newkey":
        new_key = hashlib.md5(os.urandom(16)).hexdigest()
        user = get_user(chat_id)
        if user:
            user["api_key"] = new_key
            save_user(chat_id, user)
            edit_msg(chat_id, mid2,
                f"✅ API kalit yangilandi.\n\n<code>{new_key}</code>\n\n"
                f"💵 API hisobi: {user['balance']} so'm",
                keyboard([[{"text": "🔄 APIni yangilash", "callback_data": "apidetail=newkey"}]])
            )

    elif data == "konkurs":
        users_list = sorted(all_users(), key=lambda u: float(u.get("balance", 0)), reverse=True)[:10]
        txt = "🏆 TOP-10 balanslar reytingi\n\n"
        for i, u in enumerate(users_list, 1):
            uid_val = u['id']
            bal_val = u['balance']
            txt += f"<b>{i})</b> <a href='tg://user?id={uid_val}'>{uid_val}</a> - {bal_val} so'm\n"
        edit_msg(chat_id, mid2, txt, None)

    elif data == "main":
        del_msg(chat_id, mid2)
        sms(chat_id, "🖥️ Asosiy menyuga qaytdingiz.", m)
        _del_step(chat_id)

    elif data == "yopish":
        del_msg(chat_id, mid2)

    # ============================================================
    # 📞 NOMER OLISH - saleseen.uz orqali
    # ============================================================

    elif data == "hop":
        # Roziman - davlatlar ro'yxati (availableCountries)
        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=availableCountries&apiKey={SIM_KEY}",
                timeout=10, verify=False
            )
            j = resp.json()
            if not j.get("success"):
                bot_call("answerCallbackQuery", {"callback_query_id": qid,
                    "text": f"⚠️ Xatolik: {j.get('message','API xatolik')}", "show_alert": True})
                return
            countries_data = j["result"]["countries"]  # {"1": {"UZ": "0.85"}, ...}
        except Exception:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "⚠️ API bilan bog'lanishda xatolik!", "show_alert": True})
            return

        # Har bir server ID → server tugmasi
        server_ids = list(countries_data.keys())
        _write_file(f"user/{chat_id}.servers", json.dumps(server_ids))

        # Server tanlash menusi (har bir server = bir server raqami)
        btns = []
        for i in range(0, len(server_ids), 2):
            row = []
            for sid in server_ids[i:i+2]:
                row.append({"text": f"🖥 Server {sid}", "callback_data": f"server_sel={sid}"})
            btns.append(row)
        btns.append([{"text": "⏮️ Orqaga", "callback_data": "main"}])
        edit_msg(chat_id, mid2, "🖥 Nomer olish uchun server tanlang:", keyboard(btns))

    elif data and data.startswith("server_sel="):
        server_id = data.split("=")[1]
        # Bu server uchun mavjud mamlakatlar
        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=availableCountries&apiKey={SIM_KEY}",
                timeout=10, verify=False
            )
            j = resp.json()
            if not j.get("success"):
                bot_call("answerCallbackQuery", {"callback_query_id": qid,
                    "text": "⚠️ API xatolik", "show_alert": True})
                return
            countries_data = j["result"]["countries"]
            server_countries = countries_data.get(str(server_id), {})
        except Exception:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "⚠️ Xatolik!", "show_alert": True})
            return

        if not server_countries:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "❌ Bu serverda mamlakat yo'q!", "show_alert": True})
            return

        flag_map = {
            "UZ": "🇺🇿 O'zbekiston", "RU": "🇷🇺 Rossiya", "KZ": "🇰🇿 Qozog'iston",
            "UA": "🇺🇦 Ukraina", "US": "🇺🇸 AQSh", "TR": "🇹🇷 Turkiya",
            "IN": "🇮🇳 Hindiston", "DE": "🇩🇪 Germaniya", "GB": "🇬🇧 Britaniya",
            "FR": "🇫🇷 Fransiya", "PH": "🇵🇭 Filippin", "ID": "🇮🇩 Indoneziya",
        }
        btns = []
        items = list(server_countries.items())
        for i in range(0, len(items), 2):
            row = []
            for country_code, price_usd in items[i:i+2]:
                label = flag_map.get(country_code, f"🌍 {country_code}")
                row.append({
                    "text": f"{label} (${price_usd})",
                    "callback_data": f"country_sel={country_code}={server_id}"
                })
            btns.append(row)
        btns.append([{"text": "⏮️ Orqaga", "callback_data": "hop"}])
        edit_msg(chat_id, mid2, f"🌍 Server {server_id} — mamlakat tanlang:", keyboard(btns))

    elif data and data.startswith("country_sel="):
        parts = data.split("=")
        country_code = parts[1]
        server_id = parts[2]
        # Narxni olish
        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=priceNumberFromCountry&apiKey={SIM_KEY}"
                f"&country={country_code}&server={server_id}",
                timeout=10, verify=False
            )
            j = resp.json()
            if not j.get("success"):
                bot_call("answerCallbackQuery", {"callback_query_id": qid,
                    "text": f"⚠️ {j.get('message','Xatolik')}", "show_alert": True})
                return
            price_uzs = j["result"]["prices"].get("UZS", 0)
            price_usd = j["result"]["prices"].get("USD", 0)
        except Exception:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "⚠️ Narx olishda xatolik!", "show_alert": True})
            return

        # Ustama qo'shish
        final_price = round(float(price_uzs) * (1 + SIM_FOIZ / 100), 0)

        flag_map = {
            "UZ": "🇺🇿 O'zbekiston", "RU": "🇷🇺 Rossiya", "KZ": "🇰🇿 Qozog'iston",
            "UA": "🇺🇦 Ukraina", "US": "🇺🇸 AQSh", "TR": "🇹🇷 Turkiya",
            "IN": "🇮🇳 Hindiston", "DE": "🇩🇪 Germaniya", "GB": "🇬🇧 Britaniya",
            "FR": "🇫🇷 Fransiya", "PH": "🇵🇭 Filippin", "ID": "🇮🇩 Indoneziya",
        }
        davlat = flag_map.get(country_code, country_code)

        edit_msg(chat_id, mid2,
            f"📞 Nomer ma'lumotlari\n\n"
            f"🌍 Davlat: {davlat}\n"
            f"🖥 Server: {server_id}\n"
            f"💵 Narxi: {final_price:.0f} so'm (${price_usd})\n\n"
            f"⚡️ Telegram akkaunt — tayyor, faollashtirilgan!\n"
            f"📲 Nomer sotib olishni xohlaysizmi?",
            keyboard([
                [{"text": f"✅ Sotib olish — {final_price:.0f} so'm",
                  "callback_data": f"buy_num={country_code}={server_id}={final_price:.0f}={davlat}"}],
                [{"text": "⏮️ Orqaga", "callback_data": f"server_sel={server_id}"}],
            ])
        )

    elif data and data.startswith("buy_num="):
        parts = data.split("=")
        if len(parts) < 5:
            return
        country_code = parts[1]
        server_id = parts[2]
        pric = float(parts[3])
        davlat = parts[4]

        user = get_user(chat_id)
        if not user:
            return
        if float(user.get("balance", 0)) < pric:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "❗ Sizda mablag' yetarli emas!", "show_alert": True})
            return

        # Nomer sotib olish
        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=buyNumber&apiKey={SIM_KEY}"
                f"&country={country_code}&server={server_id}",
                timeout=15, verify=False
            )
            j = resp.json()
        except Exception:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "❌ Xatolik yuz berdi!", "show_alert": True})
            return

        if not j.get("success"):
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": f"❌ {j.get('message','Nomer olishda xatolik!')}", "show_alert": True})
            return

        phone = j["result"]["number"]
        hash_code = j["result"]["hash_code"]
        real_price_uzs = j["result"]["prices"].get("UZS", pric)

        # Balansdan ayir
        new_bal = round(float(user["balance"]) - pric, 2)
        user["balance"] = str(new_bal)
        save_user(chat_id, user)

        edit_msg(chat_id, mid2,
            f"🛎 Sizga nomer berildi!\n\n"
            f"🌍 Davlat: {davlat}\n"
            f"🖥 Server: {server_id}\n"
            f"💸 Narxi: {pric:.0f} so'm\n"
            f"📞 Nomeringiz: {phone}\n\n"
            f"Nusxalash: <code>{phone}</code>\n\n"
            f"📨 Kodni olish uchun tugmani bosing!\n"
            f"⏰ Kod kelishini kuting...",
            keyboard([
                [{"text": "📩 Kodni olish", "callback_data": f"pcode_{hash_code}_{pric}"}],
            ])
        )

    elif data and data.startswith("pcode_"):
        parts = data.split("_")
        if len(parts) < 3:
            return
        hash_code = parts[1]
        so_val = parts[2]

        try:
            resp = requests.get(
                f"{SALESEEN_URL}?action=getCode&apiKey={SIM_KEY}&hash_code={hash_code}",
                timeout=10, verify=False
            )
            j = resp.json()
        except Exception:
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "⚠️ Xatolik yuz berdi!", "show_alert": True})
            return

        status = j.get("status", "")

        if j.get("success") or status == "Activated":
            result = j.get("result", {})
            smskod = result.get("code", "—")
            password = result.get("password", "")
            number = result.get("number", "")
            del_msg(chat_id, mid2)
            msg_text = (
                f"✅ Kod keldi!\n\n"
                f"📞 Nomer: <code>{number}</code>\n"
                f"🔢 Kod: <code>{smskod}</code>"
            )
            if password:
                msg_text += f"\n🔑 Parol: <code>{password}</code>"
            sms(chat_id, msg_text, None)
        elif status in ("Pending", "waiting"):
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": "⏰ Kod hali kelmadi. Biroz kuting...", "show_alert": True})
        else:
            noma = j.get("message", "Noma'lum")
            bot_call("answerCallbackQuery", {"callback_query_id": qid,
                "text": f"⚠️ Holat: {status or noma}", "show_alert": True})

    # ============================================================
    # ADMIN CALLBACK'LAR
    # ============================================================

    elif data and data.startswith("holat-"):
        new_status = data.replace("holat-", "")
        s = get_settings()
        s["status"] = new_status
        _save("settings", s)
        label = "✅ Aktiv" if new_status == "active" else "❌ Nofaol"
        edit_msg(chat_id, mid2, f"🤖 Bot holati {label} ga o'zgartirildi.", None)

    elif data and data.startswith("uadd="):
        target_uid = data.replace("uadd=", "")
        del_msg(chat_id, mid2)
        sms(chat_id, f"➕ {target_uid} ga qo'shish uchun miqdorni kiriting (so'm):", back_menu())
        _write_step(chat_id, f"uadd_amount={target_uid}")

    elif data and data.startswith("usub="):
        target_uid = data.replace("usub=", "")
        del_msg(chat_id, mid2)
        sms(chat_id, f"➖ {target_uid} dan ayirish uchun miqdorni kiriting (so'm):", back_menu())
        _write_step(chat_id, f"usub_amount={target_uid}")

    elif data and data.startswith("uact="):
        target_uid = data.replace("uact=", "")
        u = get_user(target_uid)
        if u:
            u["status"] = "active"
            save_user(target_uid, u)
            edit_msg(chat_id, mid2, f"✅ {target_uid} faollashtirildi.", None)

    elif data and data.startswith("ublock="):
        target_uid = data.replace("ublock=", "")
        u = get_user(target_uid)
        if u:
            u["status"] = "deactive"
            save_user(target_uid, u)
            edit_msg(chat_id, mid2, f"❌ {target_uid} bloklandi.", None)

    elif data and data.startswith("javob="):
        target_uid = data.replace("javob=", "")
        del_msg(chat_id, mid2)
        sms(chat_id, f"📝 {target_uid} ga javob yozing:", back_menu())
        _write_step(chat_id, f"javob_yoz={target_uid}")

    elif data and data.startswith("payadd="):
        parts = data.split("=")
        target_uid = parts[1]
        amount = float(parts[2]) if len(parts) > 2 else 0
        u = get_user(target_uid)
        if u:
            u["balance"] = str(round(float(u["balance"]) + amount, 2))
            u["outing"] = str(round(float(u.get("outing", "0")) + amount, 2))
            save_user(target_uid, u)
            edit_msg(chat_id, mid2,
                f"✅ {target_uid} ga {amount} so'm qo'shildi.\nYangi balans: {u['balance']} so'm", None)
            sms(int(target_uid), f"✅ Hisobingizga {amount} so'm qo'shildi!\n💰 Balans: {u['balance']} so'm", None)

    elif data and data.startswith("paydel="):
        parts = data.split("=")
        target_uid = parts[1]
        amount = parts[2] if len(parts) > 2 else "0"
        edit_msg(chat_id, mid2, f"❌ {target_uid} ning {amount} so'mlik to'lov so'rovi bekor qilindi.", None)
        sms(int(target_uid), f"❌ Hisobingizni {amount} so'mga to'ldirish so'rovi bekor qilindi.", None)

    elif data == "menu=tolov":
        edit_msg(chat_id, mid2,
            "💳 Hisobni to'ldirish\n\n"
            "To'lov miqdorini kiriting va adminga yuboring.\n\n"
            "📲 Admin bilan bog'laning va to'lov chekini yuboring.",
            keyboard([
                [{"text": "👨‍💼 Admin bilan bog'lanish", "callback_data": "admin_contact"}],
                [{"text": "🔙 Orqaga", "callback_data": "yopish"}],
            ])
        )

    elif data == "admin_contact":
        bot_call("answerCallbackQuery", {"callback_query_id": qid,
            "text": "Admin bilan bog'lanish uchun ☎️ Administrator tugmasini bosing", "show_alert": True})

    elif data == "pul_ishla":
        user = get_user(chat_id)
        if not user:
            return
        if not BOT_USERNAME:
            info = bot_call("getMe")
            BOT_USERNAME = info.get("result", {}).get("username", "bot")
        bonus = settings.get("referal", "0")
        edit_msg(chat_id, mid2,
            f"🚀 Referal dasturi\n\n"
            f"Sizning referal havolangiz:\nhttps://t.me/{BOT_USERNAME}?start=user{user['id']}\n\n"
            f"Har bir taklif uchun {bonus} so'm beriladi.",
            keyboard([[{"text": "🔙 Yopish", "callback_data": "yopish"}]])
        )

    elif data == "orqa":
        del_msg(chat_id, mid2)
        sms(chat_id, "🖥️ Asosiy menyuga qaytdingiz.", m)
        _del_step(chat_id)

    elif data == "absd":
        categories = get_categories()
        if not categories:
            edit_msg(chat_id, mid2, "⚠️ Tarmoqlar topilmadi.", None)
            return
        btns = [[{"text": enc("decode", c["category_name"]),
                  "callback_data": f"tanla1={c['category_id']}"}]
                for c in categories]
        edit_msg(chat_id, mid2,
                 "✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Ijtimoiy tarmoqni tanlang.",
                 keyboard(btns))

# ===========================================================================
# REST API (v2)
# ===========================================================================

def api_balance(key):
    for u in all_users():
        if u.get("api_key") == key:
            return {"balance": u["balance"], "currency": "UZS"}
    return {"error": "Incorrect API key"}

def api_services_list(key):
    found = any(u.get("api_key") == key for u in all_users())
    if not found:
        return {"error": "Incorrect API key"}
    return [{
        "service": s["service_id"],
        "name":    enc("decode", s.get("service_name", "")),
        "rate":    s["service_price"],
        "min":     s["service_min"],
        "max":     s["service_max"],
        "type":    s.get("service_type", ""),
    } for s in get_services()]

def api_orders_list(key):
    uid = None
    for u in all_users():
        if u.get("api_key") == key:
            uid = u["id"]
            break
    if not uid:
        return {"error": "Incorrect API Key"}
    orders = get_user_orders(uid)
    if not orders:
        return {"error": "No orders"}
    return [{"order": o["order_id"], "status": o["status"],
             "charge": o["retail"], "currency": "UZS"} for o in orders]

# ===========================================================================
# NARX YANGILASH (CRON)
# ===========================================================================

def update_service_prices():
    settings = get_settings()
    foiz     = float(settings.get("percent", "40"))
    svcs     = get_services()
    updates  = []
    for i, svc in enumerate(svcs):
        if str(svc.get("service_edit", "false")).lower() != "true":
            continue
        provider = get_provider(svc.get("api_service"))
        if not provider:
            continue
        try:
            resp  = requests.get(
                f"{provider['api_url']}?key={provider['api_key']}&action=services",
                timeout=10, verify=False
            )
            items = resp.json()
        except Exception:
            continue
        for item in items:
            if str(item.get("service")) == str(svc.get("service_api")):
                rate = float(item["rate"]) * _get_currency_rate(svc.get("api_currency", "UZS"))
                rp   = rate / 100 * foiz + rate
                svcs[i]["service_min"]   = item["min"]
                svcs[i]["service_max"]   = item["max"]
                svcs[i]["service_price"] = str(round(rp, 2))
                updates.append({"service_id": svc["service_id"], "new_price": rp})
                break
    _save_list("services", svcs)
    return {"status": True, "updates": updates}

# ===========================================================================
# FLASK WEB SERVER
# ===========================================================================

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    orders_list = get_orders()
    return jsonify({
        "page": "index",
        "stats": {
            "total_services":   len(get_services()),
            "completed_orders": len([o for o in orders_list if o.get("status") == "Completed"]),
            "total_orders":     len(orders_list),
            "total_users":      count_users(),
            "support":          "24/7",
        }
    })

@app.route("/api/v2", methods=["GET", "POST"])
def api_v2():
    params  = request.values
    key     = params.get("key", "")
    action  = params.get("action", "")
    if action == "balance":
        return jsonify(api_balance(key))
    elif action == "services":
        return jsonify(api_services_list(key))
    elif action == "orders":
        return jsonify(api_orders_list(key))
    else:
        return jsonify({"error": "Incorrect request"})

@app.route("/services", methods=["GET"])
def services_page():
    search = request.args.get("name", "")
    result = []
    for s in get_services():
        name = enc("decode", s.get("service_name", ""))
        if search and search.lower() not in name.lower():
            continue
        result.append({
            "id":    s["service_id"],
            "name":  name,
            "price": s["service_price"],
            "min":   s["service_min"],
            "max":   s["service_max"],
        })
    return jsonify({"services": result})

@app.route("/orders", methods=["GET"])
def orders_page():
    api_key = request.args.get("key", "")
    status  = request.args.get("status", "")
    uid = None
    for u in all_users():
        if u.get("api_key") == api_key:
            uid = u["id"]
            break
    if not uid:
        return jsonify({"orders": []})
    orders = get_user_orders(uid)
    if status:
        orders = [o for o in orders if o.get("status") == status]
    return jsonify({"orders": orders})

@app.route("/bot/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True) or {}
    try:
        handle_update(update)
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"ok": True})

@app.route("/update", methods=["GET"])
def cron_update():
    action = request.args.get("update", "")
    if action == "prices":
        return jsonify(update_service_prices())
    return jsonify({"error": "Unknown update action"})

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "404 - Page not found"}), 404

# ===========================================================================
# ISHGA TUSHIRISH
# ===========================================================================

if __name__ == "__main__":
    for folder in ["user", "set", "data"]:
        os.makedirs(folder, exist_ok=True)

    if not TELEGRAM_API_KEY:
        print("⚠️  BOT_TOKEN kiritilmagan! Railway > Variables > BOT_TOKEN qo'shing.")
    else:
        info         = bot_call("getMe")
        BOT_USERNAME = info.get("result", {}).get("username", "bot")

    if not ADMIN_ID:
        print("⚠️  ADMIN_ID kiritilmagan! Railway > Variables > ADMIN_ID qo'shing.")

    print("=" * 60)
    print("QoraCoders SMM Panel - JSON versiyasi (MySQL kerak emas)")
    print("=" * 60)
    print(f"Admin ID     : {ADMIN_ID}")
    print(f"Bot username : @{BOT_USERNAME}")
    print(f"Ma'lumotlar  : ./data/ papkasi (JSON fayllar)")
    print("=" * 60)
    print("Railway Variables (faqat 2 ta kerak):")
    print("  BOT_TOKEN  = botning token raqami")
    print("  ADMIN_ID   = sizning telegram ID raqamingiz")
    print("=" * 60)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
