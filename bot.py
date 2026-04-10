#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QoraCoders SMM Panel - Barcha PHP fayllar bitta Python fayliga o'girildi
Manbalar: Premium/app/controller/*.php, Premium/bot/bot.php, Premium/payme.php va boshqalar
"""

import os
import json
import base64
import hashlib
import random
import string
import requests
import datetime
import mysql.connector
from flask import Flask, request, jsonify, render_template_string

# ===========================================================================
# 1. DB ULANISHI
# ===========================================================================

def get_db():
    conn = mysql.connector.connect(
        host="",
        user="",
        password="",
        database="",
        charset="utf8mb4"
    )
    return conn

def fetch_one(query, params=()):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def fetch_all(query, params=()):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def execute(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    lid = cur.lastrowid
    cur.close(); conn.close()
    return lid

def count_rows(table, where=None):
    """Jadvaldan qator soni (ixtiyoriy WHERE sharti bilan)."""
    conn = get_db()
    cur = conn.cursor()
    if where:
        conditions = " AND ".join([f"{k} = %s" for k in where])
        cur.execute(f"SELECT COUNT(*) FROM `{table}` WHERE {conditions}", list(where.values()))
    else:
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
    cnt = cur.fetchone()[0]
    cur.close(); conn.close()
    return cnt

def get_settings():
    return fetch_one("SELECT * FROM settings WHERE id = 1")

# ===========================================================================
# 2. avg.php => Xizmatlar bo'yicha o'rtacha hisobot
# ===========================================================================

def avg_services():
    """Har bir xizmat bo'yicha bajarilgan buyurtmalar statistikasi."""
    services = fetch_all("SELECT * FROM `services`")
    result = []
    for svc in services:
        sid = svc['service_id']
        order = fetch_one(
            "SELECT * FROM myorder WHERE status='Completed' AND service=%s", (sid,)
        )
        result.append(order if order else {})
    return result

# ===========================================================================
# 3. bot/update.php => Narxlarni avtomatik yangilash (CRON)
# ===========================================================================

def update_service_prices():
    """
    Provayderdan narxlarni olib, mahalliy xizmatlarni yangilaydi.
    (bot/update.php mantig'i)
    """
    percent_row = fetch_one("SELECT * FROM percent WHERE id = 1")
    foiz = float(percent_row['percent']) if percent_row else 0

    services = fetch_all("SELECT * FROM services WHERE service_edit = 'true'")
    updates = []
    for svc in services:
        prv_id = svc['api_service']
        provider = fetch_one("SELECT * FROM `providers` WHERE id = %s", (prv_id,))
        if not provider:
            continue
        try:
            resp = requests.get(
                f"{provider['api_url']}?key={provider['api_key']}&action=services",
                timeout=10, verify=False
            )
            items = resp.json()
        except Exception:
            continue

        for item in items:
            if str(item.get('service')) == str(svc['service_api']):
                mini = item['min']
                maxi = item['max']
                rate = float(item['rate'])
                currency = svc.get('api_currency', 'UZS')

                # Valyuta kursini fayldan o'qish (Python da config orqali)
                fr = _get_currency_rate(currency)
                rate = rate * fr
                rp = rate / 100
                rp = rp * foiz + rate

                doi = svc['service_id']
                execute(
                    "UPDATE services SET service_min=%s, service_max=%s WHERE service_id=%s",
                    (mini, maxi, doi)
                )
                if str(svc['service_price']) != str(rp):
                    execute(
                        "UPDATE services SET service_min=%s, service_max=%s, service_price=%s WHERE service_id=%s",
                        (mini, maxi, rp, doi)
                    )
                    updates.append({
                        "service_id": doi,
                        "new_order_price": rp,
                        "new_order_min": mini,
                        "new_order_max": maxi
                    })
                break

    return {"status": True, "cron": "Synchronize service: min, max, price", "updates": updates}

def _get_currency_rate(currency):
    """Valyuta kursini qaytaradi (fayldan yoki default)."""
    rate_map = {"UZS": 1, "USD": 12500, "RUB": 130, "INR": 150, "TRY": 400}
    return rate_map.get(currency.upper(), 1)

# ===========================================================================
# 4. app/controller/api.php => REST API (v2)
# ===========================================================================

def api_balance(key):
    user = fetch_one("SELECT * FROM users WHERE api_key = %s", (key,))
    if user:
        return {"balance": user['balance'], "currency": "UZS"}
    return {"error": "Incorrect API key"}

def api_add_order(key, service, link, quantity):
    user = fetch_one("SELECT * FROM users WHERE api_key = %s AND status = 'active'", (key,))
    if not user:
        return {"error": "invalid API key"}

    svc = fetch_one("SELECT * FROM `services` WHERE service_id = %s AND service_status='on'", (service,))
    if not svc:
        return {"error": "Incorrect service ID"}
    if not link:
        return {"error": "Bad link"}
    if int(quantity) < int(svc['service_min']):
        return {"error": f"Quantity less than minimal {svc['service_min']}"}
    if int(quantity) > int(svc['service_max']):
        return {"error": f"Quantity less than maximum {svc['service_max']}"}

    narxi = float(svc['service_price']) / 1000 * int(quantity)
    if float(user['balance']) < narxi:
        return {"error": "Not enough funds on balance"}

    provider = fetch_one("SELECT * FROM `providers` WHERE id = %s", (svc['api_service'],))
    if not provider:
        return {"error": "Provider not found"}

    try:
        resp = requests.get(
            f"{provider['api_url']}?key={provider['api_key']}&action=add"
            f"&service={svc['service_api']}&link={link}&quantity={quantity}",
            timeout=15, verify=False
        )
        j = resp.json()
    except Exception:
        return {"error": "Unknown error, please try again later"}

    jid = j.get('order')
    if not jid:
        return {"error": "Unknown error, please try again later"}

    orders_count = count_rows("orders")
    order_id = orders_count + 1
    ball = float(user['balance']) - narxi
    sav = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    execute("UPDATE `users` SET balance=%s WHERE api_key=%s", (ball, key))
    execute(
        "INSERT INTO myorder(order_id,user_id,retail,status,service,order_create,last_check) "
        "VALUES (%s,%s,%s,'Pending',%s,%s,%s)",
        (order_id, user['id'], narxi, service, sav, sav)
    )
    execute(
        "INSERT INTO orders(api_order,order_id,provider,status) VALUES (%s,%s,%s,'Pending')",
        (jid, order_id, svc['api_service'])
    )
    return {"order": order_id, "charge": narxi, "currency": "UZS"}

def api_services(key):
    user = fetch_one("SELECT * FROM users WHERE api_key = %s", (key,))
    if not user:
        return {"error": "Incorrect API key"}

    services = fetch_all("SELECT * FROM `services`")
    result = []
    for s in services:
        cid = s['category_id']
        ca = fetch_one("SELECT * FROM cates WHERE cate_id = %s", (cid,))
        if not ca:
            continue
        categ = ca['category_id']
        cas = fetch_one("SELECT * FROM categorys WHERE category_id = %s", (categ,))
        if not cas:
            continue
        category = (
            base64.b64decode(cas['category_name']).decode('utf-8', errors='ignore')
            + " " +
            base64.b64decode(ca['name']).decode('utf-8', errors='ignore')
        )
        name = base64.b64decode(s['service_name']).decode('utf-8', errors='ignore')
        detail = json.loads(s.get('api_detail') or '{}')
        result.append({
            "service": s['service_id'],
            "category": category,
            "name": name,
            "rate": s['service_price'],
            "min": s['service_min'],
            "max": s['service_max'],
            "type": s['service_type'],
            "refill": detail.get('refill'),
            "cancel": detail.get('cancel'),
            "dripfeed": detail.get('dripfeed'),
        })
    return result

def api_orders(key):
    user = fetch_one("SELECT * FROM users WHERE api_key = %s", (key,))
    if not user:
        return {"error": "Incorrect API Key"}

    orders = fetch_all("SELECT * FROM myorder WHERE user_id = %s", (user['id'],))
    if not orders:
        return {"error": "No orders"}
    return [
        {
            "customer": d['user_id'],
            "service": d['service'],
            "order": d['order_id'],
            "status": d['status'],
            "charge": d['retail'],
            "currency": "UZS"
        }
        for d in orders
    ]

def api_status(key, order_ids_str=None, order_id=None):
    user = fetch_one("SELECT * FROM `users` WHERE api_key = %s", (key,))
    if not user:
        return {"error": "Incorrect API key"}

    uid = user['id']

    def _get_single(oid):
        oid = int(oid)
        rew = fetch_one("SELECT * FROM `myorder` WHERE order_id=%s AND user_id=%s", (oid, uid))
        if not rew:
            return {"error": "Incorrect order ID"}
        stati = fetch_one("SELECT * FROM orders WHERE order_id=%s", (oid,))
        if not stati:
            return {"error": "Order not found in orders table"}
        prv = stati['provider']
        provider = fetch_one("SELECT * FROM `providers` WHERE id=%s", (prv,))
        if not provider:
            return {"error": "Provider not found"}
        try:
            api_resp = requests.get(
                f"{provider['api_url']}?key={provider['api_key']}&action=status&order={stati['api_order']}",
                timeout=10, verify=False
            ).json()
        except Exception:
            api_resp = {}
        return {
            "order": oid,
            "status": rew['status'],
            "start_count": api_resp.get('start_count', "0"),
            "remains": api_resp.get('remains', "0"),
            "charge": rew['retail'],
            "currency": "UZS"
        }

    if order_ids_str:
        ids = order_ids_str.split(',')
        data = {}
        for oid in ids:
            oid = oid.strip()
            if not oid.isdigit():
                data[oid] = {"error": f"{oid} is not a number"}
            else:
                data[oid] = _get_single(oid)
        return data
    elif order_id:
        return _get_single(order_id)
    return {"error": "Incorrect request"}

# ===========================================================================
# 5. payme.php => PAYME TO'LOV INTEGRATSIYASI
# ===========================================================================

def payme_create(card_id, amount, description):
    """Payme orqali to'lov yaratish."""
    amount_tiyin = int(float(amount)) * 100
    headers = {
        "device": "6Fk1rB;",
        "user-agent": "Mozilla/57.36"
    }
    payload = {
        "method": "p2p.create",
        "params": {
            "card_id": card_id,
            "amount": amount_tiyin,
            "description": description
        }
    }
    try:
        resp = requests.post(
            "https://payme.uz/api/p2p.create",
            json=payload, headers=headers, timeout=15, verify=False
        )
        res = resp.json()
        cheque = res.get("result", {}).get("cheque", {})
        return {
            "_result": {
                "_details": {
                    "_id": cheque.get("_id"),
                    "_url": "https://checkout.paycom.uz",
                    "_pay_amount": f"{amount} UZS",
                    "_pay_url": f"https://checkout.paycom.uz/{cheque.get('_id')}"
                }
            }
        }
    except Exception as e:
        return {"error": str(e)}

def payme_check(cheque_id):
    """To'lov holatini tekshirish."""
    payload = {
        "method": "cheque.get",
        "params": {"id": cheque_id}
    }
    try:
        resp = requests.post(
            "https://payme.uz/api/cheque.get",
            json=payload, timeout=15, verify=False
        )
        res = resp.json()
        pay_time = res.get("result", {}).get("cheque", {}).get("pay_time")
        return {"mess": pay_time}
    except Exception as e:
        return {"error": str(e)}

# ===========================================================================
# 6. bot/bot.php => TELEGRAM BOT LOGIKASI
# ===========================================================================

TELEGRAM_API_KEY = os.getenv("BOT_TOKEN", "8674893543:AAEmbCiJkWchGiSgXzXrcL_NYZRFl75GEbw")
ADMIN_ID = os.getenv("ADMIN_ID", "8537782289")
SIM_KEY = "8395fA936b4874292c214df2A4c9Ae8c"
SIM_FOIZ = 50
SIM_RUB = 130
CHANNEL = "130"
VALYUTA = "so'm"

def bot_call(method, data=None):
    """Telegram Bot API'ga so'rov yuboradi."""
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/{method}"
    try:
        resp = requests.post(url, json=data or {}, timeout=15)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sms(chat_id, text, reply_markup=None):
    """Foydalanuvchiga xabar yuboradi."""
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
    """Xabarni tahrirlaydi."""
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
    """Xabarni o'chiradi."""
    return bot_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def keyboard(buttons):
    """Inline tugmalar yaratadi."""
    return json.dumps({"inline_keyboard": buttons})

def enc(mode, value):
    """base64 encode/decode."""
    if mode == "encode":
        return base64.b64encode(str(value).encode()).decode()
    elif mode == "decode":
        try:
            return base64.b64decode(str(value)).decode('utf-8', errors='ignore')
        except Exception:
            return value
    return value

def generate_code(length=7):
    """Tasodifiy kod generatsiya qiladi."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def add_user(user_id):
    """Yangi foydalanuvchini DBga qo'shadi."""
    existing = fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    if not existing:
        api_key = hashlib.md5(os.urandom(16)).hexdigest()
        referal = generate_code()
        cnt = count_rows("users")
        new_id = cnt + 1
        execute(
            "INSERT INTO users(user_id,id,status,balance,outing,api_key,referal) "
            "VALUES (%s,%s,'active','0','0',%s,%s)",
            (new_id, user_id, api_key, referal)
        )

def join_check(user_id):
    """Majburiy obunalarni tekshiradi."""
    channel_data = _read_file("set/channel")
    if not channel_data:
        return True
    channels = [c for c in channel_data.split("\n") if c.strip()]
    all_joined = True
    for ch in channels:
        resp = bot_call("getChatMember", {"chat_id": ch, "user_id": user_id})
        status = resp.get("result", {}).get("status", "")
        if status not in ("creator", "administrator", "member"):
            all_joined = False
    return all_joined

def _read_file(path):
    """Faylni o'qiydi, mavjud bo'lmasa None qaytaradi."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def _write_file(path, content):
    """Faylga yozadi."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(content))

def _read_step(user_id):
    return _read_file(f"user/{user_id}.step") or ""

def _write_step(user_id, step):
    os.makedirs("user", exist_ok=True)
    _write_file(f"user/{user_id}.step", step)

def _del_step(user_id):
    try:
        os.unlink(f"user/{user_id}.step")
    except Exception:
        pass

# --- ASOSIY MENYULAR ---

def main_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [
            [{"text": "🛍 Buyurtma berish"}, {"text": "📞 Nomer olish"}],
            [{"text": "🔐 Mening hisobim"}, {"text": "💰 Hisobni to'ldirish"}],
            [{"text": "🛒 Buyurtma xolati"}, {"text": "🚀 Referal yig'ish"}],
            [{"text": "☎️ Administrator"}, {"text": "🤝 Hamkorlik (API)"}],
        ]
    })

def admin_panel_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [
            [{"text": "⚙️ Asosiy sozlamalar"}, {"text": "📊 Statistika"}],
            [{"text": "🔔 Xabar yuborish"}, {"text": "🛍 Chegirmalar"}],
            [{"text": "👤 Foydalanuvchini boshqarish"}],
            [{"text": "⏰ Cron sozlamasi"}, {"text": "📞 Nomer API balans"}],
            [{"text": "🤖 Bot holati"}, {"text": "🎮 Donat sozlamalari"}],
            [{"text": "⏪ Orqaga"}],
        ]
    })

def back_menu():
    return json.dumps({
        "resize_keyboard": True,
        "keyboard": [[{"text": "➡️ Orqaga"}]]
    })

# --- BOT WEBHOOK HANDLER ---

def handle_update(update: dict):
    """
    Telegram webhook'dan kelgan update'ni qayta ishlaydi.
    bot/bot.php ning asosiy mantig'i.
    """
    message = update.get("message", {})
    callback = update.get("callback_query", {})

    # Callback ma'lumotlari
    cid2 = callback.get("message", {}).get("chat", {}).get("id")
    mid2 = callback.get("message", {}).get("message_id")
    data = callback.get("data", "")
    qid  = callback.get("id")
    callfrid = callback.get("from", {}).get("id")

    # Xabar ma'lumotlari
    cid  = message.get("chat", {}).get("id")
    mid  = message.get("message_id")
    text = message.get("text", "")
    name = message.get("from", {}).get("first_name", "")
    chat_id = cid2 or cid

    settings = get_settings()
    m = main_menu()

    # Bot bloklandi
    bot_del = update.get("my_chat_member", {})
    if bot_del:
        botdel_status = bot_del.get("new_chat_member", {}).get("status")
        botdel_id = bot_del.get("from", {}).get("id")
        if botdel_status == "kicked":
            execute("UPDATE `users` SET `status` = 'deactive' WHERE `id` = %s", (botdel_id,))

    # Foydalanuvchi holati
    if chat_id:
        u = fetch_one("SELECT * FROM users WHERE id = %s", (chat_id,))
        if u and u.get("status") == "deactive":
            return

    # Status fayli
    step = _read_step(cid or chat_id or 0)

    # -----------------------------------------------------------------------
    # /start buyrug'i
    # -----------------------------------------------------------------------
    if text == "/start" and join_check(cid):
        add_user(cid)
        user = fetch_one("SELECT * FROM users WHERE id = %s", (cid,))
        start_text = enc("decode", settings.get('start', ''))
        start_text = start_text.replace("{name}", name)
        start_text = start_text.replace("{balance}", str(user['balance']) if user else "0")
        start_text = start_text.replace("{time}", datetime.datetime.now().strftime("%H:%M"))
        sms(cid, start_text, m)
        return

    # /start user<ID> - referal
    if text and text.startswith("/start user"):
        ref_user_id = text.replace("/start user", "").strip()
        refid_row = fetch_one("SELECT * FROM users WHERE user_id = %s", (ref_user_id,))
        if refid_row:
            refid = refid_row['id']
            if str(refid) != str(cid):
                existing = fetch_one("SELECT * FROM users WHERE id = %s", (cid,))
                if not existing:
                    if join_check(cid):
                        pul = float(refid_row['balance'])
                        bonus = float(enc("decode", settings.get('referal', 'MA==')))
                        execute("UPDATE users SET balance=%s WHERE id=%s", (pul + bonus, refid))
                    else:
                        _write_file(f"user/{cid}.id", str(refid))
                    bot_call("sendMessage", {
                        "chat_id": refid,
                        "text": f"<b>📳 Sizda yangi <a href='tg://user?id={cid}'>taklif</a> mavjud!</b>",
                        "parse_mode": "HTML"
                    })
        add_user(cid)
        sms(cid, "🖥 Asosiy menyudasiz", m)
        return

    # -----------------------------------------------------------------------
    # Orqaga
    # -----------------------------------------------------------------------
    if text == "➡️ Orqaga":
        _del_step(cid)
        sms(cid, "🖥️ Asosiy menyudasiz", m)
        return

    # -----------------------------------------------------------------------
    # Boshqaruv paneli (faqat admin uchun)
    # -----------------------------------------------------------------------
    if text == "🗄️ Boshqaruv" and str(cid) == ADMIN_ID:
        _del_step(cid)
        sms(cid, "🖥️ Boshqaruv paneli", admin_panel_menu())
        return

    # -----------------------------------------------------------------------
    # Statistika (admin)
    # -----------------------------------------------------------------------
    if text == "📊 Statistika" and str(cid) == ADMIN_ID:
        total_users = count_rows("users")
        active_users = len(fetch_all("SELECT id FROM users WHERE status='active'"))
        deactive_users = total_users - active_users
        total_orders = count_rows("orders")
        completed = len(fetch_all("SELECT order_id FROM orders WHERE status='Completed'"))
        pending   = len(fetch_all("SELECT order_id FROM orders WHERE status='Pending'"))
        in_progress = len(fetch_all("SELECT order_id FROM orders WHERE status='In progress'"))
        canceled  = len(fetch_all("SELECT order_id FROM orders WHERE status='Canceled'"))
        partial   = len(fetch_all("SELECT order_id FROM orders WHERE status='Partial'"))
        processing= len(fetch_all("SELECT order_id FROM orders WHERE status='Processing'"))
        total_services = count_rows("services")
        sms(cid,
            f"📊 Statistika\n"
            f"• Jami foydalanuvchilar: {total_users} ta\n"
            f"• Aktiv: {active_users} ta\n"
            f"• O'chirilgan: {deactive_users} ta\n\n"
            f"📊 Buyurtmalar\n"
            f"• Jami: {total_orders} ta\n"
            f"• Bajarilgan: {completed} ta\n"
            f"• Kutilayotgan: {pending} ta\n"
            f"• Jarayonda: {in_progress} ta\n"
            f"• Bekor qilingan: {canceled} ta\n"
            f"• Qisman: {partial} ta\n"
            f"• Qayta ishlangan: {processing} ta\n\n"
            f"📊 Xizmatlar: {total_services} ta",
            admin_panel_menu()
        )
        _del_step(cid)
        return

    # -----------------------------------------------------------------------
    # Mening hisobim
    # -----------------------------------------------------------------------
    if text == "🔐 Mening hisobim" and join_check(cid):
        user = fetch_one("SELECT * FROM users WHERE id = %s", (cid,))
        if not user:
            sms(cid, "Foydalanuvchi topilmadi.", m)
            return
        orders_count = count_rows("myorder")
        sms(cid,
            f"👤 Sizning ID raqamingiz: {cid}\n\n"
            f"♻️ Holatiingiz: {user['status']}\n"
            f"💵 Balansingiz: {user['balance']} so'm\n"
            f"📊 Buyurtmalaringiz: {orders_count} ta\n"
            f"💰 Kiritilgan summa: {user['outing']} so'm",
            keyboard([
                [{"text": "💰 Hisobni to'ldirish", "callback_data": "menu=tolov"},
                 {"text": "🚀 Referal", "callback_data": "pul_ishla"}],
                [{"text": "🎟 Promokod", "callback_data": "kodpromo"},
                 {"text": "⭐️ Premium", "callback_data": "preimium"}],
            ])
        )
        return

    # -----------------------------------------------------------------------
    # Referal
    # -----------------------------------------------------------------------
    if text == "🚀 Referal yig'ish" and join_check(cid):
        user = fetch_one("SELECT * FROM users WHERE id = %s", (cid,))
        if user:
            bot_info = bot_call("getMe")
            bot_name = bot_info.get("result", {}).get("username", "bot")
            my_id = user['user_id']
            bonus = enc("decode", settings.get('referal', 'MA=='))
            sms(cid,
                f"Sizning referal havolangiz:\n\nhttps://t.me/{bot_name}?start=user{my_id}\n\n"
                f"Har bir taklif uchun {bonus} so'm beriladi.\n\n"
                f"👤 ID raqam: {my_id}",
                keyboard([[{"text": "💎 Konkurs (🏆 TOP 10)", "callback_data": "konkurs"}]])
            )
        return

    # -----------------------------------------------------------------------
    # Buyurtma berish - kategoriyalar
    # -----------------------------------------------------------------------
    if text == "🛍 Buyurtma berish" and join_check(cid):
        categories = fetch_all("SELECT * FROM `categorys`")
        if not categories:
            sms(cid, "⚠️ Tarmoqlar topilmadi.", None)
            return
        btns = [[{"text": enc("decode", c['category_name']),
                  "callback_data": f"tanla1={c['category_id']}"}]
                for c in categories]
        btns.append([{"text": "🔥 Eng yaxshi xizmatlar ⚡️", "url": "https://t.me"}])
        sms(cid, "✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Ijtimoiy tarmoqni tanlang.",
            keyboard(btns))
        return

    # -----------------------------------------------------------------------
    # Administrator murojaati
    # -----------------------------------------------------------------------
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
                [{"text": "👁️ Ko'rish", "url": f"tg://user?id={cid}"}],
                [{"text": "📑 Javob yozish", "callback_data": f"javob={cid}"}],
            ])
        })
        _write_file(f"user/{cid}.step", "")
        return

    # -----------------------------------------------------------------------
    # API kalit
    # -----------------------------------------------------------------------
    if text == "🤝 Hamkorlik (API)" and join_check(cid):
        user = fetch_one("SELECT * FROM users WHERE id = %s", (cid,))
        if user:
            sms(cid,
                f"⭐ Sizning API kalitingiz:\n<code>{user['api_key']}</code>\n\n"
                f"💵 API hisobi: {user['balance']} so'm",
                keyboard([
                    [{"text": "🔄 APIni yangilash", "callback_data": "apidetail=newkey"}],
                ])
            )
        return

    # -----------------------------------------------------------------------
    # CALLBACK QUERY'LAR
    # -----------------------------------------------------------------------
    if callback:
        _handle_callback(
            data=data, chat_id=chat_id, cid2=cid2, mid2=mid2,
            qid=qid, callfrid=callfrid, settings=settings, m=m
        )
        return

    # -----------------------------------------------------------------------
    # Foydalanuvchini ro'yxatdan o'tkazish
    # -----------------------------------------------------------------------
    if message:
        add_user(cid)

# ---------------------------------------------------------------------------
# CALLBACK HANDLER
# ---------------------------------------------------------------------------

def _handle_callback(data, chat_id, cid2, mid2, qid, callfrid, settings, m):
    """Callback query'larni qayta ishlaydi."""
    step = _read_step(chat_id or 0)

    # --- Kategoriya tanlash ---
    if data and data.startswith("tanla1="):
        n = data.split("=")[1]
        cates = fetch_all("SELECT * FROM cates WHERE category_id = %s", (n,))
        if not cates:
            bot_call("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "⚠️ Xizmat turlari topilmadi!",
                "show_alert": True
            })
            return
        seen = []
        btns = []
        for c in cates:
            name = enc("decode", c['name'])
            if name not in seen:
                seen.append(name)
                btns.append([{"text": name, "callback_data": f"tanla2={c['cate_id']}"}])
        btns.append([{"text": "⏪ Orqaga", "callback_data": "absd"}])
        edit_msg(chat_id, mid2, "⬇️ Kerakli xizmat turini tanlang:", keyboard(btns))

    # --- Ichki kategoriya ---
    elif data and data.startswith("tanla2="):
        n = data.split("=")[1]
        services = fetch_all(
            "SELECT * FROM services WHERE category_id = %s AND service_status = 'on'", (n,)
        )
        if not services:
            bot_call("answerCallbackQuery", {
                "callback_query_id": qid,
                "text": "⚠️ Xizmatlar topilmadi!",
                "show_alert": True
            })
            return
        btns = []
        for s in services:
            name = base64.b64decode(s['service_name']).decode('utf-8', errors='ignore')
            btns.append([{
                "text": f"{name} {s['service_price']} - so'm",
                "callback_data": f"ordered={s['service_id']}={n}"
            }])
        btns.append([{"text": "⏪ Orqaga", "callback_data": f"tanla1=..."}])
        edit_msg(chat_id, mid2, "💎 Xizmatlardan birini tanlang!\n💴 Narxlar 1000 tasi uchun:", keyboard(btns))

    # --- Xizmat tanlandi ---
    elif data and data.startswith("ordered="):
        parts = data.split("=")
        sid = parts[1]
        n2  = parts[2] if len(parts) > 2 else ""
        svc = fetch_one("SELECT * FROM services WHERE service_id = %s", (sid,))
        if not svc:
            return
        name = base64.b64decode(svc['service_name']).decode('utf-8', errors='ignore')
        desc_raw = svc.get('service_desc')
        desc = base64.b64decode(desc_raw).decode('utf-8', errors='ignore') if desc_raw else ""
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

    # --- Buyurtma miqdori ---
    elif data and data.startswith("order="):
        parts = data.split("=")
        oid   = parts[1]
        omin  = parts[2]
        omax  = parts[3]
        orate = parts[4]
        otype = parts[5]
        prov  = parts[6]
        serv  = parts[7]
        del_msg(chat_id, mid2)
        sms(chat_id, "⬇️ Kerakli buyurtma miqdorini kiriting:", back_menu())
        _write_step(chat_id, "order=default=sp1")
        _write_file(f"user/{chat_id}.params", f"{oid}={omin}={omax}={orate}={prov}={serv}")
        _write_file(f"user/{chat_id}.si", oid)

    # --- API kalit yangilash ---
    elif data == "apidetail=newkey":
        new_key = hashlib.md5(os.urandom(16)).hexdigest()
        execute("UPDATE users SET api_key = %s WHERE id = %s", (new_key, chat_id))
        user = fetch_one("SELECT * FROM users WHERE id = %s", (chat_id,))
        edit_msg(chat_id, mid2,
            f"✅ API kalit yangilandi.\n\n<code>{user['api_key']}</code>\n\n"
            f"💵 API hisobi: {user['balance']} so'm",
            keyboard([[{"text": "🔄 APIni yangilash", "callback_data": "apidetail=newkey"}]])
        )

    # --- Konkurs ---
    elif data == "konkurs" and join_check(chat_id):
        users = fetch_all("SELECT * FROM `users` ORDER BY balance DESC LIMIT 10")
        text = "🏆 TOP-10 balanslar reytingi\n\n"
        for i, u in enumerate(users, 1):
            text += f"<b>{i})</b> <a href='tg://user?id={u['id']}'>{u['id']}</a> - {u['balance']} so'm\n"
        edit_msg(chat_id, mid2, text, None)

    # --- Asosiy menyu ---
    elif data == "main" and join_check(chat_id):
        del_msg(chat_id, mid2)
        sms(chat_id, "🖥️ Asosiy menyuga qaytdingiz.", m)
        _del_step(chat_id)

    # --- Yopish ---
    elif data == "yopish":
        del_msg(chat_id, mid2)

# ===========================================================================
# 7. app/controller/orders.php => BUYURTMALAR TARIXI
# ===========================================================================

def get_orders_page(api_key=None, status_filter=None):
    """Foydalanuvchining buyurtmalar tarixi (HTML page uchun)."""
    if not api_key:
        return []
    user = fetch_one("SELECT * FROM users WHERE api_key = %s", (api_key,))
    if not user:
        return []
    uid = user['id']
    if status_filter:
        orders = fetch_all(
            "SELECT * FROM myorder WHERE user_id = %s AND status = %s",
            (uid, status_filter)
        )
    else:
        orders = fetch_all("SELECT * FROM myorder WHERE user_id = %s", (uid,))
    return orders

# ===========================================================================
# 8. app/controller/services.php => XIZMATLAR SAHIFASI
# ===========================================================================

def get_services_list(search=None):
    """Barcha xizmatlar ro'yxatini qaytaradi."""
    services = fetch_all("SELECT * FROM `services`")
    result = []
    for s in services:
        name = base64.b64decode(s['service_name']).decode('utf-8', errors='ignore')
        if search and search.lower() not in name.lower():
            continue
        cid = s['category_id']
        ca = fetch_one("SELECT * FROM cates WHERE cate_id = %s", (cid,))
        categ = ca['category_id'] if ca else None
        cas = fetch_one("SELECT * FROM categorys WHERE category_id = %s", (categ,)) if categ else None
        category = ""
        if cas and ca:
            category = (
                base64.b64decode(cas['category_name']).decode('utf-8', errors='ignore')
                + " > " +
                base64.b64decode(ca['name']).decode('utf-8', errors='ignore')
            )
        desc_raw = s.get('service_desc')
        desc = base64.b64decode(desc_raw).decode('utf-8', errors='ignore') if desc_raw else ""
        result.append({
            "id": s['service_id'],
            "name": name,
            "category": category,
            "price": s['service_price'],
            "min": s['service_min'],
            "max": s['service_max'],
            "description": desc,
        })
    return result

# ===========================================================================
# 9. DATABASE SQL (db.sql => CREATE TABLE)
# ===========================================================================

DB_SCHEMA = """
-- QoraCoders SMM Panel Database Schema
-- (db.sql Python string sifatida)

CREATE TABLE IF NOT EXISTS `categorys` (
  `category_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `category_name` TEXT NOT NULL,
  `category_status` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `cates` (
  `cate_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` TEXT NOT NULL,
  `category_id` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `myorder` (
  `order_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` TEXT NOT NULL,
  `retail` TEXT NOT NULL,
  `status` TEXT NOT NULL,
  `service` TEXT NOT NULL,
  `order_create` TEXT,
  `last_check` TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orders` (
  `order_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_order` TEXT NOT NULL,
  `provider` TEXT NOT NULL,
  `status` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `percent` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `percent` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `providers` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_url` VARCHAR(300) NOT NULL,
  `api_key` VARCHAR(300) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `send` (
  `send_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `time1` TEXT NOT NULL, `time2` TEXT NOT NULL,
  `time3` TEXT NOT NULL, `time4` TEXT NOT NULL, `time5` TEXT NOT NULL,
  `start_id` TEXT NOT NULL, `stop_id` TEXT NOT NULL,
  `admin_id` TEXT NOT NULL, `message_id` TEXT NOT NULL,
  `reply_markup` TEXT NOT NULL, `step` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `services` (
  `service_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `service_edit` TEXT NOT NULL,
  `category_id` TEXT NOT NULL,
  `service_price` TEXT NOT NULL,
  `service_api` TEXT NOT NULL,
  `api_service` TEXT NOT NULL,
  `api_currency` TEXT NOT NULL,
  `service_type` TEXT NOT NULL,
  `api_detail` TEXT NOT NULL,
  `service_name` TEXT NOT NULL,
  `service_desc` TEXT NOT NULL,
  `service_min` TEXT NOT NULL,
  `service_max` TEXT NOT NULL,
  `service_status` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `settings` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `site_style` TEXT NOT NULL,
  `site_theme` TEXT NOT NULL,
  `ref_status` TEXT NOT NULL,
  `referal` TEXT NOT NULL,
  `orders` TEXT NOT NULL,
  `kabinet` TEXT NOT NULL,
  `start` TEXT NOT NULL,
  `status` TEXT NOT NULL,
  `bonus` TEXT NOT NULL,
  `payme_id` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `id` TEXT NOT NULL,
  `referal` TEXT NOT NULL,
  `outing` TEXT NOT NULL,
  `status` TEXT NOT NULL,
  `balance` TEXT NOT NULL,
  `api_key` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Default settings
INSERT IGNORE INTO `percent` (`id`, `percent`) VALUES (1, '40');
INSERT IGNORE INTO `settings`
  (`id`,`site_style`,`site_theme`,`ref_status`,`referal`,`orders`,`kabinet`,`start`,`status`,`bonus`,`payme_id`)
VALUES
  (1,'theme8.0','Eternity','off','MTAw',
   '4pyFIEJ1eXVydG1hIHFhYnVsIHFpbGluZGk=',
   '8J+StSBIaXNvYmluZ2l6OiB7YmFsYW5jZX0gc28=',
   '8J+WpSBBc29zaXkgbWVueXVkYXNpeg==',
   'active','4','');
"""

def init_database():
    """Ma'lumotlar bazasini yaratadi."""
    conn = get_db()
    cur = conn.cursor()
    for statement in DB_SCHEMA.split(";"):
        statement = statement.strip()
        if statement and not statement.startswith("--"):
            try:
                cur.execute(statement)
                conn.commit()
            except Exception:
                pass
    cur.close()
    conn.close()

# ===========================================================================
# 10. FLASK WEB SERVER (index.php, api.php, services.php, orders.php routlar)
# ===========================================================================

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Asosiy sahifa (index.php)."""
    total_services  = count_rows("services")
    total_orders    = count_rows("orders")
    completed_orders = len(fetch_all("SELECT order_id FROM orders WHERE status='Completed'"))
    total_users     = count_rows("users")
    free_services   = len(fetch_all("SELECT service_id FROM services WHERE service_price='0'"))

    return jsonify({
        "page": "index",
        "stats": {
            "total_services": total_services,
            "completed_orders": completed_orders,
            "total_orders": total_orders,
            "total_users": total_users,
            "free_services": free_services,
            "support": "24/7",
        }
    })

@app.route("/api/v2", methods=["GET", "POST"])
def api_v2():
    """REST API endpoint (api.php)."""
    params = request.values
    key     = params.get("key", "")
    action  = params.get("action", "")
    service = params.get("service", "")
    link    = params.get("link", "")
    quantity= params.get("quantity", 0)
    order_id= params.get("order", "")
    orders_str = params.get("orders", "")

    if action == "balance":
        return jsonify(api_balance(key))
    elif action == "add":
        return jsonify(api_add_order(key, service, link, quantity))
    elif action == "services":
        return jsonify(api_services(key))
    elif action == "orders":
        return jsonify(api_orders(key))
    elif action == "status":
        return jsonify(api_status(key, orders_str or None, order_id or None))
    else:
        return jsonify({"error": "Incorrect request"})

@app.route("/services", methods=["GET"])
def services_page():
    """Xizmatlar sahifasi (services.php)."""
    search = request.args.get("name", "")
    data = get_services_list(search or None)
    return jsonify({"services": data})

@app.route("/orders", methods=["GET"])
def orders_page():
    """Buyurtmalar sahifasi (orders.php)."""
    api_key = request.args.get("key", "")
    status  = request.args.get("status", "")
    data = get_orders_page(api_key, status or None)
    return jsonify({"orders": data})

@app.route("/avg", methods=["GET"])
def avg_page():
    """O'rtacha statistika (avg.php)."""
    return jsonify(avg_services())

@app.route("/payme.php", methods=["GET"])
def payme_endpoint():
    """Payme to'lov endpoint (payme.php)."""
    action  = request.args.get("action", "")
    amount  = request.args.get("sum", 0)
    card    = request.args.get("card", "")
    cheque_id = request.args.get("id", "")
    desc    = request.args.get("desc", "")

    if action == "create":
        return jsonify(payme_create(card, amount, desc))
    elif action == "info":
        return jsonify(payme_check(cheque_id))
    return jsonify({"error": "Unknown action"})

@app.route("/bot/webhook", methods=["POST"])
def telegram_webhook():
    """Telegram bot webhook (bot.php)."""
    update = request.get_json(force=True) or {}
    try:
        handle_update(update)
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"ok": True})

@app.route("/update", methods=["GET"])
def cron_update():
    """Narxlarni yangilash CRON (update.php)."""
    action = request.args.get("update", "")
    if action == "prices":
        result = update_service_prices()
        return jsonify(result)
    return jsonify({"error": "Unknown update action"})

@app.errorhandler(404)
def page_not_found(e):
    """404 sahifa (404.php)."""
    return jsonify({"error": "404 - Page not found"}), 404

# ===========================================================================
# ISHGA TUSHIRISH
# ===========================================================================

if __name__ == "__main__":
    # Kerakli papkalarni yaratish
    for folder in ["user", "set", "set/pay", "donat/PUBGMOBILE", "donat/FreeFire"]:
        os.makedirs(folder, exist_ok=True)

    # Ma'lumotlar bazasini ishga tushirish (ixtiyoriy)
    # init_database()

    # Webhook o'rnatish (ixtiyoriy - o'z domeningizni kiriting)
    # bot_call("setWebhook", {"url": "https://yourdomain.com/bot/webhook"})

    print("=" * 60)
    print("QoraCoders SMM Panel - Python versiyasi")
    print("=" * 60)
    print(f"Admin ID     : {ADMIN_ID}")
    print(f"Bot username : @{BOT_USERNAME}")
    print(f"DB           : {DB_NAME}@{DB_SERVER}")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /            - Asosiy sahifa")
    print("  GET/POST /api/v2  - REST API")
    print("  GET  /services    - Xizmatlar")
    print("  GET  /orders      - Buyurtmalar")
    print("  GET  /payme.php   - Payme to'lov")
    print("  POST /bot/webhook - Telegram webhook")
    print("  GET  /update      - CRON narx yangilash")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=False)
