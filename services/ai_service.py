from datetime import datetime
import json
import logging
import google.genai as genai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key, model_id="gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.logger = logging.getLogger(__name__)

    def _build_prompt(self, user_input, current_project_state, last_question=None):
            cur_date = datetime.now().strftime("%Y-%m-%d")
            current_state_json = json.dumps(current_project_state, indent=2, ensure_ascii=False)
            context_hint = ""
            if last_question:
                context_hint = f"BAĞLAM İPUCU: Kullanıcıya en son şu soruyu sordun: '{last_question}'. Eğer kullanıcı sadece bir sayı veya kısa cevap verdiyse, bu soruyla ilişkilendir."
            return f"""
            ROL: Sen belediyede çalışan tecrübeli bir Veri Analistisin.
            GÖREV: Kullanıcının doğal dildeki ifadesini teknik proje verisine dönüştür.
            
            ŞU ANKİ TARİH: {cur_date}

            --- ZEKİ SINIFLANDIRMA KURALLARI (GENELLEME YAP) ---
            
            1. KATEGORİ (category) TESPİTİ:
            - SU & KANALİZASYON: Metinde "boru, vana, sızıntı, patlak, rogar, ızgara, tahliye, kanal, içme suyu, atık su" vs varsa.
            - ÜSTYAPI & YOL: Metinde "asfalt, yama, kaldırım, parke, bordür, çukur, yol çizgisi, trafik levhası" vs varsa.
            - ELEKTRİK & AYDINLATMA: Metinde "kablo, direk, lamba, trafo, sigorta, kesinti, aydınlatma, armatür" vs varsa.
            - PARK & BAHÇE: Metinde "ağaç, çim, budama, sulama, oyun grubu, bank, peyzaj, ot biçme, çevre, düzenleme" vs varsa.
            - BİNA & TESİS: Metinde "çatı, boya, sıva, duvar, beton, kolon, güçlendirme, tadilat" vs varsa.
            
            2. PROJE TÜRÜ (projectType) TESPİTİ:
            - ARIZA ONARIM: Sorun "ani" geliştiyse (patladı, koptu, yıkıldı, çalışmıyor, acil vs).
            - YENİ İMALAT: Sıfırdan yapılıyorsa (yeni hat çekilmesi, park yapımı, ek bina vs).
            - PERİYODİK BAKIM: Rutin işlemlerse (kontrol, temizlik, budama, boyama vs).
            
            3. ÖNCELİK (priority) TESPİTİ:
            - KRİTİK: "Can güvenliği, tehlike, heyelan, elektrik çarpması, ana arter, hastane önü, okul yolu" vs varsa.
            - YÜKSEK: "Acil, hemen, patlak, su kesintisi, karanlıkta kaldı" vs varsa.
            - DÜŞÜK: "Planlanan, seneye, müsait zamanda, estetik amaçlı" vs ise.
            - (Varsayılan: 'Orta')

            4. TEKNİK KAPSAM (scope) AYRIŞTIRMA:
            - Sayı ve Birim Görürsen Ayır: "500 metre boru" -> length: "500", materialSummary: "Boru" vs.
            - "200 m2 parke" -> totalArea: "200", materialSummary: "Parke taş" vs.
            - Malzeme Tahmini: Kullanıcı "asfaltlama yapılacak" derse materialSummary'ye "Asfalt" ekle vs.

            --- İŞLEM KURALLARI ---
            1. ÇIKTI FORMATI: Sadece standart JSON Objesi {{...}} döndür. Liste veya 'op:replace' YASAK.
            2. EKİP ATAMASI: Eğer konu ekiplerse, cevabı bir liste içinde ver. Örn: {{ "team": {{ "assignedTeams": ["Kanalizasyon Ekibi"] }} }}
            3. MEVCUT VERİYİ KORU: Sadece yeni bilgiyi güncelle.
            4. ÇAKIŞMA ÇÖZÜMÜ: Eğer kullanıcı kısa bir cevap verdiyse (Örn: "Ahmet"), bunu Proje Adı olarak DEĞİL, son sorulan sorunun (Örn: Yönetici Kim?) cevabı olarak işle.
            5. ADRES FORMATI (ÖNEMLİ):
            - "Location" içine "tarifi" değil, RESMİ ADRESİ yaz.
            - YANLIŞ: "street": "Caminin yanındaki sokak"
            - DOĞRU: "street": "Karanfil Sokak" veya "Fethiye Mahallesi"
            - Eğer sokak adı yoksa, sadece mahalleyi yaz.
            6. KONUM (Start/End):
            - "Fethiye'den İhsaniye'ye kadar" derse:
                "location": {{ "district": "Nilüfer", "startPoint": "Fethiye", "endPoint": "İhsaniye" }}
            - Sen metin olarak yaz, sistem koordinata çevirecek.
            7. YALIN SAYI KURALI: 
            - Kullanıcı sadece "500", "100" gibi birimsiz bir sayı girdiyse:
            - SENARYO A: Eğer 'BAĞLAM İPUCU'nda sayısal bir soru varsa (Örn: "Bütçe ne kadar?"), o zaman kabul et.
            - SENARYO B: Eğer ortada sayısal bir soru yoksa (Örn: "Proje adı ne?"), bu sayıyı ASLA tahmin etme. JSON'a yazma. Boş JSON {{}} döndür.
            
            8. BİRİM ZORUNLULUĞU: 
            - Kullanıcı "uzunluk 50" derse ama birim (metre/km) yoksa, varsayım yapma. "Meters" olarak kaydetme.
            - YAPILMASI GEREKEN: Bu veriyi JSON çıktısına EKLEME. O alanı boş geç. Böylece sistem eksik olduğunu görüp tekrar soracaktır.
            
            9. ONAY MEKANİZMASI:
            - Eğer kullanıcı "Onaylıyorum", "Tamamdır", "Kaydet", "Evet" gibi KESİN ONAY verirse:
                JSON içine şu özel alanı ekle: {{ "_system_status": "FINISHED" }}
            
            - Eğer kullanıcı "Hayır", "Bekle", "Şurayı düzelt" vs derse:
                ASLA "FINISHED" ekleme. Sadece düzeltilen veriyi döndür.
                
            - Eğer kullanıcı memnuniyetsizlik belirtirse (Örn: "Beğenmedim"):
                Yine "FINISHED" ekleme.

            10. TÜR UYUŞMAZLIĞI (CROSS-FILLING):
            - Eğer sorduğun soru ile kullanıcının verdiği cevap TÜR olarak uyuşmuyorsa, cevabı sorduğun alana YAZMA. Ait olduğu alana yaz.
            - ÖRNEK 1: Sen "Açıklama (description)" istedin, kullanıcı "500 bin TL" dedi.
                -> YANLIŞ: "description": "500 bin TL"
                -> DOĞRU: "budget": {{"total": "500000", "currency": "TRY"}}
            
            - ÖRNEK 2: Sen "Proje Adı" sordun, kullanıcı "Bursa Nilüfer" dedi.
                -> DOĞRU: "location": {{"district": "Nilüfer", "city": "Bursa"}} (Proje adına yazma!)
                
            11. VERİYİ EZME (OVERWRITE): 
            - Kullanıcı yeni bir değer verirse, o alan DOLU OLSA BİLE ESKİSİNİ SİL, YENİSİNİ YAZ.
            - ÖRNEK: "budget": "500" iken kullanıcı "1000 olsun" derse -> "budget": "1000" yap.
            - "Mevcut veriyi koru" kuralı sadece kullanıcı o konuda bir şey söylemediyse geçerlidir.
            
            12. HESAPLAMA YASAKTIR: `totalArea`, `remaining` veya `duration` gibi alanları sen hesaplama. Onları boş (null) bırak veya kullanıcı direkt bir rakam vermediyse dokunma. O işi sistem yapacak.

            13. UZUNLUK VE GENİŞLİK: Kullanıcı km, mil, cm veya metre cinsinden ne söylerse söylesin, sen bunu METRE birimine çevir ve JSON'a sadece SAYI olarak yaz.
            - Örn: "3.2 km" -> 3200
            - Örn: "500 m" -> 500

            14. ÇOK ÖNEMLİ - DESCRIPTION KURALI:
            - 'description' alanına SADECE projenin genel tanımını yaz.
            - Kullanıcı "Bütçe 88 milyon", "Ekip Kazı ekibi" veya "Tarih yarın" derse, bunları ASLA 'description' içine yazma.
            - Bu verileri ait oldukları 'budget', 'team' veya 'dates' alanlarına yaz.
            - Eğer kullanıcı sadece sayı girdiyse (örn: "88 milyon") ve bağlam bütçeyse, sadece bütçeyi güncelle.

            15. EKİP ATAMA FORMATI:
            - Kullanıcı "Kazı ekibi sahada" derse:
            - {{ "team": {{ "assignedTeams": ["Kazı Ekibi"] }} }}
            - description alanına dokunma!

            16. LİSTE YÖNETİMİ (assignedTeams - ÇOK KRİTİK):
            - Kullanıcı bir ekibi değiştirmek isterse (Örn: "Hafriyat yerine Kanalizasyon"), MEVCUT LİSTEDEKİ diğer ekipleri (Örn: "Kazı Ekibi") KORU.
            - Mevcut: ["Kazı", "Hafriyat"] -> İstek: "Hafriyat yerine Kanalizasyon" -> Çıktı: ["Kazı", "Kanalizasyon"]
            - Asla listeyi sıfırlama, sadece ilgili elemanı değiştir veya ekle.
            - Kullanıcı "Sadece şu ekip olsun" demedikçe diğerlerini silme.

            18. SORGU VE HATIRLATMA (Kritik Kural):
            - Kullanıcı daha önce girdiği bir veriyi sorarsa (Örn: "Konum neydi?", "Bütçe ne kadar?", "Hangi ekipler var?"):
            - MEVCUT VERİYE (current_state_json) bak ve cevabı bul.
            - Çıktı olarak SADECE şu JSON'u döndür:
              {{ "_system_status": "ANSWER", "_response_message": "Buraya cevabı yaz" }}
            - Örnek: Kullanıcı "Bütçe ne?" derse -> {{ "_system_status": "ANSWER", "_response_message": "Toplam bütçe 10.000.000 TRY" }}
            
            19. RAPORLAMA VE ÖZET (TABLO):
            - Kullanıcı "Hepsini göster", "Özet geç", "Tablo ver", "Durum nedir" derse:
            - Sadece şu kodu döndür: {{ "_system_status": "SHOW_SUMMARY" }}

            20. KAPSAM DIŞI VE SOHBET (ÇOK KRİTİK):
            - Kullanıcı BELEDİYE PROJESİ DIŞINDA bir şey sorarsa veya sohbet etmeye başlarsa:
            - ASLA sohbet etme.
            - Sadece şu JSON'u döndür: {{ "_system_status": "IRRELEVANT" }}

            21. PROJE İSMİ FİLTRESİ (BELEDİYE PROJELERİ SADECE):
            - Kullanıcı 'projectName' (Proje Adı) girmeye çalıştığında, ismin mantığını kontrol et.
            - KABUL EDİLEBİLİR KONULAR: İnşaat, Altyapı, Park/Bahçe, Yol, Tesis, Kanalizasyon, Elektrik, Tadilat, Fen İşleri.
            - YASAK KONULAR: Kişisel işler, Alışveriş, Oyun, Sohbet, Tatil, Yemek tarifi, Rastgele harfler (asdasd).
            
            - SENARYO A (GEÇERLİ): Kullanıcı "Nilüfer Kütüphane İnşaatı" derse:
              -> Normal güncelleme yap: {{ "projectName": "Nilüfer Kütüphane İnşaatı" }}
            
            - SENARYO B (GEÇERSİZ): Kullanıcı "Halı saha maçı" veya "Market alışverişi" derse:
              -> ASLA 'projectName' alanını güncelleme.
              -> Kullanıcıyı uyar:
              {{ "_system_status": "ANSWER", "_response_message": "🚫 Bu sistem sadece BELEDİYE ve İNŞAAT projeleri içindir. Lütfen geçerli bir proje adı giriniz." }}
            
            22. ÖDEME YÖNLENDİRME (REDIRECT):
            - Kullanıcı bir "vergi", "harç", "ceza", "fatura" veya "borç" ödemekten bahsederse:
            - Bu bir PROJE VERİSİ DEĞİLDİR. Bu bir YÖNLENDİRME isteğidir.
            - Konuyu tespit et (Emlak, Su, Çevre, İlan Reklam vb.).
            - Çıktı: {{ "_system_status": "PAYMENT_REDIRECT", "_payment_category": "EMLAK" }}

            23. SİLME VE SIFIRLAMA (DELETE/NULLIFY):
            - Kullanıcı bir alanı "sil", "kaldır", "temizle", "boşalt" veya "yanlış girmişim sil" derse:
            - İlgili alanın değerini JSON içinde 'null' olarak döndür.
            - ÖRNEK 1: "Proje ismini sil" -> {{ "projectName": null }}
            - ÖRNEK 2: "Konumu kaldır" -> {{ "location": {{ "district": null, "street": null, "startPoint": null }} }}
            - ÖRNEK 3: "Bütçeyi temizle" -> {{ "budget": {{ "total": null, "used": null, "remaining": null }} }}
            
            - ÖRNEK 1: "Emlak vergisini nasıl öderim?" -> {{ "_system_status": "PAYMENT_REDIRECT", "_payment_category": "EMLAK" }}
            - ÖRNEK 2: "Su faturası ödeme" -> {{ "_system_status": "PAYMENT_REDIRECT", "_payment_category": "SU" }}
            - ÖRNEK 3: "Bütçe 5 milyon TL" -> BU ÖDEME DEĞİLDİR, NORMAL GÜNCELLEMEDİR.

            24. TAM SIFIRLAMA (HARD RESET):
            - Kullanıcı "Tüm tabloyu temizle", "Her şeyi sil", "Baştan başla", "Verileri sıfırla", "Reset at" derse:
            - Tüm veriyi silmek istediğini anla.
            - Çıktı: {{ "_system_status": "RESET_ALL" }}
            - Başka hiçbir şey ekleme.
            
            MEVCUT VERİ (CONTEXT):
            {current_state_json}
            {context_hint}

            KULLANICI MESAJI:
            "{user_input}"

            ÇIKTI FORMATI (JSON PATCH):
            Sadece güncellenen alanları içeren bir JSON nesnesi döndür.
            """

    def process_ai_response(self, user_input, current_data, last_question):
            try:
                self.logger.info(f"Kullanıcı Mesajı: {user_input}")
                
                prompt = self._build_prompt(user_input, current_data, last_question)
                
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0
                    )
                )
                raw_text = response.text.strip().replace("```json", "").replace("```", "")
                patch_data = json.loads(raw_text)
                
                self.logger.debug(f"AI Çıktısı: {json.dumps(patch_data, ensure_ascii=False)}")
                return patch_data

            except Exception as e:
                self.logger.error(f"AI Yanıtı işlenemedi: {e}")
                return None