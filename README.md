# AOE2DE Stats Tracker (GODO Takip)

Age of Empires II: Definitive Edition oyuncu istatistiklerini takip eden, maç geçmişlerini analiz eden ve takım/rakip analizleri sunan bir Streamlit uygulamasıdır.

## Özellikler

- **Oyuncu Takibi:** Belirlenen oyuncuların maç geçmişini otomatik çeker.
- **Detaylı Analiz:** Maç süreleri, harita kazanma oranları, medeniyet (civ) istatistikleri.
- **Rivalry & Synergy:** Takım arkadaşı ve rakiplerle olan kazanma oranları.
- **Fail-Fast:** Veritabanı bağlantı sorunlarında anında uyarı verir.
- **Admin Paneli:** Manuel güncelleme tetikleme, oyuncu ekleme/silme ve sistem teşhisi.

## Kurulum

1.  **Gereksinimler:**
    *   Python 3.10+
    *   PostgreSQL (veya test için SQLite)

2.  **Sanal Ortam ve Bağımlılıklar:**
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    
    # Bağımlılıkları yükle
    pip install -r requirements.txt
    ```

3.  **Konfigürasyon:**
    Proje ana dizininde `.env` dosyası oluşturun veya sistem ortam değişkenlerini ayarlayın.
    
    ```env
    # .env örneği
    DATABASE_URL=postgresql://user:password@localhost:5432/aoe2stats
    
    # Veya SQLite için (varsayılan):
    # DATABASE_URL=sqlite:///./aoe_stats.db
    ```

    *Not: Streamlit Cloud dağıtımı için `secrets.toml` kullanılır.*

## Çalıştırma

### 1. Web Arayüzü (Ana Uygulama)
Uygulamayı başlatmak için:

```bash
streamlit run app/main.py
```

Tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

### 2. Arka Plan İşçisi (Worker)
Verilerin her gün otomatik güncellenmesi için worker servisini ayrı bir terminalde çalıştırın:

```bash
python services/worker.py
```
*Not: Admin panelindeki "Trigger Daily Update" butonu da manuel olarak bu işlemi tetikler.*

## Proje Yapısı

*   `app/`: Streamlit arayüz kodları (`main.py` ve `pages/`).
*   `services/`: İş mantığı.
    *   `etl/`: Veri çekme (`fetcher.py`). **Resmi AoE2 API kullanılır.**
    *   `db/`: Veritabanı modelleri ve bağlantı.
    *   `analysis/`: İstatistik hesaplama (`aggregator.py`).
*   `tests/`: Test senaryoları.

## Sorun Giderme

*   **Veritabanı Hatası:** `DATABASE_URL` ayarını kontrol edin.
*   **0 Maç Çekiliyor:** Steam/AoE API sunucularında bakım olabilir. Admin panelindeki "Diagnostics" bölümünden API durumunu kontrol edin.
