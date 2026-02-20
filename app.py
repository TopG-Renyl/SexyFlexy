import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Načtení klíče pro lokální testování
load_dotenv()

# Nastavení vzhledu stránky v prohlížeči
st.set_page_config(page_title="SexyFlexy", page_icon="🍳")

# --- KONFIGURACE API ---
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    st.error("Chyba: API klíč nebyl nalezen! Zkontroluj soubor .env.")
    st.stop() # Zastaví vykreslování stránky

URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

def nacti_znalosti():
    """Načte data ze souboru, pokud existuje. Slouží jako kontext pro chatbota."""
    if os.path.exists("moje_data.txt"):
        with open("moje_data.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "Data nenalezena."

# Připravíme instrukce
data_z_txt = nacti_znalosti()
instrukce = # PŘÍPRAVA INSTRUKCÍ
data_z_txt = nacti_znalosti()
instrukce = f"Jsi SexyFlexy, expert na simulační software FlexSim. Vysvětluj jako šéfkuchař přes kuchyni. TVÁ DATA: {data_z_txt}. Předpokládej, že všechny dotazy (např. crane, queue, procesy) se týkají FlexSimu.
Teprve když je dotaz úplně mimo (např. recept na pizzu nebo počasí), řekni: 'Tohle není z FlexSimu.' Piš stručně, bez emoji."

def posli_zpravu(text, historie):
    """Sestaví payload a odešle dotaz na Google Gemini API."""
    messages = []
    
    # Do zprávy pro API vložíme historii z paměti Streamlitu
    for h in historie:
        messages.append(h)
        
    messages.append({"role": "user", "parts": [{"text": text}]})

    payload = {
        "systemInstruction": {
            "parts": [{"text": instrukce}]
        },
        "contents": messages,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        res_json = response.json()
        try:
            casti_odpovedi = res_json['candidates'][0]['content']['parts']
            kompletni_text = "".join([cast.get('text', '') for cast in casti_odpovedi])
            return kompletni_text.strip()
        except KeyError:
            return "Bot neodpověděl ve správném formátu, zkus to znovu."
    else:
        return f"Chyba {response.status_code}: {response.text}"

# --- HLAVNÍ WEB ---

st.title("🍳 SexyFlexy: Expert na FlexSim")
st.write("Zeptej se mě na cokoliv ohledně optimalizace a simulace ve FlexSimu!")

# 1. Inicializace paměti: Pokud uživatel přijde na stránku poprvé, vytvoříme mu prázdnou historii
if "historie" not in st.session_state:
    st.session_state.historie = []

# 2. Vykreslení historie: Projdeme paměť a zobrazíme předchozí zprávy na obrazovce
for zprava in st.session_state.historie:
    # Upravíme název role, aby to Streamlit správně zobrazil ("user" nebo "assistant")
    vykreslovaci_role = "user" if zprava["role"] == "user" else "assistant"
    with st.chat_message(vykreslovaci_role):
        st.markdown(zprava["parts"][0]["text"])

# 3. Pole pro zadání textu: Tohle nahrazuje náš starý input()
uzivatel_text = st.chat_input("Napiš svůj dotaz sem...")

# 4. Co se stane, když uživatel odešle zprávu
if uzivatel_text:
    # A. Zobrazíme zprávu uživatele na webu
    with st.chat_message("user"):
        st.markdown(uzivatel_text)
    
    # B. Získáme odpověď od bota (předáme mu historii z paměti Streamlitu)
    with st.spinner("SexyFlexy vaří odpověď..."): # Ukáže se hezké načítací kolečko
        odpoved = posli_zpravu(uzivatel_text, st.session_state.historie)
        
    # C. Zobrazíme odpověď bota na webu
    with st.chat_message("assistant"):
        st.markdown(odpoved)
        
    # D. Uložíme obě zprávy do paměti (ve formátu pro Google API), aby si je bot pamatoval do dalšího kola
    st.session_state.historie.append({"role": "user", "parts": [{"text": uzivatel_text}]})

    st.session_state.historie.append({"role": "model", "parts": [{"text": odpoved}]})
