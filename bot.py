import os
from dotenv import load_dotenv
from src.manager import FullContextManager

load_dotenv()

def print_user_manual():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n" + "="*75)
    print("🏗️  İNŞAAT PROJE VE VERİ ASİSTANI (v5.0) - AKILLI MODÜLER SİSTEM")
    print("="*75)
    print("Merhaba! Ben şantiye verilerinizi düzenleyen, hesaplayan ve kaydeden asistanım.")
    print("Siz sadece sohbet eder gibi yazın, gerisini teknik servislere bırakın.\n")

    print("🚀 NELER YAPABİLİRİM? (ÖZELLİKLER)")
    print("-" * 40)
    print("📍 AKILLI KONUM (GeoService):")
    print("   • 'Nilüfer Fethiye mahallesi' derseniz, haritadan koordinatını bulurum.")
    print("   • Sokak/Cadde değişirse koordinatı otomatik güncellerim.")
    
    print("\n💰 OTOMATİK BÜTÇE (CalcService):")
    print("   • 'Bütçe 10 milyon, 2 milyonu harcandı' derseniz, kalanı (8M) ben hesaplarım.")
    print("   • Rakamları yazı ile yazsanız bile (Örn: 'üç buçuk milyon') anlarım.")

    print("\n📅 ZAMAN YÖNETİMİ (CalcService):")
    print("   • '1 Mayıs'ta başlayıp 45 gün sürecek' deyin, bitiş tarihini bulayım.")
    print("   • 'Bitiş 1 Eylül olsun' derseniz, başlangıç tarihini geriye çekerim.")

    print("\n📏 METRAJ VE ALAN:")
    print("   • '3.2 km uzunluk, 10 metre genişlik' derseniz, toplam alanı (m²) hesaplarım.")
    print("   • Kilometreyi metreye otomatik çeviririm.")

    print("\n⚠️  KOMUTLAR:")
    print("   🔙 'Geri al'   -> Hatalı giriş yaptığınızda son işlemi geri alır.")
    print("   ❌ 'Kapat'     -> Verileri kaydeder ve programdan çıkar.")
    print("="*75 + "\n")

def main():
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ HATA: .env dosyasında GEMINI_API_KEY bulunamadı!")
        return
    try:
        manager = FullContextManager(filename="data/data.json", reset=True)
    except Exception as e:
        print(f"❌ Başlatma Hatası: {e}")
        return

    print_user_manual()
    initial_msg = manager.get_next_missing_info()
    print(f"🤖 AI: {initial_msg}")

    while True:
        try:
            user_input = input("\n👤 Siz: ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "kapat", "çıkış", "q"]: 
                print("\n💾 Veriler kaydedildi. İyi çalışmalar!")
                break
            
            response = manager.chat(user_input)
            
            if response == "SESSION_COMPLETED_SUCCESSFULLY":
                print("\n✅ KAYIT TAMAMLANDI! Dosya oluşturuldu.")
                break
            
            print(f"🤖 AI: {response}")

        except KeyboardInterrupt:
            print("\n🚫 İşlem durduruldu.")
            break
        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()