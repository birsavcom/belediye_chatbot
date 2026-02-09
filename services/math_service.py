import logging
from datetime import datetime, timedelta

class CalculateService:
    def __init__(self, date_format="%Y-%m-%d"):
        self.date_format = date_format
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _clean_numeric(value):
        if value is None or str(value).strip() == "" or str(value).lower() == "none":
            return None
        try:
            return float(str(value).replace(".", "").replace(",", ""))
        except (ValueError, TypeError):
            return None

    def calculate_area(self, length, width):
        l = self._clean_numeric(length)
        w = self._clean_numeric(width)
        return l * w if l and w else None

    def calculate_budget(self, total=None, used=None, remaining=None):
        t, u, r = map(self._clean_numeric, [total, used, remaining])

        if t is not None and u is not None:
            r = t - u   
        elif t is not None and r is not None:
            u = t - r      
        elif u is not None and r is not None and t is None:
            t = u + r

        if all(v is not None for v in [t, u, r]):
            return {
                "total": str(int(t)),
                "used": str(int(u)),
                "remaining": str(int(r))
            }
        return {}

    def calculate_dates(self, start_str=None, duration=None, end_str=None):
        try:
            start_dt = datetime.strptime(start_str, self.date_format) if start_str else None
            end_dt = datetime.strptime(end_str, self.date_format) if end_str else None
            dur = int(duration) if duration else None

            if end_dt and dur:
                start_dt = end_dt - timedelta(days=dur)
                
            elif start_dt and dur and not end_dt:
                end_dt = start_dt + timedelta(days=dur)
            
            elif start_dt and end_dt and not dur:
                dur = (end_dt - start_dt).days

            if all([start_dt, end_dt, dur is not None]):
                return {
                    "plannedStart": start_dt.strftime(self.date_format),
                    "plannedEnd": end_dt.strftime(self.date_format),
                    "duration": str(dur)
                }
        except Exception as e:
            self.logger.error(f"Tarih hesaplama hatası: {e}")
        
        return {}