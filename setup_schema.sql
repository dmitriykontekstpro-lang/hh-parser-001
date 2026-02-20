-- ============================================================
-- ПОЛНАЯ СХЕМА БАЗЫ ДАННЫХ ДЛЯ HH ПАРСЕРА
-- Запустить один раз в Supabase SQL Editor
-- ============================================================

-- Расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. ТАБЛИЦА ВАКАНСИЙ (куда сохраняются собранные вакансии)
-- ============================================================
CREATE TABLE IF NOT EXISTS vacancies_hhnew (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    parsing_date_time TIMESTAMP WITH TIME ZONE,          -- Дата и время парсинга
    vacancy_link     TEXT NOT NULL UNIQUE,               -- Ссылка на вакансию (уникальная)
    raw_text         TEXT,                               -- Сырой текст вакансии
    parameters_json  JSONB,                              -- JSON с параметрами (название, зарплата, компания и т.д.)
    status_vacancy   TEXT                                -- Статус: NULL = активна, 'archiv' = в архиве
);

-- Индекс для быстрого поиска по ссылке (проверка дублей)
CREATE INDEX IF NOT EXISTS idx_vacancies_hhnew_link ON vacancies_hhnew(vacancy_link);

-- ============================================================
-- 2. ТАБЛИЦА ПОИСКОВЫХ ЗАПРОСОВ (что ищем)
-- ============================================================
CREATE TABLE IF NOT EXISTS search_queries_hhnew (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    query      TEXT NOT NULL UNIQUE,    -- Поисковый запрос, например: "Python разработчик"
    is_active  BOOLEAN DEFAULT TRUE     -- TRUE = активный (будет использоваться при парсинге)
);

-- ============================================================
-- 3. ТАБЛИЦА СТОП-СЛОВ (фильтрация по названию)
-- ============================================================
CREATE TABLE IF NOT EXISTS stop_words_hhnew (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    word       TEXT NOT NULL UNIQUE     -- Стоп-слово, например: "Senior", "Lead", "1С"
);

-- ============================================================
-- ПОЛИТИКИ БЕЗОПАСНОСТИ (RLS)
-- ============================================================

-- Вакансии
ALTER TABLE vacancies_hhnew ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read" ON vacancies_hhnew;
DROP POLICY IF EXISTS "Allow insert" ON vacancies_hhnew;
CREATE POLICY "Allow read" ON vacancies_hhnew FOR SELECT USING (true);
CREATE POLICY "Allow insert" ON vacancies_hhnew FOR INSERT WITH CHECK (true);

-- Поисковые запросы
ALTER TABLE search_queries_hhnew ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read" ON search_queries_hhnew;
DROP POLICY IF EXISTS "Allow insert" ON search_queries_hhnew;
CREATE POLICY "Allow read" ON search_queries_hhnew FOR SELECT USING (true);
CREATE POLICY "Allow insert" ON search_queries_hhnew FOR INSERT WITH CHECK (true);

-- Стоп-слова
ALTER TABLE stop_words_hhnew ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read" ON stop_words_hhnew;
DROP POLICY IF EXISTS "Allow insert" ON stop_words_hhnew;
CREATE POLICY "Allow read" ON stop_words_hhnew FOR SELECT USING (true);
CREATE POLICY "Allow insert" ON stop_words_hhnew FOR INSERT WITH CHECK (true);

-- ============================================================
-- ТЕСТОВЫЕ ДАННЫЕ (можете удалить или изменить)
-- ============================================================

INSERT INTO search_queries_hhnew (query) VALUES
    ('Python разработчик'),
    ('Data Analyst'),
    ('Маркетолог')
ON CONFLICT (query) DO NOTHING;

INSERT INTO stop_words_hhnew (word) VALUES
    ('Senior'),
    ('Lead'),
    ('1С')
ON CONFLICT (word) DO NOTHING;
