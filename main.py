import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import logging
import plotly.express as px
from openai import OpenAI

from api_client import BrawlStarsAPI
from data_processor import BrawlStarsDataProcessor
from ui_components import BrawlStarsUI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BrawlStarsApp:
    # Vordefinierte Club-Tags (mit '#' am Anfang)
    CLUB_TAGS = {
        "Spike": "#2YJQ8LRCG",
        "grand": "#CV2LQLQU",
        "MA NAJJACI SMOO": "#2UU9UlJUR",
        "i pro": "#GRP8LQJ8",
    }

    def __init__(self):
        """Initialisierung der App mit API-Key und Clients"""
        self._load_environment()
        self.api_client = BrawlStarsAPI(self.api_key)
        self.data_processor = BrawlStarsDataProcessor()
        self.ui = BrawlStarsUI()

    def _load_environment(self) -> None:
        """Laden der Umgebungsvariablen"""
        load_dotenv()
        self.api_key = os.getenv("BRAWLSTARS_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("BRAWLSTARS_API_KEY muss in .env definiert sein")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY muss in .env definiert sein")

    def run(self) -> None:
        """Hauptmethode zum Ausführen der App"""
        selected_page = st.sidebar.radio(
            "Navigation",
            ["Spielervergleich", "Brawler", "Clubs"],
            index=0
        )

        if selected_page == "Spielervergleich":
            self._show_player_comparison_page()
        elif selected_page == "Brawler":
            self._show_brawler_page()
        else:
            self._show_clubs_page()

    def _show_player_comparison_page(self) -> None:
        """Zeigt die Seite mit dem Spielervergleich an"""
        st.title("Brawl Stars Spielervergleich")
        
        # Club-Informationen laden
        club_info = self._load_club_info()
        
        # Spielerauswahl
        player1_tag, player2_tag = self._setup_player_selection(club_info)
        
        if player1_tag and player2_tag:
            self._display_player_comparison(player1_tag, player2_tag)

    def _show_brawler_page(self) -> None:
        """Zeigt die Brawler-Analyse-Seite an"""
        st.title("Brawler Analyse")
        
        # Lade alle Brawler
        brawlers_data = self.api_client.get_brawlers()
        
        if not brawlers_data or 'items' not in brawlers_data:
            st.error("Fehler beim Laden der Brawler-Daten")
            return

        # Hole alle Brawler und sortiere sie alphabetisch
        brawlers = sorted(brawlers_data.get('items', []), key=lambda x: x.get('name', ''))
        
        # Erstelle zwei Spalten: Eine für die Brawler-Liste und eine für die Details
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Brawler auswählen")
            # Erstelle eine Liste von Brawlern als Buttons
            for brawler in brawlers:
                if st.button(
                    brawler['name'],
                    key=f"brawler_{brawler['id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_brawler = brawler['id']
                    st.session_state.selected_brawler_name = brawler['name']

        with col2:
            if 'selected_brawler' in st.session_state:
                self._show_brawler_details(
                    st.session_state.selected_brawler,
                    st.session_state.selected_brawler_name
                )

    def _show_brawler_details(self, brawler_id: str, brawler_name: str) -> None:
        """Zeigt detaillierte Informationen für einen ausgewählten Brawler"""
        st.subheader(f"Details für {brawler_name}")
        
        # Lade detaillierte Brawler-Informationen
        brawler_details = self.api_client.get_brawler_info(brawler_id)
        
        if not brawler_details:
            st.error("Fehler beim Laden der Brawler-Details")
            return
        
        # Erstelle Tabs für verschiedene Informationen
        tab1, tab2 = st.tabs(["Fähigkeiten", "Globales Ranking"])
        
        with tab1:
            # Star Powers anzeigen
            st.markdown("### Star Powers")
            for star_power in brawler_details.get('starPowers', []):
                st.markdown(f"""
                    <div style='
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        margin: 5px;
                        background-color: rgba(255,255,255,0.05);
                    '>
                        <h4>{star_power['name']}</h4>
                    </div>
                """, unsafe_allow_html=True)
            
            # Gadgets anzeigen
            st.markdown("### Gadgets")
            for gadget in brawler_details.get('gadgets', []):
                st.markdown(f"""
                    <div style='
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        margin: 5px;
                        background-color: rgba(255,255,255,0.05);
                    '>
                        <h4>{gadget['name']}</h4>
                    </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            # Lade und zeige Ranking-Informationen
            rankings = self.api_client.get_brawler_rankings(brawler_id)
            if rankings and 'items' in rankings:
                st.markdown("### Top 10 Spieler Global")
                ranking_data = []
                for idx, player in enumerate(rankings['items'][:10], 1):
                    ranking_data.append({
                        'Rang': idx,
                        'Spieler': player['name'],
                        'Trophäen': player['trophies'],
                        'Club': player.get('club', {}).get('name', 'Kein Club')
                    })
                
                st.dataframe(
                    ranking_data,
                    column_config={
                        'Rang': st.column_config.NumberColumn(format="%d"),
                        'Trophäen': st.column_config.NumberColumn(format="%d")
                    },
                    hide_index=True
                )
            else:
                st.warning("Keine Ranking-Daten verfügbar")

    def _load_club_info(self) -> Dict:
        """Lädt Informationen für alle vordefinierten Clubs"""
        club_info = {}
        for name, tag in self.CLUB_TAGS.items():
            club_data = self.api_client.get_club_info(tag)
            if club_data:
                club_info[name] = club_data
        return club_info

    def _setup_player_selection(self, club_info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Erstellt die Benutzeroberfläche für die Spielerauswahl"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Spieler 1")
            # Tab für Auswahlmethode
            selection_mode1 = st.radio(
                "Auswahlmethode für Spieler 1",
                ["Aus Club auswählen", "Spieler-ID eingeben"],
                key="selection_mode1",
                horizontal=True
            )
            
            if selection_mode1 == "Aus Club auswählen":
                club1 = st.selectbox(
                    "Club auswählen (Spieler 1)",
                    options=list(club_info.keys()),
                    key="club1",
                    index=list(club_info.keys()).index("Spike")
                )
                if club1:
                    members1 = self.api_client.get_club_members(self.CLUB_TAGS[club1])
                    if members1:
                        member_list1 = [f"{m['name']} ({m['tag']})" for m in members1['items']]
                        default_index1 = next((i for i, m in enumerate(member_list1) 
                                            if "Spoony" in m), 0)
                        player1 = st.selectbox(
                            "Spieler 1 auswählen",
                            options=member_list1,
                            key="player1",
                            index=default_index1
                        )
                        player1_tag = player1.split('(')[1].rstrip(')') if player1 else None
                    else:
                        player1_tag = None
                        st.error("Fehler beim Laden der Club-Mitglieder")
            else:
                player1_tag = st.text_input(
                    "Spieler-ID eingeben (mit #)",
                    placeholder="#2YJQ8LRCG",
                    key="player1_direct"
                )
                if player1_tag and not player1_tag.startswith('#'):
                    st.error("Spieler-ID muss mit # beginnen")
                    player1_tag = None

        with col2:
            st.subheader("Spieler 2")
            # Tab für Auswahlmethode
            selection_mode2 = st.radio(
                "Auswahlmethode für Spieler 2",
                ["Aus Club auswählen", "Spieler-ID eingeben"],
                key="selection_mode2",
                horizontal=True
            )
            
            if selection_mode2 == "Aus Club auswählen":
                club2 = st.selectbox(
                    "Club auswählen (Spieler 2)",
                    options=list(club_info.keys()),
                    key="club2",
                    index=list(club_info.keys()).index("Spike")
                )
                if club2:
                    members2 = self.api_client.get_club_members(self.CLUB_TAGS[club2])
                    if members2:
                        member_list2 = [f"{m['name']} ({m['tag']})" for m in members2['items']]
                        default_index2 = next((i for i, m in enumerate(member_list2) 
                                            if "Hydropi" in m), 0)
                        player2 = st.selectbox(
                            "Spieler 2 auswählen",
                            options=member_list2,
                            key="player2",
                            index=default_index2
                        )
                        player2_tag = player2.split('(')[1].rstrip(')') if player2 else None
                    else:
                        player2_tag = None
                        st.error("Fehler beim Laden der Club-Mitglieder")
            else:
                player2_tag = st.text_input(
                    "Spieler-ID eingeben (mit #)",
                    placeholder="#2YJQ8LRCG",
                    key="player2_direct"
                )
                if player2_tag and not player2_tag.startswith('#'):
                    st.error("Spieler-ID muss mit # beginnen")
                    player2_tag = None

        # Validierung der Spieler-Tags vor der Rückgabe
        if player1_tag and player2_tag:
            # Prüfe ob die Spieler existieren
            test_player1 = self.api_client.get_player_info(player1_tag)
            test_player2 = self.api_client.get_player_info(player2_tag)
            
            if not test_player1:
                st.error(f"Spieler 1 mit Tag {player1_tag} wurde nicht gefunden.")
                return None, None
            
            if not test_player2:
                st.error(f"Spieler 2 mit Tag {player2_tag} wurde nicht gefunden.")
                return None, None

        return player1_tag, player2_tag

    def _display_player_comparison(self, player1_tag: str, player2_tag: str) -> None:
        """Zeigt den Vergleich zwischen zwei Spielern an"""
        # Spielerdaten laden
        player1_data = self.api_client.get_player_info(player1_tag)
        player2_data = self.api_client.get_player_info(player2_tag)

        if not player1_data or not player2_data:
            st.error("Fehler beim Laden der Spielerdaten")
            return

        # Club-Informationen laden
        club1_info = None
        club2_info = None
        if 'club' in player1_data and player1_data['club'].get('tag'):
            club1_info = self.api_client.get_club_info(player1_data['club']['tag'])
        if 'club' in player2_data and player2_data['club'].get('tag'):
            club2_info = self.api_client.get_club_info(player2_data['club']['tag'])

        # Spieler-Statistiken anzeigen
        col1, col2 = st.columns(2)
        self.ui.display_player_stats(player1_data, club1_info, col1)
        self.ui.display_player_stats(player2_data, club2_info, col2)

        # Trophäen-Vergleich als Balkendiagramm mit Plotly
        st.header("Trophäen-Vergleich")
        trophy_data = {
            'Spieler': [player1_data['name'], player2_data['name']],
            'Trophäen': [player1_data['trophies'], player2_data['trophies']]
        }
        trophy_df = pd.DataFrame(trophy_data)
        
        # Erstelle ein Plotly-Balkendiagramm mit dunkelblau und dunkelrot
        fig = px.bar(
            trophy_df,
            x='Spieler',
            y='Trophäen',
            color='Spieler',
            color_discrete_map={
                player1_data['name']: '#8B0000',  # Dunkelrot für Spieler 1
                player2_data['name']: '#00008B'   # Dunkelblau für Spieler 2
            },
            text='Trophäen'
        )
        
        # Anpassen des Layouts
        fig.update_traces(textposition='outside')  # Werte über den Balken
        fig.update_layout(
            showlegend=False,  # Legende ausblenden
            plot_bgcolor='rgba(0,0,0,0)',  # Transparenter Hintergrund
            height=400  # Höhe des Diagramms
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Siege-Vergleich als Balkendiagramm
        st.header("Siege-Vergleich")
        
        # Daten für verschiedene Siegestypen vorbereiten
        victories_data = {
            'Spieler': [
                player1_data['name'], player1_data['name'], player1_data['name'],
                player2_data['name'], player2_data['name'], player2_data['name']
            ],
            'Siegestyp': ['3vs3', 'Solo', 'Duo'] * 2,
            'Anzahl': [
                player1_data.get('3vs3Victories', 0),
                player1_data.get('soloVictories', 0),
                player1_data.get('duoVictories', 0),
                player2_data.get('3vs3Victories', 0),
                player2_data.get('soloVictories', 0),
                player2_data.get('duoVictories', 0)
            ]
        }
        victories_df = pd.DataFrame(victories_data)
        
        # Erstelle ein gruppiertes Balkendiagramm für die Siege
        fig_victories = px.bar(
            victories_df,
            x='Siegestyp',
            y='Anzahl',
            color='Spieler',
            barmode='group',  # Gruppierte Balken nebeneinander
            color_discrete_map={
                player1_data['name']: '#8B0000',  # Dunkelrot für Spieler 1
                player2_data['name']: '#00008B'   # Dunkelblau für Spieler 2
            },
            text='Anzahl'  # Zeigt die Werte über den Balken an
        )
        
        # Anpassen des Layouts
        fig_victories.update_traces(textposition='outside')
        fig_victories.update_layout(
            showlegend=True,  # Legende anzeigen für bessere Unterscheidung
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis_title="Spielmodus",
            yaxis_title="Anzahl Siege"
        )
        
        st.plotly_chart(fig_victories, use_container_width=True)

        # Brawler-Statistiken anzeigen
        st.header("Brawler Vergleich")
        brawler_col1, brawler_col2 = st.columns(2)
        
        # Berechne und zeige Brawler-Statistiken
        brawler_stats1 = self.data_processor.calculate_brawler_statistics(player1_data)
        brawler_stats2 = self.data_processor.calculate_brawler_statistics(player2_data)
        
        self.ui.display_brawler_stats(brawler_stats1, brawler_col1)
        self.ui.display_brawler_stats(brawler_stats2, brawler_col2)

        # Battle-Logs anzeigen
        battles1 = self.api_client.get_battle_log(player1_tag)
        battles2 = self.api_client.get_battle_log(player2_tag)
        
        if battles1 and battles2:
            self._display_battle_logs(battles1, battles2, player1_tag, player2_tag)
            
            # KI-Analyse hinzufügen
            st.header("KI-Analyse des Vergleichs")
            
            # Battle-Statistiken berechnen
            formatted_battles1, _ = self.data_processor.format_battle_log(battles1, player1_tag)
            formatted_battles2, _ = self.data_processor.format_battle_log(battles2, player2_tag)
            battle_stats1 = self.data_processor.calculate_battle_statistics(formatted_battles1)
            battle_stats2 = self.data_processor.calculate_battle_statistics(formatted_battles2)
            
            # KI-Analyse generieren
            analysis = self._generate_ai_comparison(
                player1_data, player2_data,
                brawler_stats1, brawler_stats2,
                battle_stats1, battle_stats2
            )
            
            # Analyse in einem schönen Container anzeigen
            with st.container():
                st.markdown(f"*{analysis}*")

    def _display_battle_logs(self, battles1: Dict, battles2: Dict, 
                           player1_tag: str, player2_tag: str) -> None:
        """Zeigt die Battle-Logs beider Spieler an"""
        st.header("Letzte Spiele")
        
        # Trophäenverlauf als Line Chart
        st.subheader("Trophäenverlauf der letzten Spiele")
        
        # Hole die Spielernamen aus den Player-Infos
        player1_data = self.api_client.get_player_info(player1_tag)
        player2_data = self.api_client.get_player_info(player2_tag)
        
        player1_name = player1_data['name'] if player1_data else "Spieler 1"
        player2_name = player2_data['name'] if player2_data else "Spieler 2"
        
        # Hilfsfunktion zum Berechnen der kumulierten Trophäen
        def calculate_cumulative_trophies(battles, player_tag):
            trophy_changes = []
            cumulative = 0
            
            for battle in battles['items']:
                if 'battle' not in battle or 'trophyChange' not in battle['battle']:
                    continue
                    
                trophy_change = 0
                if 'teams' in battle['battle']:
                    for team in battle['battle']['teams']:
                        for player in team:
                            if player['tag'] == player_tag:
                                trophy_change = battle['battle']['trophyChange']
                
                cumulative += trophy_change
                trophy_changes.append(cumulative)
                
            return trophy_changes

        # Berechne kumulierte Trophäen für beide Spieler
        trophies1 = calculate_cumulative_trophies(battles1, player1_tag)
        trophies2 = calculate_cumulative_trophies(battles2, player2_tag)
        
        # Erstelle DataFrame für das Line Chart mit den tatsächlichen Namen
        chart_data = pd.DataFrame({
            'Spiel': range(1, max(len(trophies1), len(trophies2)) + 1),
            player1_name: trophies1 + [None] * (len(trophies2) - len(trophies1)) if len(trophies2) > len(trophies1) else trophies1,
            player2_name: trophies2 + [None] * (len(trophies1) - len(trophies2)) if len(trophies1) > len(trophies2) else trophies2
        })
        
        # Erstelle Line Chart mit Plotly und den tatsächlichen Namen
        fig = px.line(
            chart_data,
            x='Spiel',
            y=[player1_name, player2_name],
            color_discrete_map={
                player1_name: '#8B0000',  # Dunkelrot
                player2_name: '#00008B'   # Dunkelblau
            }
        )
        
        # Anpassen des Layouts
        fig.update_layout(
            xaxis_title="Spiel Nummer",
            yaxis_title="Kumulierte Trophäenänderung",
            plot_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Ursprüngliche Battle-Log Anzeige
        col1, col2 = st.columns(2)
        
        # Rest des ursprünglichen Codes...
        with col1:
            formatted_battles1, star_count1 = self.data_processor.format_battle_log(
                battles1, player1_tag)
            if formatted_battles1:
                stats1 = self.data_processor.calculate_battle_statistics(formatted_battles1)
                
                st.metric("Siege", f"{stats1['victories']}/{stats1['total_games']}")
                st.metric("Siegrate", f"{stats1['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count1}x ⭐")
                
                st.dataframe(pd.DataFrame(formatted_battles1))

        with col2:
            formatted_battles2, star_count2 = self.data_processor.format_battle_log(
                battles2, player2_tag)
            if formatted_battles2:
                stats2 = self.data_processor.calculate_battle_statistics(formatted_battles2)
                
                st.metric("Siege", f"{stats2['victories']}/{stats2['total_games']}")
                st.metric("Siegrate", f"{stats2['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count2}x ⭐")
                
                st.dataframe(pd.DataFrame(formatted_battles2))

    def _generate_ai_comparison(self, player1_data: Dict, player2_data: Dict, 
                          brawler_stats1: Dict, brawler_stats2: Dict,
                          battle_stats1: Dict, battle_stats2: Dict) -> str:
        """Generiert eine KI-basierte Analyse des Spielervergleichs"""
        
        # Erstelle den Prompt mit allen relevanten Informationen
        prompt = f"""
        Vergleiche die folgenden zwei Brawl Stars Spieler basierend auf ihren Statistiken:

        Spieler 1 ({player1_data['name']}):
        - Trophäen: {player1_data['highestTrophies']}
        - 3vs3 Siege: {player1_data.get('3vs3Victories', 0)}
        - Solo Siege: {player1_data.get('soloVictories', 0)}
        - Duo Siege: {player1_data.get('duoVictories', 0)}
        - Club Trophäen: {player1_data.get('club', {}).get('trophies', 0)}
        - Anzahl Brawler: {brawler_stats1.get('total_brawlers', 0)}
        - Brawler Power 9+: {brawler_stats1.get('high_level_brawlers', 0)}
        - Brawler Power 11: {brawler_stats1.get('max_level_brawlers', 0)}
        - Durchschnittliche Trophäen pro Brawler: {brawler_stats1.get('avg_trophies', 0):.1f}
        - Siegrate letzte Spiele: {battle_stats1.get('win_rate', 0):.1f}%

        Spieler 2 ({player2_data['name']}):
        - Trophäen: {player2_data['highestTrophies']}
        - 3vs3 Siege: {player2_data.get('3vs3Victories', 0)}
        - Solo Siege: {player2_data.get('soloVictories', 0)}
        - Duo Siege: {player2_data.get('duoVictories', 0)}
        - Club Trophäen: {player2_data.get('club', {}).get('trophies', 0)}
        - Anzahl Brawler: {brawler_stats2.get('total_brawlers', 0)}
        - Brawler Power 9+: {brawler_stats2.get('high_level_brawlers', 0)}
        - Brawler Power 11: {brawler_stats2.get('max_level_brawlers', 0)}
        - Durchschnittliche Trophäen pro Brawler: {brawler_stats2.get('avg_trophies', 0):.1f}
        - Siegrate letzte Spiele: {battle_stats2.get('win_rate', 0):.1f}%

        Erstelle eine Analyse (maximal 6 Sätze)der Spieler im Vergleich. 
        Hebe die wichtigsten Unterschiede hervor und erwähne, wer in welchen Bereichen stärker ist.
        """

        try:
            client = OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein Brawl Stars Experte, der Spielerstatistiken analysiert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Fehler bei der OpenAI API: {str(e)}")
            return "Fehler bei der KI-Analyse. Bitte versuchen Sie es später erneut."

    def _show_clubs_page(self) -> None:
        """Zeigt die Club-Analyse-Seite an"""
        st.title("Club Analyse")

        # Zwei Tabs für vorhandene Clubs und eigene Club-ID
        tab1, tab2 = st.tabs(["Vorhandene Clubs", "Club-ID eingeben"])

        with tab1:
            selected_club = st.selectbox(
                "Club auswählen",
                options=list(self.CLUB_TAGS.keys())
            )
            if selected_club:
                club_tag = self.CLUB_TAGS[selected_club]
                self._display_club_info(club_tag)

        with tab2:
            custom_tag = st.text_input(
                "Club-Tag eingeben (mit #)",
                placeholder="#2YJQ8LRCG"
            )
            if custom_tag:
                if not custom_tag.startswith('#'):
                    st.error("Club-Tag muss mit # beginnen")
                else:
                    self._display_club_info(custom_tag)

    def _display_club_info(self, club_tag: str) -> None:
        """Zeigt detaillierte Informationen für einen Club an"""
        club_info = self.api_client.get_club_info(club_tag)
        
        if not club_info:
            st.error("Club nicht gefunden oder Fehler beim Laden der Daten")
            return

        # Club-Header mit Basis-Informationen
        st.header(club_info['name'])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trophäen", f"{club_info['trophies']:,}")
        with col2:
            st.metric("Erforderliche Trophäen", f"{club_info.get('requiredTrophies', 0):,}")
        with col3:
            st.metric("Mitglieder", f"{len(club_info.get('members', []))}/30")

        # Club-Beschreibung
        if club_info.get('description'):
            st.markdown("### Beschreibung")
            st.write(club_info['description'])

        # Mitgliederliste
        st.markdown("### Mitglieder")
        
        if 'members' in club_info:
            # Erstelle DataFrame für Mitglieder
            members_data = []
            for member in club_info['members']:
                members_data.append({
                    'Name': member['name'],
                    'Rolle': member['role'].capitalize(),
                    'Trophäen': member['trophies'],
                    'Tag': member['tag']
                })
            
            df = pd.DataFrame(members_data)
            
            # Sortiere nach Trophäen absteigend
            df = df.sort_values('Trophäen', ascending=False)
            
            # Zeige die Tabelle mit angepasstem Styling
            st.dataframe(
                df,
                column_config={
                    'Name': st.column_config.TextColumn('Name'),
                    'Rolle': st.column_config.TextColumn('Rolle'),
                    'Trophäen': st.column_config.NumberColumn('Trophäen', format="%d"),
                    'Tag': st.column_config.TextColumn('Tag')
                },
                hide_index=True
            )

            # Trophäen-Verteilung als Histogramm
            st.markdown("### Trophäen-Verteilung")
            fig = px.histogram(
                df,
                x='Trophäen',
                nbins=20,
                title='Verteilung der Mitglieder-Trophäen'
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Rollen-Verteilung als Pie-Chart
            st.markdown("### Rollen-Verteilung")
            role_counts = df['Rolle'].value_counts()
            fig_roles = px.pie(
                values=role_counts.values,
                names=role_counts.index,
                title='Verteilung der Club-Rollen'
            )
            fig_roles.update_layout(height=400)
            st.plotly_chart(fig_roles, use_container_width=True)

def main():
    """Hauptfunktion zum Starten der App"""
    app = BrawlStarsApp()
    app.run()

if __name__ == "__main__":
    main()
