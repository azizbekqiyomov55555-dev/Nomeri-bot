-- ═══════════════════════════════════════════════════
--  SMM BOT — DATABASE JADVALLAR
--  Railway MySQL Query bo'limiga ko'chirib ishga tushiring
-- ═══════════════════════════════════════════════════

-- 1. FOYDALANUVCHILAR
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY,
    user_id     INT AUTO_INCREMENT UNIQUE,
    status      VARCHAR(20)  DEFAULT 'active',
    balance     DECIMAL(12,2) DEFAULT 0.00,
    outing      DECIMAL(12,2) DEFAULT 0.00,
    api_key     VARCHAR(64)  DEFAULT '',
    referal     VARCHAR(20)  DEFAULT '',
    user_detail VARCHAR(10)  DEFAULT 'false',
    free_cate   VARCHAR(10)  DEFAULT 'false',
    lang        VARCHAR(10)  DEFAULT 'default',
    currency    VARCHAR(10)  DEFAULT 'UZS'
);

-- 2. KATEGORIYALAR
CREATE TABLE IF NOT EXISTS categorys (
    category_id     INT AUTO_INCREMENT PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL,
    category_status VARCHAR(20)  DEFAULT 'active',
    category_line   INT          DEFAULT 0
);

-- 3. XIZMATLAR
CREATE TABLE IF NOT EXISTS services (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    service_id  VARCHAR(50)  DEFAULT '',
    category_id INT          DEFAULT 0,
    name        VARCHAR(200) NOT NULL,
    rate        DECIMAL(10,4) DEFAULT 0,
    min         INT          DEFAULT 10,
    max         INT          DEFAULT 10000,
    status      VARCHAR(20)  DEFAULT 'active',
    provider_id INT          DEFAULT 0,
    type        VARCHAR(50)  DEFAULT '',
    description TEXT
);

-- 4. BUYURTMALAR
CREATE TABLE IF NOT EXISTS orders (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           BIGINT       DEFAULT 0,
    service_id        INT          DEFAULT 0,
    link              TEXT,
    quantity          INT          DEFAULT 0,
    charge            DECIMAL(12,4) DEFAULT 0,
    start_count       INT          DEFAULT 0,
    remains           INT          DEFAULT 0,
    status            VARCHAR(20)  DEFAULT 'pending',
    provider_order_id VARCHAR(50)  DEFAULT '',
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 5. TO'LOVLAR
CREATE TABLE IF NOT EXISTS payments (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT        DEFAULT 0,
    amount         DECIMAL(12,2) DEFAULT 0,
    method         VARCHAR(50)   DEFAULT 'manual',
    status         VARCHAR(20)   DEFAULT 'pending',
    transaction_id VARCHAR(100)  DEFAULT '',
    created_at     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- 6. PROVAYDERLAR
CREATE TABLE IF NOT EXISTS providers (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    name    VARCHAR(100) DEFAULT '',
    url     VARCHAR(255) DEFAULT '',
    api_key VARCHAR(255) DEFAULT '',
    status  VARCHAR(20)  DEFAULT 'active'
);

-- 7. KANALLAR (majburiy obuna)
CREATE TABLE IF NOT EXISTS channels (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    user   VARCHAR(100) DEFAULT '',
    status VARCHAR(20)  DEFAULT 'active'
);

-- 8. REFERAL
CREATE TABLE IF NOT EXISTS referal (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    referal_code VARCHAR(50)   DEFAULT '',
    owner_id     BIGINT        DEFAULT 0,
    invited_id   BIGINT        DEFAULT 0,
    bonus        DECIMAL(12,2) DEFAULT 0,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- 9. ADMINLAR
CREATE TABLE IF NOT EXISTS admins (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(30) DEFAULT ''
);

-- 10. SOZLAMALAR
CREATE TABLE IF NOT EXISTS mainsetting (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    setting VARCHAR(100) DEFAULT '',
    value   TEXT,
    status  VARCHAR(5)   DEFAULT '1'
);

-- ═══════════════════════════════════════════════════
--  NAMUNA MA'LUMOTLAR (ixtiyoriy)
-- ═══════════════════════════════════════════════════

-- Kategoriya misoli
INSERT INTO categorys (category_name, category_status, category_line)
VALUES
    ('📸 Instagram', 'active', 1),
    ('▶️ YouTube',   'active', 2),
    ('📱 TikTok',    'active', 3);

-- Xizmat misoli
INSERT INTO services (service_id, category_id, name, rate, min, max, status, description)
VALUES
    ('1', 1, '❤️ Instagram Like',      10.00, 100, 10000, 'active', 'Tez yetkaziladi'),
    ('2', 1, '👥 Instagram Follower',  50.00, 50,  5000,  'active', 'Real akkauntlar'),
    ('3', 2, '▶️ YouTube View',        5.00,  500, 50000, 'active', 'HQ views');

-- Asosiy sozlama
INSERT INTO mainsetting (setting, value, status)
VALUES
    ('maintenance', '0', '0'),
    ('min_deposit', '1000', '1');

SELECT 'Jadvallar muvaffaqiyatli yaratildi! ✅' AS natija;
