import streamlit as st
st.markdown(
    '''<style>
    body, .main, .block-container {
        background: #fff !important;
        color: #222 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1976d2 !important;
        font-weight: bold !important;
        letter-spacing: 0.5px;
    }
    .stTextInput > div > input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background: #f7f7f7 !important;
        color: #222 !important;
        border: 2px solid #1976d2 !important;
        border-radius: 6px !important;
        font-size: 1.05em;
    }
    .stButton button {
        background: #1976d2 !important;
        color: #fff !important;
        border: 2px solid #ffd600 !important;
        border-radius: 6px !important;
        font-weight: bold;
        font-size: 1.08em;
        padding: 0.5em 1.2em;
        margin: 0.2em 0;
        transition: background 0.2s;
    }
    .stButton button:hover {
        background: #ffd600 !important;
        color: #1976d2 !important;
        border: 2px solid #1976d2 !important;
    }
    .stRadio div[role="radiogroup"] > div {
        background: #fff !important;
        color: #222 !important;
        border: 2px solid #1976d2 !important;
        border-radius: 6px !important;
        margin-bottom: 0.2em;
    }
    .stRadio label {
        color: #1976d2 !important;
        font-weight: bold;
    }
    /* Statusy WCAG */
    .stRadio div[role="radiogroup"] > div:nth-child(1) label { /* ✅ */
        background: #228B22 !important;
        color: #fff !important;
        border-radius: 4px;
        padding: 2px 10px;
    }
    .stRadio div[role="radiogroup"] > div:nth-child(2) label { /* ❌ */
        background: #C62828 !important;
        color: #fff !important;
        border-radius: 4px;
        padding: 2px 10px;
    }
    .stRadio div[role="radiogroup"] > div:nth-child(3) label { /* ⚠️ */
        background: #FFD600 !important;
        color: #222 !important;
        border-radius: 4px;
        padding: 2px 10px;
    }
    .stDownloadButton button {
        background: #ffd600 !important;
        color: #222 !important;
        border: 2px solid #1976d2 !important;
        border-radius: 6px !important;
        font-weight: bold;
        font-size: 1.08em;
        padding: 0.5em 1.2em;
        margin: 0.2em 0;
    }
    .stDownloadButton button:hover {
        background: #1976d2 !important;
        color: #fff !important;
        border: 2px solid #ffd600 !important;
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #888 !important;
    }
    .stAlert, .stSuccess, .stError, .stWarning {
        border-radius: 6px !important;
        font-size: 1.05em;
    }
    </style>''', unsafe_allow_html=True)
from docx import Document
from datetime import datetime
import calendar
from openai_client import generate_recommendations
import os
import tempfile
import json
import shutil
import time
from docx.shared import Inches
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Szablony kryteriów wg typu audytowanego pliku
wcag_templates = {
    "Dokument Word": [
        {
            "id": "1.1.1",
            "description": "Alternatywa w postaci tekstu dla treści nietekstowej",
            "long_description": "Każda treść nietekstowa (np. obraz, wykres, ikona) powinna mieć alternatywny opis tekstowy, który pozwala zrozumieć jej funkcję osobom korzystającym z czytników ekranu.",
            "example_test": "Sprawdź, czy wszystkie obrazy mają atrybut ALT opisujący ich funkcję. Otwórz dokument w czytniku ekranu i zweryfikuj, czy alternatywa jest czytelna i zrozumiała."
        },
        {
            "id": "1.2.1",
            "description": "Napisy dla mediów zmiennych w czasie (tylko audio)",
            "long_description": "Nagrania audio i wideo powinny mieć napisy lub transkrypcję, aby osoby niesłyszące mogły zrozumieć treść.",
            "example_test": "Odtwórz nagranie i sprawdź, czy dostępne są napisy lub transkrypcja."
        },
        {
            "id": "1.2.2",
            "description": "Napisy dla mediów zmiennych w czasie (wideo)",
            "long_description": "Nagrania wideo powinny mieć napisy rozszerzone, aby osoby niesłyszące mogły śledzić dialogi i dźwięki.",
            "example_test": "Odtwórz nagranie wideo i sprawdź, czy dostępne są napisy rozszerzone."
        },
        {
            "id": "1.2.4",
            "description": "Transkrypcja dla mediów zmiennych w czasie (wideo)",
            "long_description": "Treści wideo powinny mieć transkrypcję tekstową, aby osoby z niepełnosprawnościami mogły zapoznać się z treścią.",
            "example_test": "Sprawdź, czy do nagrania wideo dołączona jest transkrypcja tekstowa."
        },
        {
            "id": "1.3.1",
            "description": "Informacje i relacje",
            "long_description": "Struktura dokumentu powinna być logiczna, a relacje między elementami czytelne dla czytników ekranu.",
            "example_test": "Sprawdź nagłówki, listy, tabele – czy są poprawnie oznaczone i czytelne dla czytnika ekranu."
        },
        {
            "id": "1.3.2",
            "description": "Sekwencja sensowna",
            "long_description": "Kolejność prezentacji treści powinna być logiczna i zgodna z zamierzeniem autora.",
            "example_test": "Przejdź przez dokument tabulatorem i sprawdź, czy kolejność elementów jest sensowna."
        },
        {
            "id": "1.3.3",
            "description": "Charakterystyki sensoryczne",
            "long_description": "Instrukcje nie powinny opierać się wyłącznie na cechach zmysłowych (np. kolor, kształt).",
            "example_test": "Sprawdź, czy instrukcje nie odnoszą się tylko do koloru lub położenia, np. 'kliknij czerwony przycisk'."
        },
        {
            "id": "1.4.3",
            "description": "Kontrast (minimum)",
            "long_description": "Tekst i elementy graficzne powinny mieć odpowiedni kontrast względem tła, aby były czytelne dla osób słabowidzących.",
            "example_test": "Zmierz kontrast tekstu do tła (np. narzędziem online) – powinien wynosić co najmniej 4.5:1."
        },
        {
            "id": "1.4.4",
            "description": "Zmienność rozmiaru tekstu",
            "long_description": "Użytkownik powinien móc powiększyć tekst do 200% bez utraty czytelności lub funkcjonalności.",
            "example_test": "Powiększ tekst w przeglądarce/dokumencie i sprawdź, czy treść jest nadal czytelna."
        },
        {
            "id": "1.4.5",
            "description": "Obrazy tekstu",
            "long_description": "Tekst powinien być prezentowany jako tekst, nie jako obraz, chyba że jest to niezbędne (np. logo).",
            "example_test": "Sprawdź, czy teksty informacyjne nie są grafikami. Jeśli są, czy mają alternatywę tekstową."
        },
        {
            "id": "1.4.10",
            "description": "Przełączanie zawartości",
            "long_description": "Zawartość powinna być dostępna bez konieczności przewijania w poziomie na ekranach o szerokości 320px.",
            "example_test": "Otwórz dokument/stronę na wąskim ekranie i sprawdź, czy nie trzeba przewijać w poziomie."
        },
        {
            "id": "1.4.11",
            "description": "Kontrast elementów niestandardowych",
            "long_description": "Elementy interfejsu (np. przyciski, pola) powinny mieć kontrast co najmniej 3:1 względem tła.",
            "example_test": "Zmierz kontrast przycisków i pól formularza względem tła."
        },
        {
            "id": "1.4.12",
            "description": "Rozmiar tekstu w interfejsie",
            "long_description": "Odstępy między wierszami, akapitami, literami i wyrazami powinny być wystarczające dla czytelności.",
            "example_test": "Zmień odstępy w stylach CSS/dokumencie i sprawdź, czy treść jest czytelna."
        },
        {
            "id": "2.1.1",
            "description": "Obsługa klawiatury",
            "long_description": "Wszystkie funkcje powinny być dostępne z poziomu klawiatury, bez konieczności użycia myszy.",
            "example_test": "Przejdź przez dokument/stronę wyłącznie klawiaturą i sprawdź, czy można wykonać wszystkie operacje."
        },
        {
            "id": "2.1.2",
            "description": "Brak pułapek klawiaturowych",
            "long_description": "Fokus klawiatury nie powinien utknąć w żadnym elemencie – użytkownik musi móc go opuścić.",
            "example_test": "Przejdź tabulatorem przez wszystkie elementy i sprawdź, czy można opuścić każdy z nich."
        },
        {
            "id": "2.3.1",
            "description": "Trwałość błysków",
            "long_description": "Treści nie powinny zawierać elementów migających częściej niż 3 razy na sekundę, aby nie wywoływać ataków padaczki.",
            "example_test": "Sprawdź, czy na stronie/dokumencie nie ma animacji lub efektów migających powyżej 3 Hz."
        },
        {
            "id": "2.4.1",
            "description": "Możliwość pominięcia bloków",
            "long_description": "Użytkownik powinien mieć możliwość pominięcia powtarzających się bloków treści (np. menu).",
            "example_test": "Sprawdź, czy jest dostępny link lub mechanizm pomijania powtarzających się sekcji."
        },
        {
            "id": "2.4.3",
            "description": "Porządek fokusu",
            "long_description": "Kolejność przechodzenia fokusu powinna być logiczna i zgodna z zamierzeniem autora.",
            "example_test": "Przechodź tabulatorem przez elementy i sprawdź, czy kolejność jest sensowna."
        },
        {
            "id": "2.4.4",
            "description": "Cel linku (w kontekście)",
            "long_description": "Cel każdego linku powinien być jasny z samego tekstu lub kontekstu.",
            "example_test": "Sprawdź, czy linki mają zrozumiałe opisy, np. 'Więcej informacji' w kontekście."
        },
        {
            "id": "2.4.5",
            "description": "Wiele sposobów nawigacji",
            "long_description": "Powinno istnieć więcej niż jeden sposób na znalezienie strony lub sekcji (np. wyszukiwarka, mapa strony, menu).",
            "example_test": "Sprawdź, czy można dotrzeć do każdej sekcji na co najmniej dwa sposoby."
        },
        {
            "id": "2.4.6",
            "description": "Nagłówki i etykiety",
            "long_description": "Nagłówki i etykiety powinny jasno opisywać temat lub cel treści.",
            "example_test": "Sprawdź, czy nagłówki i etykiety są zrozumiałe i jednoznaczne."
        },
        {
            "id": "2.4.7",
            "description": "Widoczność fokusu",
            "long_description": "Fokus klawiatury powinien być zawsze widoczny podczas nawigacji.",
            "example_test": "Przechodź klawiaturą przez elementy i sprawdź, czy wskaźnik fokusu jest widoczny."
        },
        {
            "id": "3.1.1",
            "description": "Język strony",
            "long_description": "Język dokumentu/strony powinien być określony programowo, aby czytniki ekranu mogły go rozpoznać.",
            "example_test": "Sprawdź, czy w kodzie strony/dokumentu jest określony język (np. lang=\"pl\")."
        },
        {
            "id": "3.1.2",
            "description": "Język fragmentów",
            "long_description": "Język fragmentów tekstu różniących się od głównego powinien być oznaczony.",
            "example_test": "Sprawdź, czy cytaty, obce wyrażenia mają oznaczony język (np. lang=\"en\")."
        },
        {
            "id": "3.2.3",
            "description": "Spójność nawigacji",
            "long_description": "Powtarzające się mechanizmy nawigacji powinny być prezentowane w tej samej kolejności na wszystkich stronach.",
            "example_test": "Przejdź przez różne strony i sprawdź, czy menu, stopka są zawsze w tym samym miejscu."
        },
        {
            "id": "3.2.4",
            "description": "Spójność identyfikacji",
            "long_description": "Elementy o tej samej funkcji powinny być identyfikowane w ten sam sposób na wszystkich stronach.",
            "example_test": "Sprawdź, czy np. przycisk 'Wyślij' zawsze wygląda i działa tak samo."
        },
        {
            "id": "3.3.1",
            "description": "Identyfikacja błędów",
            "long_description": "Błędy wprowadzania danych powinny być jasno komunikowane użytkownikowi.",
            "example_test": "Wprowadź błędne dane w formularzu i sprawdź, czy pojawia się czytelny komunikat o błędzie."
        },
        {
            "id": "3.3.2",
            "description": "Sugestie dotyczące błędów",
            "long_description": "System powinien podpowiadać użytkownikowi, jak poprawić błędy w danych.",
            "example_test": "Wprowadź błędne dane i sprawdź, czy pojawia się sugestia poprawy."
        },
        {
            "id": "4.1.3",
            "description": "Status komunikatów",
            "long_description": "Komunikaty o stanie (np. sukces, błąd) powinny być dostępne dla technologii wspomagających.",
            "example_test": "Sprawdź, czy komunikaty o stanie są odczytywane przez czytnik ekranu."
        },
    ],
    "PDF": [
        {"id": "1.1.1", "description": "Alternatywa w postaci tekstu dla treści nietekstowej"},
        {"id": "1.2.1", "description": "Napisy dla mediów zmiennych w czasie (tylko audio)"},
        {"id": "1.2.2", "description": "Napisy dla mediów zmiennych w czasie (wideo)"},
        {"id": "1.2.4", "description": "Transkrypcja dla mediów zmiennych w czasie (wideo)"},
        {"id": "1.3.1", "description": "Informacje i relacje"},
        {"id": "1.3.2", "description": "Sekwencja sensowna"},
        {"id": "1.3.3", "description": "Charakterystyki sensoryczne"},
        {"id": "1.4.3", "description": "Kontrast (minimum)"},
        {"id": "1.4.4", "description": "Zmienność rozmiaru tekstu"},
        {"id": "1.4.5", "description": "Obrazy tekstu"},
        {"id": "1.4.10", "description": "Przełączanie zawartości"},
        {"id": "1.4.11", "description": "Kontrast elementów niestandardowych"},
        {"id": "1.4.12", "description": "Rozmiar tekstu w interfejsie"},
        {"id": "2.1.1", "description": "Obsługa klawiatury"},
        {"id": "2.1.2", "description": "Brak pułapek klawiaturowych"},
        {"id": "2.3.1", "description": "Trwałość błysków"},
        {"id": "2.4.1", "description": "Możliwość pominięcia bloków"},
        {"id": "2.4.3", "description": "Porządek fokusu"},
        {"id": "2.4.4", "description": "Cel linku (w kontekście)"},
        {"id": "2.4.5", "description": "Wiele sposobów nawigacji"},
        {"id": "2.4.6", "description": "Nagłówki i etykiety"},
        {"id": "2.4.7", "description": "Widoczność fokusu"},
        {"id": "3.1.1", "description": "Język strony"},
        {"id": "3.1.2", "description": "Język fragmentów"},
        {"id": "3.2.3", "description": "Spójność nawigacji"},
        {"id": "3.2.4", "description": "Spójność identyfikacji"},
        {"id": "3.3.1", "description": "Identyfikacja błędów"},
        {"id": "3.3.2", "description": "Sugestie dotyczące błędów"},
        {"id": "4.1.3", "description": "Status komunikatów"},
    ],
    "Strona WWW": [
        {"id": "1.1.1", "description": "Alternatywa w postaci tekstu dla treści nietekstowej"},
        {"id": "1.2.1", "description": "Napisy dla mediów zmiennych w czasie (tylko audio)"},
        {"id": "1.2.2", "description": "Napisy dla mediów zmiennych w czasie (wideo)"},
        {"id": "1.2.4", "description": "Transkrypcja dla mediów zmiennych w czasie (wideo)"},
        {"id": "1.3.1", "description": "Informacje i relacje"},
        {"id": "1.3.2", "description": "Sekwencja sensowna"},
        {"id": "1.3.3", "description": "Charakterystyki sensoryczne"},
        {"id": "1.4.3", "description": "Kontrast (minimum)"},
        {"id": "1.4.4", "description": "Zmienność rozmiaru tekstu"},
        {"id": "1.4.5", "description": "Obrazy tekstu"},
        {"id": "1.4.10", "description": "Przełączanie zawartości"},
        {"id": "1.4.11", "description": "Kontrast elementów niestandardowych"},
        {"id": "1.4.12", "description": "Rozmiar tekstu w interfejsie"},
        {"id": "2.1.1", "description": "Obsługa klawiatury"},
        {"id": "2.1.2", "description": "Brak pułapek klawiaturowych"},
        {"id": "2.3.1", "description": "Trwałość błysków"},
        {"id": "2.4.1", "description": "Możliwość pominięcia bloków"},
        {"id": "2.4.3", "description": "Porządek fokusu"},
        {"id": "2.4.4", "description": "Cel linku (w kontekście)"},
        {"id": "2.4.5", "description": "Wiele sposobów nawigacji"},
        {"id": "2.4.6", "description": "Nagłówki i etykiety"},
        {"id": "2.4.7", "description": "Widoczność fokusu"},
        {"id": "3.1.1", "description": "Język strony"},
        {"id": "3.1.2", "description": "Język fragmentów"},
        {"id": "3.2.3", "description": "Spójność nawigacji"},
        {"id": "3.2.4", "description": "Spójność identyfikacji"},
        {"id": "3.3.1", "description": "Identyfikacja błędów"},
        {"id": "3.3.2", "description": "Sugestie dotyczące błędów"},
        {"id": "4.1.3", "description": "Status komunikatów"},
    ],
}

st.title("AudytAI - Kreator raportów dostępności WCAG 2.1")


# Pola metadanych raportu
st.header("Dane audytu")
# Szkice: folder przechowujący robocze wersje raportów (docx + json)
draft_dir = os.path.join(os.getcwd(), "szkice")
os.makedirs(draft_dir, exist_ok=True)
draft_files = [f for f in os.listdir(draft_dir) if f.endswith('.json')]
selected_draft = st.selectbox("Wybierz szkic audytu", ["(brak)"] + draft_files, index=0, key="selected_draft")
if st.button("Wczytaj szkic") and selected_draft != "(brak)":
    try:
        with open(os.path.join(draft_dir, selected_draft), 'r', encoding='utf-8') as df:
            data = json.load(df)
        # Ustaw wartości w session_state przed renderowaniem widgetów
        st.session_state['doc_type'] = data.get('doc_type', st.session_state.get('doc_type', 'Dokument Word'))
        st.session_state['doc_version'] = data.get('doc_version', '')
        st.session_state['audit_author'] = data.get('audit_author', '')
        st.session_state['browser_version'] = data.get('browser_version', '')
        st.session_state['app_name'] = data.get('app_name', '')
        st.session_state['tested_scope'] = data.get('tested_scope', '')
        # Load date into pickers
        try:
            d = datetime.fromisoformat(data.get('audit_date'))
            # Set pickers keys
            st.session_state['year_picker'] = d.year
            # month picker stores polish month name
            polish_months = [
                "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
                "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"
            ]
            st.session_state['month_picker'] = polish_months[d.month - 1]
            st.session_state['day_picker'] = d.day
        except Exception:
            pass
        # Responses and notes
        for k, v in data.get('responses', {}).items():
            st.session_state[k] = v
        for k, v in data.get('notes', {}).items():
            st.session_state[f"note_{k}"] = v
        st.rerun()
    except Exception as e:
        st.error(f"Błąd podczas wczytywania szkicu: {e}")

doc_type = st.selectbox("Wybierz typ pliku lub strony", ["Dokument Word", "PDF", "Strona WWW"], key='doc_type')
doc_version = st.text_input("Wersja dokumentu", value="", key='doc_version')
audit_author = st.text_input("Autor audytu", value="", key='audit_author')
browser_version = st.text_input("Wersja przeglądarki", value="", help="Np. Chrome 124.0.6367.61, Firefox 125.0.1", key='browser_version')
# Nowe pole: Narzędzia
tools_used = st.text_input("Narzędzia użyte w audycie", value="", help="Np. Wave, axe, NVDA, JAWS, Lighthouse", key='tools_used')
import locale
# Spróbuj kilku wariantów polskiej lokalizacji (Linux/macOS i Windows)
for loc in ("pl_PL.UTF-8", "pl_PL", "Polish_Poland.1250"):
    try:
        locale.setlocale(locale.LC_TIME, loc)
        break
    except Exception:
        continue
# Zamiast polegać na języku przeglądarki, wymuszamy picker z polskimi nazwami miesięcy
st.markdown("**Data audytu**")
today = datetime.today()
col_day, col_month, col_year = st.columns([1, 2, 1])
polish_months = [
    "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
    "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"
]
# Ustaw domyślne wartości pickerów na dzisiejszą datę, jeśli nie są już ustawione (np. po wczytaniu szkicu)
if 'year_picker' not in st.session_state:
    st.session_state['year_picker'] = today.year
if 'month_picker' not in st.session_state:
    st.session_state['month_picker'] = polish_months[today.month - 1]
if 'day_picker' not in st.session_state:
    st.session_state['day_picker'] = today.day
# Zakres lat: od -5 do +5 względem bieżącego roku
years = list(range(today.year - 5, today.year + 6))
selected_year = col_year.selectbox("Rok", years, key="year_picker")
selected_month_name = col_month.selectbox("Miesiąc", polish_months, key="month_picker")
month_idx = polish_months.index(selected_month_name) + 1
# Dni zależą od miesiąca i roku (obsługa lutego/lat przestępnych)
last_day = calendar.monthrange(selected_year, month_idx)[1]
days = list(range(1, last_day + 1))
selected_day = col_day.selectbox("Dzień", days, key="day_picker")
# Zbuduj obiekt datetime na podstawie wyboru
try:
    audit_date = datetime(selected_year, month_idx, selected_day)
except Exception:
    # Bezpieczny fallback na dziś
    audit_date = datetime.today()


# Ręczne formatowanie polskiej daty (odmienione miesiące)
polish_months_gen = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
]
def format_polish_date(dt):
    return f"{dt.day} {polish_months_gen[dt.month-1]} {dt.year}"

formatted = format_polish_date(audit_date)
st.markdown(f"**Wybrana data audytu:** {formatted}")

# ustaw kryteria na podstawie wybranego typu dokumentu
wcag_criteria = wcag_templates.get(doc_type, wcag_templates["Dokument Word"]) 

st.header("Lista wytycznych WCAG")
responses = {}

# Metadane raportu: nazwa aplikacji/dokumentu i zakres stron/testów
app_name = st.text_input("Nazwa aplikacji / dokumentu", value="", help="Np. 'Strona główna MySite' lub 'Dokument X'", key='app_name')
tested_scope = st.text_area("Zakres testu (np. lista stron, sekcji)", value="", help="Wypisz adresy URL lub numery stron, które były testowane, oddzielone nową linią", key='tested_scope')

# Wybór modelu (domyślnie najtańsza opcja)
model_choice = st.selectbox(
    "Wybierz model (domyślnie MOCK)",
    ("gpt-3.5-turbo", "gpt-4", "MOCK"),
    index=2,
    help="gpt-3.5-turbo — najtańsza opcja; MOCK — tryb developerski bez wywołań OpenAI",
    key='model_choice'
)

# Debug: pokaż wygenerowane rekomendacje w UI (przed zapisem do pliku)
debug_show_recs = st.checkbox(
    "Pokaż rekomendacje (AI) w aplikacji po generowaniu",
    value=True,
    help="Zaznacz, aby zobaczyć tekst rekomendacji w UI (przydatne do debugowania)")

notes = {}
uploads = {}
for crit in wcag_criteria:
    c1, c2 = st.columns([2, 5])
    # Wytyczna z większą czcionką
    c1.markdown(f"<span style='font-size:1.2em;font-weight:bold'>{crit['id']} - {crit['description']}</span>", unsafe_allow_html=True)
    responses[crit["id"]] = c1.radio(
        "Status wytycznej:",
        ("✅ Spełnione", "❌ Niespełnione", "⚠️ Nie dotyczy"),
        key=crit["id"]
    )
    # Modal info button
    show_info = c1.button(f"Co to znaczy?", key=f"info_{crit['id']}")
    if show_info:
        st.session_state[f"modal_{crit['id']}"] = True
    # Modal close logic: handle before rendering modal content
    modal_key = f"modal_{crit['id']}"
    close_key = f"close_{crit['id']}"
    # Obsługa zamknięcia modala na początku pętli
    if st.session_state.get(modal_key, False) and st.session_state.get(close_key, False):
        st.session_state[modal_key] = False
        st.session_state[close_key] = False

    # Renderowanie modala
    if st.session_state.get(modal_key, False):
        st.markdown(f"### {crit['id']} - {crit['description']}")
        st.info(f"Opis: {crit.get('long_description', crit.get('description', ''))}")
        example = crit.get('example_test', None)
        if example:
            st.markdown(f"**Jak testować:** {example}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Zamknij", key=close_key)
    # Notatka i upload w jednej kolumnie, labelki powiększone (zawsze widoczne)
    required = responses.get(crit["id"]) == "❌ Niespełnione"
    # Use full phrase "Notatka do wytycznej <id>" for clarity
    label = f"<span style='font-size:1.05em;font-weight:bold'>Notatka do wytycznej {crit['id']}{' <span style=\'color:red\'>*</span>' if required else ''}</span>"
    c2.markdown(label, unsafe_allow_html=True)
    notes[crit["id"]] = c2.text_area(
        f"Notatka do wytycznej {crit['id']}", value="", key=f"note_{crit['id']}", height=180,
        help="Wklej opis, kontekst, kroki reprodukcji. Możesz też wkleić linki lub krótki kod.",
        placeholder=f"Notatka do {crit['id']}: opisz problem, kroki reprodukcji, kontekst (wymagane jeśli kryterium nie jest niespełnione)."
    )
    # Try to use the newer 'button_label' arg when available; fall back if Streamlit version is older
    try:
        uploads[crit["id"]] = c2.file_uploader(
            "Wybierz pliki (zrzuty ekranu, zdjęcia)", type=["png", "jpg", "jpeg"], key=f"img_{crit['id']}",
            label_visibility="visible",
            help="Dodaj pliki, które pokazują problem lub potwierdzają spełnienie wytycznej.",
            accept_multiple_files=True,
            button_label="Dodaj plik"
        )
    except TypeError:
        # Older Streamlit versions don't support button_label
        uploads[crit["id"]] = c2.file_uploader(
            "Wybierz pliki (zrzuty ekranu, zdjęcia)", type=["png", "jpg", "jpeg"], key=f"img_{crit['id']}",
            label_visibility="visible",
            help="Dodaj pliki, które pokazują problem lub potwierdzają spełnienie wytycznej.",
            accept_multiple_files=True
        )
import pandas as pd

if 'report_ready' not in st.session_state:
    st.session_state['report_ready'] = False
if 'report_filename' not in st.session_state:
    st.session_state['report_filename'] = None

if st.button("Generuj raport Word"):
    # Walidacja: wymagalność notatki dla niespełnionych kryteriów
    missing_notes = []
    for crit in wcag_criteria:
        if responses.get(crit["id"]) == "❌ Niespełnione" and not notes.get(crit["id"]):
            missing_notes.append(crit["id"])
    if missing_notes:
        st.warning(f"Dla wytycznych oznaczonych jako niespełnione wymagane jest uzupełnienie notatki: {', '.join(missing_notes)}")
    else:
        doc = Document()
        # Wyśrodkowany tytuł jako nagłówek (Heading 1), bez nawiasów kwadratowych
        if app_name:
            title = f"Raport z audytu WCAG {app_name}"
        else:
            title = "Raport z audytu WCAG"
        # Tytuł jako zwykły paragraf, wyśrodkowany, pogrubiony, powiększony
        p = doc.add_paragraph()
        run = p.add_run(title)
        run.bold = True
        run.font.size = doc.styles['Heading 1'].font.size
        p.alignment = 1  # 0=left, 1=center, 2=right
        # Dodaj odstęp po tytule
        doc.add_paragraph("")
        # Wyboldowane metadane
        meta_items = [
            ("Data audytu", formatted),
            ("Autor audytu", audit_author),
            ("Wersja dokumentu", doc_version),
            ("Nazwa aplikacji / dokumentu", app_name),
            ("Typ audytowanego dokumentu", doc_type),
            ("Wersja przeglądarki", browser_version),
            ("Narzędzia użyte w audycie", tools_used)
        ]
        for label, value in meta_items:
            if value:
                para = doc.add_paragraph()
                run_label = para.add_run(f"{label}: ")
                run_label.bold = True
                para.add_run(str(value))
        if tested_scope:
            para = doc.add_paragraph()
            run_label = para.add_run("Zakres testu:")
            run_label.bold = True
            for line in [l.strip() for l in tested_scope.splitlines() if l.strip()]:
                doc.add_paragraph(line)
        doc.add_paragraph("")
        from docx.shared import Inches, Cm
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['ID', 'Nazwa wytycznej', 'Status', 'Uwagi', 'Załączniki']
        for i, h in enumerate(headers):
            hdr_cells[i].text = h
            for paragraph in hdr_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.bold = True
        # Wymuś minimalną szerokość kolumny ID (1 cm) na wszystkich komórkach tej kolumny
        try:
            for row in table.rows:
                cell = row.cells[0]
                cell.width = Cm(1)
        except Exception:
            pass
        for crit in wcag_criteria:
            row_cells = table.add_row().cells
            row_cells[0].text = crit["id"]
            row_cells[1].text = crit["description"]
            row_cells[2].text = responses[crit["id"]]
            row_cells[3].text = notes.get(crit["id"], "")
            imgs = uploads.get(crit["id"]) or []
            if imgs:
                temp_files = [] if 'temp_files' not in locals() else temp_files
                for up in imgs:
                    try:
                        suffix = os.path.splitext(up.name)[1] if hasattr(up, "name") else ".png"
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                        tf.write(up.getbuffer())
                        tf.close()
                        temp_files.append(tf.name)
                        paragraph = row_cells[4].add_paragraph()
                        run = paragraph.add_run()
                        run.add_picture(tf.name, width=Inches(1.5))
                    except Exception:
                        row_cells[4].add_paragraph(f"(Błąd przy dodawaniu obrazka {up.name})")
            else:
                row_cells[4].text = ""
        # Po utworzeniu całej tabeli wymuś szerokość kolumny ID na 0.8 cm
        # Ustal szerokości wszystkich kolumn dla estetyki
        try:
            for row in table.rows:
                row.cells[0].width = Cm(1)   # ID
                row.cells[1].width = Cm(4)   # Nazwa wytycznej
                row.cells[2].width = Cm(4)   # Status (poszerzona)
                row.cells[3].width = Cm(4.5) # 
                row.cells[4].width = Cm(3)   # Załączniki
        except Exception:
            pass
        # Dodaj sekcję rekomendacji na końcu
        doc.add_page_break()
        doc.add_heading("Rekomendacje AI dla niespełnionych kryteriów", level=2)
        # Jeśli są rekomendacje, dodaj je
        if 'recs' in locals() and recs:
            for crit in wcag_criteria:
                cid = crit["id"]
                rec = None
                if isinstance(recs, dict):
                    rec = recs.get(cid) or recs.get("_combined")
                else:
                    rec = None
                if rec:
                    doc.add_heading(f"{cid} - {crit['description']}", level=3)
                    doc.add_paragraph("Rekomendacja:")
                    for l in str(rec).splitlines():
                        l = l.strip()
                        if l:
                            if l.startswith("-") or l.startswith("•") or l[:2].isdigit():
                                for sub in l.split("- "):
                                    sub = sub.strip()
                                    if sub:
                                        doc.add_paragraph(sub)
                            else:
                                doc.add_paragraph(l)
        # ... rekomendacje AI i dalsza logika ...
        # Zapis dokumentu
        def _slugify(name: str) -> str:
            import re
            s = name.strip().lower()
            s = re.sub(r"[^a-z0-9]+", "_", s)
            s = re.sub(r"_+", "_", s).strip("_")
            return s or "report"
        date_str = datetime.today().strftime('%Y-%m-%d')
        if app_name:
            safe = _slugify(app_name)
            filename = f"Raport_WCAG_{safe}_{date_str}.docx"
        else:
            filename = f"Raport_WCAG_{date_str}.docx"
        doc.save(filename)
        st.session_state['report_ready'] = True
        st.session_state['report_filename'] = filename

# Przycisk pobierania raportu zawsze widoczny, jeśli raport został wygenerowany
if st.session_state.get('report_ready') and st.session_state.get('report_filename'):
    try:
        filesize = None
        with open(st.session_state['report_filename'], "rb") as f:
            data = f.read()
            filesize = len(data)
            st.download_button("Pobierz raport", data=data, file_name=st.session_state['report_filename'], mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        st.success(f"Raport wygenerowany: {st.session_state['report_filename']} ({filesize} bajtów)")
    except Exception as e:
        st.error(f"Utworzono plik, ale nie udało się przygotować przycisku pobierania: {e}")
        api_key = os.getenv("OPENAI_API_KEY")
        # Build notes_for_ai: include notes and indication of screenshots
        notes_for_ai = {}
        for cid in responses.keys():
            note = notes.get(cid, "")
            # Do AI przekazuj tylko tekstową notatkę, bez nazw plików
            notes_for_ai[cid] = note

        # If model_choice is MOCK, do not require API key
        if model_choice == "MOCK" or api_key:
            with st.spinner("Generuję rekomendacje..."):
                recs = generate_recommendations(responses, notes=notes_for_ai, model=model_choice)

            # Preview in UI
            if debug_show_recs and recs:
                st.subheader("Podgląd wygenerowanych rekomendacji")
                try:
                    st.json(recs)
                except Exception:
                    st.write(recs)

            if model_choice != "MOCK":
                st.info(f"Użyty model: {model_choice} — pamiętaj, że wywołania do OpenAI są płatne.")
        else:
            st.warning("Brak ustawionego OPENAI_API_KEY — ustaw zmienną środowiskową lub wybierz tryb MOCK.")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        st.error(f"Błąd podczas generowania rekomendacji: {e}")
        st.code(tb)

