import os
import json
import uuid
import copy
import logging
from datetime import datetime
from src.models import create_blank_structure
from services.ai_service import AIService
from services.geo_service import GeoService
from services.math_service import CalculateService

class FullContextManager:
    def __init__(self, filename="data/data.json", api_key=None, reset=False):
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        
        self.ai_service = AIService(api_key=api_key)
        self.geo_service = GeoService(city="Bursa") 
        self.calc_service = CalculateService()
        
        self.history_stack = []
        self.last_question = None
        
        #ödeme 
        self.payment_links = {
            "EMLAK": "https://ebelediye.bursa.bel.tr/emlak-vergisi-odeme",
            "SU": "https://buski.gov.tr/fatura-odeme",
            "CEVRE": "https://ebelediye.bursa.bel.tr/cevre-temizlik-vergisi",
            "ILAN_REKLAM": "https://ebelediye.bursa.bel.tr/ilan-reklam",
            "GENEL": "https://ebelediye.bursa.bel.tr/hizli-odeme"
        }

        if reset and os.path.exists(self.filename):
            os.remove(self.filename)
            print(f"🗑️  Eski veri dosyası '{self.filename}' silindi.")

        self.data = self.load_data()
        
        if not os.path.exists(self.filename):
            self.save()
            print(f"♻️ Sistem sıfırlandı. '{self.filename}' dosyası oluşturuldu.")
        self.last_question = self.get_next_missing_info()

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "projects" in data and data["projects"]:
                        return data
            except Exception as e:
                self.logger.error(f"Dosya okuma hatası: {e}")
        
        return create_blank_structure()

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def create_snapshot(self, force=False):
        if not self.history_stack:
            self.history_stack.append(copy.deepcopy(self.data))
            return

        if force or self.data != self.history_stack[-1]:
            self.history_stack.append(copy.deepcopy(self.data))

    def undo_last_action(self):
        if not self.history_stack:
            return "Geri alınacak işlem yok."
        
        self.data = self.history_stack.pop()
        self.save()
        self.last_question = self.get_next_missing_info()
        return f"⏪ Son işlem geri alındı.\n\nAI: {self.last_question}"

    def update_recursive(self, target, source):
        if not isinstance(source, dict):
            return

        for key, value in source.items():
            if isinstance(value, dict):
                if key not in target or not isinstance(target[key], dict):
                    target[key] = {}
                self.update_recursive(target[key], value)
            else:
                target[key] = value

    def generate_summary_table(self):
        p = self.data["projects"][0]
        
        loc = p.get("location", {})
        scope = p.get("scope", {})
        budget = p.get("budget", {})
        dates = p.get("dates", {})
        team = p.get("team", {})
        pm = team.get("projectManager", {})

        w_label = 30
        w_value = 55
        line = f"+{'-' * (w_label + 2)}+{'-' * (w_value + 2)}+"

        def row(label, value):
            value_str = str(value) if value is not None else "-"
            if len(value_str) > w_value:
                value_str = value_str[:w_value-3] + "..."
            return f"| {label:<{w_label}} | {value_str:<{w_value}} |"

        table = [
            f"\n📊 PROJE TAM DETAY RAPORU ({datetime.now().strftime('%d.%m.%Y %H:%M')})",
            line,
            f"| {'ALAN ADI':<{w_label}} | {'DEĞER':<{w_value}} |",
            line,
            row("Proje ID", p.get("id")),
            row("Proje Kodu", p.get("projectCode")),
            row("Son Güncelleme", p.get("lastUpdate")),
            line,
            row("Proje Adı", p.get("projectName")),
            row("Açıklama", p.get("description")),
            row("Kategori", p.get("category")),
            row("Proje Türü", p.get("projectType")),
            row("Öncelik", p.get("priority")),
            line,
            row("İlçe", loc.get("district")),
            row("Mahalle / Sokak", loc.get("street")),
            row("Başlangıç (Koord/Adres)", loc.get("startPoint")),
            row("Bitiş (Koord/Adres)", loc.get("endPoint")),
            line,
            row("Uzunluk", f"{scope.get('length')} m" if scope.get('length') else "-"),
            row("Genişlik", f"{scope.get('width')} m" if scope.get('width') else "-"),
            row("Toplam Alan", f"{scope.get('totalArea')} m²" if scope.get('totalArea') else "-"),
            row("Malzeme Özeti", scope.get("materialSummary")),
            line,
            row("Planlanan Başlangıç", dates.get("plannedStart")),
            row("Planlanan Bitiş", dates.get("plannedEnd")),
            row("Süre (Gün)", dates.get("duration")),
            line,
            row("Toplam Bütçe", f"{budget.get('total')} {budget.get('currency', '')}"),
            row("Harcanan", f"{budget.get('used')} {budget.get('currency', '')}"),
            row("Kalan", f"{budget.get('remaining')} {budget.get('currency', '')}"),
            line,
            row("Yönetici Adı", pm.get("name")),
            row("Yönetici Tel", pm.get("phone")),
            row("Atanan Ekipler", ", ".join(team.get("assignedTeams", []))),
            line
        ]
        standard_keys = {
            "id", "projectCode", "lastUpdate", "projectName", "description", 
            "category", "projectType", "priority", "location", "scope", 
            "dates", "budget", "team", "detail", "status"
        }

        extra_rows = []
        for key, value in p.items():
            if key not in standard_keys:
                extra_rows.append(row(f"Ekstra: {key}", value))

        detail_obj = p.get("detail", {})
        if isinstance(detail_obj, dict):
            for k, v in detail_obj.items():
                if k not in p: 
                     extra_rows.append(row(f"Detay: {k}", v))

        if extra_rows:
            table.append(f"| {'--- EKSTRA DETAYLAR ---':<{w_label + w_value + 3}} |")
            table.append(line)
            table.extend(extra_rows)
            table.append(line)

        return "\n".join(table)
    
    def auto_fill_system_fields(self):
        p = self.data["projects"][0]   
        loc = p.get("location", {})
        dist = loc.get("district", "")
        street = loc.get("street", "")
  
        if street and dist:
            coords = self.geo_service.get_coordinates(district=dist, street=street)
            if coords:
                if loc.get("startPoint") != coords:
                    print(f"[HARİTA GÜNCELLENDİ] {street} -> {coords}")
                    loc["startPoint"] = coords
        
        elif dist and not loc.get("startPoint"):
             coords = self.geo_service.get_coordinates(district=dist)
             if coords: loc["startPoint"] = coords

        scope = p.get("scope", {})
        area = self.calc_service.calculate_area(scope.get("length"), scope.get("width"))
        if area: scope["totalArea"] = area

        bud = p.get("budget", {})
        budget_updates = self.calc_service.calculate_budget(
            total=bud.get("total"), 
            used=bud.get("used"), 
            remaining=bud.get("remaining")
        )
        if budget_updates: bud.update(budget_updates)

        dates = p.get("dates", {})
        date_updates = self.calc_service.calculate_dates(
            start_str=dates.get("plannedStart"),
            duration=dates.get("duration"),
            end_str=dates.get("plannedEnd")
        )
        if date_updates: dates.update(date_updates)

        if not p.get("id"): 
            p["id"] = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
        
        if not p.get("projectCode"):
            p["projectCode"] = datetime.now().strftime("KY-%Y%m%d")
            
        p["lastUpdate"] = datetime.now().isoformat()
        
        pm = p.get("team", {}).get("projectManager", {})
        if pm.get("phone"):
             import re
             clean = re.sub(r'\D', '', pm["phone"])
             if len(clean) >= 10:
                 pm["phone"] = f"+90 {clean[-10:-7]} {clean[-7:-4]} {clean[-4:]}"

        p["detail"] = copy.deepcopy(p)
        if "detail" in p["detail"]: del p["detail"]["detail"]

    def _is_coord(self, value):
        return value and "," in str(value) and any(c.isdigit() for c in str(value))

    def chat(self, user_input):
        if user_input.lower() in ["geri al", "geri", "undo", "vazgeçtim"]:
            return self.undo_last_action()
        
        patch = self.ai_service.process_ai_response(
            user_input=user_input, 
            current_data=self.data["projects"][0], 
            last_question=self.last_question
        )
        if not patch:
            return "Veriyi anlayamadım, lütfen tekrar eder misiniz?"
        
        if patch.get("_system_status") == "PAYMENT_REDIRECT":
            category = patch.get("_payment_category", "GENEL")
            link = self.payment_links.get(category, self.payment_links["GENEL"])
            
            return (f"💳 **ÖDEME YÖNLENDİRMESİ**\n"
                    f"İlgili işlem için sizi güvenli ödeme sayfasına yönlendiriyorum:\n"
                    f"🔗 **{category} ÖDEME:** {link}\n\n"
                    f"🤖 AI: Biz projemize dönelim. {self.last_question}")
        
        system_status = patch.get("_system_status")
        if system_status == "IRRELEVANT":
            return f"⛔ Üzgünüm, sadece belediye proje verileri ile ilgili yardımcı olabilirim.\n\n🤖 AI: {self.last_question}"
            
        if system_status == "CANCELLED":
            return "SESSION_CANCELLED"
            
        if system_status == "ANSWER":
            return f"ℹ️ {patch.get('_response_message')}\n\n🤖 AI: {self.last_question}"

        if system_status == "SHOW_SUMMARY":
            return self.generate_summary_table() + f"\n\n🤖 AI: {self.last_question}"
        
        if system_status == "RESET_ALL":
            self.create_snapshot(force=True)
            self.data = create_blank_structure()
            self.save()
        
        if "_system_status" in patch:
            del patch["_system_status"]
            
        if "_response_message" in patch:
            del patch["_response_message"]

        if system_status == "FINISHED":
            self.update_recursive(self.data["projects"][0], patch)
            self.auto_fill_system_fields()
            self.save()
            return "SESSION_COMPLETED_SUCCESSFULLY"
        
        self.create_snapshot()

        self.update_recursive(self.data["projects"][0], patch)
        self.auto_fill_system_fields()
        self.save()
        
        self.last_question = self.get_next_missing_info()
        return self.last_question
        
    def get_next_missing_info(self):
        p = self.data["projects"][0]
        if not p.get("projectName"): return "Projenin adı ne olsun?"
        if not p.get("description"): return "Proje hakkında kısa bir açıklama girer misiniz?"
        if not p.get("category"): return "Proje kategorisi nedir? (Örn: Su İşleri, Üstyapı, Elektrik, Park Bahçe)"
        if not p.get("projectType"): return "Proje türü nedir? (Örn: Arıza Onarım, Yeni Yatırım, Periyodik Bakım)"
        if p.get("priority") is None:
            return "Projenin öncelik durumu nedir? (Düşük, Orta, Yüksek, Acil)"
        loc = p.get("location", {})
        if not loc.get("district"): return "Çalışma hangi ilçede yapılacak?"
        if not loc.get("street"): return "Hangi mahalle veya sokakta?" 
        if not loc.get("startPoint"): 
            if loc.get("street"):
                return f"'{loc.get('street')}' civarında tam başlangıç noktası neresi? (Bina no, Cami, Okul vb.)"
            return "Tam başlangıç noktası neresi?"
        if not loc.get("endPoint"): return "Çalışma nerede sonlanacak?"
        scope = p.get("scope", {})
        if not scope.get("length"): return "Projenin uzunluğu (metre) ne kadar?"
        if not scope.get("width"): return "Projenin genişliği (metre) ne kadar?" 
        if not scope.get("totalArea"): return "Toplam alan (m2) ne kadar?"
        if not scope.get("materialSummary"):
            return "Kullanılacak ana malzemeler nelerdir? (Örn: 100'lük boru, C35 beton)"
        dates = p.get("dates", {})
        if not dates.get("plannedStart"): return "İş ne zaman başlayacak?"
        if not dates.get("duration"): return "Tahminen kaç gün sürecek?"
        budget = p.get("budget", {})
        if not budget.get("total") or budget.get("total") == "0":
            return "Proje için ayrılan bütçe ne kadar?"
        team = p.get("team", {})
        pm = team.get("projectManager", {})
        if not pm.get("name") or pm.get("name") == "Atanmamış":
            return "Proje yöneticisi kim olacak?"  
        if not pm.get("phone"):
            return f"Proje yöneticisi {pm.get('name')} için telefon numarası girilmemiş. Lütfen numarayı belirtin."
        if not team.get("assignedTeams"):
            return "Hangi ekipler veya taşeronlar bu işe atandı?"

        return "✅ Mükemmel! Tüm detaylar eksiksiz alındı. Kaydı onaylıyor musunuz? (Evet/Hayır)"