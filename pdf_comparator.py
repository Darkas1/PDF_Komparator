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


class PDFComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Porovnávatko")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # Cesty k súborom
        self.old_pdf_path = tk.StringVar()
        self.new_pdf_path = tk.StringVar()
        self.output_pdf_path = tk.StringVar()
        
        # Nastavenia farieb (RGB tuple)
        self.new_color = (255, 0, 0)  # Plná Farba - nové
        self.old_color = (206, 183, 138)  # Bledá hnedá (Light Brown)
        
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
        
        # Tlačidlo porovnania
        compare_button = tk.Button(
            self.root,
            text="Porovnať PDF",
            command=self.compare_pdfs,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        compare_button.pack(pady=20)
  
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
    
    def pdf_to_images(self, pdf_path, dpi=150):
        """Konvertuje všetky stránky PDF na obrázky"""
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Renderovanie stránky do obrázka
                mat = fitz.Matrix(dpi/72, dpi/72)  # Transformačná matrica pre DPI
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Konverzia na NumPy array
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                # PyMuPDF vracia RGB, OpenCV pracuje s BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                images.append(img)
            
            doc.close()
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
            self.progress_label.config(text="Renderujem starý PDF...")
            self.root.update()
            old_images = self.pdf_to_images(self.old_pdf_path.get())
            
            self.progress_label.config(text="Renderujem nový PDF...")
            self.root.update()
            new_images = self.pdf_to_images(self.new_pdf_path.get())
            
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
            
            # Opýtame sa či chce otvoriť výsledný PDF
            response = messagebox.askyesno(
                "Porovnanie dokončené", 
                f"PDF súbory boli úspešne porovnané!\n\n"
                f"Výstupný súbor: {self.output_pdf_path.get()}\n\n"
                f"Porovnaných stránok: {max_pages}\n\n"
                f"Chcete otvoriť výsledný PDF?"
            )
            
            # Ak používateľ chce otvoriť PDF
            if response:
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
