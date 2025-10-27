import os
import openai
import importlib
import json

# Some openai package versions expose exceptions under openai.error, others may differ.
# Use importlib to attempt dynamic import and fallback to local exceptions if not found.
try:
    err_mod = importlib.import_module("openai.error")
    RateLimitError = getattr(err_mod, "RateLimitError")
    OpenAIError = getattr(err_mod, "OpenAIError")
except Exception:
    class RateLimitError(Exception):
        pass

    class OpenAIError(Exception):
        pass

def generate_recommendations(responses: dict, notes: dict | None = None, model: str = "gpt-3.5-turbo") -> dict:
    """
    Generate textual recommendations for failed WCAG criteria using OpenAI.

    - Expects `OPENAI_API_KEY` to be available in environment.
    - `responses` is a dict mapping criterion id -> status string (as in `app.py`).
    - `notes` should contain only text notes (no file names or file objects).
    Returns a dict mapping criterion id to recommendation string.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    # If user chooses MOCK model or API key missing, return example text instead of calling API
    if model == "MOCK" or not api_key:
        # Simple mock response useful for offline/dev testing
        failed = [cid for cid, r in responses.items() if r and str(r).startswith("❌")]
        if not failed:
            return {}
        # return dict mapping criterion id -> sample recommendation
        return {cid: f"Przykładowe rekomendacje dla {cid}: sprawdź ALT, kontrast i obsługę klawiatury." for cid in failed}

    openai.api_key = api_key

    # Build a concise prompt listing unmet criteria
    failed = [cid for cid, r in responses.items() if r and str(r).startswith("❌")]
    if not failed:
        return "Brak rekomendacji — wszystkie kryteria oznaczone jako spełnione lub nie dotyczy."

    # Build structured prompt asking for JSON output: {"1.1.1": "...", ...}
    prompt_lines = [
        "Jesteś ekspertem od dostępności cyfrowej (WCAG). Dla każdego niespełnionego kryterium WCAG wygeneruj rekomendację w formie czystego tekstu, bez grafik, wideo ani innych mediów.",
        "Każda rekomendacja powinna być opisowa (2–4 zdania, krótki akapit):",
        "- wyjaśnij na czym polega problem, dlaczego jest istotny dla dostępności, jaki ma wpływ na użytkowników (np. osoby z niepełnosprawnościami)",
        "- podaj techniczne zalecenie jak naprawić problem (zwięźle, konkretnie)",
        "- jeśli ma sens, dodaj przykładowy fragment kodu (HTML, CSS, JS) — tylko jeśli jest potrzebny, nie wymuszaj pustych pól",
        "- dodaj źródło: link do odpowiedniego dokumentu WCAG (np. https://www.w3.org/WAI/WCAG21/Understanding/1.1.1.html)",
        "Format odpowiedzi (JSON, bez dodatkowego opisu):",
        "'1.1.1': { 'naprawa': 'Dodaj tekst alternatywny do wszystkich obrazów. Tekst alternatywny umożliwia osobom korzystającym z czytników ekranu zrozumienie treści wizualnej. Brak opisu powoduje, że użytkownicy niewidomi nie wiedzą, co przedstawia obraz.', 'kod': '<img src=\"produkt.jpg\" alt=\"Zdjęcie produktu – czerwony kubek ceramiczny\">', 'w3c_link': 'https://www.w3.org/WAI/WCAG21/Understanding/1.1.1.html' }",
        "Nie dodawaj żadnych plików, grafik, screenów, miniaturek, osadzonych filmów ani znaczników multimedialnych.",
        "Zabronione elementy: <video>, <source>, <img>, <iframe>, <audio>, <embed>, linki do wideo (YouTube, Vimeo, MP4 itp.), komunikaty typu 'Nieobsługiwany format wideo', 'Nie można odtworzyć wideo', 'Brak podglądu'.",
        "Nie używaj pustych pól ani dodatkowych linii. Styl: profesjonalny, spójny, raportowy (jak audyt dostępności).",
        "",
    ]
    for cid in failed:
        # include the status and any notes provided
        note_text = ""
        if notes and cid in notes and notes[cid]:
            note_text = f"; uwagi: {notes[cid]}"
        prompt_lines.append(f"- {cid}: status = {responses.get(cid)}{note_text}")

    prompt_lines += [
        "",
        "Zwróć poprawny JSON (bez dodatkowego opisu). Jeśli nie ma uwag, zwróć pusty obiekt {}.",
    ]
    prompt = "\n".join(prompt_lines)

    # Try to support both old and new openai python SDK interfaces.
    # Newer versions expose an OpenAI client class with chat.completions.create(...)
    OpenAIClient = None
    try:
        from openai import OpenAI as OpenAIClient
    except Exception:
        OpenAIClient = None

    if OpenAIClient is not None:
        try:
            client = OpenAIClient(api_key=api_key) if api_key else OpenAIClient()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600,
            )
            # try multiple ways to extract content (dict-like or object)
            try:
                text = resp["choices"][0]["message"]["content"].strip()
            except Exception:
                try:
                    text = resp.choices[0].message.content.strip()
                except Exception:
                    text = str(resp)
            # Parse JSON output if possible
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {"_combined": text}
        except RateLimitError:
            # Quota / rate-limit issue — return a clear message to insert into the report
            return "Błąd: przekroczono limit lub brak środków w planie OpenAI (insufficient_quota). Sprawdź ustawienia rozliczeń na platform.openai.com."
        except OpenAIError:
            # re-raise OpenAI-related errors to let caller handle/report them
            raise
        except Exception:
            # If the new client exists but some unexpected error occurred, raise it
            raise

    # Fallback: try the older API surface if available (older openai packages)
    if getattr(openai, "ChatCompletion", None) is not None:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        try:
            text = resp["choices"][0]["message"]["content"].strip()
        except Exception:
            try:
                text = resp.choices[0].message.content.strip()
            except Exception:
                text = str(resp)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {"_combined": text}

    # If we reach this point, the installed openai package doesn't expose a usable API
    raise RuntimeError("Zainstalowana paczka openai nie obsługuje ani nowego, ani starego interfejsu klienta. Zainstaluj odpowiednią wersję (np. openai>=1.0.0) lub sprawdź dokumentację.")
