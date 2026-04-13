import streamlit as st
import requests
import base64
import os
import time

# --- 1. AYARLAR (SECRETS.TOML'DAN ÇEKER) ---
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("secrets.toml dosyası veya içindeki API_KEY bulunamadı!")
    st.stop()

MODEL_ADI = "models/gemini-2.5-flash-lite" 
URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. TASARIM VE OTURUM YÖNETİMİ ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {} 
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Yeni Sohbet"
    st.session_state.all_chats["Yeni Sohbet"] = []

# CSS - Tam istediğiniz sade tasarım
st.markdown("""
    <style>
    .tcdd-title { color: #d32f2f; font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 10px; }
    .bar-text { color: #d32f2f; font-weight: 700; text-align: center; margin-bottom: 5px; opacity: 0.8; }
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
    }
    div.stButton > button:hover {
        color: #d32f2f !important;
        text-decoration: none !important;
    }
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

# --- 4. SOL PANEL (YAZI VE + FORMATI) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #d32f2f;'>🚆 TCDD</h2>", unsafe_allow_html=True)
    
    if st.button("Yeni Sohbet +", use_container_width=True):
        new_id = f"Yeni Sohbet {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("📂 **Geçmiş Sohbetler +**")
    for chat_id in list(st.session_state.all_chats.keys()):
        if st.button(f"💬 {chat_id}", key=f"btn_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("Fotoğraf Yükle", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- 5. ANA EKRAN ---
st.markdown(f"<div class='tcdd-title'>{st.session_state.current_chat_id}</div>", unsafe_allow_html=True)

# Mesaj Geçmişini Göster
current_messages = st.session_state.all_chats[st.session_state.current_chat_id]
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. SORU VE ANALİZ ---
st.markdown("<div class='bar-text'>TCDD Teknik</div>", unsafe_allow_html=True) # Soru barının üstündeki yazı

if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    
    # Otomatik Başlıklandırma: İlk mesaj ise başlığı güncelle
    if not current_messages and st.session_state.current_chat_id.startswith("Yeni Sohbet"):
        new_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.all_chats[new_title] = st.session_state.all_chats.pop(st.session_state.current_chat_id)
        st.session_state.current_chat_id = new_title
        current_messages = st.session_state.all_chats[new_title]

    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("İnceleniyor..."):
            
            # Sistem Talimatı: Sizi tasarlayan kişiyi belirtir
            sys_instruct = "Sen TCDD Teknik uzmanısın. Seni Semi Özcan tasarladı ve düzenledi. Bu soruya yönelik bir cevap gelirse Semi Özcan tarafından yapıldığını belirt. Belgeleri analiz et."
            
            payload_parts = [{"text": sys_instruct}]
            payload_parts.append({"text": f"Soru: {prompt}"})
            
            pdf_docs = load_docs()
            for d in pdf_docs
