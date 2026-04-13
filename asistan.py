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

# EN GÜNCEL MODEL: Gemini 3 Flash
MODEL_ADI = "models/gemini-3-flash" 
URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(
    page_title="TCDD Teknik", 
    page_icon="Tcdd_Teknik_Logo.png", 
    layout="wide"
)

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

# --- 4. SOL PANEL ---
with st.sidebar:
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
        new_name = st.text_input("Yeni başlık:", value=st.session_state.edit_target)
        if st.button("Güncelle"):
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
prompt = st.chat_input("Mesajınızı yazın...")

# Görsel yüklendiğinde otomatik analiz tetikleyici
should_analyze = False
if img_file:
    if "last_processed_img" not in st.session_state or st.session_state.last_processed_img != img_file.name:
        should_analyze = True
        st.session_state.last_processed_img = img_file.name

if prompt or should_analyze:
    # Başlıklandırma
    if not current_messages and (st.session_state.current_chat_id.startswith("Sohbet") or st.session_state.current_chat_id == "Yeni Sohbet"):
        title_source = prompt if prompt else "Görsel Teknik Analiz"
        new_title = title_source[:20] + "..." if len(title_source) > 20 else title_source
        st.session_state.all_chats[new_title] = st.session_state.all_chats.pop(st.session_state.current_chat_id)
        st.session_state.current_chat_id = new_title
        current_messages = st.session_state.all_chats[new_title]

    if prompt:
        current_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
    elif should_analyze:
        current_messages.append({"role": "user", "content": "Görsel yüklendi, Gemini 3 tarafından analiz ediliyor..."})
        with st.chat_message("user"): st.markdown("Görsel yüklendi, Gemini 3 tarafından analiz ediliyor...")

    with st.chat_message("assistant"):
        with st.spinner("Gemini 3 Teknik Analiz Yapıyor..."):
            
            clean_p = prompt.lower().replace(" ", "") if prompt else ""
            # Kimlik koruması Onur Bey ve ekibi olarak güncellendi
            kimlik_kelimeleri = ["kimyaptı", "kimtasarladı", "senikim", "yapımcın", "kimingeliştirdi", "kimtarafındanyapıldın"]
            
            if prompt and any(k in clean_p for k in kimlik_kelimeleri):
                ans = "Beni **Onur Ladik ve Ekibi** tasarladı ve TCDD teknik sistemlerini en güncel yapay zeka modelleriyle analiz etmem için geliştirdi."
            else:
                sistem_talimati = "Sen en güncel TCDD Teknik uzmanısın. Belgeleri ve görselleri derinlemesine analiz et."
                user_query = prompt if prompt else "Yüklenen görseli Gemini 3 yeteneklerinle teknik olarak incele."
                payload_parts = [{"text": sistem_talimati}, {"text": f"Soru: {user_query}"}]
                
                pdf_docs = load_docs()
                for d in pdf_docs:
                    payload_parts.append({"inline_data": d})
                
                if img_file:
                    img_b64 = base64.b64encode(img_file.getvalue()).decode()
                    payload_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

                try:
                    response = requests.post(URL, json={"contents": [{"parts": payload_parts}]}, timeout=30)
                    res_json = response.json()
                    
                    if 'candidates' in res_json and len(res_json['candidates']) > 0:
                        ans = res_json['candidates'][0]['content']['parts'][0]['text']
                    else:
                        error_msg = res_json.get('error', {}).get('message', 'Beklenmedik bir hata oluştu.')
                        ans = f"Teknik Analiz Hatası: {error_msg}"
                except Exception as e:
                    ans = f"Bağlantı Hatası: {str(e)}"

            st.markdown(ans)
            current_messages.append({"role": "assistant", "content": ans})
            st.rerun()
