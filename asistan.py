import streamlit as st
import requests
import base64
import os

# --- 1. AYARLAR ---
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    st.error("secrets.toml dosyası veya içindeki API_KEY bulunamadı!")
    st.stop()

# ARTIK MOTOR Gemini 3 Flash!
MODEL_ADI = "models/gemini-3-flash" 
URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(
    page_title="TCDD Teknik", 
    page_icon="Tcdd_Teknik_Logo.png", 
    layout="wide"
)

# --- 2. TASARIM ---
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
    div.stButton > button:hover { color: #d32f2f !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SOHBET VE BELGE YÖNETİMİ ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"Yeni Sohbet": []} 
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "Yeni Sohbet"

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

# --- 4. SOL PANEL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #d32f2f;'>🚆 TCDD TEKNİK</h2>", unsafe_allow_html=True)
    if st.button("Yeni Sohbet +", use_container_width=True):
        new_id = f"Sohbet {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_id] = []
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    for chat_id in list(st.session_state.all_chats.keys()):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(f"💬 {chat_id[:15]}", key=f"btn_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                if len(st.session_state.all_chats) > 1:
                    del st.session_state.all_chats[chat_id]
                    st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]
                    st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("Görsel Analiz (Gemini 3)", type=["jpg", "png", "jpeg"])

# --- 5. ANA EKRAN ---
st.markdown(f"<div class='tcdd-title'>{st.session_state.current_chat_id}</div>", unsafe_allow_html=True)

messages = st.session_state.all_chats[st.session_state.current_chat_id]
for msg in messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- 6. İŞLEME VE ANALİZ ---
prompt = st.chat_input("Teknik sorunuzu buraya yazın...")

# Görsel kontrolü
should_analyze = False
if img_file:
    if "last_img" not in st.session_state or st.session_state.last_img != img_file.name:
        should_analyze = True
        st.session_state.last_img = img_file.name

if prompt or should_analyze:
    # Başlık güncelleme
    if not messages:
        new_title = (prompt[:20] if prompt else "Görsel Analiz") + "..."
        st.session_state.all_chats[new_title] = st.session_state.all_chats.pop(st.session_state.current_chat_id)
        st.session_state.current_chat_id = new_title
        messages = st.session_state.all_chats[new_title]

    user_text = prompt if prompt else "Görseli Gemini 3 Flash altyapısıyla analiz et."
    messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"): st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Gemini 3 Flash Analiz Yapıyor..."):
            
            # Kimlik ve Selamlaşma Kontrolü
            clean_p = user_text.lower().replace(" ", "")
            if "kimyaptı" in clean_p or "kimtasarladı" in clean_p:
                ans = "Beni **Onur Ladik ve Ekibi** tasarladı ve TCDD sistemleri için en güncel Gemini 3 altyapısıyla donattı."
            else:
                sistem_talimati = "Sen TCDD Teknik uzmanısın. Gemini 3 Flash gücünü kullanarak teknik analizler yap."
                payload_parts = [{"text": sistem_talimati}, {"text": f"Soru: {user_text}"}]
                
                # PDF ve Görsel Ekleme
                for d in load_docs(): payload_parts.append({"inline_data": d})
                if img_file:
                    img_b64 = base64.b64encode(img_file.getvalue()).decode()
                    payload_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

                try:
                    res = requests.post(URL, json={"contents": [{"parts": payload_parts}]}, timeout=30)
                    res_json = res.json()
                    if 'candidates' in res_json:
                        ans = res_json['candidates'][0]['content']['parts'][0]['text']
                    else:
                        ans = f"API Hatası: {res_json.get('error', {}).get('message', 'Kota dolmuş olabilir.')}"
                except Exception as e:
                    ans = f"Bağlantı Hatası: {str(e)}"

            st.markdown(ans)
            messages.append({"role": "assistant", "content": ans})
            st.rerun()
