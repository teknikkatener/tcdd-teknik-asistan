import streamlit as st
import requests
import base64
import os
import uuid

# --- 1. AYARLAR ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ API Anahtarı eksik! Secrets kısmına ekleyin.")
    st.stop()

# Daha hızlı ve kararlı model
MODEL_ADI = "gemini-1.5-flash" 
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. KREATİF TASARIM (CSS - TÜM KUTULARI SİLER) ---
st.markdown("""
    <style>
    /* Chat kutularını tamamen şeffaf yap */
    [data-testid="stChatMessageContent"] { background-color: transparent !important; border: none !important; padding: 0 !important; }
    .stChatMessage { border: none !important; background-color: transparent !important; padding: 10px 0px !important; }
    
    /* Sol menü kutuları silme */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    
    /* Başlık ve Butonlar */
    .tcdd-header { color: #d32f2f; text-align: center; font-weight: 800; font-size: 32px; margin-bottom: 20px; }
    
    div.stSidebar div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #444 !important;
        padding: 5px 0px !important;
        text-align: left !important;
        font-weight: 500 !important;
        width: 100% !important;
        box-shadow: none !important;
    }
    div.stSidebar div.stButton > button:hover { color: #d32f2f !important; text-decoration: underline !important; }

    /* Görsel Yükleyiciyi Sadece Yazı Yap */
    .stFileUploader section { border: none !important; background: transparent !important; padding: 0 !important; }
    .stFileUploader label { display: none !important; }
    .stFileUploader div[role="button"] { 
        border: none !important; 
        background: transparent !important; 
        color: #d32f2f !important; 
        font-weight: bold !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    .stFileUploader div[role="button"]::after { content: " ➕ Görsel Analiz"; font-size: 14px; }
    .stFileUploader div[role="button"] svg { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OTURUM YÖNETİMİ ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    id = str(uuid.uuid4())
    st.session_state.chats[id] = {"title": "Yeni Arıza Kaydı", "messages": []}
    st.session_state.active_chat_id = id

# --- 4. TEKNİK MOTOR (BAĞLANTI HATALARI GİDERİLDİ) ---
def teknik_motor(prompt, pdf_docs, img_file=None):
    system_instr = "Sen TCDD Teknik Uzmanısın. Seni Semi Özcan yaptı. Sadece teknik cevap ver."
    
    payload_parts = [{"text": prompt}]
    for doc in pdf_docs: payload_parts.append(doc)
    
    if img_file:
        img_b64 = base64.b64encode(img_file.getvalue()).decode()
        payload_parts.append({"inline_data": {"mime_type": img_file.type, "data": img_b64}})

    payload = {
        "contents": [{"parts": payload_parts}],
        "system_instruction": {"parts": [{"text": system_instr}]}
    }
    
    try:
        # Timeout süresini artırdık
        response = requests.post(URL, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"⚠️ Hata: {res_json.get('error', {}).get('message', 'API Kotası veya Bağlantı Sorunu')}"
    except Exception as e:
        return f"⚠️ Sunucu hatası: {str(e)}"

@st.cache_data
def belgeleri_getir():
    docs = []
    if os.path.exists("bilgi_bankasi"):
        for f in os.listdir("bilgi_bankasi")[:5]: # Hata almamak için ilk 5 dökümanı alıyoruz
            if f.lower().endswith(".pdf"):
                with open(os.path.join("bilgi_bankasi", f), "rb") as file:
                    docs.append({"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(file.read()).decode()}})
    return docs

# --- 5. SOL PANEL ---
with st.sidebar:
    st.markdown("### 🚆 TCDD TEKNİK")
    if st.button("➕ Yeni Sohbet"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "Yeni Arıza Kaydı", "messages": []}
        st.session_state.active_chat_id = new_id
        st.rerun()
    
    st.markdown("---")
    for cid in list(st.session_state.chats.keys()):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            if st.button(st.session_state.chats[cid]['title'], key=f"btn_{cid}"):
                st.session_state.active_chat_id = cid
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if not st.session_state.chats:
                    new_id = str(uuid.uuid4())
                    st.session_state.chats[new_id] = {"title": "Yeni Arıza Kaydı", "messages": []}
                    st.session_state.active_chat_id = new_id
                st.rerun()

# --- 6. ANA EKRAN ---
st.markdown("<div class='tcdd-header'>TCDD Teknik</div>", unsafe_allow_html=True)
active_id = st.session_state.active_chat_id

for m in st.session_state.chats[active_id]["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. GİRİŞ ---
# Görsel yükleme sadece bir artı ve yazı
img_file = st.file_uploader("", type=["jpg", "png", "jpeg"], key="img")

if prompt := st.chat_input("Mesajınızı yazın..."):
    if st.session_state.chats[active_id]["title"] == "Yeni Arıza Kaydı":
        st.session_state.chats[active_id]["title"] = prompt[:20] + "..."

    st.session_state.chats[active_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            pdf_data = belgeleri_getir()
            yanit = teknik_motor(prompt, pdf_data, img_file)
            st.markdown(yanit)
            st.session_state.chats[active_id]["messages"].append({"role": "assistant", "content": yanit})
            st.rerun()
