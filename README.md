# Hotel Miramare - Sistema di Gestione Arredamento

Sistema completo per la gestione dei prodotti di arredamento dell'Hotel Miramare di Sanremo.

## Caratteristiche Principali

### 🏨 Gestione Completa Prodotti
- **Catalogazione dettagliata**: Nome, categoria, fornitore, prezzo, dimensioni, peso
- **Informazioni tecniche**: Materiali, colori, descrizioni dettagliate
- **Gestione stati**: In Valutazione, Approvato, Rifiutato, Ordinato, Ricevuto
- **Note private**: Spazio per osservazioni e commenti interni

### 📸 Gestione Multimediale
- **Upload multiplo**: Carica più immagini e video contemporaneamente
- **Formati supportati**: 
  - Immagini: JPG, PNG, GIF, WebP
  - Video: MP4, AVI, MOV, WebM, WMV, FLV
- **Anteprima immediata**: Visualizzazione diretta dei file caricati
- **Galleria organizzata**: Visualizzazione ottimizzata di foto e video

### 🔍 Ricerca e Filtri Avanzati
- **Ricerca testuale**: Trova prodotti per nome
- **Filtri per categoria**: Letti, Bagno, Frigorifero, Mobili, etc.
- **Filtri per stato**: Visualizza solo prodotti con stato specifico
- **Reset rapido**: Cancella tutti i filtri con un click

### 📊 Report e Statistiche
- **Dashboard completa**: Panoramica generale con statistiche
- **Report stampabile**: Genera report PDF completi
- **Analisi costi**: Calcolo automatico dei valori totali
- **Raggruppamento**: Prodotti organizzati per categoria e stato

### 🌐 Interfaccia Moderna
- **Design responsive**: Funziona perfettamente su desktop, tablet e mobile
- **Compatibilità cross-platform**: Windows, Mac, Linux
- **Interfaccia intuitiva**: Facile da usare anche per utenti non tecnici
- **Tema professionale**: Design elegante e moderno

## Installazione e Avvio

### Prerequisiti
- Python 3.8 o superiore
- pip (gestore pacchetti Python)

### Installazione
1. Apri il terminale/prompt dei comandi
2. Naviga nella cartella del progetto:
   ```
   cd C:\Users\Italfrigo\Desktop\miramare_hotel
   ```
3. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

### Avvio dell'Applicazione
1. Avvia il server:
   ```
   python app.py
   ```
2. Apri il browser e vai su: `http://localhost:5000`

## Struttura del Progetto

```
miramare_hotel/
├── app.py                 # Applicazione principale Flask
├── requirements.txt       # Dipendenze Python
├── README.md             # Questo file
├── miramare_products.db  # Database SQLite (creato automaticamente)
├── templates/            # Template HTML
│   ├── base.html         # Template base
│   ├── index.html        # Dashboard principale
│   ├── add_product.html  # Aggiungi prodotto
│   ├── view_product.html # Visualizza prodotto
│   ├── edit_product.html # Modifica prodotto
│   └── report.html       # Report completo
└── static/
    └── uploads/          # File caricati (immagini e video)
        ├── images/       # Immagini prodotti
        └── videos/       # Video prodotti
```

## Categorie Prodotti Supportate

- **Letti**: Letti matrimoniali, singoli, divani letto
- **Bagno**: Lavabo, doccia, WC, accessori bagno
- **Frigorifero**: Frigobar, frigoriferi, congelatori
- **Mobili**: Armadi, comodini, sedie, tavoli, scrivanie
- **Illuminazione**: Lampade, lampadari, applique, LED
- **Tessuti**: Tende, biancheria, cuscini, tappeti
- **Elettrodomestici**: TV, condizionatori, asciugacapelli
- **Decorazioni**: Quadri, specchi, piante, oggetti decorativi
- **Altro**: Qualsiasi altro prodotto di arredamento

## Stati Prodotto

- **In Valutazione**: Prodotto appena inserito, in fase di valutazione
- **Approvato**: Prodotto approvato dalla proprietà
- **Rifiutato**: Prodotto non approvato
- **Ordinato**: Prodotto ordinato dal fornitore
- **Ricevuto**: Prodotto ricevuto e disponibile

## Funzionalità Avanzate

### Gestione File
- Upload automatico con nomi univoci
- Ridimensionamento automatico delle anteprime
- Supporto per file di grandi dimensioni (fino a 50MB)
- Eliminazione automatica dei file quando si elimina un prodotto

### Sicurezza
- Validazione dei tipi di file
- Nomi file sicuri (sanitizzazione automatica)
- Protezione contro upload di file pericolosi

### Performance
- Database SQLite ottimizzato
- Caricamento lazy delle immagini
- Compressione automatica dei file multimediali

## Supporto e Assistenza

Per qualsiasi problema o richiesta di funzionalità aggiuntive, il sistema è completamente personalizzabile e può essere esteso secondo le tue esigenze specifiche.

### Backup dei Dati
Il database è contenuto nel file `miramare_products.db`. Per fare un backup completo:
1. Copia il file `miramare_products.db`
2. Copia la cartella `static/uploads/` con tutti i file multimediali

### Aggiornamenti Futuri
Il sistema è progettato per essere facilmente estendibile con nuove funzionalità come:
- Integrazione con fornitori
- Gestione ordini automatica
- Notifiche email
- Sincronizzazione cloud
- App mobile dedicata

---

**Hotel Miramare - Sanremo**  
*Sistema di Gestione Arredamento Professionale*
