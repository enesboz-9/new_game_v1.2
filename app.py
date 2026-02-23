import streamlit as st
from PIL import Image, ImageFilter
import wikipedia
import requests
from io import BytesIO
import random
import time
import json
import os
import base64
from rapidfuzz import fuzz

# --- Ayarlar ---
st.set_page_config(page_title="🌟 Göster Bakalım - Pro", layout="centered")
wikipedia.set_user_agent("GosterBakalimV4/1.0 (iletisim@projen.com)")

# --- Görsel Arama Motorları ---

def get_wikipedia_img(name, cat):
    """Birinci Motor: Wikipedia API"""
    try:
        query = name
        if cat == "Şirket Logoları": query = f"{name} logo"
        
        # Wikipedia API üzerinden orijinal görseli iste
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "titles": query,
            "prop": "pageimages", "piprop": "original", "redirects": 1
        }
        res = requests.get(api_url, params=params, timeout=5).json()
        pages = res['query']['pages']
        for k, v in pages.items():
            if 'original' in v:
                return v['original']['source']
        return None
    except:
        return None

def get_backup_img(name, cat):
    """İkinci Motor: Unsplash & Genel Görsel Servisleri"""
    try:
        # Boşlukları URL formatına çevir
        search_query = name.replace(" ", "+")
        # Unsplash üzerinden kategoriye uygun görsel çekmeye çalış
        if cat == "Şehirler":
            return f"https://source.unsplash.com/featured/800x600?city,{search_query}"
        elif cat == "Futbolcular":
            return f"https://source.unsplash.com/featured/800x600?footballer,{search_query}"
        else:
            return f"https://source.unsplash.com/featured/800x600?{search_query}"
    except:
        return None

@st.cache_data(ttl=3600)
def get_img_final(name, cat):
    """Hibrit Motor: Önce Wiki, olmazsa Yedek"""
    img_url = get_wikipedia_img(name, cat)
    if not img_url:
        # Wikipedia bulamadıysa yedeği dene
        img_url = get_backup_img(name, cat)
    return img_url

# --- Yardımcı Fonksiyonlar ---
def is_guess_correct(user_guess, correct_name):
    if not user_guess: return False
    similarity = fuzz.token_sort_ratio(user_guess.lower(), correct_name.lower())
    return similarity >= 80

@st.cache_data
def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"data.json okuma hatası: {e}")
        return None

# --- Oyun Başlatma ---
data = load_data()

if "game_init" not in st.session_state:
    st.session_state.update({
        "game_init": False, "total_score": 0, "current_question": 1,
        "played_items": [], "target_item": None, "attempts": 0, "game_finished": False
    })

if not st.session_state.game_init:
    st.title("🌟 Göster Bakalım!")
    if data:
        st.session_state.category = st.selectbox("Kategori Seçin:", list(data.keys()))
        st.session_state.difficulty = st.selectbox("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"])
        if st.button("OYUNA BAŞLA"):
            d = st.session_state.difficulty
            # Zorluk ayarları (Blur seviyeleri)
            if d == "Kolay": st.session_state.blur_levels, st.session_state.mult = [25, 18, 12, 6, 0], 1
            elif d == "Orta": st.session_state.blur_levels, st.session_state.mult = [45, 30, 20, 10, 0], 2
            else: st.session_state.blur_levels, st.session_state.mult = [80, 55, 35, 15, 0], 3
            st.session_state.game_init = True
            st.rerun()
    else:
        st.stop()

# Soru Seçimi
if st.session_state.target_item is None and not st.session_state.game_finished:
    pool = data[st.session_state.category]
    available = [i for i in pool if i['name'] not in st.session_state.played_items]
    if available and st.session_state.current_question <= 5:
        target = random.choice(available)
        st.session_state.target_item = target
        st.session_state.played_items.append(target['name'])
        st.session_state.attempts = 0
    else:
        st.session_state.game_finished = True

if st.session_state.game_finished:
    st.balloons()
    st.title("🏆 Yarışma Bitti!")
    st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("🔄 Tekrar Oyna"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.stop()

# --- Oyun Ekranı ---
item = st.session_state.target_item
st.subheader(f"Soru: {st.session_state.current_question}/5 | Skor: {st.session_state.total_score}")

url = get_img_final(item['name'], st.session_state.category)

if url:
    try:
        # User-agent ekleyerek resmi indir
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        
        # Blur uygula
        blur_val = st.session_state.blur_levels[min(st.session_state.attempts, 4)]
        st.image(img.filter(ImageFilter.GaussianBlur(blur_val)), use_container_width=True)
    except:
        st.warning("Görsel yüklenirken bir sorun oluştu, yeni soruya geçiliyor...")
        st.session_state.target_item = None
        st.rerun()
else:
    st.error("Görsel bulunamadı, atlanıyor...")
    st.session_state.target_item = None
    st.rerun()

# --- Tahmin Bölümü ---
with st.form("guess_form", clear_on_submit=True):
    guess = st.text_input("Bu kim / ne?")
    if st.form_submit_button("Tahmin Et"):
        if is_guess_correct(guess, item['name']):
            st.success(f"Harika! Doğru cevap: {item['name']}")
            st.session_state.total_score += (5 - st.session_state.attempts) * 10 * st.session_state.mult
            time.sleep(2)
            st.session_state.target_item = None
            st.session_state.current_question += 1
            st.rerun()
        else:
            st.session_state.attempts += 1
            if st.session_state.attempts >= 5:
                st.error(f"Maalesef! Doğru cevap: {item['name']}")
                time.sleep(2)
                st.session_state.target_item = None
                st.session_state.current_question += 1
            st.rerun()

# İpuçları
if st.session_state.attempts > 0:
    st.info(f"📍 İpucu 1: {item['nationality']}")
if st.session_state.attempts > 2:
    st.info(f"💡 İpucu 2: {item['moment']}")
