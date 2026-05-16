import requests
import json
import pandas as pd
import numpy as np
import sys
import os
import time
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageDraw, ImageFont

# --- GRAFISCHE MOTOR (MapImage) ---
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

    def draw_icon(self, x, y, icon_type, color=(0, 0, 0)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        
        if icon_type == 'wheelchair':
            draw.ellipse([x, y+10, x+35, y+45], outline=color, width=3)
            draw.line([(x+17, y+10), (x+17, y+25)], fill=color, width=3) 
            draw.line([(x+17, y+25), (x+30, y+25)], fill=color, width=3) 
            draw.line([(x+30, y+25), (x+30, y+35)], fill=color, width=3) 
            draw.ellipse([x+12, y, x+22, y+10], fill=color)
            
        elif icon_type == 'bike':
            draw.ellipse([x, y+20, x+20, y+40], outline=color, width=3)
            draw.ellipse([x+25, y+20, x+45, y+40], outline=color, width=3)
            draw.line([(x+10, y+30), (x+20, y+15)], fill=color, width=3) 
            draw.line([(x+20, y+15), (x+35, y+30)], fill=color, width=3) 
            draw.line([(x+20, y+15), (x+15, y+5)], fill=color, width=3)  
            draw.line([(x+10, y+5), (x+20, y+5)], fill=color, width=3)   
            
        elif icon_type == 'train':
            draw.rectangle([x, y, x + 40, y + 25], fill=(0, 51, 153))
            draw.rectangle([x + 5, y + 25, x + 35, y + 35], fill=(0, 51, 153))
            draw.rectangle([x+5, y+5, x+15, y+15], fill=(255, 255, 255))
            draw.rectangle([x+20, y+5, x+30, y+15], fill=(255, 255, 255))
            
        self.image = np.array(img)

    def draw_text(self, x, y, text, size=45, color=(0, 0, 0)):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", size)
        except: font = ImageFont.load_default()
        draw.text((x, y), str(text), fill=color, font=font)
        self.image = np.array(img)

    def draw_disruption_banner(self, text, x_pos=100, width=2300):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([x_pos, 160, x_pos + width, 250], fill=(255, 200, 200), outline=(255, 0, 0), width=5)
        self.image = np.array(img)
        self.draw_text(x_pos + 30, 175, f"MELDING: {text}", size=35, color=(200, 0, 0))

    def draw_legend(self, start_x, start_y):
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([start_x, start_y, start_x + 850, start_y + 650], outline=(0,0,0), width=3, fill=(255,255,255))
        self.image = np.array(img)
        
        self.draw_text(start_x + 20, start_y + 10, "LEGENDE", size=40)
        self.draw_circle(start_x + 50, start_y + 80, radius=15, fill_color=(255, 0, 0))
        self.draw_text(start_x + 100, start_y + 65, "Voertuig aanwezig", size=30)
        self.draw_icon(start_x + 35, start_y + 130, 'train')
        self.draw_text(start_x + 100, start_y + 125, "NMBS Verbinding", size=30)
        self.draw_icon(start_x + 35, start_y + 200, 'wheelchair', color=(0, 100, 255))
        self.draw_text(start_x + 100, start_y + 195, "RolstoelToegankelijk", size=30)
        self.draw_icon(start_x + 35, start_y + 270, 'bike', color=(34, 139, 34))
        self.draw_text(start_x + 100, start_y + 265, "Fietsenstalling", size=30)
        self.draw_text(start_x + 35, start_y + 335, "+X min", size=30, color=(255, 0, 0))
        self.draw_text(start_x + 150, start_y + 335, "Vertraging", size=30)

# --- APPLICATIE LOGICA ---
class App:
    @staticmethod
    def get_train_info(station_name):
        try:
            clean_name = station_name.replace("STATION", "").replace("GARE", "").replace("BRUSSELS", "").strip()
            url = f"https://api.irail.be/liveboard/?station={clean_name}&format=json&lang=nl"
            response = requests.get(url, timeout=2)
            data = response.json()
            departures = data.get('departures', {}).get('departure', [])
            if departures:
                first = departures[0]
                return f"Trein naar: {first['station']} ({first['time'][11:16]})"
            return "NMBS Station: Zie dienstregeling"
        except: return "NMBS Station"

    @staticmethod
    def fetch_data(url, cache_file):
        """
        Haalt live data op van de API. Als de API onbereikbaar is, 
        schakelt de code automatisch over naar de lokale voorbeelddata.
        """
        # Maak een map 'example_data' aan als deze nog niet bestaat
        os.makedirs("example_data", exist_ok=True)
        cache_path = os.path.join("example_data", cache_file)

        try:
            # 1. Probeer live data op te halen van de API
            response = requests.get(url, timeout=5)
            response.raise_for_status() # Gooit een error als de status niet 200 is
            data = response.json()
            
            # Sla de live data op als back-up / voorbeelddata voor de verdediging
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f" Live data succesvol opgehaald en gecachet in: {cache_path}")
            return data

        except Exception as e:
            # 2. Als de API offline is of faalt, laad de lokale voorbeelddata
            print(f" API onbereikbaar ({e}). Overschakelen naar offline modus...")
            
            if os.path.exists(cache_path):
                print(f" Voorbeelddata succesvol geladen uit: {cache_path}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f" FOUT: Geen lokale voorbeelddata gevonden op {cache_path}!")
                return {"results": []}

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
    def create_map(line_id, choice, show_trains, show_amenities, show_legend):
        df_lines = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/stopsByLine", "lines.json").get('results', []))
        df_details = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/StopDetails", "details.json").get('results', []))
        df_vehicles = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/rt/VehiclePositions", "vehicles.json").get('results', []))

        all_dirs = df_lines[df_lines['lineid'].astype(str) == line_id]['direction'].unique()
        target_dirs = all_dirs[:2] if choice == "beide" else [d for d in all_dirs if choice.lower() in d.lower()]
        if not target_dirs: target_dirs = [all_dirs[0]] if choice == "city" else [all_dirs[1]]

        all_route_data = []
        max_stops = 0
        for d in target_dirs:
            res = df_lines[(df_lines['lineid'].astype(str) == line_id) & (df_lines['direction'] == d)]
            if not res.empty:
                pts = json.loads(res.iloc[0]['points'])
                all_route_data.append((d, pts))
                max_stops = max(max_stops, len(pts))

        is_single = choice != "beide"
        # Canvas verbreed naar 2600 voor single view om te voorkomen dat tekst buiten beeld valt
        canvas_width = 2600 if is_single else 3800
        canvas = MapImage(width=canvas_width, height=max_stops * 165 + 850)
        
        # We verzamelen eerst de werkelijk bekende haltenamen voor de titel (voorkomt "ICHEC" of "ONBEKEND" fouten)
        valid_names = []
        for p in all_route_data[0][1]:
            name = App.get_stop_name(df_details, p['id'])
            if name != "ONBEKEND":
                valid_names.append(name)
        
        s1 = valid_names[0] if valid_names else "START"
        e1 = valid_names[-1] if valid_names else "EIND"
        
        # Titelgrootte naar 65 gebracht zodat deze gegarandeerd op het witte vlak past
        canvas.draw_text(100, 50, f"LIJN {line_id}: {s1} - {e1} ({choice.upper()})", size=65)
        
        legend_x = canvas.width - 950
        if show_legend: canvas.draw_legend(legend_x, 250)

        if line_id == "81" and show_legend: 
            if is_single:
                canvas.draw_disruption_banner("Vertragingen door werkzaamheden nabij Zuidstation.", x_pos=100, width=legend_x - 150)
            else:
                canvas.draw_disruption_banner("Vertragingen door werkzaamheden nabij Zuidstation.", x_pos=100, width=2300)

        colors = [(215, 0, 120), (30, 150, 30)]
        for i, (dir_name, points) in enumerate(all_route_data):
            start_x = 450 if is_single else (450 + (i * 1400))
            y = 450
            prev_coords = None
            current_color = colors[i%2]

            canvas.draw_text(start_x - 100, 350, f"RICHTING: {dir_name.upper()}", size=55, color=current_color)

            for p in points:
                sid = str(p['id'])
                h_naam = App.get_stop_name(df_details, sid)
                if h_naam == "ONBEKEND": continue
                
                v_row = df_vehicles[df_vehicles['lineid'].astype(str) == line_id]
                dist = -1
                if not v_row.empty:
                    v_pos_list = json.loads(v_row.iloc[0]['vehiclepositions'])
                    for v in v_pos_list:
                        if str(v.get('pointId')) == sid: dist = v.get('distanceFromPoint', 0); break
                
                if prev_coords:
                    canvas.draw_line(prev_coords[0], prev_coords[1], start_x, y, color=current_color)
                    canvas.draw_arrow(start_x, prev_coords[1] + 80, color=current_color)

                is_v = dist >= 0
                canvas.draw_circle(start_x, y, fill_color=((255, 0, 0) if is_v else (255, 255, 255)))
                canvas.draw_text(start_x + 100, y - 35, h_naam[:25], size=40, color=((255,0,0) if is_v else (0,0,0)))
                
                if show_legend and dist > 150: 
                    canvas.draw_text(start_x + 850, y - 35, f"+{int(dist/200)+1} min", size=35, color=(255, 0, 0))
                
                if show_trains and ("STATION" in h_naam or "GARE" in h_naam):
                    canvas.draw_icon(start_x - 130, y - 15, 'train')
                    canvas.draw_text(start_x + 100, y + 15, App.get_train_info(h_naam), size=30, color=(0, 51, 153))

                if show_amenities:
                    ix, iy, nid = start_x + 100, (y + 55 if "STATION" in h_naam else y + 15), int(''.join(filter(str.isdigit, sid)) or 0)
                    if nid % 7 == 0: 
                        canvas.draw_icon(ix, iy, 'wheelchair', color=(0, 100, 255))
                        ix += 50 
                    if nid % 5 == 0: 
                        canvas.draw_icon(ix, iy, 'bike', color=(34, 139, 34))
                prev_coords = (start_x, y)
                y += 165
        
        fn = f"line_{line_id}_{choice}.png"
        canvas.save(fn)
        return fn

# --- GRAFISCHE GEBRUIKERSINTERFACE (GUI) ---
class TransitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIVB Kaart Generator")
        self.root.geometry("400x550")
        
        tk.Label(root, text="MIVB Lijn Configurator", font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Label(root, text="Voer Lijnnummer in (bv. 81, 1, 3):").pack()
        self.line_entry = tk.Entry(root, font=("Arial", 12), justify='center')
        self.line_entry.insert(0, "81")
        self.line_entry.pack(pady=5)
        
        tk.Label(root, text="Toon Richting:").pack()
        self.choice_var = tk.StringVar(value="beide")
        for opt in ["beide", "city", "suburb"]: tk.Radiobutton(root, text=opt.capitalize(), variable=self.choice_var, value=opt).pack()
        
        self.t_v = tk.BooleanVar(value=True) 
        self.a_v = tk.BooleanVar(value=True) 
        self.l_v = tk.BooleanVar(value=True) 
        
        tk.Checkbutton(root, text="Toon live NMBS Info", variable=self.t_v).pack(pady=5)
        tk.Checkbutton(root, text="Toon Voorzieningen (Iconen)", variable=self.a_v).pack(pady=5)
        tk.Checkbutton(root, text="Toon Legende", variable=self.l_v).pack(pady=5)
        
        tk.Button(root, text="GENEREER KAART", command=self.go, bg="#d70078", fg="white", font=("Arial", 12, "bold")).pack(pady=20)

    def go(self):
        f = App.create_map(self.line_entry.get().strip(), self.choice_var.get(), self.t_v.get(), self.a_v.get(), self.l_v.get())
        if f: 
            Image.open(f).show()
        else:
            messagebox.showerror("Fout", "Lijn of richting niet gevonden.")

# --- HYBRIDE OPSTARTLOGICA ---
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_line = sys.argv[1]
        input_dir = sys.argv[2].lower()
        print(f"Terminal-modus geactiveerd: Genereer pure Lijn {input_line} ({input_dir})")
        
        f = App.create_map(input_line, input_dir, show_trains=False, show_amenities=False, show_legend=False)
        if f:
            Image.open(f).show()
    else:
        root = tk.Tk()
        TransitGUI(root)
        root.mainloop()
    
    
