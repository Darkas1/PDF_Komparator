# PDF Komparátor

Nástroj na vizuálne porovnávanie PDF súborov s farebnými označeniami rozdielov.

## Funkcie

- ✅ Vizuálne porovnanie PDF súborov (obrázky, čiary, text, vektorová grafika)
- 🔴 Červená farba - nový/zmenený obsah
- 🟢 Zelená farba - odstránený obsah  
- 🎨 Pôvodné farby - nezmenený obsah
- 🎨 Nastaviteľné farby pomocou color pickera
- 📄 Zachovanie pôvodných rozmerov a pomerov strán
- 💾 Automatické otvorenie výsledného PDF po dokončení

## Spustenie programu

### Pomocou EXE súboru (odporúčané)
Jednoducho spustite súbor **PDF_Komparator.exe** v priečinku `dist/`.

Nevyžaduje inštaláciu Pythonu ani závislostí!

### Pomocou Python skriptu
```bash
python pdf_comparator.py
```

## Inštalácia závislostí

Pred spustením Python skriptu je potrebné nainštalovať potrebné knižnice.

### 1. Vytvorenie virtuálneho prostredia (voliteľné, ale odporúčané)

```powershell
python -m venv .venv
```

### 2. Aktivácia virtuálneho prostredia

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Inštalácia knižníc z requirements.txt

```powershell
pip install -r requirements.txt
```

Alebo môžete nainštalovať knižnice manuálne:

```powershell
pip install PyMuPDF opencv-python numpy Pillow reportlab
```

## Vytvorenie EXE súboru po úprave kódu

Ak ste vykonali zmeny v `pdf_comparator.py` a chcete vytvoriť nový EXE súbor, postupujte takto:

### 1. Aktivácia virtuálneho prostredia

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Inštalácia PyInstaller (ak ešte nie je nainštalovaný)

```powershell
pip install pyinstaller
```

### 3. Vytvorenie EXE súboru

```powershell
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name "PDF_Komparator" pdf_comparator.py
```

**Vysvetlenie parametrov:**
- `--onefile` - vytvorí jeden samostatný EXE súbor
- `--windowed` - bez konzoly (GUI aplikácia)
- `--name "PDF_Komparator"` - názov výsledného EXE súboru

### 4. Výsledok

Nový EXE súbor sa vytvorí v priečinku:
```
dist/PDF_Komparator.exe
```

### 5. Vyčistenie dočasných súborov (voliteľné)

Po úspešnom vytvorení EXE môžete odstrániť dočasné priečinky:

```powershell
Remove-Item -Recurse -Force build, __pycache__
Remove-Item PDF_Komparator.spec
```

## Alternatívny spôsob - použitie existujúcej .spec konfigurácie

Ak už máte `PDF_Komparator.spec` súbor z predchádzajúceho buildu:

```powershell
pyinstaller PDF_Komparator.spec
```

Toto je rýchlejšie, pretože používa existujúcu konfiguráciu.

## Požiadavky pre vývoj

Ak chcete upravovať zdrojový kód, potrebujete:

```powershell
pip install PyMuPDF opencv-python numpy Pillow reportlab
```

## Štruktúra projektu

```
nice_try/
├── pdf_comparator.py          # Hlavný Python skript
├── README.md                  # Tento súbor
├── PDF_Komparator.spec        # PyInstaller konfigurácia
├── dist/
│   └── PDF_Komparator.exe     # Výsledný EXE súbor
├── build/                     # Dočasné súbory (možno vymazať)
└── .venv/                     # Virtuálne Python prostredie
```

## Použitie

1. Spustite `PDF_Komparator.exe`
2. Vyberte starý PDF súbor
3. Vyberte nový PDF súbor
4. Nastavte výstupný PDF súbor
5. (Voliteľne) Zmeňte farby pomocou color pickera
6. Kliknite na "Porovnať PDF"
7. Po dokončení sa opýta, či chcete otvoriť výsledok

## Technické detaily

- **Python verzia:** 3.12.2
- **DPI renderovania:** 150
- **Threshold detekcie rozdielov:** 15
- **Formát výstupu:** PDF so zachovaním pôvodných rozmerov

## Riešenie problémov

### EXE súbor je príliš veľký
- To je normálne, obsahuje Python interpreter a všetky knižnice
- Veľkosť: cca 150-200 MB
- Pre zmenšenie môžete skúsiť `--exclude-module` pre nepoužité moduly

### Antivírus blokuje EXE
- PyInstaller EXE súbory sú niekedy označené ako podozrivé
- Pridajte výnimku vo vašom antivíruse
- Alebo spustite Python skript priamo

### Chyba pri vytváraní EXE
1. Uistite sa, že je aktivované virtuálne prostredie
2. Preinštalujte PyInstaller: `pip uninstall pyinstaller` a potom `pip install pyinstaller`
3. Vymažte `build/` a `dist/` priečinky a skúste znova

## Autor

Darina Kasparová

## Licencia

Tento projekt je voľne použiteľný pre osobné a komerčné účely.
