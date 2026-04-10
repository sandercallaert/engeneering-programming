import requests
import json
import pandas as pd
import numpy as np
import sys
from PIL import Image, ImageDraw, ImageFont

class MapImage:
    def __init__(self, width=3500, height=2000, background_color=(255, 255, 255)):
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
            draw.rectangle([x, y, x + 35, y + 35], fill=(0, 100, 255))
        elif icon_type == 'bike':
            draw.ellipse([x, y, x + 35, y + 35], fill=(34, 139, 34))
        elif icon_type == 'train':
            draw.rectangle([x, y, x + 40, y + 25], fill=(0, 51, 153))
            draw.rectangle([x + 5, y + 25, x + 35, y + 35], fill=(0, 51, 153))
        self.image = np.array(img)

    def draw_text(self, x, y, text, size=45, color=(0, 0, 0)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        draw.text((x, y), str(text), fill=color, font=font)
        self.image = np.array(img)

    def draw_disruption_banner(self, text):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 160, 2400, 250], fill=(255, 200, 200), outline=(255, 0, 0), width=5)
        self.image = np.array(img)
        self.draw_text(130, 175, f"MELDING: {text}", size=40, color=(200, 0, 0))

    def draw_legend(self, start_x, start_y):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([start_x, start_y, start_x + 850, start_y + 650], outline=(0,0,0), width=3)
        self.image = np.array(img)
        self.draw_text(start_x + 20, start_y + 10, "LEGENDE", size=40)
        self.draw_circle(start_x + 50, start_y + 80, radius=15, fill_color=(255, 0, 0))
        self.draw_text(start_x + 100, start_y + 65, "Voertuig aanwezig", size=30)
        self.draw_icon(start_x + 35, start_y + 130, 'train')
        self.draw_text(start_x + 100, start_y + 125, "NMBS Verbinding", size=30)
        self.draw_icon(start_x + 35, start_y + 200, 'wheelchair')
        self.draw_text(start_x + 100, start_y + 195, "RolstoelToegankelijk", size=30)
        self.draw_icon(start_x + 35, start_y + 270, 'bike')
        self.draw_text(start_x + 100, start_y + 265, "Fietsenstalling", size=30)
        self.draw_text(start_x + 35, start_y + 335, "+X min", size=30, color=(255, 0, 0))
        self.draw_text(start_x + 150, start_y + 335, "Vertraging", size=30)

class App:
    @staticmethod
    def get_train_info(station_name):
        try:
            clean_name = station_name.replace("STATION", "").replace("GARE", "").replace("BRUSSELS", "").strip()
            url = f"https://api.irail.be/liveboard/?station={clean_name}&format=json&lang=nl"
            response = requests.get(url, timeout=3)
            data = response.json()
            departures = data.get('departures', {}).get('departure', [])
            if departures:
                first = departures[0]
                return f"Trein naar: {first['station']} ({first['time'][11:16]})"
            return "NMBS Station: Zie dienstregeling"
        except:
            return "NMBS Station"

    @staticmethod
    def fetch_data(url, cache_file):
        try:
            df = pd.read_json(cache_file)
            return {"results": df.to_dict(orient='records')}
        except:
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                pd.DataFrame(data.get('results', [])).to_json(cache_file)
                return data
            except: return {"results": []}

    @staticmethod
    def get_stop_name(df_details, sid):
        num_id = ''.join(filter(str.isdigit, str(sid)))
        n_match = df_details[df_details['id'].astype(str).str.contains(num_id)]
        if not n_match.empty:
            n_raw = n_match.iloc[0]['name']
            n_dict = json.loads(n_raw) if isinstance(n_raw, str) else n_raw
            return n_dict.get('nl', n_dict.get('fr', 'STOP')).upper()
        return "ONBEKEND"

    @staticmethod
    def run():
        if len(sys.argv) < 2: return
        line_id = sys.argv[1]
        
        df_lines = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/stopsByLine", "lines.json").get('results', []))
        df_details = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/StopDetails", "details.json").get('results', []))
        df_vehicles = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/rt/VehiclePositions", "vehicles.json").get('results', []))

        available_directions = df_lines[df_lines['lineid'].astype(str) == line_id]['direction'].unique()
        all_route_data = []
        max_stops = 0
        
        for d_str in available_directions:
            mask = (df_lines['lineid'].astype(str) == line_id) & (df_lines['direction'] == d_str)
            res = df_lines[mask]
            if not res.empty:
                points = json.loads(res.iloc[0]['points'])
                all_route_data.append((d_str, points))
                max_stops = max(max_stops, len(points))
            if len(all_route_data) >= 2: break

        # Dynamische Titel bepalen (Eerste halte van richting 1 en eerste halte van richting 2)
        start_name = App.get_stop_name(df_details, all_route_data[0][1][0]['id'])
        end_name = App.get_stop_name(df_details, all_route_data[0][1][-1]['id'])
        full_title = f"LINE {line_id}: {start_name} - {end_name}"

        canvas = MapImage(width=3500, height=max_stops * 165 + 850)
        canvas.draw_text(100, 50, full_title, size=85)
        canvas.draw_legend(2550, 100)

        if line_id == "81":
            canvas.draw_disruption_banner("Vertragingen door wegwerkzaamheden nabij Zuidstation.")

        line_colors = [(215, 0, 120), (30, 150, 30)]

        for i, (dir_name, points) in enumerate(all_route_data):
            start_x = 450 + (i * 1400)
            y = 450
            prev_coords = None
            current_color = line_colors[i]

            canvas.draw_text(start_x - 100, 350, f"RICHTING: {dir_name.upper()}", size=55, color=current_color)

            for p in points:
                sid = str(p['id'])
                h_naam = App.get_stop_name(df_details, sid)
                if h_naam == "ONBEKEND": continue

                # Voertuigen
                v_row = df_vehicles[df_vehicles['lineid'].astype(str) == line_id]
                dist = -1
                if not v_row.empty:
                    v_pos = json.loads(v_row.iloc[0]['vehiclepositions'])
                    for v in v_pos:
                        if str(v.get('pointId')) == sid:
                            dist = v.get('distanceFromPoint', 0)
                            break
                is_v = dist >= 0
                delay_text = f"+{int(dist/200) + 1} min" if dist > 150 else ""

                if prev_coords:
                    canvas.draw_line(prev_coords[0], prev_coords[1], start_x, y, color=current_color)
                    canvas.draw_arrow(start_x, prev_coords[1] + 80, color=current_color)

                f_color = (255, 0, 0) if is_v else (255, 255, 255)
                canvas.draw_circle(start_x, y, fill_color=f_color)
                t_color = (255, 0, 0) if is_v else (0, 0, 0)
                canvas.draw_text(start_x + 100, y - 35, h_naam[:25], size=40, color=t_color)

                if delay_text:
                    canvas.draw_text(start_x + 850, y - 35, delay_text, size=35, color=(255, 0, 0))

                if "STATION" in h_naam or "GARE" in h_naam:
                    canvas.draw_icon(start_x - 130, y - 15, 'train')
                    train_info = App.get_train_info(h_naam)
                    canvas.draw_text(start_x + 100, y + 15, train_info, size=30, color=(0, 51, 153))

                # Amenities onder de naam
                icon_y = y + 55 if "STATION" in h_naam else y + 15
                icon_x = start_x + 100
                num_id = ''.join(filter(str.isdigit, sid))
                if int(num_id) % 7 == 0: 
                    canvas.draw_icon(icon_x, icon_y, 'wheelchair')
                    icon_x += 50
                if int(num_id) % 5 == 0: 
                    canvas.draw_icon(icon_x, icon_y, 'bike')

                prev_coords = (start_x, y)
                y += 165

        canvas.save(f"line_{line_id}_final_titled.png")
        print(f"Kaart voor lijn {line_id} gegenereerd met halte-titel.")

if __name__ == "__main__":
    App.run()