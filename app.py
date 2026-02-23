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
# Engellenmemek için kendimizi tanıtıyoruz
wikipedia.set_user_agent("GosterBakalim/3.0 (iletisim@projen.com)")

# --- Sayfa Ayarları ---
st.set_page_config(page_title="🌟 Göster Bakalım", layout="centered")

# --- Resim Çekme Fonksiyonu (GELİŞTİRİLMİŞ) ---
@st.cache_data(ttl=3600)
def get_img(name, cat):
    try:
        # Arama terimini optimize et
        query = name
        if cat == "Şirket Logoları": query = f"{name} logo company"
        elif cat == "Futbolcular": query = f"{name} football player portrait"
        elif cat == "Ünlüler": query = f"{name} person"
        
        search = wikipedia.search(query)
        if not search: return None
        
        # En alakalı sayfayı çek
        page = wikipedia.page(search[0], auto_suggest=False)
        images = page.images
        
        # Çöp resimleri ele (logolar, ikonlar, bayraklar)
        clean_images = [
            img for img in images 
            if img.lower().endswith(('.jpg', '.jpeg', '.png')) 
            and not any(x in img.lower() for x in ['flag', 'icon', 'symbol', 'logo_steward', 'stub', 'wikimedia-logo', 'commons-logo'])
        ]
        
        return clean_images[0] if clean_images else None
    except:
        return None

# --- Yardımcı Fonksiyonlar ---
def play_sound(file_name):
    file_path = os.path.join("sounds", file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
                st.components.v1.html(md, height=0)
        except: pass

def is_guess_correct(user_guess, correct_name):
    if not user_guess: return False
    similarity = fuzz.token_sort_ratio(user_guess.lower(), correct_name.lower())
    return similarity >= 80

@st.cache_data
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
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
        st.error("data.json dosyası bulunamadı!")
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

# --- Ekran Tasarımı ---
item = st.session_state.target_item
st.subheader(f"Soru: {st.session_state.current_question}/5 | Skor: {st.session_state.total_score}")

url = get_img(item['name'], st.session_state.category)
img_placeholder = st.empty()

if url:
    try:
        res = requests.get(url, timeout=10)
        raw_img = Image.open(BytesIO(res.content)).convert("RGB")
        blur_val = st.session_state.blur_levels[min(st.session_state.attempts, 4)]
        img_placeholder.image(raw_img.filter(ImageFilter.GaussianBlur(blur_val)), use_container_width=True)
    except:
        st.warning("Resim şu an yüklenemiyor, bu soru atlanıyor...")
        time.sleep(1)
        st.session_state.target_item = None
        st.rerun()
else:
    st.info("🔄 Görsel Wikipedia'da aranıyor veya bulunamadı, lütfen bekleyin...")
    time.sleep(1)
    st.session_state.target_item = None # Resim yoksa yeni soruya geç
    st.rerun()

# Tahmin ve İpuçları
with st.form("guess_form"):
    guess = st.text_input("Tahmininiz nedir?")
    submitted = st.form_submit_button("Gönder")

if submitted:
    if is_guess_correct(guess, item['name']):
        st.success(f"👏 Tebrikler! Doğru cevap: {item['name']}")
        play_sound("correct.mp3")
        st.session_state.total_score += (5 - st.session_state.attempts) * 10 * st.session_state.mult
        time.sleep(2)
        st.session_state.target_item = None
        st.session_state.current_question += 1
        st.rerun()
    else:
        st.session_state.attempts += 1
        if st.session_state.attempts >= 5:
            st.error(f"❌ Maalesef! Doğru cevap şuydu: {item['name']}")
            play_sound("wrong.mp3")
            time.sleep(2)
            st.session_state.target_item = None
            st.session_state.current_question += 1
        else:
            st.warning("Yanlış tahmin! Resim biraz daha netleşti.")
            play_sound("wrong.mp3")
        st.rerun()

# İpucu Gösterimi
if st.session_state.attempts > 0:
    st.info(f"📍 İpucu 1 (Milliyet): {item['nationality']}")
if st.session_state.attempts > 2:
    st.info(f"💡 İpucu 2 (Bilgi): {item['moment']}")
