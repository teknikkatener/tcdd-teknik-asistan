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

st.markdown("""
    <style>
    .tcdd-title { color: #d32f2f; font-size: 35px; font-weight: 800; text-align: center; margin-bottom: 10px; }
    .bar-text { color: #d32f2f; font-weight: 700; text-align: center; margin-bottom: 5px; opacity: 0.8; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    
    /* Düz yazı buton tasarımı */
    div.stButton > button {
        background: none !important;
        border: none !important;
        color: #444 !important;
        text-align: left !important;
        padding: 5px 0px !important;
        font-size: 15px !important;
    }
    div.stButton > button:hover {
        color: #d32f2f !important;
    }
    .delete-text { color: #ff4b4b !important; font-size: 12px !important; }
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

# --- 4. SOL PANEL (YENİ SOHBET / SİL / GEÇMİŞ) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #d32f2f;'>🚆 TCDD</h2>", unsafe_allow_html=True)
    
    if st.button("Yeni Sohbet +", use_container_width=True):
        new_id = f"Yeni Sohbet {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("📂 **Geçmiş Sohbetler +**")
    
    # Geçmiş Sohbet Listesi ve Silme Butonları
    for chat_id in list(st.session_state.all_chats.keys()):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            if st.button(f"💬 {chat_id[:15]}...", key=f"view_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.all_chats[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = "Yeni Sohbet"
                    if "Yeni Sohbet" not in st.session_state.all_chats:
                        st.session_state.all_chats["Yeni Sohbet"] = []
                st.rerun()

    if st.button("⚠️ Tüm Geçmişi Sil", key="clear_all"):
        st.session_state.all_chats = {"Yeni Sohbet": []}
        st.session_state.current_chat_id = "Yeni Sohbet"
        st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("Fotoğraf Yükle", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# --- 5. ANA EKRAN ---
st.markdown(f"<div class='tcdd-title'>{st.session_state.current_chat_id}</div>", unsafe_allow_html=True)

current_messages = st.session_state.all_chats.get(st.session_state.current_chat_id, [])
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. SORU VE ANALİZ ---
st.markdown("<div class='bar-text'>TCDD Teknik</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    
    # Otomatik Başlıklandırma
    if not current_messages and st.session_state.current_chat_id.startswith("Yeni Sohbet"):
        new_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
        st.session_state.all_chats[new_title] = st.session_state.all_chats.pop(st.session_state.current_chat_id)
        st.session_state.current_chat_id = new_title
        current_messages = st.session_state.all_chats[new_title]

    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Cevap hazırlanıyor..."):
            
            # Kimlik Bilgisi Sistem Mesajına Eklendi
            sys_msg = "Sen TCDD Teknik uzmanısın. Seni Semi Özcan tasarladı ve düzenledi. Cevaplarında teknik belgeleri baz al."
            payload_parts = [{"text": sys_msg}, {"text": f"Soru: {prompt}"}]
            
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
                    # st.rerun() kaldırıldı, bunun yerine Streamlit'in doğal akışı cevabı gösterecek.
                else:
                    st.error(f"Hata: {res_json.get('error', {}).get('message', 'Cevap alınamadı.')}")
            except Exception as e:
                st.error(f"Bağlantı hatası: {e}")
