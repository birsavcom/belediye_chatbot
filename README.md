# Belediye Proje Chatbot

Bu proje; belediyelerde altyapı/üst yapı/park-bahçe vb. işleri **sohbet ederek** toplar, girilen bilgileri **yapısal JSON** verisine dönüştürür ve `data/data.json` dosyasına kaydeder.  
LLM tarafında **Google Gemini 2.0 Flash API** kullanılır ve modelden **yalnızca JSON** döndürmesi istenir (`response_mime_type="application/json"`).

## Özellikler

- ✅ Doğal dili proje alanlarına çevirme (projectName, category, projectType, priority, location, scope, dates, budget, team)
- ✅ “Eksik alan” mantığı: Bot, sıradaki eksik bilgiyi sorar
- ✅ Özet/rapor: “özet”, “tablo”, “durum” vb. isteklerde proje raporu döndürür
- ✅ Geri alma: `geri al` ile son güncellemeyi geri alır (history stack)
- ✅ Otomatik alanlar:
  - Koordinat: `geopy` + Nominatim ile (ilçe/sokak) üzerinden
  - Bütçe kalanı/harcanan: `CalculateService`
  - Tarih ve süre: başlangıç/bitiş/süre ilişkisi
  - ID / projectCode / lastUpdate otomatik üretimi

---

## Proje Yapısı (Önerilen)

```
.
├── src/
│   ├── manager.py              # FullContextManager (konuşma akışı)
│   └── models.py               # create_blank_structure()
├── services/
│   ├── ai_service.py           # Gemini çağrısı + prompt
│   ├── geo_service.py          # Geocoding
│   └── math_service.py         # Alan/bütçe/tarih hesapları
├── data/
│   └── data.json               # Canlı proje verisi
├── logs/
│   └── bot.log                 # Uygulama logları
├── .env                        # API key ve ortam ayarları
└── main.py                     # CLI giriş noktası (örnek)
```

Senin kodunda dosya adları farklıysa sorun değil; README’deki amaç anlaşılır bir çerçeve vermek.

---

## Gereksinimler

- Python **3.10+** (3.11 önerilir)
- İnternet erişimi (Gemini API + geocoding)
- Google Gemini API key

### Python Paketleri

- `google-genai`
- `python-dotenv`
- `geopy`

---

## Kurulum

### 1) Sanal ortam

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate  # Windows
```

### 2) Bağımlılıklar

```bash
pip install -r requirements.txt
```

> Eğer projede ekstra paketler varsa `requirements.txt` ile sabitlemen önerilir.

### 3) `.env` dosyası

Proje köküne `.env` oluştur:

```bash
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

### 4) Klasörleri oluştur

```bash
mkdir -p data logs
```

### 5) Çalıştırma

Eğer giriş dosyan `main.py` ise:

```bash
python main.py
```

Çıkış:

- Bot ilk soruyu sorar: “Projenin adı ne olsun?”
- Sen doğal dille cevap verirsin
- `data/data.json` sürekli güncellenir

---

## Kullanım

### Temel örnek tek mesaj (model testi)

Aşağıdaki gibi tek mesajda her şeyi gönderebilirsin:

```text
Akıllı Otopark Sistemi kurulumu yapılacak. Proje adı: Akıllı Otopark Nilüfer.
Açıklama: Nilüfer ilçesinde ana arter çevresindeki otoparklarda plaka tanıma + doluluk sensörleri + yönlendirme ekranları ile yönetim kurulacak.
Kategori: ÜSTYAPI & YOL. Proje türü: YENİ İMALAT. Öncelik: YÜKSEK (ana arter ve hastane yakını).
Konum: Nilüfer, Fethiye Mahallesi, Ata Bulvarı; başlangıç Fethiye girişi, bitiş İhsaniye Metro durağı.
Kapsam: 3.2 km hat; 2000 m2 sensör alanı; ekipman: LED ekran, LPR kamera, IoT sensör, fiber kablo, saha kabineti.
Tarih: 2026-03-01 başlasın, 45 gün sürsün.
Bütçe: 20.000.000 TL.
Yönetici: Mert Can, 0555 234 4323.
Ekipler: Elektrik & Aydınlatma, Üstyapı, Yazılım Entegrasyon.
Kaydet, onaylıyorum.
```

### Komutlar

- `geri al` → Son güncellemeyi geri alır
- `özet` / `tablo` / `durum` → Proje raporu döndürür
- `baştan başla` / `reset` → Tüm veriyi sıfırlar
- `kapat` / `exit` → Çıkış (dosyaya kaydeder)

---

## Gemini Entegrasyonu (Önemli Notlar)

Kodunuzda Gemini çağrısı şu şekilde:

- `response_mime_type="application/json"` → modelden JSON dönmesini zorunlu kılar
- `temperature=0` → daha deterministik çıktı

---

## Veri Dosyası

- Varsayılan: `data/data.json`
- Tek proje üzerinden ilerliyor: `data["projects"][0]`

Üretimde:
- Her belediye için ayrı tenant dosyası/DB (multi-tenant) önerilir
- `projectCode` ve `id` benzersiz olmalı

---

## Güvenlik

- `.env` dosyasını **asla repoya koymayın**
- Loglarda kişisel veri (telefon, isim) varsa KVKK/PDPL açısından maskeleme düşünün
- API key sızıntısını önlemek için:
  - sunucuda secret manager
  - CI/CD’de masked variables

---

## Sık Karşılaşılan Problemler

### 1) “Veriyi anlayamadım” çok geliyorsa
- Model JSON yerine metin döndürüyor olabilir.
- Prompt’un başına/sonuna “İlk karakter `{` son karakter `}`” gibi net kural ekleyin.
- `response_mime_type="application/json"` mutlaka açık olsun.

### 2) Koordinat bulunamıyor
- İlçe/sokak yazımı farklı olabilir (örn: kısaltma vs).
- Sadece ilçe ile denemek için `street` boş bırakılabilir.
- Rate limit: Nominatim sık çağrıda bloklayabilir; cache ekleyin.

### 3) Log klasörü yoksa hata
- `logs/` klasörünü oluşturun: `mkdir -p logs`