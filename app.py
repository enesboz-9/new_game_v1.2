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

# --- Wikipedia Kimlik Tanımlama ---
wikipedia.set_user_agent("GosterBakalimV8/1.0 (iletisim@projen.com)")

# --- Sayfa Ayarları ---
st.set_page_config(page_title="🌟 Göster Bakalım!", layout="centered")

# --- Ses Çalma Fonksiyonu ---
def play_sound(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
                st.components.v1.html(md, height=0)
        except:
            pass

# --- Geliştirilmiş Akıllı Resim Çekme ---
@st.cache_data(ttl=86400)
def get_wiki_image(name, category):
    try:
        search_query = name
        # Arama terimi optimizasyonu
        if category == "Futbolcular": search_query += " footballer"
        elif category == "Şirket Logoları": search_query += " logo brand"
        elif category == "Ünlüler": search_query += " person"
        elif category == "Araba Modelleri": search_query += " car model"
        elif category == "Hayvanlar": search_query += " animal"

        # 1. YÖNTEM: Wikipedia Page Images API (En sağlamı)
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": search_query,
            "prop": "pageimages",
            "piprop": "original",
            "redirects": 1
        }
        res = requests.get(api_url, params=params, timeout=10).json()
        pages = res.get("query", {}).get("pages", {})
        for k, v in pages.items():
            if "original" in v:
                return v["original"]["source"]

        # 2. YÖNTEM: Klasik Arama ve Liste Kontrolü (Yedek)
        search_results = wikipedia.search(search_query)
        if search_results:
            page = wikipedia.page(search_results[0], auto_suggest=False)
            valid_images = [
                img for img in page.images 
                if img.lower().endswith(('.jpg', '.jpeg', '.png')) 
                and not any(bad in img.lower() for bad in ["logo", "flag", "icon", "symbol", "stub", "wikimedia"])
            ]
            if valid_images: return valid_images[0]
            
        return None
    except:
        return None

# --- Resim İndirme (Gelişmiş Headers) ---
@st.cache_data
def fetch_image(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")
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
        st.session_state.category = st.selectbox("Bir Kategori Seçin:", list(data.keys()))
        diff = st.selectbox("Zorluk Seviyesi Seçin:", ["Kolay", "Orta", "Zor"])
        if st.button("OYUNA BAŞLA"):
            st.session_state.difficulty = diff
            if diff == "Kolay": st.session_state.blur_levels, st.session_state.multiplier = [15, 10, 5, 2, 0], 1
            elif diff == "Orta": st.session_state.blur_levels, st.session_state.multiplier = [30, 20, 10, 5, 0], 2
            else: st.session_state.blur_levels, st.session_state.multiplier = [50, 35, 20, 8, 0], 3
            st.session_state.game_init = True
            st.rerun()
    else:
        st.error("data.json dosyası bulunamadı!")
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

# --- Oyun Bitiş ---
if st.session_state.game_finished:
    st.balloons(); st.header("🏆 Tur Tamamlandı!"); st.metric("Toplam Puan", st.session_state.total_score)
    if st.button("🔄 Tekrar Oyna"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.stop()

# --- Oyun Ekranı ---
item = st.session_state.target_item
st.title(f"Soru {st.session_state.current_question}/5")
st.subheader(f"Skor: {st.session_state.total_score}")

image_placeholder = st.empty()
image_url = get_wiki_image(item['name'], st.session_state.category)

if image_url:
    raw_img = fetch_image(image_url)
    if raw_img:
        idx = min(st.session_state.attempts, 4)
        blur_val = st.session_state.blur_levels[idx]
        display_img = raw_img.filter(ImageFilter.GaussianBlur(blur_val)) if blur_val > 0 else raw_img
        image_placeholder.image(display_img, use_container_width=True)
    else:
        st.warning("Resim indirilemedi, yeni soruya geçiliyor...")
        time.sleep(1); st.session_state.target_item = None; st.rerun()
else:
    st.warning("Resim bulunamadı, yeni soruya geçiliyor...")
    time.sleep(1); st.session_state.target_item = None; st.rerun()

# --- İpucu ve Tahmin ---
with st.expander("💡 İpucu Al", expanded=True):
    if st.session_state.attempts > 0: st.info(f"🌍 Milliyet/Köken: {item['nationality']}")
    if st.session_state.attempts > 1: st.info(f"✨ Hakkında: {item['moment']}")

with st.form("guess_form", clear_on_submit=True):
    user_guess = st.text_input("Tahmininiz nedir?").strip()
    col1, col2 = st.columns(2)
    submit = col1.form_submit_button("Tahmin Et", use_container_width=True)
    pass_btn = col2.form_submit_button("Pas Geç", use_container_width=True)

if submit:
    correct_name = item['name'].lower()
    if user_guess.lower() and (user_guess.lower() in correct_name and len(user_guess) > 3):
        play_sound("sounds/correct.mp3")
        image_placeholder.image(raw_img, use_container_width=True, caption=f"TEBRİKLER! {item['name']}")
        puan = (5 - st.session_state.attempts) * 20 * st.session_state.multiplier
        st.session_state.total_score += puan
        st.success(f"✅ DOĞRU! +{puan} Puan")
        time.sleep(3); st.session_state.target_item = None
        st.session_state.current_question += 1; st.rerun()
    else:
        st.session_state.attempts += 1
        if st.session_state.attempts >= 5:
            st.error(f"❌ Hak bitti! Cevap: {item['name']}")
            image_placeholder.image(raw_img, use_container_width=True, caption=f"Cevap: {item['name']}")
            time.sleep(3); st.session_state.target_item = None
            st.session_state.current_question += 1; st.rerun()
        else:
            st.warning(f"❌ Yanlış! {5 - st.session_state.attempts} hakkınız kaldı."); st.rerun()

if pass_btn:
    image_placeholder.image(raw_img, use_container_width=True, caption=f"Cevap: {item['name']}")
    st.info(f"⏭️ Pas geçildi. Cevap: **{item['name']}**")
    time.sleep(3); st.session_state.target_item = None
    st.session_state.current_question += 1; st.rerun()
