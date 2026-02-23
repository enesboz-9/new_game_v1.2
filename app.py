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

# --- Wikipedia Güvenlik Ayarı ---
# Wikipedia'nın sizi bot sanıp engellememesi için geçerli bir User-Agent şarttır.
wikipedia.set_user_agent("GosterBakalimV3/1.0 (iletisim@projen.com)")

# --- Sayfa Ayarları ---
st.set_page_config(page_title="🌟 Göster Bakalım", layout="centered")

# --- Geliştirilmiş Görsel Çekme Fonksiyonu ---
@st.cache_data(ttl=3600)
def get_img(name, cat):
    try:
        # Wikipedia API'den doğrudan görsel URL'sini sorgula
        S = requests.Session()
        URL = "https://en.wikipedia.org/w/api.php"
        
        # Arama terimini optimize et
        query = name
        if cat == "Şirket Logoları": query = f"{name} brand logo"
        
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": query,
            "prop": "pageimages",
            "piprop": "original",
            "redirects": 1
        }
        
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        
        pages = DATA['query']['pages']
        for k, v in pages.items():
            if 'original' in v:
                return v['original']['source']
        
        # Eğer API'den sonuç gelmezse klasik yöntemi dene
        search = wikipedia.search(query)
        if search:
            page = wikipedia.page(search[0], auto_suggest=False)
            images = [img for img in page.images if img.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if images: return images[0]
            
        return None
    except:
        return None

# --- Yardımcı Fonksiyonlar ---
def is_guess_correct(user_guess, correct_name):
    if not user_guess: return False
    # Hem tam eşleşme hem de benzerlik kontrolü
    similarity = fuzz.token_sort_ratio(user_guess.lower(), correct_name.lower())
    return similarity >= 80

@st.cache_data
def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# --- Oyun Mantığı ---
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
        st.error("data.json dosyası eksik veya hatalı!")
    st.stop()

# Yeni Soru Belirleme
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

# Oyun Sonu
if st.session_state.game_finished:
    st.balloons()
    st.title("🏆 Yarışma Bitti!")
    st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("🔄 Tekrar Oyna"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.stop()

# --- Görsel Görüntüleme Bölümü ---
item = st.session_state.target_item
st.subheader(f"Soru: {st.session_state.current_question}/5 | Skor: {st.session_state.total_score}")

url = get_img(item['name'], st.session_state.category)

if url:
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        blur_val = st.session_state.blur_levels[min(st.session_state.attempts, 4)]
        st.image(img.filter(ImageFilter.GaussianBlur(blur_val)), use_container_width=True)
    except Exception as e:
        st.error("Görsel indirilemedi, yeni soruya geçiliyor...")
        st.session_state.target_item = None
        st.rerun()
else:
    st.warning(f"'{item['name']}' için görsel bulunamadı, atlanıyor...")
    time.sleep(1)
    st.session_state.target_item = None
    st.rerun()

# --- Tahmin Formu ---
with st.form("guess_form", clear_on_submit=True):
    user_guess = st.text_input("Tahmininiz:")
    btn = st.form_submit_button("Gönder")

if btn:
    if is_guess_correct(user_guess, item['name']):
        st.success(f"✅ Doğru! Cevap: {item['name']}")
        st.session_state.total_score += (5 - st.session_state.attempts) * 10 * st.session_state.mult
        time.sleep(2)
        st.session_state.target_item = None
        st.session_state.current_question += 1
        st.rerun()
    else:
        st.session_state.attempts += 1
        if st.session_state.attempts >= 5:
            st.error(f"❌ Bilemediniz! Doğru cevap: {item['name']}")
            time.sleep(2)
            st.session_state.target_item = None
            st.session_state.current_question += 1
        else:
            st.warning("Yanlış! Görsel netleşiyor...")
        st.rerun()

# İpuçları
if st.session_state.attempts > 0:
    st.info(f"📍 İpucu: {item['nationality']}")
if st.session_state.attempts > 2:
    st.info(f"💡 Bilgi: {item['moment']}")
