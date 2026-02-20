-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Vacancies table
CREATE TABLE IF NOT EXISTS vacancies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    vacancy_link TEXT NOT NULL UNIQUE,
    raw_text TEXT,
    parsing_date_time TIMESTAMP WITH TIME ZONE,
    parameters_json JSONB
);

-- 2. Search Queries table (Where we search for jobs)
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    query TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Stop Words table (Titles containing these will be skipped)
CREATE TABLE IF NOT EXISTS stop_words (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()),
    word TEXT NOT NULL UNIQUE -- e.g. "Senior", "Lead" if you only want Junior
);

-- RLS Policies (Optional but recommended)
ALTER TABLE vacancies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON vacancies FOR SELECT USING (true);
CREATE POLICY "Enable insert for service role" ON vacancies FOR INSERT WITH CHECK (true);

ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON search_queries FOR SELECT USING (true);
CREATE POLICY "Enable insert for service role" ON search_queries FOR INSERT WITH CHECK (true);

ALTER TABLE stop_words ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON stop_words FOR SELECT USING (true);
CREATE POLICY "Enable insert for service role" ON stop_words FOR INSERT WITH CHECK (true);
