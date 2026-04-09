import requests
import json
import pandas as pd
import numpy as np
import sys
from PIL import Image, ImageDraw, ImageFont

class MapImage:
    def __init__(self, width=2500, height=2000, background_color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.image = np.full((height, width, 3), background_color, dtype=np.uint8)
    
    def save(self, filename):
        img = Image.fromarray(self.image)
        img.save(filename)

    def draw_line(self, x1, y1, x2, y2, width=20, color=(215, 0, 120)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
        self.image = np.array(img)

    def draw_arrow(self, x, y, color=(215, 0, 120)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        # FEATURE 3: Richting aangeven met pijltjes
        points = [(x - 20, y - 15), (x, y + 15), (x + 20, y - 15)]
        draw.polygon(points, fill=color)
        self.image = np.array(img)

    def draw_circle(self, x, y, radius=40, outline_color=(0, 0, 0), fill_color=(255, 255, 255)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_color, outline=outline_color, width=5)
        self.image = np.array(img)

    def draw_icon(self, x, y, icon_type):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        if icon_type == 'wheelchair':
            draw.rectangle([x, y, x + 30, y + 30], fill=(0, 100, 255))
        elif icon_type == 'bike':
            draw.ellipse([x, y, x + 30, y + 30], fill=(34, 139, 34))
        self.image = np.array(img)

    def draw_text(self, x, y, text, size=45, color=(0, 0, 0)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        draw.text((x, y), text, fill=color, font=font)
        self.image = np.array(img)

    def draw_disruption_banner(self, text):
        # FEATURE 2: Real-time storingen tonen
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 150, 1500, 240], fill=(255, 200, 200), outline=(255, 0, 0), width=5)
        self.image = np.array(img)
        self.draw_text(120, 165, f"OPGELET: {text}", size=35, color=(200, 0, 0))

    def draw_legend(self, start_x, start_y):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([start_x, start_y, start_x + 700, start_y + 500], outline=(0,0,0), width=3)
        self.image = np.array(img)
        self.draw_text(start_x + 20, start_y + 10, "LEGENDE", size=40)
        self.draw_circle(start_x + 50, start_y + 80, radius=15, fill_color=(255, 0, 0))
        self.draw_text(start_x + 100, start_y + 65, "Voertuig aanwezig", size=30)
        self.draw_icon(start_x + 35, start_y + 130, 'wheelchair')
        self.draw_text(start_x + 100, start_y + 125, "Rolstoeltoegankelijk", size=30)
        self.draw_icon(start_x + 35, start_y + 190, 'bike')
        self.draw_text(start_x + 100, start_y + 185, "Fietsenstalling", size=30)
        self.draw_text(start_x + 35, start_y + 245, "+X min", size=30, color=(255, 0, 0))
        self.draw_text(start_x + 150, start_y + 245, "Vertraging voertuig", size=30)
        self.draw_arrow(start_x + 50, start_y + 315)
        self.draw_text(start_x + 100, start_y + 300, "Rijrichting", size=30)

class App:
    @staticmethod
    def fetch_data(url, cache_file):
        # FEATURE 4: Data Caching
        try:
            # Probeer lokaal bestand te laden
            df = pd.read_json(cache_file)
            print(f"Loaded {cache_file} from cache.")
            return {"results": df.to_dict(orient='records')}
        except:
            # Indien niet aanwezig, haal op van API
            print(f"Fetching {url} from API...")
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                # Sla op als cache
                pd.DataFrame(data.get('results', [])).to_json(cache_file)
                return data
            except Exception as e:
                print(f"Error connecting to API: {e}")
                return {"results": []}

    @staticmethod
    def run():
        if len(sys.argv) != 3:
            print("Usage: python main.py <line_number> <direction>")
            return

        line_id = sys.argv[1]
        direction_str = sys.argv[2].capitalize()

        # Data ophalen met Cache
        df_lines = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/stopsByLine", "cache_lines.json").get('results', []))
        df_details = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/StopDetails", "cache_details.json").get('results', []))
        df_vehicles = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/rt/VehiclePositions", "cache_vehicles.json").get('results', []))
        df_disruptions = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/rt/Disruptions", "cache_disruptions.json").get('results', []))

        # --- STORINGEN LOGICA ---
        disruption_msg = None
        if not df_disruptions.empty:
            for _, row in df_disruptions.iterrows():
                content = str(row.get('text', '')).lower()
                if line_id in content:
                    try:
                        text_dict = json.loads(row['text']) if isinstance(row['text'], str) else row['text']
                        disruption_msg = text_dict.get('nl', text_dict.get('fr', 'Storing gemeld'))
                    except: disruption_msg = "Verstoring op deze lijn"
                    break
        # Mock voor demo
        if not disruption_msg and line_id == "81":
             disruption_msg = "Vertragingen door wegwerkzaamheden nabij Zuidstation."

        line_mask = (df_lines['lineid'].astype(str) == line_id) & (df_lines['direction'] == direction_str)
        selected_line = df_lines[line_mask]
        if selected_line.empty:
            print("Lijn of richting niet gevonden.")
            return

        points_list = json.loads(selected_line.iloc[0]['points'])
        stop_ids = [str(p['id']) for p in points_list]

        # Voertuigen data
        active_stops_data = {}
        v_row = df_vehicles[df_vehicles['lineid'].astype(str) == line_id]
        if not v_row.empty:
            v_list = json.loads(v_row.iloc[0]['vehiclepositions'])
            for v in v_list:
                active_stops_data[str(v.get('pointId'))] = v.get('distanceFromPoint', 0)

        canvas = MapImage(width=2500, height=len(stop_ids) * 160 + 600)
        
        # --- RICHTING TITEL ---
        last_stop_id_raw = str(stop_ids[-1])
        last_numeric_id = ''.join(filter(str.isdigit, last_stop_id_raw))
        dest_match = df_details[df_details['id'].astype(str).str.contains(last_numeric_id)]
        dest_name = "Eindpunt"
        if not dest_match.empty:
            n_raw = dest_match.iloc[0]['name']
            n_dict = json.loads(n_raw) if isinstance(n_raw, str) else n_raw
            dest_name = n_dict.get('nl', n_dict.get('fr', str(n_raw)))

        canvas.draw_text(100, 50, f"LINE {line_id} > RICHTING {dest_name.upper()}", size=80)
        if disruption_msg: canvas.draw_disruption_banner(disruption_msg)
        canvas.draw_legend(1600, 100)

        x, y = 600, 350
        prev_coords = None

        for sid in stop_ids:
            numeric_sid = ''.join(filter(str.isdigit, sid))
            name_match = df_details[df_details['id'].astype(str).isin([sid, numeric_sid])]
            if name_match.empty: continue
            
            raw_name = name_match.iloc[0]['name']
            name_dict = json.loads(raw_name) if isinstance(raw_name, str) else raw_name
            halte_naam = name_dict.get('nl', name_dict.get('fr', sid))

            is_vehicle = sid in active_stops_data
            # FEATURE 2: Vertraging berekenen (+X min)
            delay_text = f"+{int(active_stops_data[sid]/200) + 1} min" if is_vehicle and active_stops_data[sid] > 150 else ""

            if prev_coords:
                canvas.draw_line(prev_coords[0], prev_coords[1], x, y)
                # FEATURE 3: Richting pijltje halverwege
                canvas.draw_arrow(x, prev_coords[1] + (y - prev_coords[1]) // 2)

            fill = (255, 0, 0) if is_vehicle else (255, 255, 255)
            canvas.draw_circle(x, y, radius=40, fill_color=fill)
            canvas.draw_text(x + 120, y - 30, halte_naam.upper(), size=45, color=((255, 0, 0) if is_vehicle else (0, 0, 0)))

            if delay_text:
                canvas.draw_text(x + 850, y - 30, delay_text, size=40, color=(255, 0, 0))

            # FEATURE 1: Amenities (Mock)
            if int(numeric_sid) % 7 == 0: canvas.draw_icon(x + 120, y + 25, 'wheelchair')
            if int(numeric_sid) % 5 == 0: 
                off = 160 if int(numeric_sid) % 7 == 0 else 120
                canvas.draw_icon(x + off, y + 25, 'bike')

            prev_coords = (x, y)
            y += 160

        out_file = f"line_{line_id}_{direction_str}_final.png"
        canvas.save(out_file)
        print(f"Success! Map saved as {out_file}")

if __name__ == "__main__":
    App.run()