from geopy.geocoders import Nominatim
import logging

class GeoService:
    def __init__(self, city="Bursa", country="Türkiye", user_agent="municipal_bot"):
        self.geolocator = Nominatim(user_agent=user_agent)
        self.city = city
        self.country = country
        self.logger = logging.getLogger(__name__)

    def get_coordinates(self, district: str, street: str = None) -> str:
        queries = []
        if street and district:
            queries.append(f"{street}, {district}, {self.city}, {self.country}")
        
        if district:
            queries.append(f"{district}, {self.city}, {self.country}")

        for query in queries:
            try:
                location = self.geolocator.geocode(query, timeout=5)
                if location:
                    self.logger.info(f"📍 Konum bulundu: {query}")
                    return f"{location.latitude}, {location.longitude}"
            except Exception as e:
                self.logger.error(f"❌ Harita sorgu hatası ({query}): {e}")
        
        self.logger.warning(f"⚠️ Konum belirlenemedi: {district} / {street}")
        return None