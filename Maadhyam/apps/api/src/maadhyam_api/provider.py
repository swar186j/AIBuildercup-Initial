"""Shared bounded Gemini transport. Never log prompts or provider exceptions."""
def gemini_client(api_key: str):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=20000,
        retry_options=types.HttpRetryOptions(attempts=2, initial_delay=0.5,
            max_delay=1, exp_base=2, jitter=True,
            http_status_codes=[429, 500, 502, 503, 504]),
    ))
