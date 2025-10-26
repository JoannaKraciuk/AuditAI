# Prototyp agenta WCAG

Krótko: prosta aplikacja Streamlit generująca raporty WCAG w formacie Word.

Uruchomienie (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
setx OPENAI_API_KEY "<twój_klucz>"            # lub ustaw w bieżącej sesji: $env:OPENAI_API_KEY = '<twój_klucz>'
streamlit run app.py
```

Uwaga: jeżeli nie ustawisz `OPENAI_API_KEY`, aplikacja wygeneruje raport bez sekcji rekomendacji lub doda informację, że klucz nie jest ustawiony.

Model:

- W UI dostępny jest selector modelu. Domyślnie wybrany jest `gpt-3.5-turbo` (najtańsza opcja).

.env i konfiguracja:

- Skopiuj `.env.example` do `.env` i uzupełnij `OPENAI_API_KEY` (nie commituj `.env`).
- Aplikacja automatycznie załaduje zmienne z `.env` przy starcie (używa `python-dotenv`).

Nowe pola raportu:

- `Nazwa aplikacji / dokumentu` — wpisz nazwę, pojawi się w nagłówku raportu i w nazwie pliku wynikowego.
- `Zakres testu` — lista stron/sekcji/działań testowych; każdy wiersz zostanie wypisany w raporcie jako punkt.
