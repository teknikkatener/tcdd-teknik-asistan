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
        color
