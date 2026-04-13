import streamlit as st
import requests
import base64
import os
import uuid

# --- 1. AYARLAR (MODEL ADRESI VE GÜNCELLEME) ---
API_KEY = st.secrets["GEMINI_API_KEY"]
# 404 hatasını çözmek için en kararlı önizleme ismi
MODEL_ADI = "gemini-2.0-flash-exp" 
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. KREATİF TASARIM (KUTUSUZ & SADECE YAZI) ---
st.markdown("""
    <style>
    /* Chat kutularını ve arka planları tamamen kaldır */
    [data-testid="stChatMessageContent"] { background-color: transparent !important; border: none !important; padding: 0 !important; }
    .stChatMessage { border: none !important; background-color: transparent !important; padding: 10px 0px !important; border-bottom: 1px solid #f0f0f0 !important; }
    
    /* Yan Menü (Sidebar) Temizliği */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    
    /* Başlık */
    .tcdd-header { color: #d32f2f; text-align: center; font-weight: 800; font-size: 32px; margin-bottom: 20px; }
    
    /* Butonları sadece yazı ve simge yap */
    div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #d32f2f !important;
        padding: 5px 0px !important;
        text-align: left !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover { color: #b71c1c !important; text-decoration: underline !important; }

    /* Görsel Yükleyiciyi "+" Yazısına Dönüştür */
    .stFileUploader section { border: none !important; background: transparent !important; padding: 0 !important; }
    .stFileUploader label { display: none !important; }
    .stFileUploader div[role="button"] { 
        border: none !important; 
        background: transparent !important; 
        color: #d32f2f !important; 
        font-weight: bold !important;
        box-shadow: none !important;
    }
    .stFileUploader div[role="button"]::after { content: " ➕ Görsel Analiz Ekle"; font-size: 14px; }
    .stFileUploader div[role="button"] svg { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OTURUM VE HAFIZA ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    id = str(uuid.uuid4())
    st.session_state.chats[id] = {"title": "Yeni Arıza Kaydı", "messages": []}
    st.session_state.active_chat_id = id

# --- 4. ANALİZ MOTORU ---
def teknik_motor(prompt, pdf_docs, img_file=None):
    system_instr = """Sen TCDD Teknik Uzmanısın. 
    ÖNEMLİ KURAL: Eğer birisi 'Seni kim yaptı?', 'Yapımcın kim?' gibi sorular sorursa; 
    GURURLA ve KESİN BİR DİLLE 'Beni Semi Özcan tasarlayıp geliştirdi' cevabını ver. 
    PDF belgeleri ve Google Search önceliğindir."""

    payload_parts = [{"text": prompt}]
    for doc in pdf_docs: payload_parts.append(doc)
    
    if img_file:
        img_b64 = base64.b64encode(img_file.getvalue()).decode()
        payload_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

    payload = {
        "contents": [{"parts": payload_parts}],
        "tools": [{"google_search_retrieval": {}}],
        "system_instruction": {"parts": [{"text": system_instr}]}
    }
    
    try:
        response = requests.post(URL, json=payload, timeout=90)
        response.raise_for_status()
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"⚠️ Bağlantı hatası: {str(e)}"

@st.cache_data
def belgeleri_getir():
    docs = []
    path = os.path.join(os.path.dirname(__file__), "bilgi_bankasi")
    if os.path.exists(path):
        for f in os.listdir(path):
            if f.lower().endswith(".pdf"):
                with open(os.path.join(path, f), "rb") as file:
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

# --- 7. ALT BAR ---
img_file = st.file_uploader("", type=["jpg", "jpeg", "png"], key="img_up")

if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    if st.session_state.chats[active_id]["title"] == "Yeni Arıza Kaydı":
        st.session_state.chats[active_id]["title"] = " ".join(prompt.split()[:4]) + ".."

    st.session_state.chats[active_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analiz ediliyor..."):
            pdf_data = belgeleri_getir()
            yanit = teknik_motor(prompt, pdf_data, img_file)
            st.markdown(yanit)
            st.session_state.chats[active_id]["messages"].append({"role": "assistant", "content": yanit})
            st.rerun()
