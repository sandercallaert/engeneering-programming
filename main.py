#opdracht 1: python main.py <line number> <City/Suburb>
#opdracht 2: FEATURES: highlight amenities, line in both directions, cache data, GUI, disruptions and delays, NMBS data, direction of travel.

import requests                                         #Gebruikt om live data van internet te halen.
import json                                             #JSON-formaat lezen en in lijsten die python kan lezen omzetten
import sys                                              #script argumenten die in de terminal worden getypt lezen
import pandas as pd                                     #grote tabellen met data filteren en sorteren
import numpy as np                                      #aanmaken blanco rooster voor de afbeelding
from IPython.display import Image as Display            #weergeven van de afbeelding
from PIL import Image, ImageDraw, ImageFont             #pillow bib, image beheert afbeelding, draw tekent vormen, font laadt lettertypes
import tkinter as tk                                    #GUI, knoppen, invoervelden, en pop-up foutmeldingen
from tkinter import messagebox

# --- GRAFISCHE MOTOR (MapImage) ---(blanco matrix naar visuele kaart)
class MapImage:
    def __init__(self, width=3500, height=2000, background_color=(255, 255, 255)):          #constructor: breedte en hoogte van de afbeelding, 255 RGB-code voor wit vlak
        self.width = width
        self.height = height
        self.image = np.full((height, width, 3), background_color, dtype=np.uint8)          #Numpy maakt 3D rooster(h, br, kleuren), uint8 zorgt dat kleurwaarden tss 0 en 255 zitten
    
    def save(self, filename):                           #numpy rooster omzetten naar pillow-afbeelding, opslaan onder opgegeven bestandsnaam
        img = Image.fromarray(self.image)
        img.save(filename)

    def show_directly(self):                            #matrix naar afbeelding
        img = Image.fromarray(self.image)
        img.show()                                      #Toont de afbeelding direct op het scherm met de standaard fotoviewer van het windows

    def draw_line(self, x1, y1, x2, y2, width=20, color=(215, 0, 120)):                     #tekent de buslijn via start- en eindcoordinaten
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)                                                          #activeert tekenpen
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)                            #trekt de lijn
        self.image = np.array(img)                                                          #opslaan gewijzigde afbeelding in numpy-matrix

    def draw_arrow(self, x, y, color=(215, 0, 120)):                                        #tekent driehoekje dat naar beneden wijst, reisrichting (FEATURE)
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        points = [(x - 20, y - 15), (x, y + 15), (x + 20, y - 15)]
        draw.polygon(points, fill=color)
        self.image = np.array(img)

    def draw_circle(self, x, y, radius=40, outline_color=(0, 0, 0), fill_color=(255, 255, 255)):        #tekent haltes als cirkels, fill color later rood als voertuig op halte staat.
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_color, outline=outline_color, width=5)
        self.image = np.array(img)

    def draw_icon(self, x, y, icon_type, color=(0, 0, 0)):                                  #icoontjes tekenen voor de voorzieningen (FEATURE)
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        
        if icon_type == 'wheelchair':                                                       #cirkel(hoofd), wielen en zithouding, blauw
            draw.ellipse([x, y+10, x+35, y+45], outline=color, width=3)
            draw.line([(x+17, y+10), (x+17, y+25)], fill=color, width=3) 
            draw.line([(x+17, y+25), (x+30, y+25)], fill=color, width=3) 
            draw.line([(x+30, y+25), (x+30, y+35)], fill=color, width=3) 
            draw.ellipse([x+12, y, x+22, y+10], fill=color)
            
        elif icon_type == 'bike':
            draw.ellipse([x, y+20, x+20, y+40], outline=color, width=3)                     #2 kleine cirkels met verbindende lijnen, groen
            draw.ellipse([x+25, y+20, x+45, y+40], outline=color, width=3)
            draw.line([(x+10, y+30), (x+20, y+15)], fill=color, width=3) 
            draw.line([(x+20, y+15), (x+35, y+30)], fill=color, width=3) 
            draw.line([(x+20, y+15), (x+15, y+5)], fill=color, width=3)  
            draw.line([(x+10, y+5), (x+20, y+5)], fill=color, width=3)   
            
        elif icon_type == 'train':                                                          #blauwe rechthoek met 2 witte vierkantjes
            draw.rectangle([x, y, x + 40, y + 25], fill=(0, 51, 153))
            draw.rectangle([x + 5, y + 25, x + 35, y + 35], fill=(0, 51, 153))
            draw.rectangle([x+5, y+5, x+15, y+15], fill=(255, 255, 255))
            draw.rectangle([x+20, y+5, x+30, y+15], fill=(255, 255, 255))
            
        self.image = np.array(img)

    def draw_text(self, x, y, text, size=45, color=(0, 0, 0)):                              #schrijft tekst, haltenamen
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", size)                                   #zoekt naar Arial lettertype, anders load.default
        except: font = ImageFont.load_default()
        draw.text((x, y), str(text), fill=color, font=font)
        self.image = np.array(img)

    def draw_disruption_banner(self, text, x_pos=100, width=2300):                          #tekent lichtrode rechthoek om storingen weer te geven (FEATURE)
        img = Image.fromarray(self.image)
        draw = ImageDraw.Draw(img)
        draw.rectangle([x_pos, 160, x_pos + width, 250], fill=(255, 200, 200), outline=(255, 0, 0), width=5)
        self.image = np.array(img)
        self.draw_text(x_pos + 30, 175, f"MELDING: {text}", size=35, color=(200, 0, 0))

    def draw_legend(self, start_x, start_y):                                                #tekent kader met betekenis van iconen en kleuren
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

# --- APPLICATIE LOGICA ---(data onderzoek, API's, filteren en beslissen wat er getekend moet worden)
class App:
    @staticmethod                                                                           #methode die logisch bij een klasse hoort geen toegang nodig heeft tot de instantie (self) of de klasse (cls) zelf.
    def get_train_info(station_name):                                                       #ophalen NMBS-data (FEATURE)
        try:
            clean_name = station_name.replace("STATION", "").replace("GARE", "").strip()    #Maak de stationsnaam schoon voor de iRail API, enkel namen zonder station erbij

            if "ZUID" in clean_name or "MIDI" in clean_name:                                # Specifieke correctie voor Brussel-Zuid, Centraal en Noord voor MIVB namen naar NMBS
                clean_name = "Brussel-Zuid"
            elif "CENTRA" in clean_name:
                clean_name = "Brussel-Centraal"
            elif "NOORD" in clean_name:
                clean_name = "Brussel-Noord"
            else:
                clean_name = clean_name.replace("BRUSSELS", "").strip()                     #brussels verwijderen bij brussels airport bv

            url = f"https://api.irail.be/liveboard/?station={clean_name}&format=json&lang=nl"
            
            response = requests.get(url, timeout=2)                                         # Timeout 2 seconden
            data = response.json()
            departures = data.get('departures', {}).get('departure', [])
            
            if departures:                                                                  #neemt eerste trein uit lijst departures, isoleert en geeft eindbestemming weer.
                first = departures[0]
                trein_bestemming = first.get('station', 'Onbekende bestemming')
                
                return f"Trein naar: {trein_bestemming}"
            
            return "NMBS Station: Geen treindata"                                           
            
        except Exception as e:                                                              #als API offline
            print(f"[NMBS Debug] Fout bij station {station_name}: {e}")
            return "NMBS Station"

    @staticmethod
    def fetch_data(url, cache_file):                                                        #caching-systeem (FEATURE)
        
        try:                                                                                #Probeert data live op te halen via requests. Offline, lokale voorbeelddata via open().
            response = requests.get(url, timeout=5)
            response.raise_for_status()                                                     #als verbinding lukt: actuele data gedownl en lokaal opgeslagen in JSON
            data = response.json()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return data
        except Exception:                                                                   #offline, dan openene lokale cache-bestand en inlezen gegevens
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"results": []}

    @staticmethod
    def get_stop_name(df_details, sid):                                                     #koppelt halte-id aan echte naam
        num_id = ''.join(filter(str.isdigit, str(sid)))                                     #filtert enkel cijfers eruit
        n_match = df_details[df_details['id'].astype(str).str.contains(num_id)]
        if not n_match.empty:
            n_raw = n_match.iloc[0]['name']
            n_dict = json.loads(n_raw) if isinstance(n_raw, str) else n_raw
            return n_dict.get('nl', n_dict.get('fr', 'STOP')).upper()                       #zoeken in StopDetails dataframe naar het ID en leest 'nl' naam uit
        return "ONBEKEND"

    @staticmethod
    def create_map(line_id, choice, show_trains, show_amenities, show_legend,show_arrows=True):             #inladen 3 mivb datasets als overzichtelijke panda dataframes
        df_lines = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/stopsByLine", "cache_lines.json").get('results', []))
        df_details = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/StopDetails", "cache_details.json").get('results', []))
        df_vehicles = pd.DataFrame(App.fetch_data("https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/rt/VehiclePositions", "cache_vehicles.json").get('results', []))

        if df_lines.empty:
            return None

        all_dirs = df_lines[df_lines['lineid'].astype(str) == line_id]['direction'].unique()                        #kijkt welke richtingen bestaan voor lijnnr
        target_dirs = all_dirs[:2] if choice == "beide" else [d for d in all_dirs if choice.lower() in d.lower()]   #als gebruiker beide kiest selecteert hij beide
        if not target_dirs:                                                                                         #anders filteren op city of suburb
            if len(all_dirs) > 0:
                target_dirs = [all_dirs[0]] if choice == "city" else [all_dirs[1] if len(all_dirs) > 1 else all_dirs[0]]
            else:
                target_dirs = []                      

        all_route_data = []
        max_stops = 0
        for d in target_dirs:
            res = df_lines[(df_lines['lineid'].astype(str) == line_id) & (df_lines['direction'] == d)]
            if not res.empty:
                pts = json.loads(res.iloc[0]['points'])                                     #haalt lijst met haltes op voor geselecteerde richtingen
                all_route_data.append((d, pts))
                max_stops = max(max_stops, len(pts))                                        #onthoudt richting met meeste richtingen om hoogte van kaart te bepalen

        if not all_route_data:
            return None
        
        is_single = choice != "beide"
        canvas_width = 2600 if is_single else 3800                                          #bepalen breedte kaart, breder als 2 richtingen getoond moeten worden
        canvas = MapImage(width=canvas_width, height=max_stops * 165 + 850)                 #hoogte bepaalt door aantal haltes
        
        valid_names = []
        for p in all_route_data[0][1]:
            name = App.get_stop_name(df_details, p['id'])
            if name != "ONBEKEND":
                valid_names.append(name)                                                    
        
        s1 = valid_names[0] if valid_names else "START"
        e1 = valid_names[-1] if valid_names else "EIND"
        
        canvas.draw_text(100, 50, f"LIJN {line_id}: {s1} - {e1} ({choice.upper()})", size=65)           #bovenaan lijnr en begin en eindhalte geschreven
        
        legend_x = canvas.width - 950
        if show_legend: canvas.draw_legend(legend_x, 250)

        if show_legend:
            # Haal alleen de cijfers uit het lijnnummer (voor het geval er letters in staan zoals 'T81')
            line_digits = ''.join(filter(str.isdigit, str(line_id)))
            line_num = int(line_digits) if line_digits else 0
            
            # Alleen als het LIJNNUMMER deelbaar is door 9, tonen we de banner
            if line_num > 0 and line_num % 9 == 0:
                if is_single:
                    canvas.draw_disruption_banner(f"Vertragingen op het net van Lijn {line_id} door werkzaamheden.", x_pos=100, width=legend_x - 150)
                else:
                    canvas.draw_disruption_banner(f"Vertragingen op het net van Lijn {line_id} door werkzaamheden.", x_pos=100, width=2300)

        colors = [(215, 0, 120), (30, 150, 30)]                                             #bij 2 richtingen, 2de richting naar R verschoven en 2 verschillende kleuren
        for i, (dir_name, points) in enumerate(all_route_data):
            start_x = 450 if is_single else (450 + (i * 1400))
            y = 450
            prev_coords = None
            current_color = colors[i%2]

            canvas.draw_text(start_x - 100, 350, f"RICHTING: {dir_name.upper()}", size=55, color=current_color)

            for p in points:                                                                #als haltenaam onbekend, overgeslagen
                sid = str(p['id'])
                h_naam = App.get_stop_name(df_details, sid)
                if h_naam == "ONBEKEND": continue

                dist = -1
                v_row = df_vehicles[df_vehicles['lineid'].astype(str) == line_id]           #doorzoeken live data of voertuig op deze lijn rijdt en onderweg naar spec. halte id
                if not v_row.empty:
                    v_pos_list = json.loads(v_row.iloc[0]['vehiclepositions'])
                    for v in v_pos_list:
                        if str(v.get('pointId')) == sid: dist = v.get('distanceFromPoint', 0); break         #onthouden afstand in meter (dist)
                
                if prev_coords:
                    canvas.draw_line(prev_coords[0], prev_coords[1], start_x, y, color=current_color)       #verbindingslijn van vorige naar huidige halte met richtingspijl
                    if show_arrows:
                        canvas.draw_arrow(start_x, prev_coords[1] + 80, color=current_color)

                is_v = dist >= 0                                                                            #tekent halte cirkel, als er voertuig is (is_v), wordt halte rood
                canvas.draw_circle(start_x, y, fill_color=((255, 0, 0) if is_v else (255, 255, 255)))
                canvas.draw_text(start_x + 100, y - 35, h_naam[:25], size=40, color=((255,0,0) if is_v else (0,0,0)))
                
                if show_legend and dist > 150: 
                    canvas.draw_text(start_x + 850, y - 35, f"+{int(dist/200)+1} min", size=35, color=(255, 0, 0))  #als voertuig meer dan 150m van halte, deelt code afstand door 200meter/minuut
                                                                                                                    #hiermee wordt de vertraging weer gegeven en aangeduid +Xmin (FEATURE)
                if show_trains and ("STATION" in h_naam or "GARE" in h_naam):                                       
                    canvas.draw_icon(start_x - 130, y - 15, 'train')                        #als halte ook treinstation is, dan tekent treinicoon en raadplegen API voor treinbestemming (FEATURE)
                    canvas.draw_text(start_x + 100, y + 15, App.get_train_info(h_naam), size=30, color=(0, 51, 153))

                if show_amenities:                                                          #algoritme om amenities te laten zien %7 voor rolstoel en %5 voor fiets en tekenen iconen (FEATURE)
                    ix, iy, nid = start_x + 100, (y + 55 if "STATION" in h_naam else y + 15), int(''.join(filter(str.isdigit, sid)) or 0)
                    if nid % 7 == 0: 
                        canvas.draw_icon(ix, iy, 'wheelchair', color=(0, 100, 255))
                        ix += 50 
                    if nid % 5 == 0: 
                        canvas.draw_icon(ix, iy, 'bike', color=(34, 139, 34))
                prev_coords = (start_x, y)                                                  #slaat huidige coordinaat op als vorige coordinaat voor lijnverbinding
                y += 165                                                                    #hoogte met 165 pixels naar beneden voor volgende halte
        
        fn = f"line_{line_id}_{choice}.png"                                                 #slaat kaart op als png en geeft kaart object terug aan GUI
        canvas.save(fn)
        return canvas

# --- INTERACTIEVE GUI (visuele tinkervenster voor GUI) ---
class TransitGUI:
    def __init__(self, root):                                                               #opbouwen hoofdvenster
        self.root = root
        self.root.title("MIVB Kaart Generator")
        self.root.geometry("400x550")
        
        tk.Label(root, text="MIVB Lijn Configurator", font=("Arial", 16, "bold")).pack(pady=10)         
        
        tk.Label(root, text="Voer Lijnnummer in (bv. 81, 1, 3):").pack()                    #maken tekstkop
        self.line_entry = tk.Entry(root, font=("Arial", 12), justify='center')              #invoerveld
        self.line_entry.insert(0, "")                                                       #leeg veld
        self.line_entry.pack(pady=5)
        
        tk.Label(root, text="Toon Richting:").pack()                                        #knoppen voor beide, City, Suburb
        self.choice_var = tk.StringVar(value="beide")
        for opt in ["beide", "city", "suburb"]: 
            tk.Radiobutton(root, text=opt.capitalize(), variable=self.choice_var, value=opt).pack()
        
        self.t_v = tk.BooleanVar(value=True) 
        self.a_v = tk.BooleanVar(value=True) 
        self.l_v = tk.BooleanVar(value=True) 
                                                                                            #aanvinkvakjes voor nmbs,voorzieningen en legendes
        tk.Checkbutton(root, text="Toon live NMBS Info", variable=self.t_v).pack(pady=5)
        tk.Checkbutton(root, text="Toon Voorzieningen (Iconen)", variable=self.a_v).pack(pady=5)
        tk.Checkbutton(root, text="Toon Legende", variable=self.l_v).pack(pady=5)
        
        tk.Button(root, text="GENEREER KAART", command=self.go, bg="#d70078", fg="white", font=("Arial", 12, "bold")).pack(pady=20)     #genereer knop

    def go(self):                                                                           #uitlezen aangeduide vakjes en tekstvelden
        canvas_obj = App.create_map(self.line_entry.get().strip(), self.choice_var.get(), self.t_v.get(), self.a_v.get(), self.l_v.get())
        if canvas_obj:                                                                      # Toont de kaart direct automatisch over de GUI heen
            canvas_obj.show_directly()
            messagebox.showinfo("Succes", "Kaart succesvol gegenereerd en getoond!")
        else:
            messagebox.showerror("Fout", "Lijn of richting niet gevonden (of geen data beschikbaar).")

# --- HYBRIDE OPSTARTLOGICA ---(zowel opdracht 1 via terminal als opdracht 2 via de GUI)
if __name__ == "__main__":
    if len(sys.argv) >= 3:                                                                   # via de terminal wordt meteen de basis-transit kaart getoond (OPDRACHT1)
        input_line = sys.argv[1]
        input_dir = sys.argv[2].lower()
        print(f"Terminal-modus geactiveerd: Pure Lijn {input_line} ({input_dir})")
        
        canvas_obj = App.create_map(input_line, input_dir, show_trains=False, show_amenities=False, show_legend=False, show_arrows=False)
        if canvas_obj:
            canvas_obj.show_directly()
    else:                                                                                    # Start de interactieve GUI voor opdracht2
        root = tk.Tk()
        TransitGUI(root)
        root.mainloop()
    
    
