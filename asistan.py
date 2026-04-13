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
    st.session_state.all_chats = {"Yeni Sohbet": []} 
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Yeni Sohbet"

st.markdown("""
    <style>
    .tcdd-title { color: #d32f2f; font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #444 !important;
        text-align: left !important;
        padding: 5px 0px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        color: #d32f2f !important;
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

# --- 4. SOL PANEL (YENİ SOHBET / DÜZENLE / SİL) ---
with st.sidebar:
    # İstediğiniz yeni başlık buraya eklendi
    st.markdown("<h2 style='text-align: center; color: #d32f2f; font-size: 24px;'>🚆 TCDD TEKNİK Aİ</h2>", unsafe_allow_html=True)
    
    if st.button("Yeni Sohbet +", use_container_width=True):
        new_id = f"Sohbet {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("📂 **Geçmiş Sohbetler**")
    
    for chat_id in list(st.session_state.all_chats.keys()):
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
        with col1:
            if st.button(f"💬 {chat_id[:12]}", key=f"v_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("✏️", key=f"ed_{chat_id}"):
                st.session_state.edit_target = chat_id
        with col3:
            if st.button("🗑️", key=f"dl_{chat_id}"):
                if len(st.session_state.all_chats) > 1:
                    del st.session_state.all_chats[chat_id]
                    st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]
                    st.rerun()

    if "edit_target" in st.session_state:
        new_name = st.text_input("Yeni başlık yazın:", value=st.session_state.edit_target)
        if st.button("Başlığı Güncelle"):
            st.session_state.all_chats[new_name] = st.session_state.all_chats.pop(st.session_state.edit_target)
            st.session_state.current_chat_id = new_name
            del st.session_state.edit_target
            st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("Görsel Analiz", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- 5. ANA EKRAN ---
st.markdown(f"<div class='tcdd-title'>{st.session_state.current_chat_id}</div>", unsafe_allow_html=True)

current_messages = st.session_state.all_chats.get(st.session_state.current_chat_id, [])
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. SORU VE ANALİZ ---
if prompt := st.chat_input("Mesajınızı yazın..."):
    
    # Otomatik Başlıklandırma
    if not current_messages and (st.session_state.current_chat_id.startswith("Sohbet") or st.session_state.current_chat_id == "Yeni Sohbet"):
        new_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.all_chats[new_title] = st.session_state.all_chats.pop(st.session_state.current_chat_id)
        st.session_state.current_chat_id = new_title
        current_messages = st.session_state.all_chats[new_title]

    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            
            low
