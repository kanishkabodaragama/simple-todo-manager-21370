# Supabase Integration Notes

This backend currently uses an in-memory store for todos to keep the implementation simple. If you need persistence and auth, integrate Supabase as follows.

## Required Environment Variables

Copy `.env.example` to `.env` and set:

- SUPABASE_URL
- SUPABASE_ANON_KEY

Optionally:
- BACKEND_CORS_ORIGINS

## Python Client

Install the official Supabase Python client if integrating:

pip install supabase

Note: This project currently does not include the dependency since we are not using Supabase at runtime.

## Example Pseudocode

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def save_todo_to_supabase(todo: dict):
    return supabase.table("todos").insert(todo).execute()

## Auth and Email Redirect

When implementing user signup, set `emailRedirectTo` using SITE_URL from environment. The deployment agent will map it to the correct URL.

This document must be updated if you change how the backend uses Supabase.
