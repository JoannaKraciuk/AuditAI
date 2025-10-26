## Szybkie instrukcje dla AI (agentów kodujących)

Ten projekt to prosty prototyp Streamlit do generowania raportów WCAG w formacie Word.
Skoncentruj się na zmianach w `app.py` — to jedyne główne źródło aplikacji.

- Główne biblioteki: `streamlit`, `python-docx`.
- Uruchomienie deweloperskie (PowerShell):

  ```powershell
  .\venv\Scripts\Activate.ps1
  pip install streamlit python-docx
  streamlit run app.py
  ```

Kluczowe pliki i wzorce

- `app.py` — UI Streamlit i logika tworzenia raportu. Sprawdź:
  - `wcag_criteria` — lista słowników {"id","description"} definiująca check-listę.
  - Radio widgety tworzą mapę `responses` wykorzystywaną do budowy tabeli w dokumencie.
  - Generowanie pliku Word przy użyciu `Document()` i `add_table()`; plik zapisywany jako `Raport_WCAG.docx`.

Typowe zmiany, które mogą być wymagane

- Dodać integrację z OpenAI: w handlerze przycisku `Generuj raport Word` wstaw wywołanie API, które wygeneruje sekcję "Rekomendacje". Przykładowy punkt integracji: za `doc.add_paragraph("Tutaj pojawią się rekomendacje...")` wstaw funkcję, która stworzy tekst na podstawie `responses`.
- Rozszerzyć `wcag_criteria` — łatwe, bo to pojedyncza lista w `app.py`.
- Zmienić format eksportu: modyfikuj logikę `table` i pola zapisywane do pliku.

Konwencje projektowe (wyciągalne z kodu)

- UI jest jednoplatformowy: cały przepływ jest w `app.py` (brak modularizacji). Wprowadzaj nowe funkcje w osobnych modułach tylko jeśli dodajesz testy / poprawiasz strukturę.
- Pliki wynikowe: stała nazwa `Raport_WCAG.docx` — jeśli dodajesz wersjonowanie lub nazwy dynamiczne, upewnij się, że UI umożliwia pobranie nowej nazwy.

Debug i testy

- Brak istniejącej konfiguracji testów; szybkie sprawdzenie: uruchom Streamlit lokalnie i kliknij "Generuj raport Word".
- Sprawdź, że `venv` zawiera wymagane pakiety; jeśli nie ma `requirements.txt`, dodaj go przy zmianach.

Co NIE zmieniać bez testu manualnego

- Nie zmieniaj bezpośrednio struktury `wcag_criteria` — UI mapuje ją przez `key=crit['id']`.
- Nie usuwaj bez sprawdzenia zapisu pliku: `doc.save(filename)` znajduje się w handlerze, stąd zależy od tego download button w Streamlit.

Gdzie dodać więcej kontekstu

- Jeśli chcesz zintegrować OpenAI, dodaj plik `openai_client.py` i dokumentuj kluczowe funkcje w README; w instrukcjach Copilot dodaj jednozdaniowe komentarze pokazujące gdzie w `app.py` wstawić wywołanie.

Jeśli chcesz, mogę: 1) wstawić przykład integracji z OpenAI (mały wrapper i przykład użycia w `app.py`), 2) dodać `requirements.txt`, 3) rozdzielić logikę eksportu do `export.py`.

-- koniec instrukcji --
