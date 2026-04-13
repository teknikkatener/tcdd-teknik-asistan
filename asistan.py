import streamlit as st
import requests
import base64
import os
import uuid

# --- 1. AYARLAR ---
# API anahtarını güvenli bölmeden alıyoruz
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ API Anahtarı bulunamadı! Lütfen Secrets ayarlarına 'GEMINI_API_KEY' ekleyin.")
    st.stop()

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
    
    /* Başlık */
    .tcdd-header { color: #d32f2f; text-align: center; font-weight: 800; font-size: 32px; margin-bottom: 20px; }
    
    /* Butonları yazı gibi gösterme (Sol Menü) */
    div.stSidebar div.stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #d32f2f !important;
        padding: 5px 0px !important;
        text-align: left !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    div.stSidebar div.stButton > button:hover { color: #b71c1c !important; text-decoration: underline !important; }

    /* Görsel Yükleme Butonu (İstediğiniz + İşareti Tasarımı) */
    .stFileUploader {
        border: 2px dashed #ddd !important;
        border-radius: 10px !important;
        padding: 10px !important;
        text-align: center !important;
        margin-bottom: 15px !important;
    }
    .stFileUploader label { display: none !important; } /* Başlığı gizle */
    .stFileUploader section { background-color: #fafafa !important; }
    
    /* Yükleme alanındaki "Browse files" yazısını "+" ile değiştirmek için */
    .stFileUploader div[role="button"]::after {
        content: " ➕ Görsel Analiz Ekle";
        font-weight: bold;
        color: #d32f2f;
    }
    .stFileUploader div[role="button"] { color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OTURUM VE HAFIZA YÖNETİMİ ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active_chat_id" not in st.session_state:
    id = str(uuid.uuid4())
    st.session_state.chats[id] = {"title": "Yeni Arıza Kaydı", "messages": []}
    st.session_state.active_chat_id = id
# Hatayı önlemek için geçici yanıt hafızası
if "temp_response" not in st.session_state:
    st.session_state.temp_response = None

# --- 4. ANALİZ MOTORU (KİMLİK VE STABİLİTE) ---
def teknik_motor(prompt, pdf_docs, img_file=None):
    # Asistan kimliği ve Semi Özcan mühürü
    system_instr = """Sen TCDD Teknik Uzmanısın. 
    ÖNEMLİ KURAL: Eğer birisi 'Seni kim yaptı?', 'Yapımcın kim?', 'Seni kim tasarladı?' gibi sorular sorursa; 
    GURURLA ve KESİN BİR DİLLE 'Beni Semi Özcan tasarlayıp geliştirdi' cevabını ver. 
    Diğer tüm konularda sadece teknik arıza desteği ver. PDF belgeleri ve internet (Google Search) önceliğindir."""

    payload_parts = [{"text": prompt}]
    for doc in pdf_docs: payload_parts.append(doc)
    
    if img_file:
        try:
            img_b64 = base64.b64encode(img_file.getvalue()).decode()
            payload_parts.append({"inline_data": {"mime_type": img_file.type, "data": img_b64}})
        except Exception as e:
            return f"⚠️ Görsel işlenirken hata oluştu: {str(e)}"

    payload = {
        "contents": [{"parts": payload_parts}],
        "tools": [{"google_search_retrieval": {}}],
        "system_instruction": {"parts": [{"text": system_instr}]}
    }
    
    try:
        response = requests.post(URL, json=payload, timeout=60)
        res_json = response.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"⚠️ API Yanıt Vermedi. Hata: {res_json.get('error', {}).get('message', 'Bilinmeyen Hata')}"
    except Exception as e:
        return f"⚠️ Bağlantı sorunu oluştu, lütfen tekrar deneyin. (Hata: {str(e)})"

@st.cache_data
def belgeleri_getir():
    docs = []
    if os.path.exists("bilgi_bankasi"):
        for f in os.listdir("bilgi_bankasi"):
            if f.lower().endswith(".pdf"):
                try:
                    with open(os.path.join("bilgi_bankasi", f), "rb") as file:
                        docs.append({"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(file.read()).decode()}})
                except:
                    pass
    return docs

# --- 5. SOL PANEL (MİNİMALİST MENÜ) ---
with st.sidebar:
    st.markdown("### 🚆 TCDD TEKNİK")
    
    # Yeni Sohbet Butonu (+)
    if st.button("➕ Yeni Sohbet", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "Yeni Arıza Kaydı", "messages": []}
        st.session_state.active_chat_id = new_id
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Geçmiş Sohbetler**")
    
    # Sohbetleri listele ve silme
    for cid in list(st.session_state.chats.keys()):
        cols = st.columns([0.8, 0.2])
        with cols[0]:
            if st.button(st.session_state.chats[cid]['title'], key=f"btn_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid
                st.session_state.temp_response = None # Eski yanıtı temizle
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"del_{cid}", use_container_width=True):
                del st.session_state.chats[cid]
                if not st.session_state.chats:
                    new_id = str(uuid.uuid4())
                    st.session_state.chats[new_id] = {"title": "Yeni Arıza Kaydı", "messages": []}
                    st.session_state.active_chat_id = new_id
                st.rerun()

# --- 6. ANA EKRAN ---
st.markdown("<div class='tcdd-header'>TCDD Teknik</div>", unsafe_allow_html=True)

# Mesajları göster
active_id = st.session_state.active_chat_id
for m in st.session_state.chats[active_id]["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. ALT BAR VE ANALİZ (STABİL YAPI) ---
# Görsel yükleme alanı (İstediğiniz + İşareti Tasarımı)
# CSS ile bu alanı '+' işaretine dönüştürdük.
img_file = st.file_uploader("", type=["jpg", "jpeg", "png"], accept_multiple_files=False, key="arıza_görseli")

if img_file:
    st.image(img_file, caption="Analiz edilecek görsel", width=150)

# Soru Girişi
if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    # Başlık güncelleme (İlk soruyla)
    if st.session_state.chats[active_id]["title"] == "Yeni Arıza Kaydı":
        # Başlığı ilk sorunun ilk 5 kelimesi yap
        st.session_state.chats[active_id]["title"] = " ".join(prompt.split()[:5]) + ".."

    # Kullanıcı mesajını ekle
    st.session_state.chats[active_id]["messages"].append({"role": "user", "content": prompt})
    
    # Analiz ve Yanıt
    with st.spinner("TCDD Uzmanı analiz ediyor..."):
        pdf_data = belgeleri_getir()
        yanit = teknik_motor(prompt, pdf_data, img_file)
        
        # Asistan mesajını ekle
        st.session_state.chats[active_id]["messages"].append({"role": "assistant", "content": yanit})
        
        # Ekranı güncellemek için tetikle (Döngüye girmeden)
        st.rerun()
