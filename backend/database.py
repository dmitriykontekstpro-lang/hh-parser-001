from supabase import create_client, Client
from backend.config import config
import logging

# Setup Supabase client
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def get_search_queries():
    """Fetches active search queries from Supabase."""
    try:
        response = supabase.table("search_queries_hhnew").select("query").eq("is_active", True).execute()
        return [item['query'] for item in response.data] if response.data else []
    except Exception as e:
        logging.error(f"Error fetching search queries: {e}")
        return []

def get_stop_words():
    """Fetches stop words from Supabase."""
    try:
        response = supabase.table("stop_words_hhnew").select("word").execute()
        return [item['word'] for item in response.data] if response.data else []
    except Exception as e:
        logging.error(f"Error fetching stop words: {e}")
        return []

def vacancy_exists(link: str) -> bool:
    """Checks if a vacancy already exists in the database."""
    try:
        response = supabase.table("vacancies_hhnew").select("vacancy_link", count="exact").eq("vacancy_link", link).execute()
        return response.count > 0 if response.count is not None else len(response.data) > 0
    except Exception as e:
        logging.error(f"Error checking vacancy existence: {e}")
        return False

def insert_vacancy(vacancy_data: dict):
    """Inserts a new vacancy into Supabase."""
    try:
        response = supabase.table("vacancies_hhnew").insert(vacancy_data).execute()
        return response.data
    except Exception as e:
        logging.error(f"Error inserting vacancy: {e}")
        return None

def get_vacancies_without_status(limit: int = 100):
    """
    Returns vacancies where status_vacancy IS NULL or EMPTY.
    Returns list of (id, vacancy_link) tuples.
    """
    try:
        response = (
            supabase.table("vacancies_hhnew")
            .select("id, vacancy_link")
            .is_("status_vacancy", "null")
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error fetching vacancies without status: {e}")
        return []

def update_vacancy_status(vacancy_id: str, status: str):
    """Updates status_vacancy field for a given vacancy id."""
    try:
        response = (
            supabase.table("vacancies_hhnew")
            .update({"status_vacancy": status})
            .eq("id", vacancy_id)
            .execute()
        )
        return response.data
    except Exception as e:
        logging.error(f"Error updating vacancy status {vacancy_id}: {e}")
        return None
