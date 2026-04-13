import streamlit as st
import requests
import base64
import os
import time

# --- 1. AYARLAR ---
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("secrets.toml dosyası veya içindeki API_KEY bulunamadı!")
    st.stop()

MODEL_ADI = "models/gemini-2.5-flash-lite" 
URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. TASARIM VE SOHBET YÖNETİMİ ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"Sohbet 1": []} 
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Sohbet 1"

st.markdown("""
    <style>
    .tcdd-title { color: #d32f2f; font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    
    /* Butonları düz yazı ve + şeklinde yapma */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #444 !important;
        text-align: left !important;
        padding: 5px 0px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        color: #d32f2f !important;
        background: none !important;
    }
    /* Silme butonu için özel stil */
    .delete-btn { color: #ff4b4b !important; opacity: 0.5; }
    .delete-btn:hover { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BİLGİ BANKASI ---
@st.cache_data
def load_docs():
    docs = []
    folder = "bilgi_bankasi"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith(".pdf"):
                with open(os.path.join(folder, f), "rb") as file:
                    docs.append({"mime_type": "application/pdf", "data": base64.b64encode(file.read()).decode()})
    return docs

# --- 4. SOL PANEL (YALIN TASARIM) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #d32f2f;'>🚆 TCDD</h2>", unsafe_allow_html=True)
    
    if st.button("Yeni Sohbet +", use_container_width=True):
        new_id = f"Sohbet {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("📂 **Geçmiş Sohbetler**")
    
    # Sohbet Listesi ve Silme İşlemi
    for chat_id in list(st.session_state.all_chats.keys()):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(f"💬 {chat_id[:15]}", key=f"view_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                if len(st.session_state.all_chats) > 1:
                    del st.session_state.all_chats[chat_id]
                    st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]
                    st.rerun()
                else:
                    st.session_state.all_chats = {"Sohbet 1": []}
                    st.session_state.current_chat_id = "Sohbet 1"
                    st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("Görsel Analiz", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- 5. ANA EKRAN ---
st.markdown(f"<div class='tcdd-title'>TCDD Teknik - {st.session_state.current_chat_id}</div>", unsafe_allow_html=True)

current_messages = st.session_state.all_chats.get(st.session_state.current_chat_id, [])
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. SORU VE ANALİZ ---
if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("İnceleniyor..."):
            
            # --- ÖZEL KİMLİK FİLTRESİ ---
            test_prompt = prompt.lower().replace(" ", "")
            kimlik_sorulari = ["kimyaptı", "kimtasarladı", "senikim", "kimtarafından", "yapımcın"]
            
            if any(q in test_prompt for q in kimlik_sorulari):
                ans = "Beni **Semi Özcan** tasarladı ve TCDD teknik sistemlerini analiz etmem için geliştirdi."
                st.markdown(ans)
                current_messages.append({"role": "assistant", "content": ans})
            else:
                # Teknik Akış (Hiç bozulmadı)
                sistem_talimati = "Sen TCDD Teknik uzmanısın. Belgeleri analiz et ve teknik cevaplar ver."
                payload_parts = [{"text": sistem_talimati}, {"text": f"Soru: {prompt}"}]
                
                pdf_docs = load_docs()
                for d in pdf_docs:
                    payload_parts.append({"inline_data": d})
                
                if img_file:
                    img_b64 = base64.b64encode(img_file.getvalue()).decode()
                    payload_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

                try:
                    response = requests.post(URL, json={"contents": [{"parts": payload_parts}]}, timeout=30)
                    res_json = response.json()
                    if 'candidates' in res_json:
                        ans = res_json['candidates'][0]['content']['parts'][0]['text']
                        st.markdown(ans)
                        current_messages.append({"role": "assistant", "content": ans})
                    else:
                        st.error("Cevap alınamadı, API anahtarını kontrol edin.")
                except Exception as e:
                    st.error(f"Hata: {e}")
