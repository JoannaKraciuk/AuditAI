# AudytAI

Prosta aplikacja Streamlit do generowania raportów WCAG w formacie Word i Excel, z automatycznym zapisem szkiców, obsługą rekomendacji AI (OpenAI), jasnym motywem i wysokim kontrastem zgodnym z WCAG.

## Uruchomienie (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
setx OPENAI_API_KEY "<twój_klucz>"            # lub ustaw w bieżącej sesji: $env:OPENAI_API_KEY = '<twój_klucz>'
streamlit run app.py
```

## Funkcje

- Generowanie raportów WCAG (Word, Excel)
- Automatyczny zapis i ładowanie szkiców audytu
- Rekomendacje AI (OpenAI, tryb MOCK domyślny)
- Jasny motyw, kontrastowe kolory statusów
- Bezpieczne repozytorium: dane, szkice i raporty ukryte przez `.gitignore`

## Bezpieczeństwo

- Plik `.gitignore` ukrywa szkice, pliki raportów, dane i klucze API
- Nie commituj pliku `.env` ani folderu `szkice/`

## Repozytorium

[github.com/JoannaKraciuk/AudytAI](https://github.com/JoannaKraciuk/AudytAI)
