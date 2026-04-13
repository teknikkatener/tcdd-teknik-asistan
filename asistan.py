import streamlit as st
import requests
import base64
import os
import uuid

# --- 1. AYARLAR ---
API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_ADI = "gemini-2.0-flash-lite-preview-02-05" 
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ADI}:generateContent?key={API_KEY}"

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. KREATİF TASARIM (CSS) ---
st.markdown("""
    <style>
    /* Kutusuz, temiz yazı tipi odaklı tasarım */
    [data-testid="stChatMessageContent"] { background-color: transparent !important; border: none !important; padding-left: 0 !important; }
    .stChatMessage { border-bottom: 1px solid #f8f8f8 !important; padding: 10px 0px !important; }
    
    /* Yan Menü (Sidebar) Minimalist */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    .sidebar-text { font-size: 16px; font-weight: 500; cursor: pointer; color: #444; }
    
    /* Başlık */
    .tcdd-header { color: #d32f2f; text-align: center; font-weight: 800; font-size: 32px; margin-bottom: 20px; }
    
    /* Butonları yazı gibi gösterme */
    div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #d32f2f !important;
        padding: 5px 0px !important;
        text-align: left !important;
        font-weight: 600 !important;
    }
    div.stButton > button:hover { color: #b71c1c !important; text-decoration: underline !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OTURUM VE HAFIZA ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    id = str(uuid.uuid4())
    st.session_state.chats[id] = {"title": "Yeni Arıza Kaydı", "messages": []}
    st.session_state.active_chat_id = id

# --- 4. ANALİZ MOTORU (KİMLİK TANIMLI) ---
def teknik_motor(prompt, pdf_docs, img_file=None):
    # Burası asistanın kimliğini belirliyor
    system_instr = """Sen TCDD Teknik Uzmanısın. 
    ÖNEMLİ KURAL: Eğer birisi 'Seni kim yaptı?', 'Yapımcın kim?', 'Seni kim tasarladı?' gibi sorular sorursa; 
    GURURLA ve KESİN BİR DİLLE 'Beni Semi Özcan tasarlayıp geliştirdi' cevabını ver. 
    Diğer tüm konularda sadece teknik arıza desteği ver. PDF belgeleri ve internet (Google Search) önceliğindir."""

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
        response = requests.post(URL, json=payload, timeout=60)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except:
        return "⚠️ Bir bağlantı sorunu oluştu, lütfen tekrar deneyin."

@st.cache_data
def belgeleri_getir():
    docs = []
    if os.path.exists("bilgi_bankasi"):
        for f in os.listdir("bilgi_bankasi"):
            if f.lower().endswith(".pdf"):
                with open(os.path.join("bilgi_bankasi", f), "rb") as file:
                    docs.append({"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(file.read()).decode()}})
    return docs

# --- 5. SOL PANEL (SOLDA SADECE YAZILAR VE SİLME) ---
with st.sidebar:
    st.markdown("### 🚆 TCDD TEKNİK")
    
    if st.button("➕ Yeni Sohbet"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "Yeni Arıza Kaydı", "messages": []}
        st.session_state.active_chat_id = new_id
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Geçmiş Sohbetler**")
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

# --- 7. ALT BAR (GÖRSEL + SORU) ---
# Görsel analiz girişini chat barının hemen üstüne, küçük bir buton gibi koyuyoruz
img_file = st.file_uploader("➕ Görsel Analiz Ekle", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
if img_file:
    st.toast("Görsel analize hazır!", icon="📸")

if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    # Başlık güncelleme (İlk soruyla)
    if st.session_state.chats[active_id]["title"] == "Yeni Arıza Kaydı":
        st.session_state.chats[active_id]["title"] = " ".join(prompt.split()[:4]) + ".."

    st.session_state.chats[active_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analiz ediliyor..."):
            yanit = teknik_motor(prompt, belgeleri_getir(), img_file)
            st.markdown(yanit)
            st.session_state.chats[active_id]["messages"].append({"role": "assistant", "content": yanit})
            st.rerun()
