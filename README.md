# Brawl Stars Spielervergleich

Eine Streamlit-Anwendung zum Vergleich von Brawl Stars Spielern mit erweiterten Statistiken, Battle-Logs, Brawler-Analysen und KI-gestützten Vergleichen.

## Features

### Spielervergleich
- Detaillierte Statistiken zweier Spieler im direkten Vergleich
- Flexible Spielerauswahl über Club-Mitgliederlisten oder direkte Tag-Eingabe
- Visualisierung von Trophäen und Siegen
- Battle-Log Analyse mit Siegquoten und Star-Player-Statistiken
- KI-gestützte Zusammenfassung des Spielervergleichs

### Brawler-Analyse
- Vollständige Liste aller verfügbaren Brawler
- Detaillierte Informationen zu jedem Brawler
- Star Powers und Gadgets Übersicht
- Globales Ranking der Top-Spieler pro Brawler
- Visuelle Darstellung der Brawler-Statistiken

### Club-Analyse
- Übersicht über Club-Statistiken
- Mitgliederliste mit detaillierten Informationen
- Trophäen-Verteilung innerhalb des Clubs
- Rollen-Verteilung im Club
- Vergleichsmöglichkeiten zwischen verschiedenen Clubs

## Verwendung

1. Nach dem Start öffnet sich das Dashboard im Standard-Webbrowser
2. Navigation über das Seitenmenü:
   - Spielervergleich
   - Brawler-Analyse
   - Club-Analyse
3. Flexible Auswahlmöglichkeiten:
   - Spieler aus Club-Listen
   - Direkte Tag-Eingabe
   - Brawler-Auswahl
   - Club-Auswahl

## Projektstruktur

### main.py
- Hauptanwendungsdatei mit der `BrawlStarsApp`-Klasse
- Multi-Page-Navigation
- Integration von OpenAI für KI-Analysen
- Erweiterte Visualisierungen mit Plotly

### api_client.py
- Vollständige Integration der Brawl Stars API
- Cached API-Requests für bessere Performance
- Erweiterte Fehlerbehandlung
- Unterstützung für alle API-Endpunkte

### data_processor.py
- Umfangreiche Datenverarbeitung
- Battle-Log-Analyse
- Brawler-Statistiken
- Club-Daten-Aufbereitung

### ui_components.py
- Modulare UI-Komponenten
- Responsive Layouts
- Interaktive Plotly-Visualisierungen
- Einheitliches Styling

## Technische Details

### Verwendete Technologien
- Python 3.x
- Streamlit für das Web-Interface
- Pandas für Datenverarbeitung
- Plotly für interaktive Visualisierungen
- OpenAI API für KI-Analysen

### Installation

1. Repository klonen:
```bash
git clone [repository-url]
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

4. `.env` Datei erstellen und API-Keys eintragen:
```
# Brawl Stars API Key (https://developer.brawlstars.com/)
BRAWLSTARS_API_KEY=your_brawlstars_api_key_here

# OpenAI API Key (https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here
```

5. Starten Sie die Streamlit-Anwendung:
```bash
streamlit run main.py
```

Die Anwendung öffnet sich automatisch in Ihrem Standard-Webbrowser unter:
   - Lokale URL: http://localhost:8501
   - Netzwerk URL: http://192.168.x.x:8501 (für Zugriff im lokalen Netzwerk)

### Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

### Autor

Sascha / saschaSpoonbill

