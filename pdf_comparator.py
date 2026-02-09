import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import cv2
import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, PageBreak
from reportlab.lib.units import inch
import fitz  # PyMuPDF
import os
import tempfile
try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False
    print("VAROVANIE: pikepdf nie je nainštalovaný. Filtrovanie vrstiev nebude fungovať.")


class PDFComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Porovnávatko")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Cesty k súborom
        self.old_pdf_path = tk.StringVar()
        self.new_pdf_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar()
        
        # Nastavenia farieb (RGB tuple)
        self.new_color = (255, 0, 0)  # Plná Farba - nové
        self.old_color = (206, 183, 138)  # Bledá hnedá (Light Brown)
        
        # Nastavenie automatického otvorenia PDF
        self.auto_open_pdf = tk.BooleanVar(value=True)
        
        # Správa vrstiev PDF
        self.layer_settings = {}  # Dictionary pre uloženie checkboxov vrstiev
        self.enabled_layers = set()  # Množina povolených vrstiev
        
        # Sledovanie posledných PDF súborov pre reset vrstiev
        self.last_old_pdf = ""
        self.last_new_pdf = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        # Nadpis
        title_label = tk.Label(
            self.root, 
            text="PDF Porovnávatko", 
            font=("Arial", 18, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Frame pre vstupy
        input_frame = tk.Frame(self.root, padx=20, pady=10)
        input_frame.pack(fill="both", expand=True)
        
        # Starý PDF
        self.create_file_row(
            input_frame, 
            "Starý PDF:", 
            self.old_pdf_path, 
            row=0
        )
        
        # Nový PDF
        self.create_file_row(
            input_frame, 
            "Nový PDF:", 
            self.new_pdf_path, 
            row=1
        )
        
        # Výstupný PDF
        self.create_file_row(
            input_frame, 
            "Výstupný PDF:", 
            self.output_pdf_path, 
            row=2,
            is_save=True
        )
        
        # Nastavenia farieb
        color_frame = tk.LabelFrame(
            self.root, 
            text="Nastavenie farieb",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10
        )
        color_frame.pack(fill="x", padx=20, pady=10)
        
        # Farba - nové farba
        red_frame = tk.Frame(color_frame)
        red_frame.pack(fill="x", pady=5)
        
        tk.Label(
            red_frame,
            text="Farba (nový obsah):",
            font=("Arial", 9),
            width=25,
            anchor="w"
        ).pack(side="left")
        
        # Farebný indikátor pre červenú
        self.red_indicator = tk.Canvas(
            red_frame,
            width=40,
            height=25,
            bg=self._rgb_to_hex(self.new_color),
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.red_indicator.pack(side="left", padx=10)
        
        tk.Button(
            red_frame,
            text="Vybrať farbu...",
            command=self.choose_new_color,
            width=15
        ).pack(side="left", padx=5)
        
        tk.Label(
            red_frame,
            text=f"RGB: {self.new_color}",
            font=("Arial", 8),
            fg="gray"
        ).pack(side="left", padx=5)
        
        # Farba - odstránené
        green_frame = tk.Frame(color_frame)
        green_frame.pack(fill="x", pady=5)
        
        tk.Label(
            green_frame,
            text="Farba (odstránený obsah):",
            font=("Arial", 9),
            width=25,
            anchor="w"
        ).pack(side="left")
        
        # Farebný indikátor pre odstránené
        self.green_indicator = tk.Canvas(
            green_frame,
            width=40,
            height=25,
            bg=self._rgb_to_hex(self.old_color),
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.green_indicator.pack(side="left", padx=10)
        
        tk.Button(
            green_frame,
            text="Vybrať farbu...",
            command=self.choose_old_color,
            width=15
        ).pack(side="left", padx=5)
        
        tk.Label(
            green_frame,
            text=f"RGB: {self.old_color}",
            font=("Arial", 8),
            fg="gray"
        ).pack(side="left", padx=5)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, padx=20)
        self.progress_frame.pack(fill="x", pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame, 
            text="", 
            font=("Arial", 9)
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=300
        )
        
        # Frame pre tlačidlá
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=10)
        
        # Tlačidlo pre správu vrstiev
        layers_button = tk.Button(
            buttons_frame,
            text="Nastavenie vrstiev PDF",
            command=self.open_layer_settings,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        layers_button.pack(side="left", padx=5)
        
        # Tlačidlo porovnania
        compare_button = tk.Button(
            buttons_frame,
            text="Porovnať PDF",
            command=self.compare_pdfs,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        compare_button.pack(side="left", padx=5)
  
    def create_file_row(self, parent, label_text, var, row, is_save=False):
        """Vytvorí riadok s labelom, entry a tlačidlom pre výber súboru"""
        label = tk.Label(
            parent, 
            text=label_text, 
            font=("Arial", 10),
            width=15,
            anchor="w"
        )
        label.grid(row=row, column=0, pady=10, sticky="w")
        
        entry = tk.Entry(
            parent, 
            textvariable=var, 
            width=50,
            font=("Arial", 9)
        )
        entry.grid(row=row, column=1, pady=10, padx=10)
        
        button_text = "Uložiť ako..." if is_save else "Vybrať..."
        command = lambda: self.save_file(var) if is_save else self.browse_file(var)
        
        button = tk.Button(
            parent,
            text=button_text,
            command=command,
            width=12
        )
        button.grid(row=row, column=2, pady=10)
    
    def browse_file(self, var):
        """Otvorí dialóg pre výber PDF súboru"""
        filename = filedialog.askopenfilename(
            title="Vyberte PDF súbor",
            filetypes=[("PDF súbory", "*.pdf"), ("Všetky súbory", "*.*")]
        )
        if filename:
            var.set(filename)
    
    def save_file(self, var):
        """Otvorí dialóg pre uloženie PDF súboru"""
        filename = filedialog.asksaveasfilename(
            title="Uložiť výstupný PDF ako",
            defaultextension=".pdf",
            filetypes=[("PDF súbory", "*.pdf"), ("Všetky súbory", "*.*")]
        )
        if filename:
            var.set(filename)
    
    def _rgb_to_hex(self, rgb):
        """Konvertuje RGB tuple na hexadecimálny formát pre Tkinter"""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def check_pdf_change_and_reset_layers(self):
        """Skontroluje, či sa zmenili PDF súbory a resetuje výber vrstiev"""
        current_old = self.old_pdf_path.get()
        current_new = self.new_pdf_path.get()
        
        if current_old != self.last_old_pdf or current_new != self.last_new_pdf:
            # PDF sa zmenilo, resetujeme výber vrstiev
            self.enabled_layers.clear()
            self.layer_settings.clear()
            self.last_old_pdf = current_old
            self.last_new_pdf = current_new
    
    def get_pdf_layers(self, pdf_path):
        """Získa zoznam vrstiev z PDF súboru"""
        try:
            doc = fitz.open(pdf_path)
            layers = []
            
            # PyMuPDF používa layer_ui_configs() pre získanie vrstiev
            try:
                layer_list = doc.layer_ui_configs()
                if layer_list:
                    for layer in layer_list:
                        # Každá vrstva je dictionary s 'text' (meno vrstvy) a 'number' (ID)
                        layer_name = layer.get('text', f"Vrstva {layer.get('number', '?')}")
                        layers.append(layer_name)
            except:
                # Starší spôsob alebo alternatíva
                pass
            
            doc.close()
            return layers
        except Exception as e:
            return []
    
    def open_layer_settings(self):
        """Otvorí okno pre nastavenie vrstiev PDF"""
        # Validácia - musíme mať vybraté aspoň jeden PDF
        if not self.old_pdf_path.get() and not self.new_pdf_path.get():
            messagebox.showwarning("Upozornenie", "Vyberte aspoň jeden PDF súbor pre nastavenie vrstiev!")
            return
        
        # Skontrolujeme, či sa zmenili PDF súbory
        self.check_pdf_change_and_reset_layers()
        
        # Získame vrstvy z oboch PDF
        old_layers = self.get_pdf_layers(self.old_pdf_path.get()) if self.old_pdf_path.get() else []
        new_layers = self.get_pdf_layers(self.new_pdf_path.get()) if self.new_pdf_path.get() else []
        
        # Spojíme vrstvy z oboch PDF (odstránime duplikáty)
        all_layers = sorted(set(old_layers + new_layers))
        
        if not all_layers:
            messagebox.showinfo("Info", "Vybrané PDF súbory neobsahujú žiadne vrstvy.")
            return
        
        # Ak je enabled_layers prázdny (prvé otvorenie alebo po resete), nastavime všetky vrstvy
        if not self.enabled_layers:
            self.enabled_layers = set(all_layers)
        
        # Vytvoríme nové okno
        layer_window = tk.Toplevel(self.root)
        layer_window.title("Nastavenie vrstiev PDF")
        layer_window.geometry("500x450")
        layer_window.resizable(False, False)
        
        # Nadpis
        title_label = tk.Label(
            layer_window,
            text="Vyberte vrstvy na porovnanie",
            font=("Arial", 14, "bold"),
            pady=15
        )
        title_label.pack()
        
        # Info text
        info_text = f"Starý PDF: {len(old_layers)} vrstiev\nNový PDF: {len(new_layers)} vrstiev\nCelkovo: {len(all_layers)} unikátnych vrstiev"
        info_label = tk.Label(
            layer_window,
            text=info_text,
            font=("Arial", 9),
            fg="gray",
            justify="left"
        )
        info_label.pack()
        
        # Master checkbox pre všetky vrstvy
        master_var = tk.BooleanVar(value=True)
        
        def update_enabled_layers_global():
            """Aktualizuje enabled_layers podľa aktuálneho stavu checkboxov"""
            self.enabled_layers.clear()
            for layer_name, var in self.layer_settings.items():
                if var.get():
                    self.enabled_layers.add(layer_name)
        
        def toggle_all_layers():
            """Prepne všetky vrstvy naraz a automaticky uloží"""
            state = master_var.get()
            for layer_var in self.layer_settings.values():
                layer_var.set(state)
            # Automaticky uložíme
            update_enabled_layers_global()
        
        master_frame = tk.Frame(layer_window, pady=10)
        master_frame.pack(fill="x", padx=20)
        
        master_checkbox = tk.Checkbutton(
            master_frame,
            text="Vybrať / Zrušiť všetky vrstvy",
            variable=master_var,
            command=toggle_all_layers,
            font=("Arial", 10, "bold")
        )
        master_checkbox.pack(anchor="w")
        
        tk.Frame(layer_window, height=2, bg="gray").pack(fill="x", padx=20, pady=5)
        
        # Scrollable frame pre vrstvy
        canvas = tk.Canvas(layer_window, height=200)
        scrollbar = ttk.Scrollbar(layer_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 20))
        
        # Vytvoríme checkboxy pre každú vrstvu
        self.layer_settings.clear()
        
        def update_enabled_layers():
            """Aktualizuje enabled_layers podľa aktuálneho stavu checkboxov"""
            update_enabled_layers_global()
        
        for layer_name in all_layers:
            # Načítame uložený stav (ak existuje v enabled_layers)
            is_enabled = layer_name in self.enabled_layers
            var = tk.BooleanVar(value=is_enabled)
            self.layer_settings[layer_name] = var
            
            # Info o tom, v ktorých PDF je vrstva
            in_old = layer_name in old_layers
            in_new = layer_name in new_layers
            
            if in_old and in_new:
                suffix = " (oba PDF)"
            elif in_old:
                suffix = " (len starý PDF)"
            else:
                suffix = " (len nový PDF)"
            
            # Automatické ukladanie pri zmene checkboxu
            def create_callback(layer_var=var):
                return lambda: update_enabled_layers()
            
            checkbox = tk.Checkbutton(
                scrollable_frame,
                text=layer_name + suffix,
                variable=var,
                font=("Arial", 9),
                anchor="w",
                command=create_callback()
            )
            checkbox.pack(fill="x", pady=2, padx=10)
        
    def choose_new_color(self):
        """Otvorí color picker pre výber červenej farby"""
        color = colorchooser.askcolor(
            color=self._rgb_to_hex(self.new_color),
            title="Vyberte farbu pre nový obsah"
        )
        if color[0]:  # color[0] je RGB tuple, color[1] je hex string
            self.new_color = tuple(int(c) for c in color[0])
            self.red_indicator.config(bg=self._rgb_to_hex(self.new_color))
    
    def choose_old_color(self):
        """Otvorí color picker pre výber zelenej farby"""
        color = colorchooser.askcolor(
            color=self._rgb_to_hex(self.old_color),
            title="Vyberte farbu pre odstránený obsah"
        )
        if color[0]:  # color[0] je RGB tuple, color[1] je hex string
            self.old_color = tuple(int(c) for c in color[0])
            self.green_indicator.config(bg=self._rgb_to_hex(self.old_color))
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrahuje text z PDF súboru - DEPRECATED, používame vizuálne porovnanie"""
        pass
    
    def pdf_to_images(self, pdf_path, dpi=150, filter_layers=False):
        """Konvertuje všetky stránky PDF na obrázky
        
        Args:
            pdf_path: Cesta k PDF súboru
            dpi: Rozlíšenie renderovania
            filter_layers: Ak True, renderuje len vybrané vrstvy. Ak False, renderuje všetky vrstvy.
        """
        try:
            # Ak potrebujeme filtrovať vrstvy a máme pikepdf
            if filter_layers and self.enabled_layers and PIKEPDF_AVAILABLE:
                # Vytvoríme dočasný PDF s vypnutými vrstvami
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_pdf.close()
                
                try:
                    # Použijeme pikepdf na úpravu vrstiev
                    with pikepdf.open(pdf_path) as pdf:
                        # Získame OCG (Optional Content Groups)
                        if '/OCProperties' in pdf.Root:
                            ocprops = pdf.Root.OCProperties
                            
                            if '/OCGs' in ocprops:
                                ocgs = ocprops.OCGs
                                
                                # Nastavenie base state na OFF pre všetky vrstvy
                                if '/D' not in ocprops:
                                    ocprops.D = pikepdf.Dictionary()
                                
                                d_dict = ocprops.D
                                
                                # Nastavime BaseState na OFF (všetky vrstvy vypnuté)
                                d_dict.BaseState = pikepdf.Name('/OFF')
                                
                                # Vytvoríme zoznam vrstiev na zapnutie (ON array)
                                on_layers = pikepdf.Array()
                                
                                for ocg in ocgs:
                                    try:
                                        if '/Name' in ocg:
                                            layer_name = str(ocg.Name)
                                            # Odstránime '/' z začiatku ak existuje
                                            if layer_name.startswith('/'):
                                                layer_name = layer_name[1:]                                            
                                            # Ak je vrstva v povolených, pridáme ju do ON
                                            if layer_name in self.enabled_layers:
                                                on_layers.append(ocg)
                                    except Exception as e:
                                        pass  # Pokračujeme pri chybe
                                
                                # Nastavime ON pole
                                d_dict.ON = on_layers
                                
                        # Uložíme modifikovaný PDF
                        pdf.save(temp_pdf.name)
                    
                    # Teraz renderujeme modifikovaný PDF
                    doc = fitz.open(temp_pdf.name)
                    
                except Exception as e:
                    # Ak zlyhalo, použijeme pôvodný PDF
                    doc = fitz.open(pdf_path)
                    temp_pdf.name = None
            else:
                # Štandardné otvorenie bez filtrovania
                doc = fitz.open(pdf_path)
                temp_pdf = None
            
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Renderovanie stránky do obrázka
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Konverzia na NumPy array
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                # PyMuPDF vracia RGB, OpenCV pracuje s BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                images.append(img)
            
            doc.close()
            
            # Odstránime dočasný PDF
            if temp_pdf and temp_pdf.name:
                try:
                    os.remove(temp_pdf.name)
                except:
                    pass
            
            return images
        except Exception as e:
            raise Exception(f"Chyba pri čítaní PDF: {str(e)}")
    
    def compare_images(self, old_img, new_img, new_color=(255, 0, 0), old_color=(206, 183, 138)):
        """
        Porovná dva obrázky a vytvorí výstupný obrázok:
        - Pôvodné farby = rovnaký obsah (ako v projekte)
        - Farba - nové = nový obsah (pridané čiary, text, objekty)
        - Hnedá = starý obsah (odstránený obsah)
        
        Args:
            old_img: Starý obrázok
            new_img: Nový obrázok
            new_color: RGB farba pre nový obsah (tuple)
            old_color: RGB farba pre odstránený obsah (tuple)
        """
        # Zabezpečiť rovnaké rozmery
        h1, w1 = old_img.shape[:2]
        h2, w2 = new_img.shape[:2]
        
        # Použiť väčšie rozmery
        max_h = max(h1, h2)
        max_w = max(w1, w2)
        
        # Rozšíriť obrázky na rovnaké rozmery (biela výplň)
        old_resized = np.ones((max_h, max_w, 3), dtype=np.uint8) * 255
        new_resized = np.ones((max_h, max_w, 3), dtype=np.uint8) * 255
        
        old_resized[0:h1, 0:w1] = old_img
        new_resized[0:h2, 0:w2] = new_img
        
        # Začneme s NOVÝM obrázkom v plných farbách (nie grayscale)
        result = new_resized.copy()
        
        # Konverzia na grayscale len pre detekciu rozdielov
        old_gray = cv2.cvtColor(old_resized, cv2.COLOR_BGR2GRAY)
        new_gray = cv2.cvtColor(new_resized, cv2.COLOR_BGR2GRAY)
        
        # Prah pre detekciu rozdielov (nižšia tolerancia pre presnejšiu detekciu)
        threshold = 15
        
        # Absolútny rozdiel
        diff = cv2.absdiff(old_gray, new_gray)
        
        # Detekcia obsahu (nie je to biela stránka)
        # Považujeme pixel za "obsah" ak je tmavší ako 240
        content_threshold = 240
        old_has_content = old_gray < content_threshold
        new_has_content = new_gray < content_threshold
        
        # 1. HNEDÁ - Odstránený obsah (bol v starom, nie je v novom)
        # Kde bol obsah v starom PDF ale v novom je biela
        removed_content = old_has_content & (~new_has_content)
        
        # Aplikujeme hnedú farbu s nastavenou RGB hodnotou (BGR formát pre OpenCV)
        result[removed_content] = [old_color[2], old_color[1], old_color[0]]  # BGR - RGB -> BGR
        
        # 2. Farba - nové - Nový/zmenený obsah
        # A) Obsah je v novom, ale nebol v starom
        new_content = new_has_content & (~old_has_content)
        
        # B) Obsah je v oboch, ale líši sa (zmenený)
        # Kontrolujeme či je rozdiel väčší ako threshold
        changed_content = (diff > threshold) & old_has_content & new_has_content
        
        # Kombinujeme nový a zmenený obsah
        red_mask = new_content | changed_content
        
        # Aplikujeme červenú farbu s nastavenou RGB hodnotou (BGR formát pre OpenCV)
        result[red_mask] = [new_color[2], new_color[1], new_color[0]]  # BGR - RGB -> BGR
        
        # Pre lepšiu viditeľnosť: zhrubnutie farebných označení (voliteľné)
        # Toto pomôže lepšie vidieť tenké čiary
        kernel = np.ones((2, 2), np.uint8)
        
        # Vytvoríme masky pre morfologické operácie
        red_mask_dilated = cv2.dilate(red_mask.astype(np.uint8), kernel, iterations=1)
        removed_mask_dilated = cv2.dilate(removed_content.astype(np.uint8), kernel, iterations=1)
        
        # Aplikujeme rozšírené masky s nastaviteľnými farbami (BGR formát)
        result[red_mask_dilated > 0] = [new_color[2], new_color[1], new_color[0]]
        result[removed_mask_dilated > 0] = [old_color[2], old_color[1], old_color[0]]
        
        return result
    
    def images_to_pdf(self, images, output_path):
        """Vytvorí PDF z obrázkov so zachovaním pôvodných rozmerov a optimálnou kompresiou"""
        try:
            # Vytvoríme PDF pomocou PyMuPDF (fitz) pre lepšiu kontrolu
            pdf_document = fitz.open()
            
            for i, img in enumerate(images):
                # OpenCV používa BGR, potrebujeme RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Získame rozmery obrázka v pixeloch
                height, width = img.shape[:2]
                
                # Konverzia na PIL pre uloženie
                pil_img = Image.fromarray(img_rgb)
                
                # Uloženie do dočasného súboru ako JPEG s optimálnou kompresiou (kvalita 85)
                # JPEG redukuje veľkosť súboru až o 90% oproti PNG bez výraznej straty kvality
                temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                pil_img.save(temp_img.name, "JPEG", quality=85, optimize=True)
                temp_img.close()
                
                # Vytvoríme stránku s presne rovnakými rozmermi ako obrázok
                # fitz používa body (72 DPI), takže prepočítame z pixelov
                # Predpokladáme že obrázok bol renderovaný pri 150 DPI
                dpi = 150
                page_width = width * 72 / dpi
                page_height = height * 72 / dpi
                
                # Vytvoríme novú stránku
                page = pdf_document.new_page(width=page_width, height=page_height)
                
                # Vložíme obrázok na celú stránku
                page.insert_image(
                    fitz.Rect(0, 0, page_width, page_height),
                    filename=temp_img.name
                )
                
                # Odstránime dočasný súbor
                try:
                    os.remove(temp_img.name)
                except:
                    pass
            
            # Uložíme PDF s kompresiou a optimalizáciou
            pdf_document.save(
                output_path,
                garbage=4,  # Maximálne čistenie nepoužívaných objektov
                deflate=True,  # Kompresia streamov
                clean=True  # Optimalizácia PDF štruktúry
            )
            pdf_document.close()
                
        except Exception as e:
            raise Exception(f"Chyba pri vytváraní PDF: {str(e)}")
    
    def compare_pdfs(self):
        """Hlavná funkcia na vizuálne porovnanie PDF súborov"""
        # Validácia vstupov
        if not self.old_pdf_path.get():
            messagebox.showerror("Chyba", "Vyberte starý PDF súbor!")
            return
        
        if not self.new_pdf_path.get():
            messagebox.showerror("Chyba", "Vyberte nový PDF súbor!")
            return
        
        if not self.output_pdf_path.get():
            messagebox.showerror("Chyba", "Vyberte cestu pre výstupný PDF!")
            return
        
        try:
            # Spustenie progress baru
            self.progress_label.config(text="Spracovávam...")
            self.progress_bar.pack(pady=5)
            self.progress_bar.start(10)
            self.root.update()
            
            # Konverzia PDF na obrázky
            # Ak sú nastavené filtre vrstiev, renderujeme len vybrané vrstvy
            # Inak renderujeme všetky vrstvy
            use_layer_filter = bool(self.enabled_layers)
            
            self.progress_label.config(text="Renderujem starý PDF...")
            self.root.update()
            old_images = self.pdf_to_images(self.old_pdf_path.get(), filter_layers=use_layer_filter)
            
            self.progress_label.config(text="Renderujem nový PDF...")
            self.root.update()
            new_images = self.pdf_to_images(self.new_pdf_path.get(), filter_layers=use_layer_filter)
            
            # Určenie počtu stránok
            max_pages = max(len(old_images), len(new_images))
            
            # Porovnanie stránok
            result_images = []
            for i in range(max_pages):
                self.progress_label.config(text=f"Porovnávam stránku {i+1}/{max_pages}...")
                self.root.update()
                
                # Získanie obrázkov stránok (alebo biela stránka ak neexistuje)
                if i < len(old_images):
                    old_img = old_images[i]
                else:
                    # Biela stránka ak starý PDF má menej stránok
                    h, w = new_images[i].shape[:2]
                    old_img = np.ones((h, w, 3), dtype=np.uint8) * 255
                
                if i < len(new_images):
                    new_img = new_images[i]
                else:
                    # Biela stránka ak nový PDF má menej stránok
                    h, w = old_images[i].shape[:2]
                    new_img = np.ones((h, w, 3), dtype=np.uint8) * 255
                
                # Porovnanie s nastaviteľnými farbami
                result_img = self.compare_images(
                    old_img, 
                    new_img,
                    new_color=self.new_color,
                    old_color=self.old_color
                )
                result_images.append(result_img)
            
            # Vytvorenie výstupného PDF
            self.progress_label.config(text="Vytváram výstupný PDF...")
            self.root.update()
            self.images_to_pdf(result_images, self.output_pdf_path.get())
            
            # Dokončenie
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.progress_label.config(text="")
            
            # Zobrazíme správu o úspešnom dokončení
            layer_info = ""
            if self.enabled_layers:
                layer_info = f"\nPorovnané vrstvy: {len(self.enabled_layers)}"
            
            messagebox.showinfo(
                "Porovnanie dokončené", 
                f"PDF súbory boli úspešne porovnané!\n\n"
                f"Výstupný súbor: {self.output_pdf_path.get()}\n\n"
                f"Porovnaných stránok: {max_pages}{layer_info}"
            )
            
            # Ak je zaškrtnuté automatické otvorenie, otvoríme PDF
            if self.auto_open_pdf.get():
                try:
                    os.startfile(self.output_pdf_path.get())
                except Exception as e:
                    messagebox.showerror("Chyba", f"Nepodarilo sa otvoriť PDF:\n{str(e)}")
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.progress_label.config(text="")
            messagebox.showerror("Chyba", f"Nastala chyba:\n{str(e)}")


def main():
    root = tk.Tk()
    app = PDFComparatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
