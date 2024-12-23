import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

class BrawlStarsUI:
    """
    Klasse für alle UI-Komponenten der Brawl Stars App.
    Handhabt das Rendering aller visuellen Elemente.
    """

    def __init__(self):
        """Initialisiert die UI-Komponente mit Standardfarben und Stilen"""
        self.colors = {
            'primary': '#FF9900',
            'secondary': '#6E44FF',
            'victory': '#00FF00',
            'defeat': '#FF0000',
            'draw': '#888888'
        }
        
        self.chart_config = {
            'height': 400,
            'template': 'plotly_dark'
        }

    def display_player_stats(self, player_data: Dict[str, Any], club_info: Dict[str, Any], column) -> None:
        """
        Zeigt die Statistiken eines Spielers und seines Clubs an.

        Args:
            player_data (Dict[str, Any]): Spielerdaten
            club_info (Dict[str, Any]): Club-Informationen
            column: Streamlit-Spaltenobjekt
        """
        with column:
            st.header(f"Statistiken: {player_data['name']}")
            
            # Spieler-Statistiken
            stats = {
                '🏆 Trophäen': player_data['trophies'],
                '🏅 Höchste Trophäen': player_data['highestTrophies'],
                '🎯 3v3 Siege': player_data.get('3vs3Victories', 0),
                '🎮 Solo Siege': player_data.get('soloVictories', 0),
                '👥 Duo Siege': player_data.get('duoVictories', 0),
                '🏅 Level': player_data['expLevel']
            }

            # Stats in Spalten anzeigen
            for label, value in stats.items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"{label}:")
                with col2:
                    st.write(f"{value:,}")

            # Club-Informationen
            if club_info:
                st.write("---")
                st.write("🏰 Club-Informationen:")
                club_stats = {
                    'Name': club_info.get('name', 'Kein Club'),
                    '🏆 Club-Trophäen': f"{club_info.get('trophies', 0):,}",
                    '🎯 Erforderliche Trophäen': f"{club_info.get('requiredTrophies', 0):,}",
                    '👥 Mitglieder': f"{len(club_info.get('members', []))}/30"
                }
                
                for label, value in club_stats.items():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"{label}:")
                    with col2:
                        st.write(value)

    def create_comparison_charts(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Erstellt Vergleichsdiagramme für zwei Spieler.

        Args:
            player1_data (Dict): Daten des ersten Spielers
            player2_data (Dict): Daten des zweiten Spielers
        """
        st.header("Statistik-Vergleich")

        # Trophäen-Vergleich
        self._create_trophy_comparison(player1_data, player2_data)
        
        # Siege-Vergleich
        self._create_victories_comparison(player1_data, player2_data)

    def _create_trophy_comparison(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Erstellt ein Balkendiagramm für den Trophäenvergleich.

        Args:
            player1_data (Dict): Daten des ersten Spielers
            player2_data (Dict): Daten des zweiten Spielers
        """
        trophy_data = pd.DataFrame({
            'Metrik': ['Aktuelle Trophäen', 'Höchste Trophäen'],
            player1_data['name']: [
                player1_data['trophies'],
                player1_data['highestTrophies']
            ],
            player2_data['name']: [
                player2_data['trophies'],
                player2_data['highestTrophies']
            ]
        })

        fig = px.bar(
            trophy_data,
            x='Metrik',
            y=[player1_data['name'], player2_data['name']],
            barmode='group',
            title='Trophäen-Vergleich',
            **self.chart_config
        )
        
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Trophäen",
            legend_title="Spieler"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _create_victories_comparison(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Erstellt ein Balkendiagramm für den Siege-Vergleich.

        Args:
            player1_data (Dict): Daten des ersten Spielers
            player2_data (Dict): Daten des zweiten Spielers
        """
        victory_data = pd.DataFrame({
            'Modus': ['3v3', 'Solo', 'Duo'],
            player1_data['name']: [
                player1_data.get('3vs3Victories', 0),
                player1_data.get('soloVictories', 0),
                player1_data.get('duoVictories', 0)
            ],
            player2_data['name']: [
                player2_data.get('3vs3Victories', 0),
                player2_data.get('soloVictories', 0),
                player2_data.get('duoVictories', 0)
            ]
        })

        fig = px.bar(
            victory_data,
            x='Modus',
            y=[player1_data['name'], player2_data['name']],
            barmode='group',
            title='Siege-Vergleich',
            **self.chart_config
        )
        
        fig.update_layout(
            xaxis_title="Spielmodus",
            yaxis_title="Anzahl Siege",
            legend_title="Spieler"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_battle_log(self, battles: List[Dict], player_name: str, 
                         star_count: int, column) -> None:
        """
        Zeigt das Battle-Log eines Spielers mit zusätzlichen Statistiken an.
        """
        with column:
            st.subheader(f"Letzte Spiele: {player_name}")
            
            if not battles:
                st.warning("Keine Kampfdaten verfügbar")
                return
            
            # Berechne Statistiken
            total_games = len(battles)
            victories = sum(1 for battle in battles if battle['Ergebnis'] == 'Sieg')
            win_rate = (victories / total_games * 100) if total_games > 0 else 0
            
            # Zeige Zusammenfassung
            st.write("📊 Zusammenfassung der letzten 20 Spiele:")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                st.metric("Siege", f"{victories}/{total_games}")
            with stats_col2:
                st.metric("Siegrate", f"{win_rate:.1f}%")
            with stats_col3:
                st.metric("Star Player", f"{star_count}x ⭐")
            
            # Battle-Log Tabelle
            st.write("🎮 Detaillierte Spiele:")
            st.dataframe(pd.DataFrame(battles))

    def _style_battle_results(self, df: pd.DataFrame) -> List:
        """
        Stilisiert die Battle-Log-Tabelle.

        Args:
            df (pd.DataFrame): Battle-Log DataFrame

        Returns:
            List: Liste mit Styling-Eigenschaften
        """
        return ['background-color: #2E7D32' if x == 'Sieg'
                else 'background-color: #C62828' if x == 'Niederlage'
                else 'background-color: #455A64' if x == 'Unentschieden'
                else '' for x in df]

    def show_error_message(self, message: str) -> None:
        """
        Zeigt eine Fehlermeldung an.

        Args:
            message (str): Anzuzeigende Fehlermeldung
        """
        st.error(f"⚠️ {message}")

    def show_success_message(self, message: str) -> None:
        """
        Zeigt eine Erfolgsmeldung an.

        Args:
            message (str): Anzuzeigende Erfolgsmeldung
        """
        st.success(f"✅ {message}")

    def create_win_rate_chart(self, statistics: Dict[str, Any], player_name: str) -> None:
        """
        Erstellt ein Kreisdiagramm für die Gewinnrate.

        Args:
            statistics (Dict[str, Any]): Spielerstatistiken
            player_name (str): Name des Spielers
        """
        fig = go.Figure(data=[go.Pie(
            labels=['Siege', 'Niederlagen', 'Unentschieden'],
            values=[statistics['wins'], statistics['losses'], statistics['draws']],
            hole=.3,
            marker_colors=[self.colors['victory'], 
                         self.colors['defeat'], 
                         self.colors['draw']]
        )])
        
        fig.update_layout(
            title=f"Gewinnrate: {player_name}",
            **self.chart_config
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_brawler_stats(self, brawler_stats: Dict, column) -> None:
        """Zeigt Brawler-Statistiken in einer Spalte an"""
        with column:
            st.metric("Anzahl Brawler", brawler_stats['total_brawlers'])
            st.metric("≥ Power 9", brawler_stats['high_level_brawlers'])
            st.metric("Power 11", brawler_stats['max_level_brawlers'])
            st.metric("Ø Trophäen", f"{brawler_stats['avg_trophies']:.1f}")
