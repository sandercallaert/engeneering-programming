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
        draw.rectangle([start_x, start_y, start_x + 750, start_y + 550], outline=(0,0,0), width=3)
        self.image = np.array(img)
        self.draw_text(start_x + 20, start_y + 10, "LEGENDE", size=40)
        self.draw_circle(start_x + 50, start_y + 80, radius=15, fill_color=(255, 0, 0))
        self.draw_text(start_x + 100, start_y + 65, "Voertuig aanwezig", size=30)
        self.draw_icon(start_x + 35, start_y + 130, 'wheelchair')
        self.draw_text(start_x + 100, start_y + 125, "Toegankelijk", size=30)
        self.draw_icon(start_x + 35, start_y + 190, 'bike')
        self.draw_text(start_x + 100, start_y + 185, "Fietsenstalling", size=30)
        self.draw_text(start_x + 35, start_y + 245, "+X min", size=30, color=(255, 0, 0))
        self.draw_text(start_x + 150, start_y + 245, "Vertraging", size=30)
        self.draw_arrow(start_x + 50, start_y + 315)
        self.draw_text(start_x + 100, start_y + 300, "Rijrichting", size=30)

class App:
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
    def run():
        if len(sys.argv) < 2:
            print("Usage: python main.py <line_number>")
            return

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

        canvas = MapImage(width=3500, height=max_stops * 160 + 800)
        canvas.draw_text(100, 50, f"LINE {line_id} - DUAL DIRECTION OVERVIEW", size=80)
        canvas.draw_legend(2600, 100)

        if line_id == "81":
            canvas.draw_disruption_banner("Vertragingen door wegwerkzaamheden nabij Zuidstation.")

        line_colors = [(215, 0, 120), (30, 150, 30)]

        for i, (dir_name, points) in enumerate(all_route_data):
            start_x = 450 + (i * 1350)
            y = 450
            prev_coords = None
            current_color = line_colors[i]

            canvas.draw_text(start_x - 100, 350, f"RICHTING: {dir_name.upper()}", size=55, color=current_color)

            for p in points:
                sid = str(p['id'])
                num_id = ''.join(filter(str.isdigit, sid))
                
                n_match = df_details[df_details['id'].astype(str).str.contains(num_id)]
                if n_match.empty: continue
                
                n_raw = n_match.iloc[0]['name']
                n_dict = json.loads(n_raw) if isinstance(n_raw, str) else n_raw
                h_naam = n_dict.get('nl', n_dict.get('fr', ''))
                
                if not h_naam or h_naam.lower() == "onbekend": continue

                # Voertuigen
                dist = -1
                v_row = df_vehicles[df_vehicles['lineid'].astype(str) == line_id]
                if not v_row.empty:
                    v_positions = json.loads(v_row.iloc[0]['vehiclepositions'])
                    for v in v_positions:
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
                canvas.draw_text(start_x + 100, y - 35, h_naam[:25].upper(), size=40, color=t_color)

                if delay_text:
                    canvas.draw_text(start_x + 850, y - 35, delay_text, size=35, color=(255, 0, 0))

                # FEATURE 1: Amenities (ONDER de naam)
                icon_y = y + 15
                icon_x_offset = start_x + 100
                
                if int(num_id) % 7 == 0: 
                    canvas.draw_icon(icon_x_offset, icon_y, 'wheelchair')
                    icon_x_offset += 50
                if int(num_id) % 5 == 0: 
                    canvas.draw_icon(icon_x_offset, icon_y, 'bike')

                prev_coords = (start_x, y)
                y += 160

        canvas.save(f"line_{line_id}_final_v2.png")
        print(f"Lijn {line_id} voltooid met icoontjes onder de naam.")

if __name__ == "__main__":
    App.run()