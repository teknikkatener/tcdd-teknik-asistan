import streamlit as st

import requests

import base64

import os

import time



# --- 1. AYARLAR (SECRETS.TOML'DAN ÇEKER) ---

# Dosyayı yüklediğiniz için artık doğrudan st.secrets içinden okuyoruz

try:

    API_KEY = st.secrets["API_KEY"]

except Exception:

    st.error("secrets.toml dosyası veya içindeki API_KEY bulunamadı!")

    st.stop()



# Model ismi ve URL yapısı (Hiç dokunulmadı)

MODEL_ADI = "models/gemini-2.5-flash-lite" 

URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ADI}:generateContent?key={API_KEY}"



st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")



# --- 2. TASARIM VE OTURUM YÖNETİMİ ---

if "all_chats" not in st.session_state:

    st.session_state.all_chats = {} # Tüm geçmiş sohbetler

if "current_chat_id" not in st.session_state:

    st.session_state.current_chat_id = "Sohbet 1"

    st.session_state.all_chats["Sohbet 1"] = []



# CSS

st.markdown("""

    <style>

    .tcdd-title { color: #d32f2f; font-size: 40px; font-weight: 800; text-align: center; margin-bottom: 20px; }

    [data-testid="stSidebar"] { background-color: #f1f3f5; border-right: 1px solid #ddd; }

    .stChatInputContainer { width: 85% !important; margin: 0 auto !important; }

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



# --- 4. SOL PANEL (GEÇMİŞ VE YENİ SOHBET) ---

with st.sidebar:

    st.markdown("### 🚆 TCDD TEKNİK")

    

    if st.button("➕ Yeni Sohbet", use_container_width=True):

        new_id = f"Sohbet {len(st.session_state.all_chats) + 1}"

        st.session_state.all_chats[new_id] = []

        st.session_state.current_chat_id = new_id

        st.rerun()



    st.markdown("---")

    st.markdown("📂 **Geçmiş Sohbetler**")

    for chat_id in list(st.session_state.all_chats.keys()):

        if st.button(f"💬 {chat_id}", key=f"btn_{chat_id}", use_container_width=True):

            st.session_state.current_chat_id = chat_id

            st.rerun()



    st.markdown("---")

    st.markdown("📸 **Görsel Analiz**")

    img_file = st.file_uploader("Fotoğraf Yükle", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

    if img_file:

        st.image(img_file, caption="Hazır", use_container_width=True)



# --- 5. ANA EKRAN ---

st.markdown(f"<div class='tcdd-title'>TCDD Teknik - {st.session_state.current_chat_id}</div>", unsafe_allow_html=True)



# Mevcut Sohbet Geçmişi

current_messages = st.session_state.all_chats[st.session_state.current_chat_id]

for msg in current_messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])



# --- 6. SORU VE ANALİZ ---

if prompt := st.chat_input("Teknik sorunuzu yazın..."):

    # Mesajı ekle ve göster

    current_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):

        st.markdown(prompt)



    with st.chat_message("assistant"):

        with st.spinner("Bilgi bankası ve görsel inceleniyor..."):

            

            # Veri Paketleme

            payload_parts = [{"text": "Sen TCDD Teknik uzmanısın. Belgeleri ve varsa fotoğrafı analiz et."}]

            payload_parts.append({"text": f"Soru: {prompt}"})

            

            # PDF'leri sadece ihtiyaç olduğunda ekle

            pdf_docs = load_docs()

            for d in pdf_docs:

                payload_parts.append({"inline_data": d})

            

            # Fotoğraf varsa ekle

            if img_file:

                img_b64 = base64.b64encode(img_file.getvalue()).decode()

                payload_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})



            # API Çağrısı

            try:

                response = requests.post(URL, json={"contents": [{"parts": payload_parts}]}, timeout=30)

                res_json = response.json()

                

                if 'candidates' in res_json:

                    ans = res_json['candidates'][0]['content']['parts'][0]['text']

                    st.markdown(ans)

                    current_messages.append({"role": "assistant", "content": ans})

                else:

                    err = res_json.get('error', {}).get('message', 'Bilinmeyen hata.')

                    st.error(f"Analiz Hatası: {err}")

            except Exception as e:

                st.error(f"Bağlantı zaman aşımına uğradı. Dosyalar çok büyük olabilir. Hata: {e}")
