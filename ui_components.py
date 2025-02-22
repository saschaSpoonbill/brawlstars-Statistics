import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

class BrawlStarsUI:
    """
    Class for all UI components of the Brawl Stars App.
    Handles the rendering of all visual elements.
    """

    def __init__(self, data_processor):
        """
        Initializes the UI component with default colors and styles
        
        Args:
            data_processor: Instance of BrawlStarsDataProcessor
        """
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
        
        self.data_processor = data_processor

    def display_player_stats(self, player_data: Dict[str, Any], club_info: Dict[str, Any], column) -> None:
        """
        Displays the statistics of a player and their club.

        Args:
            player_data (Dict[str, Any]): Player data
            club_info (Dict[str, Any]): Club information
            column: Streamlit column object
        """
        with column:
            st.header(f"Statistics: {player_data['name']}")
            
            # Get highest trophy brawler
            highest_brawler = self.data_processor.get_highest_trophy_brawler(player_data)
            
            # Player statistics
            stats = {
                '🏆 Trophies': player_data['trophies'],
                '🏅 Highest Trophies': player_data['highestTrophies'],
                '🎯 3v3 Victories': player_data.get('3vs3Victories', 0),
                '🎮 Solo Victories': player_data.get('soloVictories', 0),
                '👥 Duo Victories': player_data.get('duoVictories', 0),
                '🏅 Level': player_data['expLevel'],
                '👑 Best Brawler': f"{highest_brawler.get('name', '-')} ({highest_brawler.get('trophies', 0)} 🏆)"
            }

            # Display stats in columns
            for label, value in stats.items():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"{label}:")
                with col2:
                    if isinstance(value, int):
                        st.write(f"{value:,}")
                    else:
                        st.write(value)

            # Club information
            if club_info:
                st.write("---")
                st.write("🏰 Club Information:")
                club_stats = {
                    'Name': club_info.get('name', 'No Club'),
                    '🏆 Club Trophies': f"{club_info.get('trophies', 0):,}",
                    '🎯 Required Trophies': f"{club_info.get('requiredTrophies', 0):,}",
                    '👥 Members': f"{len(club_info.get('members', []))}/30"
                }
                
                for label, value in club_stats.items():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"{label}:")
                    with col2:
                        st.write(value)

    def create_comparison_charts(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Creates comparison charts for two players.

        Args:
            player1_data (Dict): Data of the first player
            player2_data (Dict): Data of the second player
        """
        st.header("Statistics Comparison")

        # Trophy comparison
        self._create_trophy_comparison(player1_data, player2_data)
        
        # Victory comparison
        self._create_victories_comparison(player1_data, player2_data)

    def _create_trophy_comparison(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Creates a bar chart for trophy comparison.

        Args:
            player1_data (Dict): Data of the first player
            player2_data (Dict): Data of the second player
        """
        trophy_data = pd.DataFrame({
            'Metric': ['Current Trophies', 'Highest Trophies'],
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
            x='Metric',
            y=[player1_data['name'], player2_data['name']],
            barmode='group',
            title='Trophy Comparison',
            **self.chart_config
        )
        
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Trophies",
            legend_title="Player"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _create_victories_comparison(self, player1_data: Dict, player2_data: Dict) -> None:
        """
        Creates a bar chart for victory comparison.

        Args:
            player1_data (Dict): Data of the first player
            player2_data (Dict): Data of the second player
        """
        victory_data = pd.DataFrame({
            'Mode': ['3v3', 'Solo', 'Duo'],
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
            x='Mode',
            y=[player1_data['name'], player2_data['name']],
            barmode='group',
            title='Victory Comparison',
            **self.chart_config
        )
        
        fig.update_layout(
            xaxis_title="Game Mode",
            yaxis_title="Number of Victories",
            legend_title="Player"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_battle_log(self, battles: List[Dict], player_name: str, 
                         star_count: int, column) -> None:
        """
        Displays the battle log of a player with additional statistics.
        """
        with column:
            st.subheader(f"Recent Games: {player_name}")
            
            if not battles:
                st.warning("No battle data available")
                return
            
            # Calculate statistics
            total_games = len(battles)
            victories = sum(1 for battle in battles if battle['Result'] == 'Victory')
            win_rate = (victories / total_games * 100) if total_games > 0 else 0
            
            # Show summary
            st.write("📊 Summary of last 20 games:")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                st.metric("Victories", f"{victories}/{total_games}")
            with stats_col2:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with stats_col3:
                st.metric("Star Player", f"{star_count}x ⭐")
            
            # Battle log table
            st.write("🎮 Detailed Games:")
            st.dataframe(pd.DataFrame(battles))

    def _style_battle_results(self, df: pd.DataFrame) -> List:
        """
        Styles the battle log table.

        Args:
            df (pd.DataFrame): Battle log DataFrame

        Returns:
            List: List with styling properties
        """
        return ['background-color: #2E7D32' if x == 'Victory'
                else 'background-color: #C62828' if x == 'Defeat'
                else 'background-color: #455A64' if x == 'Draw'
                else '' for x in df]

    def show_error_message(self, message: str) -> None:
        """
        Shows an error message.

        Args:
            message (str): Error message to display
        """
        st.error(f"⚠️ {message}")

    def show_success_message(self, message: str) -> None:
        """
        Shows a success message.

        Args:
            message (str): Success message to display
        """
        st.success(f"✅ {message}")

    def create_win_rate_chart(self, statistics: Dict[str, Any], player_name: str) -> None:
        """
        Creates a pie chart for the win rate.

        Args:
            statistics (Dict[str, Any]): Player statistics
            player_name (str): Name of the player
        """
        fig = go.Figure(data=[go.Pie(
            labels=['Victories', 'Defeats', 'Draws'],
            values=[statistics['wins'], statistics['losses'], statistics['draws']],
            hole=.3,
            marker_colors=[self.colors['victory'], 
                         self.colors['defeat'], 
                         self.colors['draw']]
        )])
        
        fig.update_layout(
            title=f"Win Rate: {player_name}",
            **self.chart_config
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_brawler_stats(self, stats: Dict, column) -> None:
        """Displays brawler statistics in the given column"""
        with column:
            st.subheader("Brawler Statistics")
            
            # Create three rows of metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Brawlers", stats.get('total_brawlers', 0))
                st.metric("Power 9+ Brawlers", stats.get('high_level_brawlers', 0))
                st.metric("Power 11 Brawlers", stats.get('max_level_brawlers', 0))
            
            with col2:
                st.metric("Total Gears", stats.get('total_gears', 0))
                st.metric("Total Star Powers", stats.get('total_starpowers', 0))
                st.metric("Total Gadgets", stats.get('total_gadgets', 0))

    def display_brawler_details(self, brawler_details: List[Dict], column) -> None:
        """
        Displays detailed brawler information in a table.
        
        Args:
            brawler_details (List[Dict]): List of formatted brawler details
            column: Streamlit column object
        """
        with column:
            st.subheader("Detailed Brawler Information")
            
            # Convert to DataFrame for better display
            df = pd.DataFrame(brawler_details)
            
            # Configure column display
            st.dataframe(
                df,
                column_config={
                    'Name': st.column_config.TextColumn('Name', width='medium'),
                    'Power': st.column_config.NumberColumn('Power', format='%d'),
                    'Rank': st.column_config.NumberColumn('Rank', format='%d'),
                    'Trophies': st.column_config.NumberColumn('Trophies', format='%d'),
                    'Highest Trophies': st.column_config.NumberColumn('Highest', format='%d'),
                    'Gears': st.column_config.TextColumn('Gears', width='large'),
                    'Star Powers': st.column_config.TextColumn('Star Powers', width='large'),
                    'Gadgets': st.column_config.TextColumn('Gadgets', width='large')
                },
                hide_index=True,
                use_container_width=True
            )
