import streamlit as st
from PIL import Image, ImageFilter
import wikipedia
import requests
from io import BytesIO
import random
import time
import json
import os
from rapidfuzz import fuzz

# --- Ayarlar ---
wikipedia.set_user_agent("GosterBakalim/2.0 (iletisim@ornek.com)")
st.set_page_config(page_title="🌟 Göster Bakalım", layout="centered")

# --- Benzerlik Kontrolü (%80) ---
def is_guess_correct(user_guess, correct_name):
    similarity = fuzz.token_sort_ratio(user_guess.lower(), correct_name.lower())
    return similarity >= 80

# --- Veri Yükleme ---
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

data = load_data()

# --- Hafıza (Session State) ---
if "game_init" not in st.session_state:
    st.session_state.update({
        "game_init": False, "total_score": 0, "current_question": 1,
        "played_items": [], "target_item": None, "attempts": 0, "game_finished": False
    })

# --- BAŞLANGIÇ EKRANI ---
if not st.session_state.game_init:
    st.title("🌟 Göster Bakalım!")
    st.write("Kategori ve Zorluk Seçin:")
    
    if data:
        cat = st.selectbox("Kategori:", list(data.keys()))
        diff = st.selectbox("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"])
        
        if st.button("OYUNA BAŞLA"):
            st.session_state.category = cat
            st.session_state.difficulty = diff
            
            # --- ZORLUK AYARLARI ---
            if diff == "Kolay":
                # Daha az bulanık, daha kolay ipucu, standart puan
                st.session_state.blur_levels = [15, 10, 5, 2, 0]
                st.session_state.mult = 1
            elif diff == "Orta":
                # Orta bulanık, 2 kat puan
                st.session_state.blur_levels = [35, 20, 10, 5, 0]
                st.session_state.mult = 2
            else: # Zor
                # Çok yoğun bulanık, 3 kat puan
                st.session_state.blur_levels = [60, 45, 30, 15, 0]
                st.session_state.mult = 3
            
            st.session_state.game_init = True
            st.rerun()
    else:
        st.error("data.json dosyası eksik!")
    st.stop()

# --- Soru Seçme ---
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

# --- Oyun Sonu ---
if st.session_state.game_finished:
    st.balloons()
    st.title("🏆 Yarışma Bitti!")
    st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("Tekrar Oyna"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.stop()

# --- ANA OYUN ---
item = st.session_state.target_item
st.subheader(f"Soru: {st.session_state.current_question}/5 | Zorluk: {st.session_state.difficulty}")

# Wikipedia Resim Çekme
@st.cache_data(ttl=3600)
def get_img(name, cat):
    try:
        q = name + (" logo" if cat == "Şirket Logoları" else "")
        page = wikipedia.page(wikipedia.search(q)[0], auto_suggest=False)
        return [i for i in page.images if i.lower().endswith(('.jpg', '.png')) and "flag" not in i.lower()][0]
    except: return None

url = get_img(item['name'], st.session_state.category)
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}) if url else None
raw_img = Image.open(BytesIO(response.content)).convert("RGB") if response else None

if raw_img:
    # Bulanıklık uygula
    b = st.session_state.blur_levels[min(st.session_state.attempts, 4)]
    st.image(raw_img.filter(ImageFilter.GaussianBlur(b)) if b > 0 else raw_img, use_container_width=True)
else:
    st.error("Resim bulunamadı, geçiliyor...")
    st.session_state.target_item = None
    st.rerun()

# Tahmin ve Pas Formu
with st.form("game_form", clear_on_submit=True):
    guess = st.text_input("Tahmininiz:")
    c1, c2 = st.columns(2)
    if c1.form_submit_button("Tahmin Et"):
        if is_guess_correct(guess, item['name']):
            st.success(f"DOĞRU! Cevap: {item['name']}")
            # Puan = (Kalan Hak) * 10 * Zorluk Çarpanı
            puan = (5 - st.session_state.attempts) * 10 * st.session_state.mult
            st.session_state.total_score += puan
            time.sleep(2)
            st.session_state.target_item = None
            st.session_state.current_question += 1
            st.rerun()
        else:
            st.session_state.attempts += 1
            if st.session_state.attempts >= 5:
                st.error(f"HAKKINIZ BİTTİ! Cevap: {item['name']}")
                time.sleep(2)
                st.session_state.target_item = None
                st.session_state.current_question += 1
            st.rerun()
    
    if c2.form_submit_button("Pas Geç"):
        st.info(f"Cevap: {item['name']}")
        st.image(raw_img, use_container_width=True)
        time.sleep(3)
        st.session_state.target_item = None
        st.session_state.current_question += 1
        st.rerun()

# İpuçları (Yanlış yaptıkça açılır)
if st.session_state.attempts > 0: st.info(f"📍 Milliyet: {item['nationality']}")
if st.session_state.attempts > 1: st.info(f"💡 Bilgi: {item['moment']}")
