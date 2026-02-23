# 🌟 Göster Bakalım: Genel Kültür Tahmin Oyunu

Bu uygulama, Wikipedia üzerinden dinamik olarak çekilen görselleri (bulanıklaştırılmış halde) tahmin etmeye dayalı, eğlenceli ve interaktif bir bilgi yarışmasıdır. 

## 🚀 Özellikler

* **Çoklu Kategori:** Futbolcular, Şirket Logoları, Ünlüler ve Şehirler arasından seçim yapın.
* **Dinamik Zorluk Seviyeleri:** * **Kolay:** Az bulanıklık, standart puan.
    * **Orta:** Orta seviye bulanıklık, 2x puan çarpanı.
    * **Zor:** Yoğun bulanıklık, 3x puan çarpanı.
* **Akıllı Tahmin Sistemi:** `rapidfuzz` kütüphanesi sayesinde %80 benzerlikteki yazım hataları doğru kabul edilir.
* **İpucu Sistemi:** Her yanlış tahminde "Milliyet" ve "İkonik Bilgi" gibi ipuçları otomatik olarak açılır.
* **Wikipedia Entegrasyonu:** Görseller her seferinde Wikipedia üzerinden canlı olarak çekilir.

## 🛠️ Kurulum

Yerel makinenizde çalıştırmak için:

1. Bu depoyu klonlayın.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt

