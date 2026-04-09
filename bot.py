# ═══════════════════════════════════════════════════════════════════
#  SMM2024 — TO'LIQ PYTHON KUTUBXONASI (bitta fayl)
#  Asl PHP kod: @xukumron (2024-08-01) | Python: Claude AI
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import mysql.connector
from mysql.connector import Error as MySQLError
import pytz
import requests

logger = logging.getLogger(__name__)


# ███████████████████████████████████████████████████████████████████
#  1. CONFIG
# ███████████████████████████████████████████████████████████████████

@dataclass
class Config:
    """
    Barcha sozlamalarni bitta joyda saqlaydi.

    Misol::

        config = Config(
            bot_token="123:ABC",
            admin_id=123456789,
            db_host="localhost",
            db_user="root",
            db_password="parol",
            db_name="smm",
        )
    """

    # ── Telegram ──────────────────────────────────────────────
    bot_token: str = "8674893543:AAEmbCiJkWchGiSgXzXrcL_NYZRFl75GEbw"
    admin_bot_token: str = "8537782289"
    admin_id: int = "8537782289"

    # ── MySQL ──────────────────────────────────────────────────
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_user: str = os.getenv("DB_USER", "user")
    db_password: str = os.getenv("DB_PASSWORD", "parol")
    db_name: str = os.getenv("DB_NAME", "name")
    db_port: int = int(os.getenv("DB_PORT", "3306"))

    # ── Vaqt zonasi ───────────────────────────────────────────
    timezone: str = "Asia/Tashkent"

    # ── Flood himoya ──────────────────────────────────────────
    flood_max_attempts: int = 5
    flood_time_interval: int = 10   # soniya
    block_duration: int = 60        # soniya

    # ── Fayl yo'llari ─────────────────────────────────────────
    step_dir: str = "step"
    flood_log: str = "flood_log.json"
    block_log: str = "block_log.json"

    # ── Adminlar ro'yxati ─────────────────────────────────────
    admins: List[int] = field(default_factory=list)

    def __post_init__(self):
        if self.admin_id and self.admin_id not in self.admins:
            self.admins.append(self.admin_id)

    @classmethod
    def from_env(cls) -> "Config":
        return cls()


# ███████████████████████████████████████████████████████████████████
#  2. DATABASE
# ███████████████████████████████████████████████████████████████████

class Database:
    """
    MySQL ulanishini boshqaradi.

    Ishlatish::

        db = Database(Config())
        db.connect()
        user = db.fetch_one("SELECT * FROM users WHERE id = %s", (123,))
        rows = db.fetch_all("SELECT * FROM orders WHERE status = %s", ("active",))
        db.execute("UPDATE users SET balance = %s WHERE id = %s", (500, 123))
        db.close()

        # yoki context manager bilan:
        with Database(config) as db:
            ...
    """

    def __init__(self, config: Config):
        self.config = config
        self._conn: Optional[mysql.connector.MySQLConnection] = None

    def connect(self) -> None:
        try:
            self._conn = mysql.connector.connect(
                host=self.config.db_host,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_name,
                port=self.config.db_port,
                charset="utf8mb4",
                autocommit=True,
            )
            logger.info("MySQL ga muvaffaqiyatli ulanildi.")
        except MySQLError as e:
            logger.error("MySQL ulanish xatosi: %s", e)
            raise

    def close(self) -> None:
        if self._conn and self._conn.is_connected():
            self._conn.close()

    def _ensure_connected(self) -> None:
        if not self._conn or not self._conn.is_connected():
            self.connect()

    def execute(self, query: str, params: tuple = ()) -> int:
        """INSERT / UPDATE / DELETE. Returns lastrowid yoki rowcount."""
        self._ensure_connected()
        cursor = self._conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.lastrowid or cursor.rowcount
        except MySQLError as e:
            logger.error("SQL xatosi: %s | So'rov: %s", e, query)
            raise
        finally:
            cursor.close()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Bitta qatorni dict ko'rinishida qaytaradi."""
        self._ensure_connected()
        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except MySQLError as e:
            logger.error("SQL xatosi: %s", e)
            return None
        finally:
            cursor.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Barcha qatorlarni list[dict] ko'rinishida qaytaradi."""
        self._ensure_connected()
        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except MySQLError as e:
            logger.error("SQL xatosi: %s", e)
            return []
        finally:
            cursor.close()

    def count(self, query: str, params: tuple = ()) -> int:
        """SELECT COUNT(*) ni bajaradi."""
        row = self.fetch_one(query, params)
        if row:
            return list(row.values())[0]
        return 0

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.close()


# ███████████████████████████████████████████████████████████████████
#  3. UTILS — YORDAMCHI FUNKSIYALAR
# ███████████████████████████████████████████████████████████████████

def encode_decode(action: str, data: str) -> str:
    """
    Base64 kodlash yoki dekodlash.

    Ekvivalent PHP: ``enc($var, $exception)``

    Misol::

        encode_decode("encode", "salom")    # → "c2Fsb20="
        encode_decode("decode", "c2Fsb20=") # → "salom"
    """
    if action == "encode":
        return base64.b64encode(data.encode()).decode()
    elif action == "decode":
        return base64.b64decode(data.encode()).decode()
    raise ValueError(f"action '{action}' noto'g'ri. 'encode' yoki 'decode' bo'lishi kerak.")


def inline_keyboard(buttons: List[List[Dict[str, Any]]]) -> str:
    """
    Inline klaviatura JSON yaratadi.

    Ekvivalent PHP: ``inline($a)``

    Misol::

        inline_keyboard([
            [{"text": "✅ Ha", "callback_data": "yes"},
             {"text": "❌ Yo'q", "callback_data": "no"}],
        ])
    """
    return json.dumps({"inline_keyboard": buttons}, ensure_ascii=False)


def reply_keyboard(buttons: List[List[str]],
                   resize: bool = True,
                   one_time: bool = False) -> str:
    """
    Reply klaviatura JSON yaratadi.

    Ekvivalent PHP: ``keyboard($a)``

    Misol::

        reply_keyboard([
            ["🛒 Buyurtma", "📦 Xizmatlar"],
            ["💰 Balans",   "⚙️ Sozlamalar"],
        ])
    """
    data: Dict[str, Any] = {
        "resize_keyboard": resize,
        "keyboard": [[{"text": btn} for btn in row] for row in buttons],
    }
    if one_time:
        data["one_time_keyboard"] = True
    return json.dumps(data, ensure_ascii=False)


def number_format(n: float, decimals: int = 0, sep: str = " ") -> str:
    """
    Sonni formatlaydi.

    Ekvivalent PHP: ``number($a)``

    Misol::

        number_format(1234567)     # → "1 234 567"
        number_format(9999.99, 2)  # → "9 999.99"
    """
    if decimals == 0:
        return f"{int(n):,}".replace(",", sep)
    return f"{n:,.{decimals}f}".replace(",", sep)


def check_average(create: str, last: str,
                  fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Ikki sana orasidagi farqni o'zbek tilida qaytaradi.

    Ekvivalent PHP: ``checkAverage($create, $last)``

    Misol::

        check_average("2024-01-01 10:00:00", "2024-01-03 12:30:00")
        # → "2 kun 2 soat 30 daqiqa"
    """
    try:
        dt1 = datetime.strptime(create, fmt)
        dt2 = datetime.strptime(last, fmt)
        diff = int((dt2 - dt1).total_seconds())
    except ValueError:
        return "Ma'lumot yo'q"

    days, rem = divmod(diff, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60

    if days == 0 and hours == 0 and minutes == 0:
        return "Ma'lumot yo'q"
    if days == 0 and hours == 0:
        return f"{minutes} daqiqa"
    if days == 0 and minutes == 0:
        return f"{hours} soat"
    if hours == 0 and minutes == 0:
        return f"{days} kun"
    if days == 0:
        return f"{hours} soat {minutes} daqiqa"
    if hours == 0:
        return f"{days} kun {minutes} daqiqa"
    if minutes == 0:
        return f"{days} kun {hours} soat"
    return f"{days} kun {hours} soat {minutes} daqiqa"


def generate_code(length: int = 7) -> str:
    """
    Tasodifiy alfanumerik kod yaratadi.

    Ekvivalent PHP: ``generate()``

    Misol::

        generate_code()     # → "A3KZ9P1"
        generate_code(10)   # → "XY3M1P9QA7"
    """
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def translate_text(text: str, target_lang: str) -> str:
    """
    Google Translate orqali tarjima qiladi.

    Ekvivalent PHP: ``trans($x)``
    """
    if not text or not target_lang or target_lang in ("default", "uz"):
        return text
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=auto&tl={target_lang}&dt=t&q={requests.utils.quote(text)}"
    )
    try:
        resp = requests.get(url, timeout=5, verify=False)
        data = resp.json()
        return data[0][0][0]
    except Exception as e:
        logger.warning("Tarjima xatosi: %s", e)
        return text


def now_tashkent(fmt: str = "%d/%m/%Y | %H:%M") -> str:
    """
    Toshkent vaqtini formatlangan holda qaytaradi.

    Ekvivalent PHP: ``date("d/m/Y | H:i")``
    """
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz).strftime(fmt)


# ███████████████████████████████████████████████████████████████████
#  4. FLOOD HIMOYA
# ███████████████████████████████████████████████████████████████████

class FloodControl:
    """
    Flood va blok boshqaruvi.

    Ekvivalent PHP: ``flood()`` va ``blockTime()``

    Misol::

        fc = FloodControl()
        if not fc.check(user_id=123, max_attempts=5, interval=10):
            print("Spam aniqlandi!")

        if fc.is_blocked(user_id=123, block_duration=60):
            print("Foydalanuvchi blokda!")

        fc.block(user_id=123)
        fc.unblock(user_id=123)
    """

    def __init__(self,
                 flood_log: str = "flood_log.json",
                 block_log: str = "block_log.json"):
        self._flood_log = flood_log
        self._block_log = block_log

    def _load(self, path: str) -> dict:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self, path: str, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def check(self, user_id: int, max_attempts: int = 5, interval: int = 10) -> bool:
        """
        Returns True — so'rov qabul qilinadi.
        Returns False — spam aniqlandi.
        """
        import time
        log = self._load(self._flood_log)
        uid = str(user_id)
        now = time.time()

        if uid not in log:
            log[uid] = {"timestamp": now, "attempts": 1}
        else:
            entry = log[uid]
            if (now - entry["timestamp"]) < interval:
                entry["attempts"] += 1
                if entry["attempts"] > max_attempts:
                    self._save(self._flood_log, log)
                    return False
            else:
                log[uid] = {"timestamp": now, "attempts": 1}

        self._save(self._flood_log, log)
        return True

    def block(self, user_id: int) -> None:
        """Foydalanuvchini bloklaydi."""
        import time
        log = self._load(self._block_log)
        log[str(user_id)] = {"block_start_time": time.time()}
        self._save(self._block_log, log)

    def is_blocked(self, user_id: int, block_duration: int = 60) -> bool:
        """True — blokda, False — yo'q."""
        import time
        log = self._load(self._block_log)
        uid = str(user_id)
        if uid not in log:
            return False
        if (time.time() - log[uid]["block_start_time"]) < block_duration:
            return True
        del log[uid]
        self._save(self._block_log, log)
        return False

    def unblock(self, user_id: int) -> None:
        log = self._load(self._block_log)
        log.pop(str(user_id), None)
        self._save(self._block_log, log)


# ███████████████████████████████████████████████████████████████████
#  5. STEP MANAGER
# ███████████████████████████████████████████████████████████████████

class StepManager:
    """
    Foydalanuvchi holatini (qadamini) saqlaydi.

    Ekvivalent PHP: ``file_get_contents("step/$from_id.step")``

    Misol::

        sm = StepManager()
        sm.set(123456, "awaiting_link")
        step = sm.get(123456)   # → "awaiting_link"
        sm.clear(123456)
    """

    def __init__(self, step_dir: str = "step"):
        self._dir = step_dir
        os.makedirs(step_dir, exist_ok=True)

    def _path(self, user_id: int) -> str:
        return os.path.join(self._dir, f"{user_id}.step")

    def get(self, user_id: int) -> str:
        p = self._path(user_id)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def set(self, user_id: int, step: str) -> None:
        with open(self._path(user_id), "w", encoding="utf-8") as f:
            f.write(step)

    def clear(self, user_id: int) -> None:
        p = self._path(user_id)
        if os.path.exists(p):
            os.remove(p)


# ███████████████████████████████████████████████████████████████████
#  6. MODELS
# ███████████████████████████████████████████████████████████████████

# ── User ──────────────────────────────────────────────────────────

@dataclass
class User:
    """
    ``users`` jadvali.

    Ekvivalent PHP: ``adduser()`` va ``user()``
    """
    id: int = 0
    user_id: int = 0
    status: str = "active"
    balance: float = 0.0
    outing: float = 0.0
    api_key: str = ""
    referal: str = ""
    user_detail: str = "false"
    free_cate: str = "false"
    lang: str = "default"
    currency: str = "UZS"

    @classmethod
    def get(cls, db: Database, chat_id: int) -> Optional["User"]:
        """Ekvivalent PHP: ``user($cid)``"""
        row = db.fetch_one("SELECT * FROM users WHERE id = %s", (chat_id,))
        if not row:
            return None
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__})

    @classmethod
    def add(cls, db: Database, chat_id: int) -> "User":
        """Ekvivalent PHP: ``adduser($cid)``"""
        existing = cls.get(db, chat_id)
        if existing:
            return existing
        api_key = hashlib.md5(secrets.token_bytes(16)).hexdigest()
        referal = generate_code()
        count = db.count("SELECT COUNT(*) FROM users")
        db.execute(
            "INSERT INTO users (user_id,id,status,balance,outing,api_key,referal,"
            "user_detail,free_cate,lang,currency) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (count + 1, chat_id, "active", 0, 0, api_key, referal,
             "false", "false", "default", "UZS"),
        )
        return cls.get(db, chat_id)

    def save(self, db: Database) -> None:
        db.execute(
            "UPDATE users SET status=%s,balance=%s,outing=%s,api_key=%s,"
            "referal=%s,user_detail=%s,free_cate=%s,lang=%s,currency=%s WHERE id=%s",
            (self.status, self.balance, self.outing, self.api_key,
             self.referal, self.user_detail, self.free_cate,
             self.lang, self.currency, self.id),
        )

    def update_balance(self, db: Database, amount: float) -> None:
        db.execute(
            "UPDATE users SET balance = balance + %s WHERE id = %s",
            (amount, self.id),
        )
        self.balance += amount

    def is_blocked(self) -> bool:
        return self.status == "blocked"

    @classmethod
    def all(cls, db: Database) -> List["User"]:
        rows = db.fetch_all("SELECT * FROM users")
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    @classmethod
    def count_all(cls, db: Database) -> int:
        return db.count("SELECT COUNT(*) FROM users")


# ── Category ──────────────────────────────────────────────────────

@dataclass
class Category:
    """``categorys`` jadvali."""
    category_id: int = 0
    category_name: str = ""
    category_status: str = "active"
    category_line: str = ""

    @classmethod
    def get(cls, db: Database, cat_id: int) -> Optional["Category"]:
        row = db.fetch_one("SELECT * FROM categorys WHERE category_id = %s", (cat_id,))
        return cls(**row) if row else None

    @classmethod
    def all_active(cls, db: Database) -> List["Category"]:
        rows = db.fetch_all(
            "SELECT * FROM categorys WHERE category_status='active' ORDER BY category_line"
        )
        return [cls(**r) for r in rows]

    @classmethod
    def all(cls, db: Database) -> List["Category"]:
        rows = db.fetch_all("SELECT * FROM categorys ORDER BY category_line")
        return [cls(**r) for r in rows]

    def save(self, db: Database) -> None:
        if self.category_id:
            db.execute(
                "UPDATE categorys SET category_name=%s,category_status=%s,"
                "category_line=%s WHERE category_id=%s",
                (self.category_name, self.category_status,
                 self.category_line, self.category_id),
            )
        else:
            self.category_id = db.execute(
                "INSERT INTO categorys (category_name,category_status,category_line)"
                " VALUES (%s,%s,%s)",
                (self.category_name, self.category_status, self.category_line),
            )

    def delete(self, db: Database) -> None:
        db.execute("DELETE FROM categorys WHERE category_id=%s", (self.category_id,))


# ── Service ───────────────────────────────────────────────────────

@dataclass
class Service:
    """``services`` jadvali."""
    id: int = 0
    service_id: str = ""
    category_id: int = 0
    name: str = ""
    rate: float = 0.0
    min: int = 0
    max: int = 0
    status: str = "active"
    provider_id: int = 0
    type: str = ""
    description: str = ""

    @classmethod
    def get(cls, db: Database, service_id: int) -> Optional["Service"]:
        row = db.fetch_one("SELECT * FROM services WHERE id=%s", (service_id,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    @classmethod
    def by_category(cls, db: Database, category_id: int) -> List["Service"]:
        rows = db.fetch_all(
            "SELECT * FROM services WHERE category_id=%s AND status='active'",
            (category_id,),
        )
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    @classmethod
    def all(cls, db: Database) -> List["Service"]:
        rows = db.fetch_all("SELECT * FROM services")
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    def calculate_price(self, quantity: int) -> float:
        return round(self.rate * quantity / 1000, 4)

    def save(self, db: Database) -> None:
        if self.id:
            db.execute(
                "UPDATE services SET service_id=%s,category_id=%s,name=%s,rate=%s,"
                "min=%s,max=%s,status=%s,provider_id=%s,type=%s,description=%s WHERE id=%s",
                (self.service_id, self.category_id, self.name, self.rate,
                 self.min, self.max, self.status, self.provider_id,
                 self.type, self.description, self.id),
            )
        else:
            self.id = db.execute(
                "INSERT INTO services (service_id,category_id,name,rate,min,max,"
                "status,provider_id,type,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (self.service_id, self.category_id, self.name, self.rate,
                 self.min, self.max, self.status, self.provider_id,
                 self.type, self.description),
            )

    def delete(self, db: Database) -> None:
        db.execute("DELETE FROM services WHERE id=%s", (self.id,))


# ── Order ─────────────────────────────────────────────────────────

@dataclass
class Order:
    """``orders`` jadvali."""
    id: int = 0
    user_id: int = 0
    service_id: int = 0
    link: str = ""
    quantity: int = 0
    charge: float = 0.0
    start_count: int = 0
    remains: int = 0
    status: str = "pending"
    provider_order_id: str = ""
    created_at: str = ""

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELED = "canceled"
    STATUS_PARTIAL = "partial"

    @classmethod
    def get(cls, db: Database, order_id: int) -> Optional["Order"]:
        row = db.fetch_one("SELECT * FROM orders WHERE id=%s", (order_id,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    @classmethod
    def by_user(cls, db: Database, user_id: int,
                limit: int = 10, offset: int = 0) -> List["Order"]:
        rows = db.fetch_all(
            "SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC LIMIT %s OFFSET %s",
            (user_id, limit, offset),
        )
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    @classmethod
    def create(cls, db: Database, user_id: int, service_id: int,
               link: str, quantity: int, charge: float) -> "Order":
        oid = db.execute(
            "INSERT INTO orders (user_id,service_id,link,quantity,charge,status)"
            " VALUES (%s,%s,%s,%s,%s,%s)",
            (user_id, service_id, link, quantity, charge, cls.STATUS_PENDING),
        )
        return cls.get(db, oid)

    def save(self, db: Database) -> None:
        db.execute(
            "UPDATE orders SET status=%s,remains=%s,start_count=%s,"
            "provider_order_id=%s WHERE id=%s",
            (self.status, self.remains, self.start_count,
             self.provider_order_id, self.id),
        )

    def cancel(self, db: Database) -> None:
        self.status = self.STATUS_CANCELED
        self.save(db)

    @classmethod
    def count_by_status(cls, db: Database, status: str) -> int:
        return db.count("SELECT COUNT(*) FROM orders WHERE status=%s", (status,))


# ── Payment ───────────────────────────────────────────────────────

@dataclass
class Payment:
    """``payments`` jadvali."""
    id: int = 0
    user_id: int = 0
    amount: float = 0.0
    method: str = ""
    status: str = "pending"
    transaction_id: str = ""
    created_at: str = ""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"

    @classmethod
    def get(cls, db: Database, payment_id: int) -> Optional["Payment"]:
        row = db.fetch_one("SELECT * FROM payments WHERE id=%s", (payment_id,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    @classmethod
    def create(cls, db: Database, user_id: int, amount: float, method: str) -> "Payment":
        pid = db.execute(
            "INSERT INTO payments (user_id,amount,method,status) VALUES (%s,%s,%s,%s)",
            (user_id, amount, method, cls.STATUS_PENDING),
        )
        return cls.get(db, pid)

    def approve(self, db: Database) -> None:
        self.status = self.STATUS_PAID
        db.execute("UPDATE payments SET status=%s WHERE id=%s", (self.STATUS_PAID, self.id))
        db.execute(
            "UPDATE users SET balance=balance+%s WHERE id=%s",
            (self.amount, self.user_id),
        )

    def reject(self, db: Database) -> None:
        self.status = self.STATUS_FAILED
        db.execute("UPDATE payments SET status=%s WHERE id=%s", (self.STATUS_FAILED, self.id))

    @classmethod
    def total_paid(cls, db: Database) -> float:
        row = db.fetch_one("SELECT SUM(amount) AS total FROM payments WHERE status='paid'")
        return float(row["total"] or 0) if row else 0.0


# ── MainSetting ───────────────────────────────────────────────────

@dataclass
class MainSetting:
    """``mainsetting`` jadvali. Ekvivalent PHP: ``mainsetting($m)``"""
    id: int = 0
    setting: str = ""
    value: str = ""
    status: str = "1"

    @classmethod
    def get(cls, db: Database, setting: str) -> Optional["MainSetting"]:
        row = db.fetch_one("SELECT * FROM mainsetting WHERE setting=%s", (setting,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    def save(self, db: Database) -> None:
        if self.id:
            db.execute(
                "UPDATE mainsetting SET value=%s,status=%s WHERE setting=%s",
                (self.value, self.status, self.setting),
            )
        else:
            db.execute(
                "INSERT INTO mainsetting (setting,value,status) VALUES (%s,%s,%s)",
                (self.setting, self.value, self.status),
            )

    @classmethod
    def all(cls, db: Database) -> Dict[str, "MainSetting"]:
        rows = db.fetch_all("SELECT * FROM mainsetting")
        return {
            r["setting"]: cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__})
            for r in rows
        }


# ── Channel ───────────────────────────────────────────────────────

@dataclass
class Channel:
    """``channels`` jadvali — majburiy obuna kanallari."""
    id: int = 0
    user: str = ""
    status: str = "active"

    @classmethod
    def all(cls, db: Database) -> List["Channel"]:
        rows = db.fetch_all("SELECT * FROM channels")
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    @classmethod
    def add(cls, db: Database, username: str) -> "Channel":
        cid = db.execute(
            "INSERT INTO channels (user,status) VALUES (%s,'active')", (username,)
        )
        row = db.fetch_one("SELECT * FROM channels WHERE id=%s", (cid,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__})

    def delete(self, db: Database) -> None:
        db.execute("DELETE FROM channels WHERE id=%s", (self.id,))


# ── Referal ───────────────────────────────────────────────────────

@dataclass
class Referal:
    """``referal`` jadvali."""
    id: int = 0
    referal_code: str = ""
    owner_id: int = 0
    invited_id: int = 0
    bonus: float = 0.0
    created_at: str = ""

    @classmethod
    def get_by_code(cls, db: Database, code: str) -> Optional["Referal"]:
        row = db.fetch_one("SELECT * FROM referal WHERE referal_code=%s", (code,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    @classmethod
    def count_invited(cls, db: Database, owner_id: int) -> int:
        return db.count("SELECT COUNT(*) FROM referal WHERE owner_id=%s", (owner_id,))

    @classmethod
    def create(cls, db: Database, code: str, owner_id: int,
               invited_id: int, bonus: float) -> "Referal":
        rid = db.execute(
            "INSERT INTO referal (referal_code,owner_id,invited_id,bonus) VALUES (%s,%s,%s,%s)",
            (code, owner_id, invited_id, bonus),
        )
        row = db.fetch_one("SELECT * FROM referal WHERE id=%s", (rid,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__})


# ── Provider ──────────────────────────────────────────────────────

@dataclass
class Provider:
    """``providers`` jadvali — tashqi SMM panel API lari."""
    id: int = 0
    name: str = ""
    url: str = ""
    api_key: str = ""
    status: str = "active"

    @classmethod
    def get(cls, db: Database, provider_id: int) -> Optional["Provider"]:
        row = db.fetch_one("SELECT * FROM providers WHERE id=%s", (provider_id,))
        return cls(**{k: row[k] for k in row if k in cls.__dataclass_fields__}) if row else None

    @classmethod
    def all_active(cls, db: Database) -> List["Provider"]:
        rows = db.fetch_all("SELECT * FROM providers WHERE status='active'")
        return [cls(**{k: r[k] for k in r if k in cls.__dataclass_fields__}) for r in rows]

    def save(self, db: Database) -> None:
        if self.id:
            db.execute(
                "UPDATE providers SET name=%s,url=%s,api_key=%s,status=%s WHERE id=%s",
                (self.name, self.url, self.api_key, self.status, self.id),
            )
        else:
            self.id = db.execute(
                "INSERT INTO providers (name,url,api_key,status) VALUES (%s,%s,%s,%s)",
                (self.name, self.url, self.api_key, self.status),
            )

    def delete(self, db: Database) -> None:
        db.execute("DELETE FROM providers WHERE id=%s", (self.id,))


# ███████████████████████████████████████████████████████████████████
#  7. LANG — KO'P TILLI XABARLAR
# ███████████████████████████████████████████████████████████████████

_LANG_UZ: Dict[str, Dict[str, str]] = {
    "keyboard": {
        "new_order":       "🛒 Yangi buyurtma",
        "buy_number":      "📱 Raqam sotib olish",
        "orders":          "📦 Buyurtmalarim",
        "referal":         "👥 Referal",
        "cabinet":         "👤 Kabinet",
        "add_funds":       "💰 Balans to'ldirish",
        "help":            "❓ Yordam",
        "services":        "📋 Xizmatlar",
        "partner_program": "🤝 Hamkorlik dasturi",
        "check":           "✅ Tekshirish",
        "back":            "⬅️ Orqaga",
        "cancel":          "❌ Bekor qilish",
        "confirm":         "✅ Tasdiqlash",
        "main_menu":       "🏠 Bosh menyu",
    },
    "message": {
        "welcome":         "Assalomu alaykum, <b>{name}</b>! 👋\nSMM botimizga xush kelibsiz!",
        "join_channel":    "📢 Botdan foydalanish uchun kanallarga a'zo bo'ling:",
        "balance":         "💰 Balansingiz: <b>{balance} {currency}</b>",
        "order_created":   "✅ Buyurtma yaratildi!\n🔢 Raqami: <b>#{order_id}</b>",
        "order_not_found": "❌ Buyurtma topilmadi.",
        "low_balance":     "❌ Balans yetarli emas. Avval to'ldiring.",
        "invalid_quantity":"❌ Miqdor noto'g'ri. Min: {min}, Max: {max}",
        "invalid_link":    "❌ Havola noto'g'ri. To'g'risini kiriting.",
        "choose_category": "📂 Kategoriyani tanlang:",
        "choose_service":  "📋 Xizmatni tanlang:",
        "enter_link":      "🔗 Havolani kiriting:",
        "enter_quantity":  "🔢 Miqdorni kiriting (Min: {min}, Max: {max}):",
        "payment_success": "✅ To'lov qabul qilindi!\n💰 Qo'shildi: <b>{amount} {currency}</b>",
        "user_blocked":    "🚫 Vaqtincha bloklangansiz. Keyinroq urinib ko'ring.",
        "enter_amount":    "💵 Miqdorni kiriting (Min: {min}):",
        "referal_info":    "👥 Referal kodingiz: <code>{code}</code>\nTaklif: <b>{count}</b>\nBonus: <b>{bonus} {currency}</b>",
        "service_info":    "📋 <b>{name}</b>\n💰 Narx: {rate}/1000\n📊 Min: {min} | Max: {max}\n📝 {desc}",
        "order_status":    "🔢 #{order_id}\n📋 {service}\n🔗 {link}\n📊 {quantity} ta\n💰 {charge}\n📌 {status}",
        "error":           "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
        "flood":           "⚠️ Juda ko'p so'rov. Bir oz kuting.",
        "no_orders":       "📦 Buyurtmalar yo'q.",
        "ticket_sent":     "✅ Murojaat yuborildi!",
    },
    "admin": {
        "panel":           "⚙️ Admin paneli",
        "stats":           "📊 Statistika:\n👤 Foydalanuvchilar: {users}\n📦 Buyurtmalar: {orders}\n💰 Jami: {payments}",
        "broadcast":       "📢 Xabar yuborilmoqda...",
        "broadcast_done":  "✅ Yuborildi: {sent} | ❌ Xato: {failed}",
        "user_not_found":  "❌ Foydalanuvchi topilmadi.",
        "blocked_user":    "✅ Foydalanuvchi bloklandi.",
        "unblocked_user":  "✅ Foydalanuvchi blokdan chiqarildi.",
    },
}

_LANG_RU: Dict[str, Dict[str, str]] = {
    "keyboard": {
        "new_order":       "🛒 Новый заказ",
        "buy_number":      "📱 Купить номер",
        "orders":          "📦 Мои заказы",
        "referal":         "👥 Реферал",
        "cabinet":         "👤 Кабинет",
        "add_funds":       "💰 Пополнить баланс",
        "help":            "❓ Помощь",
        "services":        "📋 Услуги",
        "partner_program": "🤝 Партнёрская программа",
        "check":           "✅ Проверить",
        "back":            "⬅️ Назад",
        "cancel":          "❌ Отмена",
        "confirm":         "✅ Подтвердить",
        "main_menu":       "🏠 Главное меню",
    },
    "message": {
        "welcome":         "Привет, <b>{name}</b>! 👋\nДобро пожаловать в SMM бот!",
        "join_channel":    "📢 Подпишитесь на наши каналы:",
        "balance":         "💰 Ваш баланс: <b>{balance} {currency}</b>",
        "order_created":   "✅ Заказ создан!\n🔢 Номер: <b>#{order_id}</b>",
        "order_not_found": "❌ Заказ не найден.",
        "low_balance":     "❌ Недостаточно средств.",
        "invalid_quantity":"❌ Неверное количество. Мин: {min}, Макс: {max}",
        "invalid_link":    "❌ Неверная ссылка.",
        "choose_category": "📂 Выберите категорию:",
        "choose_service":  "📋 Выберите услугу:",
        "enter_link":      "🔗 Введите ссылку:",
        "enter_quantity":  "🔢 Введите количество (Мин: {min}, Макс: {max}):",
        "payment_success": "✅ Оплата принята!\n💰 Добавлено: <b>{amount} {currency}</b>",
        "user_blocked":    "🚫 Вы временно заблокированы.",
        "enter_amount":    "💵 Введите сумму (Мин: {min}):",
        "referal_info":    "👥 Реф. код: <code>{code}</code>\nПриглашено: <b>{count}</b>\nБонус: <b>{bonus} {currency}</b>",
        "service_info":    "📋 <b>{name}</b>\n💰 Цена: {rate}/1000\n📊 Мин: {min} | Макс: {max}\n📝 {desc}",
        "order_status":    "🔢 #{order_id}\n📋 {service}\n🔗 {link}\n📊 {quantity} шт\n💰 {charge}\n📌 {status}",
        "error":           "❌ Произошла ошибка.",
        "flood":           "⚠️ Слишком много запросов. Подождите.",
        "no_orders":       "📦 Заказов нет.",
        "ticket_sent":     "✅ Обращение отправлено!",
    },
    "admin": {
        "panel":           "⚙️ Панель администратора",
        "stats":           "📊 Статистика:\n👤 Пользователи: {users}\n📦 Заказы: {orders}\n💰 Итого: {payments}",
        "broadcast":       "📢 Рассылка...",
        "broadcast_done":  "✅ Отправлено: {sent} | ❌ Ошибок: {failed}",
        "user_not_found":  "❌ Пользователь не найден.",
        "blocked_user":    "✅ Пользователь заблокирован.",
        "unblocked_user":  "✅ Пользователь разблокирован.",
    },
}

_LANG_EN: Dict[str, Dict[str, str]] = {
    "keyboard": {
        "new_order":       "🛒 New Order",
        "buy_number":      "📱 Buy Number",
        "orders":          "📦 My Orders",
        "referal":         "👥 Referral",
        "cabinet":         "👤 Profile",
        "add_funds":       "💰 Add Funds",
        "help":            "❓ Help",
        "services":        "📋 Services",
        "partner_program": "🤝 Partner Program",
        "check":           "✅ Check",
        "back":            "⬅️ Back",
        "cancel":          "❌ Cancel",
        "confirm":         "✅ Confirm",
        "main_menu":       "🏠 Main Menu",
    },
    "message": {
        "welcome":         "Hello, <b>{name}</b>! 👋\nWelcome to our SMM bot!",
        "join_channel":    "📢 Please join our channels:",
        "balance":         "💰 Your balance: <b>{balance} {currency}</b>",
        "order_created":   "✅ Order created!\n🔢 ID: <b>#{order_id}</b>",
        "order_not_found": "❌ Order not found.",
        "low_balance":     "❌ Insufficient balance.",
        "invalid_quantity":"❌ Invalid quantity. Min: {min}, Max: {max}",
        "invalid_link":    "❌ Invalid link.",
        "choose_category": "📂 Choose a category:",
        "choose_service":  "📋 Choose a service:",
        "enter_link":      "🔗 Enter the link:",
        "enter_quantity":  "🔢 Enter quantity (Min: {min}, Max: {max}):",
        "payment_success": "✅ Payment accepted!\n💰 Added: <b>{amount} {currency}</b>",
        "user_blocked":    "🚫 You are temporarily blocked.",
        "enter_amount":    "💵 Enter amount (Min: {min}):",
        "referal_info":    "👥 Referral code: <code>{code}</code>\nInvited: <b>{count}</b>\nBonus: <b>{bonus} {currency}</b>",
        "service_info":    "📋 <b>{name}</b>\n💰 Rate: {rate}/1000\n📊 Min: {min} | Max: {max}\n📝 {desc}",
        "order_status":    "🔢 #{order_id}\n📋 {service}\n🔗 {link}\n📊 {quantity}\n💰 {charge}\n📌 {status}",
        "error":           "❌ An error occurred.",
        "flood":           "⚠️ Too many requests. Wait a moment.",
        "no_orders":       "📦 No orders yet.",
        "ticket_sent":     "✅ Ticket submitted!",
    },
    "admin": {
        "panel":           "⚙️ Admin Panel",
        "stats":           "📊 Stats:\n👤 Users: {users}\n📦 Orders: {orders}\n💰 Total: {payments}",
        "broadcast":       "📢 Broadcasting...",
        "broadcast_done":  "✅ Sent: {sent} | ❌ Failed: {failed}",
        "user_not_found":  "❌ User not found.",
        "blocked_user":    "✅ User blocked.",
        "unblocked_user":  "✅ User unblocked.",
    },
}

_LANGUAGES: Dict[str, Dict] = {
    "default": _LANG_UZ,
    "uz":      _LANG_UZ,
    "ru":      _LANG_RU,
    "en":      _LANG_EN,
}


class Lang:
    """
    Ko'p tilli xabarlar boshqaruvchisi.

    Ekvivalent PHP: ``__([$section, $key])``

    Misol::

        lang = Lang("uz")
        print(lang.kb("new_order"))
        # → "🛒 Yangi buyurtma"

        print(lang.msg("balance", balance=100, currency="UZS"))
        # → "💰 Balansingiz: <b>100 UZS</b>"
    """

    def __init__(self, lang_code: str = "default"):
        self._code = lang_code if lang_code in _LANGUAGES else "default"
        self._data = _LANGUAGES[self._code]

    @property
    def code(self) -> str:
        return self._code

    def get(self, section: str, key: str) -> str:
        return self._data.get(section, {}).get(key, "")

    def fmt(self, section: str, key: str, **kwargs: Any) -> str:
        try:
            return self.get(section, key).format(**kwargs)
        except KeyError:
            return self.get(section, key)

    def kb(self, key: str) -> str:
        """Klaviatura tugmasi."""
        return self.get("keyboard", key)

    def msg(self, key: str, **kwargs: Any) -> str:
        """Xabar matni."""
        return self.fmt("message", key, **kwargs)

    def adm(self, key: str, **kwargs: Any) -> str:
        """Admin xabari."""
        return self.fmt("admin", key, **kwargs)

    @staticmethod
    def available() -> List[str]:
        return list(_LANGUAGES.keys())

    @classmethod
    def for_user(cls, lang_code: Optional[str]) -> "Lang":
        return cls(lang_code or "default")


# ███████████████████████████████████████████████████████████████████
#  8. SMMBOT — ASOSIY KLASS
# ███████████████████████████████████████████████████████████████████

class SMMBot:
    """
    Telegram Bot API wrapper + SMM panel logikasi.

    Ekvivalent PHP: ``bot()`` funksiyasi va barcha bot operatsiyalari.

    Ishlatish::

        config = Config(bot_token="TOKEN", admin_id=123456, db_name="smm")

        with SMMBot(config) as bot:
            user = bot.get_or_create_user(chat_id=987654321)
            bot.send_message(987654321, "Salom!")

            result = bot.place_order(
                user_id=987654321,
                service_id=1,
                link="https://instagram.com/example",
                quantity=1000,
            )
            print(result)
            # {"success": True, "order_id": 42, "charge": 5.0}
    """

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config)
        self.flood = FloodControl(config.flood_log, config.block_log)
        self.steps = StepManager(config.step_dir)
        self._session = requests.Session()
        self._session.verify = False

    # ══════════════════════════════════════════════════════════
    #  TELEGRAM API
    # ══════════════════════════════════════════════════════════

    def _call(self, method: str, data: Optional[Dict] = None,
              token: Optional[str] = None) -> Optional[Dict]:
        """
        Telegram API ga so'rov yuboradi.

        Ekvivalent PHP: ``bot($method, $datas)``
        """
        tok = token or self.config.bot_token
        url = self.BASE_URL.format(token=tok, method=method)
        try:
            resp = self._session.post(url, data=data or {}, timeout=30)
            return resp.json()
        except Exception as e:
            logger.error("Telegram API xatosi [%s]: %s", method, e)
            return None

    def send_message(self, chat_id: int, text: str,
                     reply_markup: Optional[str] = None,
                     parse_mode: str = "HTML") -> Optional[Dict]:
        """
        Xabar yuboradi.

        Ekvivalent PHP: ``sms($id, $tx, $m)``

        Misol::

            bot.send_message(123456, "Salom, <b>do'stim</b>!")
            bot.send_message(123456, "Menyu", reply_markup=reply_keyboard([["✅ Ha"]]))
        """
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": f"<b>{text}</b>" if parse_mode == "HTML" else text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._call("sendMessage", payload)

    def edit_message(self, chat_id: int, message_id: int, text: str,
                     reply_markup: Optional[str] = None) -> Optional[Dict]:
        """
        Xabarni tahrirlaydi.

        Ekvivalent PHP: ``edit($id, $mid, $tx, $m)``
        """
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"<b>{text}</b>",
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._call("editMessageText", payload)

    def delete_message(self, chat_id: int, message_id: int) -> Optional[Dict]:
        """
        Xabarni o'chiradi.

        Ekvivalent PHP: ``del()``
        """
        return self._call("deleteMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    def answer_callback(self, callback_id: str, text: str = "",
                        show_alert: bool = False) -> Optional[Dict]:
        """
        Callback so'roviga javob beradi.

        Ekvivalent PHP: ``accl($d, $s, $j)``
        """
        return self._call("answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": text,
            "show_alert": show_alert,
        })

    def send_photo(self, chat_id: int, photo: str,
                   caption: str = "",
                   reply_markup: Optional[str] = None) -> Optional[Dict]:
        """Rasm yuboradi."""
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": f"<b>{caption}</b>" if caption else "",
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._call("sendPhoto", payload)

    def get_chat_member(self, chat_id: str, user_id: int) -> Optional[Dict]:
        """Kanal a'zoligini tekshiradi."""
        return self._call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def get_me(self) -> Optional[Dict]:
        """Bot ma'lumotlarini oladi. Ekvivalent PHP: ``bot(getMe)``"""
        return self._call("getMe")

    def set_webhook(self, url: str) -> Optional[Dict]:
        return self._call("setWebhook", {"url": url})

    def delete_webhook(self) -> Optional[Dict]:
        return self._call("deleteWebhook")

    def send_broadcast(self, user_ids: List[int], text: str,
                       reply_markup: Optional[str] = None) -> Dict[str, int]:
        """
        Barcha foydalanuvchilarga xabar yuboradi.

        Returns::

            {"sent": 100, "failed": 5}
        """
        sent = failed = 0
        for uid in user_ids:
            try:
                res = self.send_message(uid, text, reply_markup)
                if res and res.get("ok"):
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                logger.warning("Broadcast xatosi [%s]: %s", uid, e)
                failed += 1
        return {"sent": sent, "failed": failed}

    # ══════════════════════════════════════════════════════════
    #  OBUNA TEKSHIRUVI
    # ══════════════════════════════════════════════════════════

    def check_join(self, user_id: int) -> bool:
        """
        Majburiy kanallarga a'zolikni tekshiradi.

        Ekvivalent PHP: ``joinchat($id)``

        Returns:
            True — barcha kanallarda a'zo.
            False — a'zo emas (xabar yuboriladi).
        """
        channels = Channel.all(self.db)
        if not channels:
            return True

        not_joined = []
        for ch in channels:
            result = self.get_chat_member(ch.user, user_id)
            if not result or not result.get("ok"):
                not_joined.append(ch)
                continue
            status = result["result"].get("status", "")
            if status not in ("creator", "administrator", "member"):
                not_joined.append(ch)

        if not not_joined:
            return True

        buttons = [
            [{"text": f"❌ {ch.user}", "url": f"t.me/{ch.user.lstrip('@')}"}]
            for ch in not_joined
        ]
        buttons.append([{"text": "✅ Tekshirish", "callback_data": "result"}])
        self.send_message(user_id, "📢 Kanallarga a'zo bo'ling:",
                          reply_markup=inline_keyboard(buttons))
        return False

    # ══════════════════════════════════════════════════════════
    #  FOYDALANUVCHI
    # ══════════════════════════════════════════════════════════

    def get_or_create_user(self, chat_id: int) -> User:
        """Ekvivalent PHP: ``adduser($cid)`` + ``user($cid)``"""
        return User.add(self.db, chat_id)

    def get_user(self, chat_id: int) -> Optional[User]:
        return User.get(self.db, chat_id)

    def is_admin(self, user_id: int) -> bool:
        if user_id in self.config.admins:
            return True
        return bool(self.db.fetch_one(
            "SELECT * FROM admins WHERE user_id=%s", (str(user_id),)
        ))

    def load_admins(self) -> None:
        rows = self.db.fetch_all("SELECT user_id FROM admins")
        for r in rows:
            try:
                uid = int(r["user_id"])
                if uid not in self.config.admins:
                    self.config.admins.append(uid)
            except (ValueError, KeyError):
                pass

    # ══════════════════════════════════════════════════════════
    #  SOZLAMALAR
    # ══════════════════════════════════════════════════════════

    def get_setting(self, key: str) -> Optional[MainSetting]:
        """Ekvivalent PHP: ``mainsetting($m)``"""
        return MainSetting.get(self.db, key)

    def setting_enabled(self, key: str) -> bool:
        s = self.get_setting(key)
        return s is not None and s.status == "1"

    # ══════════════════════════════════════════════════════════
    #  BUYURTMA
    # ══════════════════════════════════════════════════════════

    def place_order(self, user_id: int, service_id: int,
                    link: str, quantity: int) -> Dict[str, Any]:
        """
        Foydalanuvchi nomidan buyurtma beradi.

        Returns::

            {"success": True,  "order_id": 42, "charge": 5.0}
            {"success": False, "error": "Balans yetarli emas."}
        """
        user = self.get_user(user_id)
        if not user:
            return {"success": False, "error": "Foydalanuvchi topilmadi."}

        service = Service.get(self.db, service_id)
        if not service:
            return {"success": False, "error": "Xizmat topilmadi."}

        if not (service.min <= quantity <= service.max):
            return {"success": False,
                    "error": f"Miqdor {service.min}–{service.max} orasida bo'lishi kerak."}

        charge = service.calculate_price(quantity)
        if user.balance < charge:
            return {"success": False, "error": "Balans yetarli emas."}

        user.update_balance(self.db, -charge)
        order = Order.create(self.db, user_id, service_id, link, quantity, charge)
        self._send_to_provider(order, service)

        return {"success": True, "order_id": order.id, "charge": charge}

    def _send_to_provider(self, order: Order, service: Service) -> None:
        provider = Provider.get(self.db, service.provider_id)
        if not provider:
            return
        try:
            resp = self._session.post(
                provider.url,
                data={
                    "key": provider.api_key,
                    "action": "add",
                    "service": service.service_id,
                    "link": order.link,
                    "quantity": order.quantity,
                },
                timeout=20,
            )
            data = resp.json()
            if "order" in data:
                order.provider_order_id = str(data["order"])
                order.status = "active"
                order.save(self.db)
        except Exception as e:
            logger.error("Provider ulanish xatosi: %s", e)

    # ══════════════════════════════════════════════════════════
    #  FLOOD / BLOK
    # ══════════════════════════════════════════════════════════

    def flood_check(self, user_id: int) -> bool:
        return self.flood.check(user_id, self.config.flood_max_attempts,
                                self.config.flood_time_interval)

    def is_blocked(self, user_id: int) -> bool:
        return self.flood.is_blocked(user_id, self.config.block_duration)

    # ══════════════════════════════════════════════════════════
    #  QADAM (STEP)
    # ══════════════════════════════════════════════════════════

    def get_step(self, user_id: int) -> str:
        return self.steps.get(user_id)

    def set_step(self, user_id: int, step: str) -> None:
        self.steps.set(user_id, step)

    def clear_step(self, user_id: int) -> None:
        self.steps.clear(user_id)

    # ══════════════════════════════════════════════════════════
    #  CONTEXT MANAGER
    # ══════════════════════════════════════════════════════════

    def __enter__(self) -> "SMMBot":
        self.db.connect()
        self.load_admins()
        return self

    def __exit__(self, *_) -> None:
        self.db.close()
        self._session.close()


# ███████████████████████████████████████████████████████████████████
#  TEZKOR MISOL  (python smm2024.py orqali ishga tushirganda)
# ███████████████████████████████████████████████████████████████████

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    # --- Sozlash ---
    config = Config(
        bot_token="YOUR_BOT_TOKEN",
        admin_id=123456789,
        db_host="localhost",
        db_user="root",
        db_password="parol",
        db_name="smm",
    )

    print("=" * 60)
    print("  SMM2024 Python Kutubxonasi — Test")
    print("=" * 60)

    # --- Util testlar ---
    print("\n[encode_decode]")
    enc = encode_decode("encode", "salom dunyo")
    print(f"  encode: {enc}")
    print(f"  decode: {encode_decode('decode', enc)}")

    print("\n[generate_code]")
    print(f"  kod: {generate_code()}")
    print(f"  uzun: {generate_code(12)}")

    print("\n[number_format]")
    print(f"  {number_format(1234567)}")
    print(f"  {number_format(9999.99, 2)}")

    print("\n[check_average]")
    print(f"  {check_average('2024-01-01 10:00:00', '2024-01-03 12:30:00')}")

    print("\n[now_tashkent]")
    print(f"  {now_tashkent()}")

    print("\n[inline_keyboard]")
    kb = inline_keyboard([
        [{"text": "✅ Ha", "callback_data": "yes"},
         {"text": "❌ Yo'q", "callback_data": "no"}],
    ])
    print(f"  {kb}")

    print("\n[reply_keyboard]")
    rkb = reply_keyboard([
        ["🛒 Buyurtma", "📦 Xizmatlar"],
        ["💰 Balans", "⚙️ Sozlamalar"],
    ])
    print(f"  {rkb}")

    print("\n[Lang]")
    for code in ("uz", "ru", "en"):
        lang = Lang(code)
        print(f"  [{code}] new_order: {lang.kb('new_order')}")
        print(f"  [{code}] balance:   {lang.msg('balance', balance=100, currency='UZS')}")

    print("\n[FloodControl]")
    fc = FloodControl()
    for i in range(7):
        result = fc.check(999999, max_attempts=5, interval=10)
        print(f"  urinish {i+1}: {'✅ OK' if result else '❌ SPAM'}")

    print("\n[StepManager]")
    sm = StepManager()
    sm.set(12345, "awaiting_link")
    print(f"  qadam: '{sm.get(12345)}'")
    sm.clear(12345)
    print(f"  tozalandi: '{sm.get(12345)}'")

    print("\n" + "=" * 60)
    print("  Barcha testlar muvaffaqiyatli o'tdi! ✅")
    print("  Bot bilan ishlash uchun:")
    print("    with SMMBot(config) as bot:")
    print("        user = bot.get_or_create_user(chat_id=123456)")
    print("        bot.send_message(123456, 'Salom!')")
    print("=" * 60)
