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

# --- Wikipedia Güvenlik Ayarı ---
wikipedia.set_user_agent("GosterBakalimV5/1.0 (iletisim@projen.com)")

# --- Sayfa Ayarları ---
st.set_page_config(page_title="🌟 Göster Bakalım", layout="centered")

# --- Yenilenmiş Görsel Çekme Motoru ---
@st.cache_data(ttl=3600)
def get_img_final(name, cat):
    # 1. Yöntem: Wikipedia Page Images API (En güvenlisi)
    try:
        query = name
        if cat == "Şirket Logoları": query = f"{name} logo"
        
        S = requests.Session()
        URL = "https://en.wikipedia.org/w/api.php"
        
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": query,
            "prop": "pageimages",
            "piprop": "original",
            "redirects": 1
        }
        
        R = S.get(url=URL, params=PARAMS, timeout=5)
        DATA = R.json()
        
        pages = DATA['query']['pages']
        for k, v in pages.items():
            if 'original' in v:
                return v['original']['source']
    except:
        pass

    # 2. Yöntem: Yedek Motor (Picsum veya Placeholder - Oyunun çökmesini engeller)
    # Eğer Wikipedia'dan gelmezse, kategoriye göre rastgele ama sabit bir görsel döndürür
    hash_id = sum(ord(c) for c in name) % 1000 # İsimden benzersiz bir ID üretir
    if cat == "Şehirler":
        return f"https://picsum.photos/seed/{hash_id}/800/600"
    
    return None

# --- Yardımcı Fonksiyonlar ---
def is_guess_correct(user_guess, correct_name):
    if not user_guess: return False
    return fuzz.token_sort_ratio(user_guess.lower(), correct_name.lower()) >= 80

@st.cache_data
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
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
            if d == "Kolay": st.session_state.blur_levels, st.session_state.mult = [20, 15, 10, 5, 0], 1
            elif d == "Orta": st.session_state.blur_levels, st.session_state.mult = [40, 25, 15, 8, 0], 2
            else: st.session_state.blur_levels, st.session_state.mult = [70, 50, 30, 15, 0], 3
            st.session_state.game_init = True
            st.rerun()
    else:
        st.error("data.json dosyası bulunamadı!")
    st.stop()

# Soru Yönetimi
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
    st.balloons(); st.title("🏆 Oyun Bitti!"); st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("Tekrar Oyna"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.stop()

# --- Görüntüleme ---
item = st.session_state.target_item
st.subheader(f"Soru: {st.session_state.current_question}/5 | Skor: {st.session_state.total_score}")

url = get_img_final(item['name'], st.session_state.category)

if url:
    try:
        # Wikipedia'nın engellememesi için User-Agent ile çekiyoruz
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        img = Image.open(BytesIO(res.content)).convert("RGB")
        blur_val = st.session_state.blur_levels[min(st.session_state.attempts, 4)]
        st.image(img.filter(ImageFilter.GaussianBlur(blur_val)), use_container_width=True)
    except:
        st.warning("Görsel yüklenemedi, yeni soruya geçiliyor...")
        st.session_state.target_item = None
        st.rerun()
else:
    st.info("Bu öğe için görsel bulunamadı, yeni soru seçiliyor...")
    st.session_state.target_item = None
    time.sleep(1)
    st.rerun()

# Form
with st.form("guess_form", clear_on_submit=True):
    guess = st.text_input("Tahmininiz:")
    if st.form_submit_button("Gönder"):
        if is_guess_correct(guess, item['name']):
            st.success(f"✅ Doğru! {item['name']}")
            st.session_state.total_score += (5 - st.session_state.attempts) * 10 * st.session_state.mult
            time.sleep(2)
            st.session_state.target_item = None
            st.session_state.current_question += 1
            st.rerun()
        else:
            st.session_state.attempts += 1
            if st.session_state.attempts >= 5:
                st.error(f"❌ Elendin! Cevap: {item['name']}")
                time.sleep(2)
                st.session_state.target_item = None
                st.session_state.current_question += 1
            st.rerun()
