import streamlit as st
import google.generativeai as genai
import os
import uuid

# --- 1. AYARLAR (KENDİ KENDİNİ TEST EDEN MOTOR) ---
# Buraya API anahtarınızı tırnak içine yazın
API_KEY = "AIzaSyDiPz8xBichTdC5wz30BQyv6PeFFRrTIH0"
genai.configure(api_key=API_KEY)

# Bulutun en sevdiği, en hatasız model ismi
MODEL_ADI = "gemini-2.0-flash-exp" 

st.set_page_config(page_title="TCDD Teknik", page_icon="🚆", layout="wide")

# --- 2. TASARIM (SİZİN İSTEDİĞİNİZ SADE STİL) ---
st.markdown("""
    <style>
    [data-testid="stChatMessageContent"] { background-color: transparent !important; border: none !important; padding: 0 !important; }
    .stChatMessage { border: none !important; background-color: transparent !important; padding: 10px 0px !important; border-bottom: 1px solid #f0f0f0 !important; }
    .tcdd-header { color: #d32f2f; text-align: center; font-weight: 800; font-size: 32px; margin-bottom: 20px; }
    div.stButton > button { background-color: transparent !important; border: none !important; color: #d32f2f !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BAĞLANTI TESTİ (SİSTEM AÇILIRKEN KONTROL EDER) ---
def baglanti_test_et():
    try:
        test_model = genai.GenerativeModel(MODEL_ADI)
        response = test_model.generate_content("test", generation_config={"max_output_tokens": 5})
        return True, "Bağlantı Başarılı"
    except Exception as e:
        return False, str(e)

# --- 4. OTURUM ---
if "chats" not in st.session_state:
    st.session_state.chats = {str(uuid.uuid4()): {"title": "Yeni Arıza Kaydı", "messages": []}}
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]

# --- 5. ANALİZ MOTORU ---
def teknik_motor(prompt, pdf_files, img_file=None):
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_ADI,
            system_instruction="Sen TCDD Teknik Uzmanısın. Seni Semi Özcan tasarladı. Sadece teknik cevap ver."
        )
        
        parts = [prompt]
        # PDF'leri işle
        for pdf in pdf_files:
            with open(pdf, "rb") as f:
                parts.append({"mime_type": "application/pdf", "data": f.read()})
        
        # Görseli işle
        if img_file:
            parts.append({"mime_type": "image/jpeg", "data": img_file.getvalue()})

        # Yanıt al (Google Search dahil)
        response = model.generate_content(parts, tools=[{"google_search_retrieval": {}}])
        return response.text
    except Exception as e:
        return f"❌ Teknik Hata: {str(e)}"

# --- 6. ANA EKRAN ---
st.markdown("<div class='tcdd-header'>TCDD Teknik</div>", unsafe_allow_html=True)

# Bağlantı Durumu Göstergesi
is_ok, msg = baglanti_test_et()
if not is_ok:
    st.error(f"🔌 Bağlantı Kurulamadı! Detay: {msg}")
else:
    st.success("✅ Sistem Aktif: Google ile bağlantı kuruldu.")

active_id = st.session_state.active_chat_id
for m in st.session_state.chats[active_id]["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. GİRİŞ ---
img_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if prompt := st.chat_input("Teknik sorunuzu yazın..."):
    st.session_state.chats[active_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analiz ediliyor..."):
            # Bilgi bankasındaki PDF yollarını al
            base_path = os.path.join(os.path.dirname(__file__), "bilgi_bankasi")
            pdfs = [os.path.join(base_path, f) for f in os.listdir(base_path) if f.lower().endswith(".pdf")] if os.path.exists(base_path) else []
            
            yanit = teknik_motor(prompt, pdfs, img_file)
            st.markdown(yanit)
            st.session_state.chats[active_id]["messages"].append({"role": "assistant", "content": yanit})
            st.rerun()
