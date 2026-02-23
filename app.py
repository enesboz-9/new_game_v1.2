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

# --- Wikipedia Güvenlik Kimliği ---
wikipedia.set_user_agent("GosterBakalimGenel/1.0 (iletisim@projen.com)")

# --- Sayfa Ayarları ---
st.set_page_config(page_title="🌟 Göster Bakalım!", layout="centered")

# --- Wikipedia'dan Akıllı Resim Çekme ---
@st.cache_data(ttl=86400)
def get_wiki_image(name, category):
    try:
        # Kategoriye göre arama terimini güçlendir
        search_query = name
        if category == "Futbolcular": search_query += " footballer"
        elif category == "Şirket Logoları": search_query += " logo brand"
        elif category == "Ünlüler": search_query += " person"
        
        search_results = wikipedia.search(search_query)
        if not search_results: return None
        
        page = wikipedia.page(search_results[0], auto_suggest=False)
        
        # Senin başarılı filtren:
        valid_images = [
            img for img in page.images 
            if img.lower().endswith(('.jpg', '.jpeg', '.png')) 
            and not any(bad in img.lower() for bad in ["logo", "flag", "icon", "symbol", "stub"])
        ]
        
        return valid_images[0] if valid_images else None
    except:
        return None

# --- Resim İndirme (Tarayıcı Taklidi İle) ---
@st.cache_data
def fetch_image(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img.convert("RGB")
        return None
    except:
        return None

# --- Veri Yükleme ---
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

data = load_data()

# --- Session State ---
if "game_init" not in st.session_state:
    st.session_state.update({
        "game_init": False, "total_score": 0, "current_question": 1,
        "played_names": [], "target_item": None, "attempts": 0, "game_finished": False
    })

# --- Başlangıç Ekranı ---
if not st.session_state.game_init:
    st.title("🌟 Göster Bakalım!")
    if data:
        st.session_state.category = st.selectbox("Kategori Seçin:", list(data.keys()))
        diff = st.selectbox("Zorluk Seviyesi:", ["Kolay", "Orta", "Zor"])
        if st.button("OYUNA BAŞLA"):
            st.session_state.difficulty = diff
            if diff == "Kolay": st.session_state.blur_levels, st.session_state.multiplier = [20, 15, 8, 3, 0], 1
            elif diff == "Orta": st.session_state.blur_levels, st.session_state.multiplier = [40, 25, 15, 8, 0], 2
            else: st.session_state.blur_levels, st.session_state.multiplier = [65, 45, 25, 12, 0], 3
            st.session_state.game_init = True
            st.rerun()
    else:
        st.error("data.json bulunamadı!")
    st.stop()

# --- Soru Seçme ---
if st.session_state.target_item is None and not st.session_state.game_finished:
    pool = data[st.session_state.category]
    available = [p for p in pool if p['name'] not in st.session_state.played_names]
    if available and st.session_state.current_question <= 5:
        target = random.choice(available)
        st.session_state.target_item = target
        st.session_state.played_names.append(target['name'])
        st.session_state.attempts = 0
    else:
        st.session_state.game_finished = True

if st.session_state.game_finished:
    st.balloons(); st.header("🏆 Oyun Bitti!"); st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("🔄 Yeniden Başla"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.stop()

# --- Oyun Ekranı ---
item = st.session_state.target_item
st.subheader(f"Soru {st.session_state.current_question}/5 | Skor: {st.session_state.total_score}")
image_placeholder = st.empty()

image_url = get_wiki_image(item['name'], st.session_state.category)

if image_url:
    raw_img = fetch_image(image_url)
    if raw_img:
        idx = min(st.session_state.attempts, 4)
        blur_val = st.session_state.blur_levels[idx]
        display_img = raw_img.filter(ImageFilter.GaussianBlur(blur_val))
        image_placeholder.image(display_img, use_container_width=True)
    else:
        st.warning("Resim indirilemedi, atlanıyor...")
        time.sleep(1); st.session_state.target_item = None; st.rerun()
else:
    st.warning("Görsel bulunamadı, yeni soruya geçiliyor...")
    time.sleep(1); st.session_state.target_item = None; st.rerun()

# Tahmin Formu
with st.form("guess_form", clear_on_submit=True):
    user_guess = st.text_input("Tahmininiz:").lower().strip()
    if st.form_submit_button("Tahmin Et"):
        correct_name = item['name'].lower()
        # Senin başarılı esnek eşleşme mantığın:
        if user_guess and (user_guess in correct_name and len(user_guess) > 3):
            st.success(f"✅ DOĞRU! Cevap: {item['name']}")
            st.session_state.total_score += (5 - st.session_state.attempts) * 20 * st.session_state.multiplier
            time.sleep(2); st.session_state.target_item = None
            st.session_state.current_question += 1; st.rerun()
        else:
            st.session_state.attempts += 1
            if st.session_state.attempts >= 5:
                st.error(f"❌ Hak bitti! Cevap: {item['name']}")
                time.sleep(2); st.session_state.target_item = None
                st.session_state.current_question += 1
            st.rerun()

# İpuçları
if st.session_state.attempts > 0:
    st.info(f"📍 İpucu 1: {item['nationality']}")
if st.session_state.attempts > 2:
    st.info(f"💡 İpucu 2: {item['moment']}")
