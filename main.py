"""
╔══════════════════════════════════════════════════════════╗
║         SMM BOT — TO'LIQ KOD (Webhook + Admin)          ║
║  To'lov: Admin qo'lda | Rejim: Webhook (Railway/VPS)    ║
╚══════════════════════════════════════════════════════════╝
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from smm2024 import (
    Category, Channel, Config, Lang, Order,
    Payment, Referal, Service, SMMBot, User,
    inline_keyboard, now_tashkent, number_format, reply_keyboard,
)

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════
#  SOZLASH  (environment variables dan o'qiladi)
# ════════════════════════════════════════════════════════════════════
config = Config(
    bot_token   = os.getenv("BOT_TOKEN",    "TOKEN_SHUNGA"),
    admin_id    = int(os.getenv("ADMIN_ID", "123456789")),
    db_host     = os.getenv("DB_HOST",      "localhost"),
    db_user     = os.getenv("DB_USER",      "root"),
    db_password = os.getenv("DB_PASSWORD",  "parol"),
    db_name     = os.getenv("DB_NAME",      "smm"),
    db_port     = int(os.getenv("DB_PORT",  "3306")),
)

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")   # https://xxx.up.railway.app
PORT        = int(os.getenv("PORT", 8080))
MIN_DEPOSIT = 1000   # minimal to'ldirish summasi (so'm)
REFERAL_BONUS = 500.0

# ════════════════════════════════════════════════════════════════════
#  YORDAMCHI: KLAVIATURALAR
# ════════════════════════════════════════════════════════════════════

def main_menu(lang: Lang) -> str:
    return reply_keyboard([
        [lang.kb("new_order"),   lang.kb("orders")],
        [lang.kb("add_funds"),   lang.kb("cabinet")],
        [lang.kb("referal"),     lang.kb("help")],
    ])

def admin_menu() -> str:
    return reply_keyboard([
        ["📊 Statistika",   "👤 Foydalanuvchi"],
        ["💰 Balans berish", "📢 Reklama"],
        ["➕ Kanal qo'sh",   "📋 Kanallar"],
        ["🏠 Bosh menyu"],
    ])

def back_btn(lang: Lang) -> str:
    return reply_keyboard([[lang.kb("back")]])


# ════════════════════════════════════════════════════════════════════
#  ASOSIY UPDATE HANDLER
# ════════════════════════════════════════════════════════════════════

def handle_update(update: dict) -> None:
    try:
        if "message" in update:
            _handle_message(update["message"])
        elif "callback_query" in update:
            _handle_callback(update["callback_query"])
    except Exception as e:
        logger.error("handle_update xatosi: %s", e, exc_info=True)


# ════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ════════════════════════════════════════════════════════════════════

def _handle_message(msg: dict) -> None:
    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()
    tg_user = msg.get("from", {})
    name    = tg_user.get("first_name", "Foydalanuvchi")

    with SMMBot(config) as bot:

        # ── Flood / Blok ────────────────────────────────────────────
        if bot.is_blocked(chat_id):
            bot.send_message(chat_id, "🚫 Vaqtincha bloklangansiz.")
            return
        if not bot.flood_check(chat_id):
            bot.flood.block(chat_id)
            bot.send_message(chat_id, "⚠️ Juda ko'p so'rov. Bir oz kuting.")
            return

        user = bot.get_or_create_user(chat_id)
        lang = Lang.for_user(user.lang)
        step = bot.get_step(chat_id)

        # ════════════════════════════════════════════════════════════
        #  /start
        # ════════════════════════════════════════════════════════════
        if text == "/start" or text.startswith("/start "):
            if not bot.check_join(chat_id):
                return
            parts = text.split()
            if len(parts) > 1:
                _apply_referal(bot, chat_id, parts[1])
            bot.clear_step(chat_id)
            bot.send_message(
                chat_id,
                lang.msg("welcome", name=name),
                reply_markup=main_menu(lang),
            )
            return

        # ════════════════════════════════════════════════════════════
        #  ADMIN BUYRUQLARI
        # ════════════════════════════════════════════════════════════
        if text == "/admin" and bot.is_admin(chat_id):
            bot.clear_step(chat_id)
            bot.send_message(chat_id, "⚙️ <b>Admin paneli</b>", reply_markup=admin_menu())
            return

        if bot.is_admin(chat_id):
            if _handle_admin_text(bot, chat_id, text, step, lang, user, name):
                return

        # ════════════════════════════════════════════════════════════
        #  FOYDALANUVCHI MENYULARI
        # ════════════════════════════════════════════════════════════

        # ── Orqaga / Bosh menyu ──────────────────────────────────────
        if text in (lang.kb("back"), lang.kb("main_menu")):
            bot.clear_step(chat_id)
            bot.send_message(
                chat_id,
                lang.msg("welcome", name=name),
                reply_markup=main_menu(lang),
            )
            return

        # ── Kabinet ──────────────────────────────────────────────────
        if text == lang.kb("cabinet"):
            bot.clear_step(chat_id)
            bal = number_format(float(user.balance), 2)
            txt = (
                f"👤 <b>Kabinet</b>\n\n"
                f"🆔 ID: <code>{chat_id}</code>\n"
                f"💰 Balans: <b>{bal} {user.currency}</b>\n"
                f"🔑 API: <code>{user.api_key}</code>\n"
                f"📅 Vaqt: {now_tashkent()}"
            )
            kb = inline_keyboard([
                [{"text": "💰 Balans to'ldirish", "callback_data": "add_funds"}],
                [{"text": "🌐 Til o'zgartirish",  "callback_data": "change_lang"}],
            ])
            bot.send_message(chat_id, txt, reply_markup=kb)
            return

        # ── Balans to'ldirish ────────────────────────────────────────
        if text == lang.kb("add_funds"):
            bot.set_step(chat_id, "awaiting_deposit_amount")
            bot.send_message(
                chat_id,
                lang.msg("enter_amount", min=number_format(MIN_DEPOSIT)),
                reply_markup=back_btn(lang),
            )
            return

        # ── Buyurtmalarim ────────────────────────────────────────────
        if text == lang.kb("orders"):
            bot.clear_step(chat_id)
            orders = Order.by_user(bot.db, chat_id, limit=10)
            if not orders:
                bot.send_message(chat_id, lang.msg("no_orders"))
                return
            STATUS_MAP = {
                "pending":   "⏳ Kutilmoqda",
                "active":    "🔄 Jarayonda",
                "completed": "✅ Bajarildi",
                "canceled":  "❌ Bekor qilindi",
                "partial":   "⚠️ Qisman",
            }
            for o in orders:
                svc = Service.get(bot.db, o.service_id)
                bot.send_message(
                    chat_id,
                    lang.msg(
                        "order_status",
                        order_id = o.id,
                        service  = svc.name if svc else str(o.service_id),
                        link     = o.link,
                        quantity = o.quantity,
                        charge   = number_format(float(o.charge), 2) + f" {user.currency}",
                        status   = STATUS_MAP.get(o.status, o.status),
                    )
                )
            return

        # ── Yangi buyurtma ───────────────────────────────────────────
        if text == lang.kb("new_order"):
            bot.clear_step(chat_id)
            if not bot.check_join(chat_id):
                return
            cats = Category.all_active(bot.db)
            if not cats:
                bot.send_message(chat_id, "❌ Hozircha kategoriyalar yo'q.")
                return
            rows = [[{"text": c.category_name,
                      "callback_data": f"cat_{c.category_id}"}] for c in cats]
            rows.append([{"text": lang.kb("back"), "callback_data": "back_main"}])
            bot.send_message(
                chat_id,
                lang.msg("choose_category"),
                reply_markup=inline_keyboard(rows),
            )
            return

        # ── Referal ──────────────────────────────────────────────────
        if text == lang.kb("referal"):
            bot.clear_step(chat_id)
            count = Referal.count_invited(bot.db, chat_id)
            row   = bot.db.fetch_one(
                "SELECT SUM(bonus) AS total FROM referal WHERE owner_id=%s", (chat_id,)
            )
            total_bonus = float(row["total"] or 0) if row else 0
            ref_link    = f"https://t.me/smmbot?start={user.referal}"
            bot.send_message(
                chat_id,
                f"👥 <b>Referal dasturi</b>\n\n"
                f"🔗 Havolingiz:\n<code>{ref_link}</code>\n\n"
                + lang.msg(
                    "referal_info",
                    code     = user.referal,
                    count    = count,
                    bonus    = number_format(total_bonus, 2),
                    currency = user.currency,
                )
            )
            return

        # ── Yordam / Ticket ──────────────────────────────────────────
        if text == lang.kb("help"):
            bot.set_step(chat_id, "awaiting_ticket")
            bot.send_message(
                chat_id,
                "❓ <b>Yordam</b>\n\nSavolingizni yozing, adminlarga yuboriladi:",
                reply_markup=back_btn(lang),
            )
            return

        # ════════════════════════════════════════════════════════════
        #  QADAM BOSHQARUVI
        # ════════════════════════════════════════════════════════════
        _handle_step(bot, chat_id, text, step, lang, user)


# ════════════════════════════════════════════════════════════════════
#  QADAM HANDLER
# ════════════════════════════════════════════════════════════════════

def _handle_step(bot, chat_id, text, step, lang, user):
    if not step:
        return

    # ── Balans to'ldirish: summa ─────────────────────────────────────
    if step == "awaiting_deposit_amount":
        try:
            amount = float(text.replace(" ", "").replace(",", "."))
        except ValueError:
            bot.send_message(chat_id, "❌ To'g'ri summa kiriting!")
            return
        if amount < MIN_DEPOSIT:
            bot.send_message(
                chat_id,
                lang.msg("enter_amount", min=number_format(MIN_DEPOSIT))
            )
            return
        p = Payment.create(bot.db, chat_id, amount, "manual")
        bot.clear_step(chat_id)
        bot.send_message(
            chat_id,
            f"📋 <b>To'lov so'rovi yuborildi</b>\n\n"
            f"🔢 Raqam: <b>#{p.id}</b>\n"
            f"💰 Summa: <b>{number_format(amount)} {user.currency}</b>\n\n"
            f"⏳ Admin tasdiqlashini kuting.",
            reply_markup=reply_keyboard([[lang.kb("main_menu")]]),
        )
        for adm in config.admins:
            try:
                bot.send_message(
                    adm,
                    f"💰 <b>Yangi to'lov so'rovi</b>\n\n"
                    f"👤 ID: <code>{chat_id}</code>\n"
                    f"💵 Summa: <b>{number_format(amount)} UZS</b>\n"
                    f"🔢 #: <b>{p.id}</b>",
                    reply_markup=inline_keyboard([
                        [
                            {"text": "✅ Tasdiqlash", "callback_data": f"pay_approve_{p.id}"},
                            {"text": "❌ Rad etish",  "callback_data": f"pay_reject_{p.id}"},
                        ]
                    ]),
                )
            except Exception:
                pass
        return

    # ── Buyurtma: havola ─────────────────────────────────────────────
    if step.startswith("awaiting_link|"):
        svc_id = int(step.split("|")[1])
        if not text.startswith("http"):
            bot.send_message(chat_id, lang.msg("invalid_link"))
            return
        svc = Service.get(bot.db, svc_id)
        bot.set_step(chat_id, f"awaiting_qty|{svc_id}|{text}")
        bot.send_message(
            chat_id,
            lang.msg("enter_quantity", min=svc.min, max=svc.max),
        )
        return

    # ── Buyurtma: miqdor ─────────────────────────────────────────────
    if step.startswith("awaiting_qty|"):
        parts  = step.split("|")
        svc_id = int(parts[1])
        link   = parts[2]
        try:
            qty = int(text.replace(" ", ""))
        except ValueError:
            bot.send_message(chat_id, "❌ Raqam kiriting!")
            return
        svc = Service.get(bot.db, svc_id)
        if not svc:
            bot.send_message(chat_id, lang.msg("error"))
            return
        if not (svc.min <= qty <= svc.max):
            bot.send_message(chat_id, lang.msg("invalid_quantity", min=svc.min, max=svc.max))
            return
        charge = svc.calculate_price(qty)
        bot.set_step(chat_id, f"confirm_order|{svc_id}|{link}|{qty}")
        bot.send_message(
            chat_id,
            f"📋 <b>Buyurtmani tasdiqlang</b>\n\n"
            f"🛒 Xizmat: {svc.name}\n"
            f"🔗 Havola: {link}\n"
            f"🔢 Miqdor: {qty}\n"
            f"💰 Narx: <b>{number_format(charge, 2)} {user.currency}</b>\n"
            f"💳 Balansingiz: {number_format(float(user.balance), 2)} {user.currency}",
            reply_markup=inline_keyboard([
                [
                    {"text": "✅ Tasdiqlash", "callback_data": "order_confirm"},
                    {"text": "❌ Bekor",       "callback_data": "order_cancel"},
                ]
            ]),
        )
        return

    # ── Ticket ───────────────────────────────────────────────────────
    if step == "awaiting_ticket":
        bot.clear_step(chat_id)
        lang2 = Lang.for_user(user.lang)
        bot.send_message(chat_id, lang2.msg("ticket_sent"),
                         reply_markup=main_menu(lang2))
        for adm in config.admins:
            try:
                bot.send_message(
                    adm,
                    f"📩 <b>Yangi murojaat</b>\n\n"
                    f"👤 ID: <code>{chat_id}</code>\n"
                    f"💬 Xabar: {text}",
                    reply_markup=inline_keyboard([
                        [{"text": "💬 Javob berish",
                          "callback_data": f"reply_ticket_{chat_id}"}]
                    ]),
                )
            except Exception:
                pass
        return

    # ── Admin: foydalanuvchi ID ──────────────────────────────────────
    if step == "admin_awaiting_user_id":
        try:
            uid = int(text)
        except ValueError:
            bot.send_message(chat_id, "❌ To'g'ri ID kiriting!")
            return
        u = User.get(bot.db, uid)
        if not u:
            bot.send_message(chat_id, "❌ Foydalanuvchi topilmadi!")
            return
        bot.set_step(chat_id, f"admin_awaiting_amount|{uid}")
        bot.send_message(
            chat_id,
            f"👤 ID: <code>{uid}</code>\n"
            f"💰 Joriy balans: {number_format(float(u.balance), 2)} UZS\n\n"
            f"Qo'shilajak summani kiriting:"
        )
        return

    # ── Admin: summa ─────────────────────────────────────────────────
    if step.startswith("admin_awaiting_amount|"):
        uid = int(step.split("|")[1])
        try:
            amount = float(text.replace(" ", "").replace(",", "."))
        except ValueError:
            bot.send_message(chat_id, "❌ To'g'ri summa kiriting!")
            return
        u = User.get(bot.db, uid)
        u.update_balance(bot.db, amount)
        bot.clear_step(chat_id)
        bot.send_message(
            chat_id,
            f"✅ <b>{number_format(amount)} UZS</b> qo'shildi!\n"
            f"👤 ID: <code>{uid}</code>\n"
            f"💰 Yangi balans: {number_format(float(u.balance + amount), 2)} UZS",
            reply_markup=admin_menu(),
        )
        try:
            bot.send_message(
                uid,
                f"✅ Balansingiz to'ldirildi!\n"
                f"💰 Qo'shildi: <b>{number_format(amount)} UZS</b>",
            )
        except Exception:
            pass
        return

    # ── Admin: reklama matni ─────────────────────────────────────────
    if step == "admin_awaiting_broadcast":
        bot.clear_step(chat_id)
        users    = User.all(bot.db)
        user_ids = [u.user_id for u in users if u.user_id]
        bot.send_message(chat_id, "📢 Yuborilmoqda...", reply_markup=admin_menu())
        result = bot.send_broadcast(user_ids, text)
        bot.send_message(
            chat_id,
            f"✅ Yuborildi: <b>{result['sent']}</b> | ❌ Xato: <b>{result['failed']}</b>",
        )
        return

    # ── Admin: kanal ─────────────────────────────────────────────────
    if step == "admin_awaiting_channel":
        username = text.lstrip("@")
        bot.clear_step(chat_id)
        Channel.add(bot.db, f"@{username}")
        bot.send_message(
            chat_id,
            f"✅ Kanal qo'shildi: @{username}",
            reply_markup=admin_menu(),
        )
        return

    # ── Admin: ticket javob ──────────────────────────────────────────
    if step.startswith("admin_reply_ticket|"):
        target_id = int(step.split("|")[1])
        bot.clear_step(chat_id)
        try:
            bot.send_message(target_id, f"📩 <b>Admin javobi:</b>\n\n{text}")
            bot.send_message(chat_id, "✅ Javob yuborildi!", reply_markup=admin_menu())
        except Exception:
            bot.send_message(chat_id, "❌ Yuborib bo'lmadi.", reply_markup=admin_menu())
        return


# ════════════════════════════════════════════════════════════════════
#  ADMIN TEXT HANDLER
# ════════════════════════════════════════════════════════════════════

def _handle_admin_text(bot, chat_id, text, step, lang, user, name) -> bool:
    if text == "📊 Statistika":
        bot.clear_step(chat_id)
        u_total  = User.count_all(bot.db)
        o_active = Order.count_by_status(bot.db, "active")
        o_done   = Order.count_by_status(bot.db, "completed")
        total_p  = Payment.total_paid(bot.db)
        bot.send_message(
            chat_id,
            f"📊 <b>Statistika</b>\n\n"
            f"👤 Foydalanuvchilar: <b>{u_total}</b>\n"
            f"📦 Aktiv buyurtmalar: <b>{o_active}</b>\n"
            f"✅ Bajarilgan: <b>{o_done}</b>\n"
            f"💰 Jami to'lovlar: <b>{number_format(total_p, 2)} UZS</b>\n"
            f"📅 {now_tashkent()}",
            reply_markup=admin_menu(),
        )
        return True

    if text == "💰 Balans berish":
        bot.set_step(chat_id, "admin_awaiting_user_id")
        bot.send_message(
            chat_id, "👤 Foydalanuvchi ID sini kiriting:", reply_markup=back_btn(lang)
        )
        return True

    if text == "📢 Reklama":
        bot.set_step(chat_id, "admin_awaiting_broadcast")
        bot.send_message(
            chat_id,
            "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
            reply_markup=back_btn(lang),
        )
        return True

    if text == "➕ Kanal qo'sh":
        bot.set_step(chat_id, "admin_awaiting_channel")
        bot.send_message(
            chat_id, "📢 Kanal username ini kiriting (@bilan):", reply_markup=back_btn(lang)
        )
        return True

    if text == "📋 Kanallar":
        bot.clear_step(chat_id)
        channels = Channel.all(bot.db)
        if not channels:
            bot.send_message(chat_id, "❌ Kanallar yo'q.", reply_markup=admin_menu())
            return True
        rows = [
            [{"text": f"❌ {ch.user}", "callback_data": f"del_channel_{ch.id}"}]
            for ch in channels
        ]
        bot.send_message(
            chat_id,
            "📋 <b>Kanallar</b> (o'chirish uchun bosing):",
            reply_markup=inline_keyboard(rows),
        )
        return True

    if text == "👤 Foydalanuvchi":
        bot.set_step(chat_id, "admin_awaiting_user_id")
        bot.send_message(
            chat_id, "🔍 Foydalanuvchi ID sini kiriting:", reply_markup=back_btn(lang)
        )
        return True

    if text == "🏠 Bosh menyu":
        bot.clear_step(chat_id)
        bot.send_message(
            chat_id,
            lang.msg("welcome", name=name),
            reply_markup=main_menu(lang),
        )
        return True

    return False


# ════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ════════════════════════════════════════════════════════════════════

def _handle_callback(cq: dict) -> None:
    chat_id = cq["from"]["id"]
    cq_id   = cq["id"]
    data    = cq.get("data", "")
    msg_id  = cq["message"]["message_id"]
    name    = cq["from"].get("first_name", "")

    with SMMBot(config) as bot:
        user = bot.get_or_create_user(chat_id)
        lang = Lang.for_user(user.lang)

        # ── Obuna tekshiruvi ────────────────────────────────────────
        if data == "result":
            if bot.check_join(chat_id):
                bot.answer_callback(cq_id, "✅ Rahmat!", show_alert=True)
                bot.delete_message(chat_id, msg_id)
                bot.send_message(
                    chat_id,
                    lang.msg("welcome", name=name),
                    reply_markup=main_menu(lang),
                )
            else:
                bot.answer_callback(cq_id, "❌ Hali ham a'zo bo'lmadingiz!", show_alert=True)
            return

        # ── Kabinet → balans to'ldirish ──────────────────────────────
        if data == "add_funds":
            bot.answer_callback(cq_id)
            bot.set_step(chat_id, "awaiting_deposit_amount")
            bot.send_message(
                chat_id,
                lang.msg("enter_amount", min=number_format(MIN_DEPOSIT)),
                reply_markup=back_btn(lang),
            )
            return

        # ── Kategoriya ───────────────────────────────────────────────
        if data.startswith("cat_"):
            bot.answer_callback(cq_id)
            cat_id   = int(data[4:])
            services = Service.by_category(bot.db, cat_id)
            if not services:
                bot.answer_callback(cq_id, "❌ Bu kategoriyada xizmat yo'q!", show_alert=True)
                return
            rows = [
                [{"text": f"{s.name} — {number_format(s.rate, 2)}/1000",
                  "callback_data": f"svc_{s.id}"}]
                for s in services
            ]
            rows.append([{"text": lang.kb("back"), "callback_data": "back_cats"}])
            bot.edit_message(
                chat_id, msg_id,
                lang.msg("choose_service"),
                reply_markup=inline_keyboard(rows),
            )
            return

        if data == "back_cats":
            bot.answer_callback(cq_id)
            cats = Category.all_active(bot.db)
            rows = [[{"text": c.category_name,
                      "callback_data": f"cat_{c.category_id}"}] for c in cats]
            rows.append([{"text": lang.kb("back"), "callback_data": "back_main"}])
            bot.edit_message(
                chat_id, msg_id,
                lang.msg("choose_category"),
                reply_markup=inline_keyboard(rows),
            )
            return

        if data == "back_main":
            bot.answer_callback(cq_id)
            bot.delete_message(chat_id, msg_id)
            bot.send_message(
                chat_id,
                lang.msg("welcome", name=name),
                reply_markup=main_menu(lang),
            )
            return

        # ── Xizmat ───────────────────────────────────────────────────
        if data.startswith("svc_"):
            bot.answer_callback(cq_id)
            svc = Service.get(bot.db, int(data[4:]))
            if not svc:
                bot.answer_callback(cq_id, "❌ Xizmat topilmadi!", show_alert=True)
                return
            bot.edit_message(
                chat_id, msg_id,
                lang.msg(
                    "service_info",
                    name = svc.name,
                    rate = number_format(svc.rate, 2),
                    min  = svc.min,
                    max  = svc.max,
                    desc = svc.description or "—",
                ),
                reply_markup=inline_keyboard([
                    [{"text": "🛒 Buyurtma berish", "callback_data": f"order_{svc.id}"}],
                    [{"text": lang.kb("back"),       "callback_data": f"cat_{svc.category_id}"}],
                ]),
            )
            return

        # ── Buyurtma boshlash ────────────────────────────────────────
        if data.startswith("order_"):
            bot.answer_callback(cq_id)
            svc_id = int(data[6:])
            bot.set_step(chat_id, f"awaiting_link|{svc_id}")
            bot.delete_message(chat_id, msg_id)
            bot.send_message(
                chat_id, lang.msg("enter_link"), reply_markup=back_btn(lang)
            )
            return

        # ── Buyurtmani tasdiqlash ────────────────────────────────────
        if data == "order_confirm":
            step = bot.get_step(chat_id)
            if not step or not step.startswith("confirm_order|"):
                bot.answer_callback(cq_id, "❌ Xatolik!", show_alert=True)
                return
            parts  = step.split("|")
            svc_id = int(parts[1])
            link   = parts[2]
            qty    = int(parts[3])
            bot.clear_step(chat_id)
            bot.answer_callback(cq_id)
            result = bot.place_order(chat_id, svc_id, link, qty)
            if result["success"]:
                bot.edit_message(
                    chat_id, msg_id,
                    lang.msg("order_created", order_id=result["order_id"]),
                )
                bot.send_message(chat_id, "🏠", reply_markup=main_menu(lang))
                svc = Service.get(bot.db, svc_id)
                for adm in config.admins:
                    try:
                        bot.send_message(
                            adm,
                            f"📦 <b>Yangi buyurtma #{result['order_id']}</b>\n"
                            f"👤 ID: <code>{chat_id}</code>\n"
                            f"🛒 Xizmat: {svc.name if svc else svc_id}\n"
                            f"🔗 {link}\n"
                            f"🔢 {qty} ta | 💰 {number_format(result['charge'], 2)} UZS",
                        )
                    except Exception:
                        pass
            else:
                bot.edit_message(chat_id, msg_id, f"❌ {result['error']}")
                bot.send_message(chat_id, "🏠", reply_markup=main_menu(lang))
            return

        if data == "order_cancel":
            bot.answer_callback(cq_id)
            bot.clear_step(chat_id)
            bot.edit_message(chat_id, msg_id, "❌ Bekor qilindi.")
            bot.send_message(chat_id, "🏠", reply_markup=main_menu(lang))
            return

        # ── To'lovni tasdiqlash (Admin) ──────────────────────────────
        if data.startswith("pay_approve_"):
            if not bot.is_admin(chat_id):
                bot.answer_callback(cq_id, "❌ Ruxsat yo'q!", show_alert=True)
                return
            pay_id = int(data[12:])
            p = Payment.get(bot.db, pay_id)
            if not p:
                bot.answer_callback(cq_id, "❌ To'lov topilmadi!", show_alert=True)
                return
            if p.status == "paid":
                bot.answer_callback(cq_id, "⚠️ Allaqachon tasdiqlangan!", show_alert=True)
                return
            p.approve(bot.db)
            bot.answer_callback(cq_id, "✅ Tasdiqlandi!")
            bot.edit_message(
                chat_id, msg_id,
                f"✅ <b>To'lov #{pay_id} tasdiqlandi</b>\n"
                f"👤 ID: <code>{p.user_id}</code>\n"
                f"💰 Summa: {number_format(float(p.amount), 2)} UZS",
            )
            try:
                bot.send_message(
                    p.user_id,
                    lang.msg(
                        "payment_success",
                        amount   = number_format(float(p.amount), 2),
                        currency = "UZS",
                    ),
                )
            except Exception:
                pass
            return

        if data.startswith("pay_reject_"):
            if not bot.is_admin(chat_id):
                bot.answer_callback(cq_id, "❌ Ruxsat yo'q!", show_alert=True)
                return
            pay_id = int(data[11:])
            p = Payment.get(bot.db, pay_id)
            if not p:
                bot.answer_callback(cq_id, "❌ Topilmadi!", show_alert=True)
                return
            p.reject(bot.db)
            bot.answer_callback(cq_id, "❌ Rad etildi.")
            bot.edit_message(
                chat_id, msg_id,
                f"❌ <b>To'lov #{pay_id} rad etildi</b>\n"
                f"👤 ID: <code>{p.user_id}</code>",
            )
            try:
                bot.send_message(p.user_id, "❌ To'lov so'rovingiz rad etildi.")
            except Exception:
                pass
            return

        # ── Kanal o'chirish (Admin) ──────────────────────────────────
        if data.startswith("del_channel_"):
            if not bot.is_admin(chat_id):
                bot.answer_callback(cq_id, "❌ Ruxsat yo'q!", show_alert=True)
                return
            ch_id = int(data[12:])
            bot.db.execute("DELETE FROM channels WHERE id=%s", (ch_id,))
            bot.answer_callback(cq_id, "✅ O'chirildi!")
            channels = Channel.all(bot.db)
            if channels:
                rows = [
                    [{"text": f"❌ {ch.user}", "callback_data": f"del_channel_{ch.id}"}]
                    for ch in channels
                ]
                bot.edit_message(
                    chat_id, msg_id,
                    "📋 <b>Kanallar</b>:",
                    reply_markup=inline_keyboard(rows),
                )
            else:
                bot.edit_message(chat_id, msg_id, "✅ Barcha kanallar o'chirildi.")
            return

        # ── Til tanlash ──────────────────────────────────────────────
        if data == "change_lang":
            bot.answer_callback(cq_id)
            bot.edit_message(
                chat_id, msg_id,
                "🌐 Tilni tanlang:",
                reply_markup=inline_keyboard([
                    [
                        {"text": "🇺🇿 O'zbekcha", "callback_data": "setlang_uz"},
                        {"text": "🇷🇺 Русский",   "callback_data": "setlang_ru"},
                        {"text": "🇬🇧 English",   "callback_data": "setlang_en"},
                    ]
                ]),
            )
            return

        if data.startswith("setlang_"):
            new_lang = data[8:]
            bot.db.execute("UPDATE users SET lang=%s WHERE id=%s", (new_lang, chat_id))
            bot.answer_callback(cq_id, "✅ Til o'zgartirildi!")
            lang2 = Lang(new_lang)
            bot.delete_message(chat_id, msg_id)
            bot.send_message(
                chat_id,
                lang2.msg("welcome", name=name),
                reply_markup=main_menu(lang2),
            )
            return

        # ── Ticket javob (Admin) ─────────────────────────────────────
        if data.startswith("reply_ticket_"):
            if not bot.is_admin(chat_id):
                bot.answer_callback(cq_id, "❌ Ruxsat yo'q!", show_alert=True)
                return
            target_id = int(data[13:])
            bot.answer_callback(cq_id)
            bot.set_step(chat_id, f"admin_reply_ticket|{target_id}")
            bot.send_message(
                chat_id,
                f"💬 <code>{target_id}</code> ga javob yozing:",
                reply_markup=back_btn(lang),
            )
            return

        bot.answer_callback(cq_id)


# ════════════════════════════════════════════════════════════════════
#  REFERAL YORDAMCHI
# ════════════════════════════════════════════════════════════════════

def _apply_referal(bot: SMMBot, new_user_id: int, code: str) -> None:
    owner = bot.db.fetch_one("SELECT * FROM users WHERE referal=%s", (code,))
    if not owner or owner["id"] == new_user_id:
        return
    exists = bot.db.fetch_one(
        "SELECT id FROM referal WHERE invited_id=%s", (new_user_id,)
    )
    if exists:
        return
    try:
        Referal.create(bot.db, code, owner["id"], new_user_id, REFERAL_BONUS)
        bot.db.execute(
            "UPDATE users SET balance=balance+%s WHERE id=%s",
            (REFERAL_BONUS, owner["id"])
        )
        bot.send_message(
            owner["id"],
            f"🎉 Yangi referal!\n"
            f"💰 +{number_format(REFERAL_BONUS)} UZS balansingizga qo'shildi!",
        )
    except Exception as e:
        logger.warning("Referal xatosi: %s", e)


# ════════════════════════════════════════════════════════════════════
#  WEBHOOK SERVER
# ════════════════════════════════════════════════════════════════════

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Railway health check."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SMM Bot ishlayapti!")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        self.send_response(200)
        self.end_headers()
        try:
            handle_update(json.loads(body))
        except Exception as e:
            logger.error("POST xatosi: %s", e)

    def log_message(self, *args):
        pass


# ════════════════════════════════════════════════════════════════════
#  ISHGA TUSHIRISH
# ════════════════════════════════════════════════════════════════════

def main():
    with SMMBot(config) as bot:
        if WEBHOOK_URL:
            res = bot.set_webhook(f"{WEBHOOK_URL}/")
            logger.info("Webhook o'rnatildi: %s", res)
        else:
            logger.warning("WEBHOOK_URL yo'q! Railway environment variable qo'shing.")

    logger.info("=" * 55)
    logger.info("  SMM Bot ishga tushdi!  Port: %s", PORT)
    logger.info("=" * 55)
    HTTPServer(("0.0.0.0", PORT), WebhookHandler).serve_forever()


if __name__ == "__main__":
    main()
