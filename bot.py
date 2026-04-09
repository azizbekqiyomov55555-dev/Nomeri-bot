"""
╔══════════════════════════════════════════════════════════╗
║      SMM BOT — TO'LIQ KOD (SQLite, Webhook, Admin)      ║
║  MySQL yo'q! SQLite ishlatiladi — sozlama shart emas.   ║
╚══════════════════════════════════════════════════════════╝
"""

import base64
import hashlib
import json
import logging
import os
import random
import secrets
import sqlite3
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

import pytz
import requests
import urllib3

urllib3.disable_warnings()

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════
#  SOZLASH
# ════════════════════════════════════════════════════════════════════
BOT_TOKEN    = os.getenv("BOT_TOKEN",   "TOKEN_SHUNGA")
ADMIN_ID     = int(os.getenv("ADMIN_ID", "123456789"))
WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "")
PORT         = int(os.getenv("PORT", 8080))
DB_PATH      = os.getenv("DB_PATH", "smm_bot.db")
MIN_DEPOSIT  = 1000
REFERAL_BONUS = 500.0
TG_API       = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ════════════════════════════════════════════════════════════════════
#  DATABASE — SQLite
# ════════════════════════════════════════════════════════════════════

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Jadvallarni yaratadi (birinchi ishga tushganda)."""
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,
            user_id     INTEGER,
            status      TEXT DEFAULT 'active',
            balance     REAL DEFAULT 0,
            outing      REAL DEFAULT 0,
            api_key     TEXT DEFAULT '',
            referal     TEXT DEFAULT '',
            lang        TEXT DEFAULT 'default',
            currency    TEXT DEFAULT 'UZS'
        );
        CREATE TABLE IF NOT EXISTS categorys (
            category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name   TEXT NOT NULL,
            category_status TEXT DEFAULT 'active',
            category_line   INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS services (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id  TEXT DEFAULT '',
            category_id INTEGER DEFAULT 0,
            name        TEXT NOT NULL,
            rate        REAL DEFAULT 0,
            min         INTEGER DEFAULT 10,
            max         INTEGER DEFAULT 10000,
            status      TEXT DEFAULT 'active',
            provider_id INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER DEFAULT 0,
            service_id  INTEGER DEFAULT 0,
            link        TEXT DEFAULT '',
            quantity    INTEGER DEFAULT 0,
            charge      REAL DEFAULT 0,
            status      TEXT DEFAULT 'pending',
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER DEFAULT 0,
            amount      REAL DEFAULT 0,
            method      TEXT DEFAULT 'manual',
            status      TEXT DEFAULT 'pending',
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS channels (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            user   TEXT DEFAULT '',
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS referal (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            referal_code TEXT DEFAULT '',
            owner_id     INTEGER DEFAULT 0,
            invited_id   INTEGER DEFAULT 0,
            bonus        REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS admins (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS steps (
            user_id INTEGER PRIMARY KEY,
            step    TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS mainsetting (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            setting TEXT DEFAULT '',
            value   TEXT DEFAULT '',
            status  TEXT DEFAULT '1'
        );
        """)
        # Namuna kategoriya va xizmatlar
        existing = db.execute("SELECT COUNT(*) FROM categorys").fetchone()[0]
        if existing == 0:
            db.execute("INSERT INTO categorys (category_name, category_line) VALUES (?,?)",
                       ("📸 Instagram", 1))
            db.execute("INSERT INTO categorys (category_name, category_line) VALUES (?,?)",
                       ("▶️ YouTube", 2))
            db.execute("INSERT INTO categorys (category_name, category_line) VALUES (?,?)",
                       ("📱 TikTok", 3))
            db.execute("""INSERT INTO services
                (service_id, category_id, name, rate, min, max, description)
                VALUES (?,?,?,?,?,?,?)""",
                ("1", 1, "❤️ Instagram Like", 10.0, 100, 10000, "Tez yetkaziladi"))
            db.execute("""INSERT INTO services
                (service_id, category_id, name, rate, min, max, description)
                VALUES (?,?,?,?,?,?,?)""",
                ("2", 1, "👥 Instagram Follower", 50.0, 50, 5000, "Real akkauntlar"))
            db.execute("""INSERT INTO services
                (service_id, category_id, name, rate, min, max, description)
                VALUES (?,?,?,?,?,?,?)""",
                ("3", 2, "▶️ YouTube View", 5.0, 500, 50000, "HQ views"))
        db.commit()
    logger.info("Database tayyor: %s", DB_PATH)


# ════════════════════════════════════════════════════════════════════
#  DB YORDAMCHI FUNKSIYALAR
# ════════════════════════════════════════════════════════════════════

def db_one(query: str, params=()) -> Optional[sqlite3.Row]:
    with get_db() as db:
        return db.execute(query, params).fetchone()

def db_all(query: str, params=()) -> List[sqlite3.Row]:
    with get_db() as db:
        return db.execute(query, params).fetchall()

def db_run(query: str, params=()) -> int:
    with get_db() as db:
        cur = db.execute(query, params)
        db.commit()
        return cur.lastrowid or cur.rowcount


# ════════════════════════════════════════════════════════════════════
#  FOYDALANUVCHI
# ════════════════════════════════════════════════════════════════════

def get_or_create_user(chat_id: int) -> sqlite3.Row:
    user = db_one("SELECT * FROM users WHERE id=?", (chat_id,))
    if user:
        return user
    api_key = hashlib.md5(secrets.token_bytes(16)).hexdigest()
    referal = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
    db_run(
        "INSERT OR IGNORE INTO users (id, user_id, api_key, referal) VALUES (?,?,?,?)",
        (chat_id, chat_id, api_key, referal)
    )
    return db_one("SELECT * FROM users WHERE id=?", (chat_id,))

def update_balance(user_id: int, amount: float):
    db_run("UPDATE users SET balance=balance+? WHERE id=?", (amount, user_id))


# ════════════════════════════════════════════════════════════════════
#  QADAM (STEP)
# ════════════════════════════════════════════════════════════════════

def get_step(user_id: int) -> str:
    row = db_one("SELECT step FROM steps WHERE user_id=?", (user_id,))
    return row["step"] if row else ""

def set_step(user_id: int, step: str):
    db_run("INSERT OR REPLACE INTO steps (user_id, step) VALUES (?,?)", (user_id, step))

def clear_step(user_id: int):
    db_run("DELETE FROM steps WHERE user_id=?", (user_id,))


# ════════════════════════════════════════════════════════════════════
#  TELEGRAM API
# ════════════════════════════════════════════════════════════════════

session = requests.Session()
session.verify = False

def tg(method: str, data: dict = None) -> Optional[dict]:
    try:
        r = session.post(f"{TG_API}/{method}", json=data or {}, timeout=30)
        return r.json()
    except Exception as e:
        logger.error("TG API [%s]: %s", method, e)
        return None

def send_msg(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": f"<b>{text}</b>", "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", payload)

def edit_msg(chat_id, msg_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": msg_id,
               "text": f"<b>{text}</b>", "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("editMessageText", payload)

def del_msg(chat_id, msg_id):
    return tg("deleteMessage", {"chat_id": chat_id, "message_id": msg_id})

def answer_cb(cq_id, text="", alert=False):
    return tg("answerCallbackQuery",
              {"callback_query_id": cq_id, "text": text, "show_alert": alert})

def set_webhook(url):
    return tg("setWebhook", {"url": url})


# ════════════════════════════════════════════════════════════════════
#  KLAVIATURALAR
# ════════════════════════════════════════════════════════════════════

def ikb(buttons: list) -> str:
    return json.dumps({"inline_keyboard": buttons})

def rkb(buttons: list, resize=True) -> str:
    return json.dumps({
        "keyboard": [[{"text": b} for b in row] for row in buttons],
        "resize_keyboard": resize,
    })

def main_menu() -> str:
    return rkb([
        ["🛒 Yangi buyurtma", "📦 Buyurtmalarim"],
        ["💰 Balans to'ldirish", "👤 Kabinet"],
        ["👥 Referal", "❓ Yordam"],
    ])

def admin_menu() -> str:
    return rkb([
        ["📊 Statistika",    "👤 Foydalanuvchi"],
        ["💰 Balans berish", "📢 Reklama"],
        ["➕ Kanal qo'sh",   "📋 Kanallar"],
        ["🏠 Bosh menyu"],
    ])

def back_btn() -> str:
    return rkb([["⬅️ Orqaga"]])


# ════════════════════════════════════════════════════════════════════
#  YORDAMCHI
# ════════════════════════════════════════════════════════════════════

def nf(n, dec=0):
    if dec == 0:
        return f"{int(n):,}".replace(",", " ")
    return f"{n:,.{dec}f}".replace(",", " ")

def now_uz():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz).strftime("%d/%m/%Y | %H:%M")

def is_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    return bool(db_one("SELECT id FROM admins WHERE user_id=?", (str(user_id),)))

def check_join(chat_id: int) -> bool:
    channels = db_all("SELECT * FROM channels WHERE status='active'")
    if not channels:
        return True
    not_joined = []
    for ch in channels:
        res = tg("getChatMember", {"chat_id": ch["user"], "user_id": chat_id})
        if not res or not res.get("ok"):
            not_joined.append(ch)
            continue
        if res["result"].get("status", "") not in ("creator", "administrator", "member"):
            not_joined.append(ch)
    if not not_joined:
        return True
    buttons = [
        [{"text": f"❌ {ch['user']}", "url": f"t.me/{ch['user'].lstrip('@')}"}]
        for ch in not_joined
    ]
    buttons.append([{"text": "✅ Tekshirish", "callback_data": "check_join"}])
    send_msg(chat_id, "📢 Kanallarga a'zo bo'ling:", reply_markup=ikb(buttons))
    return False

def apply_referal(new_id: int, code: str):
    owner = db_one("SELECT * FROM users WHERE referal=?", (code,))
    if not owner or owner["id"] == new_id:
        return
    if db_one("SELECT id FROM referal WHERE invited_id=?", (new_id,)):
        return
    try:
        db_run("INSERT INTO referal (referal_code,owner_id,invited_id,bonus) VALUES (?,?,?,?)",
               (code, owner["id"], new_id, REFERAL_BONUS))
        update_balance(owner["id"], REFERAL_BONUS)
        send_msg(owner["id"],
                 f"🎉 Yangi referal!\n💰 +{nf(REFERAL_BONUS)} UZS balansingizga qo'shildi!")
    except Exception as e:
        logger.warning("Referal xatosi: %s", e)


# ════════════════════════════════════════════════════════════════════
#  UPDATE HANDLER
# ════════════════════════════════════════════════════════════════════

def handle_update(update: dict):
    try:
        if "message" in update:
            _on_message(update["message"])
        elif "callback_query" in update:
            _on_callback(update["callback_query"])
    except Exception as e:
        logger.error("handle_update: %s", e, exc_info=True)


# ════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════

def _on_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()
    name    = msg.get("from", {}).get("first_name", "Foydalanuvchi")

    user = get_or_create_user(chat_id)
    step = get_step(chat_id)

    # ── /start ──────────────────────────────────────────────────────
    if text == "/start" or text.startswith("/start "):
        if not check_join(chat_id):
            return
        parts = text.split()
        if len(parts) > 1:
            apply_referal(chat_id, parts[1])
        clear_step(chat_id)
        send_msg(chat_id,
                 f"Assalomu alaykum, {name}! 👋\nSMM botimizga xush kelibsiz!",
                 reply_markup=main_menu())
        return

    # ── /admin ──────────────────────────────────────────────────────
    if text == "/admin" and is_admin(chat_id):
        clear_step(chat_id)
        send_msg(chat_id, "⚙️ Admin paneli", reply_markup=admin_menu())
        return

    # ── Admin text ──────────────────────────────────────────────────
    if is_admin(chat_id) and _admin_text(chat_id, text, step, name):
        return

    # ── Orqaga ──────────────────────────────────────────────────────
    if text in ("⬅️ Orqaga", "🏠 Bosh menyu"):
        clear_step(chat_id)
        send_msg(chat_id, f"Assalomu alaykum, {name}! 👋", reply_markup=main_menu())
        return

    # ── Kabinet ─────────────────────────────────────────────────────
    if text == "👤 Kabinet":
        clear_step(chat_id)
        send_msg(
            chat_id,
            f"👤 Kabinet\n\n"
            f"🆔 ID: <code>{chat_id}</code>\n"
            f"💰 Balans: {nf(float(user['balance']), 2)} UZS\n"
            f"🔑 API: <code>{user['api_key']}</code>\n"
            f"📅 {now_uz()}",
            reply_markup=ikb([
                [{"text": "💰 Balans to'ldirish", "callback_data": "add_funds"}],
            ])
        )
        return

    # ── Balans to'ldirish ────────────────────────────────────────────
    if text == "💰 Balans to'ldirish":
        set_step(chat_id, "await_deposit")
        send_msg(chat_id,
                 f"💵 Summani kiriting (min: {nf(MIN_DEPOSIT)} UZS):",
                 reply_markup=back_btn())
        return

    # ── Buyurtmalarim ────────────────────────────────────────────────
    if text == "📦 Buyurtmalarim":
        clear_step(chat_id)
        orders = db_all(
            "SELECT o.*, s.name as sname FROM orders o "
            "LEFT JOIN services s ON o.service_id=s.id "
            "WHERE o.user_id=? ORDER BY o.id DESC LIMIT 10", (chat_id,)
        )
        if not orders:
            send_msg(chat_id, "📦 Buyurtmalar yo'q.", reply_markup=main_menu())
            return
        STATUS = {
            "pending": "⏳ Kutilmoqda", "active": "🔄 Jarayonda",
            "completed": "✅ Bajarildi", "canceled": "❌ Bekor",
            "partial": "⚠️ Qisman",
        }
        for o in orders:
            send_msg(chat_id,
                     f"🔢 #{o['id']}\n"
                     f"📋 {o['sname'] or o['service_id']}\n"
                     f"🔗 {o['link']}\n"
                     f"📊 {o['quantity']} ta\n"
                     f"💰 {nf(float(o['charge']), 2)} UZS\n"
                     f"📌 {STATUS.get(o['status'], o['status'])}")
        return

    # ── Yangi buyurtma ───────────────────────────────────────────────
    if text == "🛒 Yangi buyurtma":
        clear_step(chat_id)
        if not check_join(chat_id):
            return
        cats = db_all("SELECT * FROM categorys WHERE category_status='active' ORDER BY category_line")
        if not cats:
            send_msg(chat_id, "❌ Kategoriyalar yo'q.", reply_markup=main_menu())
            return
        rows = [[{"text": c["category_name"], "callback_data": f"cat_{c['category_id']}"}]
                for c in cats]
        rows.append([{"text": "⬅️ Orqaga", "callback_data": "back_main"}])
        send_msg(chat_id, "📂 Kategoriyani tanlang:", reply_markup=ikb(rows))
        return

    # ── Referal ──────────────────────────────────────────────────────
    if text == "👥 Referal":
        clear_step(chat_id)
        count = db_one("SELECT COUNT(*) as c FROM referal WHERE owner_id=?",
                       (chat_id,))["c"]
        total = db_one("SELECT SUM(bonus) as t FROM referal WHERE owner_id=?",
                       (chat_id,))
        total_bonus = float(total["t"] or 0) if total else 0
        ref_link = f"https://t.me/smmbot?start={user['referal']}"
        send_msg(chat_id,
                 f"👥 Referal dasturi\n\n"
                 f"🔗 Havolingiz:\n<code>{ref_link}</code>\n\n"
                 f"👤 Taklif qilinganlar: {count}\n"
                 f"💰 Jami bonus: {nf(total_bonus, 2)} UZS")
        return

    # ── Yordam ───────────────────────────────────────────────────────
    if text == "❓ Yordam":
        set_step(chat_id, "await_ticket")
        send_msg(chat_id,
                 "❓ Savolingizni yozing, adminlarga yuboriladi:",
                 reply_markup=back_btn())
        return

    # ── Qadam handler ────────────────────────────────────────────────
    _step_handler(chat_id, text, step, user, name)


# ════════════════════════════════════════════════════════════════════
#  QADAM HANDLER
# ════════════════════════════════════════════════════════════════════

def _step_handler(chat_id, text, step, user, name=""):
    if not step:
        return

    # Balans to'ldirish
    if step == "await_deposit":
        try:
            amount = float(text.replace(" ", "").replace(",", "."))
        except ValueError:
            send_msg(chat_id, "❌ Raqam kiriting!")
            return
        if amount < MIN_DEPOSIT:
            send_msg(chat_id, f"❌ Minimum: {nf(MIN_DEPOSIT)} UZS")
            return
        pid = db_run(
            "INSERT INTO payments (user_id, amount, method) VALUES (?,?,?)",
            (chat_id, amount, "manual")
        )
        clear_step(chat_id)
        send_msg(chat_id,
                 f"📋 To'lov so'rovi yuborildi\n\n"
                 f"🔢 #{pid}\n"
                 f"💰 {nf(amount)} UZS\n\n"
                 f"⏳ Admin tasdiqlashini kuting.",
                 reply_markup=main_menu())
        for adm in _get_admins():
            try:
                send_msg(adm,
                         f"💰 Yangi to'lov so'rovi\n\n"
                         f"👤 ID: <code>{chat_id}</code>\n"
                         f"💵 {nf(amount)} UZS\n"
                         f"🔢 #{pid}",
                         reply_markup=ikb([[
                             {"text": "✅ Tasdiqlash", "callback_data": f"pay_ok_{pid}"},
                             {"text": "❌ Rad etish",  "callback_data": f"pay_no_{pid}"},
                         ]]))
            except Exception:
                pass
        return

    # Buyurtma: havola
    if step.startswith("await_link|"):
        svc_id = int(step.split("|")[1])
        if not text.startswith("http"):
            send_msg(chat_id, "❌ To'g'ri havola kiriting (http bilan)!")
            return
        svc = db_one("SELECT * FROM services WHERE id=?", (svc_id,))
        set_step(chat_id, f"await_qty|{svc_id}|{text}")
        send_msg(chat_id, f"🔢 Miqdorni kiriting (Min: {svc['min']}, Max: {svc['max']}):")
        return

    # Buyurtma: miqdor
    if step.startswith("await_qty|"):
        parts  = step.split("|")
        svc_id = int(parts[1])
        link   = parts[2]
        try:
            qty = int(text.replace(" ", ""))
        except ValueError:
            send_msg(chat_id, "❌ Raqam kiriting!")
            return
        svc = db_one("SELECT * FROM services WHERE id=?", (svc_id,))
        if not (svc["min"] <= qty <= svc["max"]):
            send_msg(chat_id, f"❌ Min: {svc['min']}, Max: {svc['max']}")
            return
        charge = round(svc["rate"] * qty / 1000, 4)
        set_step(chat_id, f"confirm_order|{svc_id}|{link}|{qty}")
        bal = float(db_one("SELECT balance FROM users WHERE id=?", (chat_id,))["balance"])
        send_msg(chat_id,
                 f"📋 Buyurtmani tasdiqlang\n\n"
                 f"🛒 {svc['name']}\n"
                 f"🔗 {link}\n"
                 f"🔢 {qty} ta\n"
                 f"💰 Narx: {nf(charge, 2)} UZS\n"
                 f"💳 Balans: {nf(bal, 2)} UZS",
                 reply_markup=ikb([[
                     {"text": "✅ Tasdiqlash", "callback_data": "order_ok"},
                     {"text": "❌ Bekor",       "callback_data": "order_no"},
                 ]]))
        return

    # Ticket
    if step == "await_ticket":
        clear_step(chat_id)
        send_msg(chat_id, "✅ Murojaat yuborildi!", reply_markup=main_menu())
        for adm in _get_admins():
            try:
                send_msg(adm,
                         f"📩 Yangi murojaat\n\n"
                         f"👤 ID: <code>{chat_id}</code>\n"
                         f"💬 {text}",
                         reply_markup=ikb([[
                             {"text": "💬 Javob berish",
                              "callback_data": f"reply_{chat_id}"}
                         ]]))
            except Exception:
                pass
        return

    # Admin: user id
    if step == "admin_user_id":
        try:
            uid = int(text)
        except ValueError:
            send_msg(chat_id, "❌ To'g'ri ID kiriting!")
            return
        u = db_one("SELECT * FROM users WHERE id=?", (uid,))
        if not u:
            send_msg(chat_id, "❌ Foydalanuvchi topilmadi!")
            return
        set_step(chat_id, f"admin_amount|{uid}")
        send_msg(chat_id,
                 f"👤 ID: <code>{uid}</code>\n"
                 f"💰 Balans: {nf(float(u['balance']), 2)} UZS\n\n"
                 f"Qo'shilajak summani kiriting:")
        return

    # Admin: summa berish
    if step.startswith("admin_amount|"):
        uid = int(step.split("|")[1])
        try:
            amount = float(text.replace(" ", "").replace(",", "."))
        except ValueError:
            send_msg(chat_id, "❌ Raqam kiriting!")
            return
        update_balance(uid, amount)
        clear_step(chat_id)
        new_bal = float(db_one("SELECT balance FROM users WHERE id=?", (uid,))["balance"])
        send_msg(chat_id,
                 f"✅ {nf(amount)} UZS qo'shildi!\n"
                 f"👤 ID: <code>{uid}</code>\n"
                 f"💰 Yangi balans: {nf(new_bal, 2)} UZS",
                 reply_markup=admin_menu())
        try:
            send_msg(uid, f"✅ Balansingiz to'ldirildi!\n💰 +{nf(amount)} UZS")
        except Exception:
            pass
        return

    # Admin: reklama
    if step == "admin_broadcast":
        clear_step(chat_id)
        users = db_all("SELECT id FROM users")
        sent = failed = 0
        send_msg(chat_id, "📢 Yuborilmoqda...", reply_markup=admin_menu())
        for u in users:
            try:
                r = send_msg(u["id"], text)
                if r and r.get("ok"):
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        send_msg(chat_id, f"✅ Yuborildi: {sent} | ❌ Xato: {failed}")
        return

    # Admin: kanal qo'shish
    if step == "admin_channel":
        username = text.lstrip("@")
        db_run("INSERT INTO channels (user, status) VALUES (?,?)",
               (f"@{username}", "active"))
        clear_step(chat_id)
        send_msg(chat_id, f"✅ @{username} qo'shildi!", reply_markup=admin_menu())
        return

    # Admin: ticket javob
    if step.startswith("admin_reply|"):
        target = int(step.split("|")[1])
        clear_step(chat_id)
        try:
            send_msg(target, f"📩 Admin javobi:\n\n{text}")
            send_msg(chat_id, "✅ Javob yuborildi!", reply_markup=admin_menu())
        except Exception:
            send_msg(chat_id, "❌ Yuborib bo'lmadi.", reply_markup=admin_menu())
        return


# ════════════════════════════════════════════════════════════════════
#  ADMIN TEXT HANDLER
# ════════════════════════════════════════════════════════════════════

def _admin_text(chat_id, text, step, name) -> bool:
    if text == "📊 Statistika":
        clear_step(chat_id)
        u_count = db_one("SELECT COUNT(*) as c FROM users")["c"]
        o_act   = db_one("SELECT COUNT(*) as c FROM orders WHERE status='active'")["c"]
        o_done  = db_one("SELECT COUNT(*) as c FROM orders WHERE status='completed'")["c"]
        total_p = db_one("SELECT SUM(amount) as t FROM payments WHERE status='paid'")
        total   = float(total_p["t"] or 0) if total_p else 0
        send_msg(chat_id,
                 f"📊 Statistika\n\n"
                 f"👤 Foydalanuvchilar: {u_count}\n"
                 f"📦 Aktiv buyurtmalar: {o_act}\n"
                 f"✅ Bajarilgan: {o_done}\n"
                 f"💰 Jami to'lovlar: {nf(total, 2)} UZS\n"
                 f"📅 {now_uz()}",
                 reply_markup=admin_menu())
        return True

    if text == "💰 Balans berish":
        set_step(chat_id, "admin_user_id")
        send_msg(chat_id, "👤 Foydalanuvchi ID sini kiriting:", reply_markup=back_btn())
        return True

    if text == "📢 Reklama":
        set_step(chat_id, "admin_broadcast")
        send_msg(chat_id, "📢 Xabar matnini yozing:", reply_markup=back_btn())
        return True

    if text == "➕ Kanal qo'sh":
        set_step(chat_id, "admin_channel")
        send_msg(chat_id, "📢 Kanal username (@bilan):", reply_markup=back_btn())
        return True

    if text == "📋 Kanallar":
        clear_step(chat_id)
        channels = db_all("SELECT * FROM channels")
        if not channels:
            send_msg(chat_id, "❌ Kanallar yo'q.", reply_markup=admin_menu())
            return True
        rows = [[{"text": f"❌ {ch['user']}", "callback_data": f"del_ch_{ch['id']}"}]
                for ch in channels]
        send_msg(chat_id, "📋 Kanallar (o'chirish uchun bosing):", reply_markup=ikb(rows))
        return True

    if text == "👤 Foydalanuvchi":
        set_step(chat_id, "admin_user_id")
        send_msg(chat_id, "🔍 Foydalanuvchi ID sini kiriting:", reply_markup=back_btn())
        return True

    if text == "🏠 Bosh menyu":
        clear_step(chat_id)
        send_msg(chat_id, f"🏠 Bosh menyu", reply_markup=main_menu())
        return True

    return False


# ════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ════════════════════════════════════════════════════════════════════

def _on_callback(cq: dict):
    chat_id = cq["from"]["id"]
    cq_id   = cq["id"]
    data    = cq.get("data", "")
    msg_id  = cq["message"]["message_id"]
    name    = cq["from"].get("first_name", "")

    user = get_or_create_user(chat_id)

    # Obuna tekshiruvi
    if data == "check_join":
        if check_join(chat_id):
            answer_cb(cq_id, "✅ Rahmat!", alert=True)
            del_msg(chat_id, msg_id)
            send_msg(chat_id, f"Assalomu alaykum, {name}! 👋",
                     reply_markup=main_menu())
        else:
            answer_cb(cq_id, "❌ Hali a'zo bo'lmadingiz!", alert=True)
        return

    # Balans to'ldirish (kabinet)
    if data == "add_funds":
        answer_cb(cq_id)
        set_step(chat_id, "await_deposit")
        send_msg(chat_id, f"💵 Summani kiriting (min: {nf(MIN_DEPOSIT)} UZS):",
                 reply_markup=back_btn())
        return

    # Kategoriya
    if data.startswith("cat_"):
        answer_cb(cq_id)
        cat_id   = int(data[4:])
        services = db_all(
            "SELECT * FROM services WHERE category_id=? AND status='active'", (cat_id,)
        )
        if not services:
            answer_cb(cq_id, "❌ Xizmatlar yo'q!", alert=True)
            return
        rows = [[{"text": f"{s['name']} — {nf(s['rate'], 2)}/1000",
                  "callback_data": f"svc_{s['id']}"}]
                for s in services]
        rows.append([{"text": "⬅️ Orqaga", "callback_data": "back_cats"}])
        edit_msg(chat_id, msg_id, "📋 Xizmatni tanlang:", reply_markup=ikb(rows))
        return

    if data == "back_cats":
        answer_cb(cq_id)
        cats = db_all("SELECT * FROM categorys WHERE category_status='active' ORDER BY category_line")
        rows = [[{"text": c["category_name"], "callback_data": f"cat_{c['category_id']}"}]
                for c in cats]
        rows.append([{"text": "⬅️ Orqaga", "callback_data": "back_main"}])
        edit_msg(chat_id, msg_id, "📂 Kategoriyani tanlang:", reply_markup=ikb(rows))
        return

    if data == "back_main":
        answer_cb(cq_id)
        del_msg(chat_id, msg_id)
        send_msg(chat_id, f"🏠 Bosh menyu", reply_markup=main_menu())
        return

    # Xizmat
    if data.startswith("svc_"):
        answer_cb(cq_id)
        svc = db_one("SELECT * FROM services WHERE id=?", (int(data[4:]),))
        if not svc:
            answer_cb(cq_id, "❌ Topilmadi!", alert=True)
            return
        edit_msg(chat_id, msg_id,
                 f"📋 {svc['name']}\n"
                 f"💰 Narx: {nf(svc['rate'], 2)}/1000\n"
                 f"📊 Min: {svc['min']} | Max: {svc['max']}\n"
                 f"📝 {svc['description'] or '—'}",
                 reply_markup=ikb([
                     [{"text": "🛒 Buyurtma berish", "callback_data": f"order_{svc['id']}"}],
                     [{"text": "⬅️ Orqaga",          "callback_data": f"cat_{svc['category_id']}"}],
                 ]))
        return

    # Buyurtma boshlash
    if data.startswith("order_"):
        answer_cb(cq_id)
        svc_id = int(data[6:])
        set_step(chat_id, f"await_link|{svc_id}")
        del_msg(chat_id, msg_id)
        send_msg(chat_id, "🔗 Havolani kiriting:", reply_markup=back_btn())
        return

    # Buyurtma tasdiqlash
    if data == "order_ok":
        step = get_step(chat_id)
        if not step or not step.startswith("confirm_order|"):
            answer_cb(cq_id, "❌ Xatolik!", alert=True)
            return
        parts  = step.split("|")
        svc_id = int(parts[1])
        link   = parts[2]
        qty    = int(parts[3])
        svc    = db_one("SELECT * FROM services WHERE id=?", (svc_id,))
        charge = round(svc["rate"] * qty / 1000, 4)
        bal    = float(db_one("SELECT balance FROM users WHERE id=?", (chat_id,))["balance"])
        if bal < charge:
            answer_cb(cq_id, "❌ Balans yetarli emas!", alert=True)
            return
        update_balance(chat_id, -charge)
        oid = db_run(
            "INSERT INTO orders (user_id,service_id,link,quantity,charge,status) "
            "VALUES (?,?,?,?,?,?)",
            (chat_id, svc_id, link, qty, charge, "pending")
        )
        clear_step(chat_id)
        answer_cb(cq_id)
        edit_msg(chat_id, msg_id,
                 f"✅ Buyurtma yaratildi!\n🔢 #{oid}")
        send_msg(chat_id, "🏠 Bosh menyu", reply_markup=main_menu())
        for adm in _get_admins():
            try:
                send_msg(adm,
                         f"📦 Yangi buyurtma #{oid}\n\n"
                         f"👤 ID: <code>{chat_id}</code>\n"
                         f"🛒 {svc['name']}\n"
                         f"🔗 {link}\n"
                         f"🔢 {qty} ta | 💰 {nf(charge, 2)} UZS")
            except Exception:
                pass
        return

    if data == "order_no":
        answer_cb(cq_id)
        clear_step(chat_id)
        edit_msg(chat_id, msg_id, "❌ Bekor qilindi.")
        send_msg(chat_id, "🏠", reply_markup=main_menu())
        return

    # To'lov tasdiqlash (Admin)
    if data.startswith("pay_ok_"):
        if not is_admin(chat_id):
            answer_cb(cq_id, "❌ Ruxsat yo'q!", alert=True)
            return
        pay_id = int(data[7:])
        p = db_one("SELECT * FROM payments WHERE id=?", (pay_id,))
        if not p:
            answer_cb(cq_id, "❌ Topilmadi!", alert=True)
            return
        if p["status"] == "paid":
            answer_cb(cq_id, "⚠️ Allaqachon tasdiqlangan!", alert=True)
            return
        db_run("UPDATE payments SET status='paid' WHERE id=?", (pay_id,))
        update_balance(p["user_id"], float(p["amount"]))
        answer_cb(cq_id, "✅ Tasdiqlandi!")
        edit_msg(chat_id, msg_id,
                 f"✅ To'lov #{pay_id} tasdiqlandi\n"
                 f"👤 ID: <code>{p['user_id']}</code>\n"
                 f"💰 {nf(float(p['amount']), 2)} UZS")
        try:
            send_msg(p["user_id"],
                     f"✅ Balansingiz to'ldirildi!\n"
                     f"💰 +{nf(float(p['amount']), 2)} UZS qo'shildi!")
        except Exception:
            pass
        return

    if data.startswith("pay_no_"):
        if not is_admin(chat_id):
            answer_cb(cq_id, "❌ Ruxsat yo'q!", alert=True)
            return
        pay_id = int(data[7:])
        p = db_one("SELECT * FROM payments WHERE id=?", (pay_id,))
        if not p:
            answer_cb(cq_id, "❌ Topilmadi!", alert=True)
            return
        db_run("UPDATE payments SET status='failed' WHERE id=?", (pay_id,))
        answer_cb(cq_id, "❌ Rad etildi.")
        edit_msg(chat_id, msg_id,
                 f"❌ To'lov #{pay_id} rad etildi\n"
                 f"👤 ID: <code>{p['user_id']}</code>")
        try:
            send_msg(p["user_id"], "❌ To'lov so'rovingiz rad etildi.")
        except Exception:
            pass
        return

    # Kanal o'chirish
    if data.startswith("del_ch_"):
        if not is_admin(chat_id):
            answer_cb(cq_id, "❌ Ruxsat yo'q!", alert=True)
            return
        ch_id = int(data[7:])
        db_run("DELETE FROM channels WHERE id=?", (ch_id,))
        answer_cb(cq_id, "✅ O'chirildi!")
        channels = db_all("SELECT * FROM channels")
        if channels:
            rows = [[{"text": f"❌ {ch['user']}", "callback_data": f"del_ch_{ch['id']}"}]
                    for ch in channels]
            edit_msg(chat_id, msg_id, "📋 Kanallar:", reply_markup=ikb(rows))
        else:
            edit_msg(chat_id, msg_id, "✅ Barcha kanallar o'chirildi.")
        return

    # Ticket javob
    if data.startswith("reply_"):
        if not is_admin(chat_id):
            answer_cb(cq_id, "❌ Ruxsat yo'q!", alert=True)
            return
        target = int(data[6:])
        answer_cb(cq_id)
        set_step(chat_id, f"admin_reply|{target}")
        send_msg(chat_id, f"💬 <code>{target}</code> ga javob yozing:",
                 reply_markup=back_btn())
        return

    answer_cb(cq_id)


# ════════════════════════════════════════════════════════════════════
#  YORDAMCHI
# ════════════════════════════════════════════════════════════════════

def _get_admins() -> list:
    admins = [ADMIN_ID]
    rows = db_all("SELECT user_id FROM admins")
    for r in rows:
        try:
            uid = int(r["user_id"])
            if uid not in admins:
                admins.append(uid)
        except Exception:
            pass
    return admins


# ════════════════════════════════════════════════════════════════════
#  WEBHOOK SERVER
# ════════════════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SMM Bot ishlayapti!")

    def do_POST(self):
        n    = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        self.send_response(200)
        self.end_headers()
        try:
            handle_update(json.loads(body))
        except Exception as e:
            logger.error("POST: %s", e)

    def log_message(self, *a):
        pass


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()

    if WEBHOOK_URL:
        res = set_webhook(f"{WEBHOOK_URL}/")
        logger.info("Webhook: %s", res)
    else:
        logger.warning("WEBHOOK_URL yo'q!")

    logger.info("Bot ishga tushdi! Port: %s", PORT)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
