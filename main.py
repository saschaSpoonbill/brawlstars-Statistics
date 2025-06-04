import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import logging
import plotly.express as px
import together
import json
import pathlib
from bs4 import BeautifulSoup
import shutil
import plotly.graph_objects as go

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="BrawlerInsight",
    page_icon="🏆",  # Optional: fügt ein Favicon/Icon hinzu
    layout="wide"
)

def inject_ga():
    """Inject Google Analytics code into Streamlit's index.html"""
    GA_ID = "google_analytics"

    GA_JS = """
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-NCG7739DG5"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'G-NCG7739DG5');
    </script>
    """

    # Insert the script in the head tag of the static template
    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    logging.info(f'editing {index_path}')
    soup = BeautifulSoup(index_path.read_text(), features="html.parser")
    if not soup.find(id=GA_ID): 
        bck_index = index_path.with_suffix('.bck')
        if bck_index.exists():
            shutil.copy(bck_index, index_path)  
        else:
            shutil.copy(index_path, bck_index)  
        html = str(soup)
        new_html = html.replace('<head>', '<head>\n' + GA_JS)
        index_path.write_text(new_html)

# Inject Google Analytics
inject_ga()

from api_client import BrawlStarsAPI
from data_processor import BrawlStarsDataProcessor
from ui_components import BrawlStarsUI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BrawlStarsApp:
    # Predefined club tags (starting with '#')
    CLUB_TAGS = {
        "Venom Vipers": "#JOLVRPRP",
        "grand": "#CV2LQLQU",
        "i pro": "#GRP8LQJ8",
        "MA NAJJACI SMOO": "#2UU9UlJUR",
        "Spike": "#2YJQ8LRCG"
    }

    def __init__(self):
        """Initialize the app with API key and clients"""
        self._load_environment()
        self.api_client = BrawlStarsAPI(self.api_key)
        self.data_processor = BrawlStarsDataProcessor()
        self.ui = BrawlStarsUI(self.data_processor)

    def _load_environment(self) -> None:
        """Load environment variables"""
        load_dotenv()
        self.api_key = os.getenv("BRAWLSTARS_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("BRAWLSTARS_API_KEY must be defined in .env")
        if not self.together_api_key:
            raise ValueError("TOGETHER_API_KEY must be defined in .env")
        # Initialize Together AI
        together.api_key = self.together_api_key

    def run(self) -> None:
        """Main method to run the app"""
        # Get current page from URL parameters using the new method
        current_page = st.query_params.get("page", "main")
        
        if current_page == "extended_stats":
            self._show_extended_stats_page()
            return
        
        # Sidebar navigation
        selected_page = st.sidebar.radio(
            "Navigation",
            ["Player Comparison", "Clubs", "Brawlers"],
            index=0
        )
        
        # Add Buy Me a Coffee section at bottom of sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            """
            <div style='text-align: center; color: #888;'>
                <p>Help keep this service running!</p>
                <a href='https://buymeacoffee.com/brawlerinsight' target='_blank'>
                    <img src='https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png' 
                         alt='Buy Me A Coffee' 
                         style='height: 40px; width: 160px;'>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

        if selected_page == "Player Comparison":
            self._show_player_comparison_page()
        elif selected_page == "Clubs":
            self._show_clubs_page()
        else:
            self._show_brawler_page()

    def _show_player_comparison_page(self) -> None:
        """Shows the player comparison page"""
        st.title("Brawl Stars Player Comparison")
        
        # Load club information
        club_info = self._load_club_info()
        
        # Player selection
        player1_tag, player2_tag = self._setup_player_selection(club_info)
        
        if player1_tag and player2_tag:
            self._display_player_comparison(player1_tag, player2_tag)

    def _show_brawler_page(self) -> None:
        """Shows the brawler analysis page"""
        st.title("Brawler Analysis")
        
        # Initialize session state variables if they don't exist
        if 'selected_brawler' not in st.session_state:
            st.session_state.selected_brawler = None
        if 'selected_brawler_name' not in st.session_state:
            st.session_state.selected_brawler_name = None
        
        # Load all brawlers
        brawlers_data = self.api_client.get_brawlers()
        
        if not brawlers_data or 'items' not in brawlers_data:
            st.error("Error loading brawler data")
            return

        # Get all brawlers and sort them alphabetically
        brawlers = sorted(brawlers_data.get('items', []), key=lambda x: x.get('name', ''))
        
        # Create a grid layout for brawler selection
        st.write("### Select Brawler")
        
        # Create a search box for brawlers
        search_term = st.text_input("🔍 Search Brawler", "").lower()
        
        # Filter brawlers based on search
        if search_term:
            brawlers = [b for b in brawlers if search_term in b['name'].lower()]
        
        # Create a grid of brawlers using columns
        cols_per_row = 6  # Number of brawlers per row
        
        for i in range(0, len(brawlers), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(brawlers):
                    brawler = brawlers[i + j]
                    # Create a button with brawler name
                    if col.button(
                        brawler['name'],
                        key=f"brawler_{brawler['id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_brawler = brawler['id']
                        st.session_state.selected_brawler_name = brawler['name']
                        # Scroll to top when a brawler is selected
                        st.rerun()

        # Show selected brawler details in an expander
        if 'selected_brawler' in st.session_state and st.session_state.selected_brawler_name:
            with st.expander(f"Details for {st.session_state.selected_brawler_name}", expanded=True):
                self._show_brawler_details(
                    st.session_state.selected_brawler,
                    st.session_state.selected_brawler_name
                )

        if 'selected_brawler_name' in st.session_state and st.session_state.selected_brawler_name:
            # Lade Tips für den ausgewählten Brawler
            brawler_tips = self._load_brawler_tips(st.session_state.selected_brawler_name)
            
            if brawler_tips:
                st.write("---")
                st.header(f"Tips for {st.session_state.selected_brawler_name}")
                
                # Game Modes and Maps
                with st.expander("Game Modes and Maps", expanded=True):
                    for tip in brawler_tips.get('GameModesAndMaps', []):
                        st.write(f"• {tip}")
                
                # Recommended Build
                with st.expander("Recommended Build", expanded=True):
                    for tip in brawler_tips.get('RecommendedBuild', []):
                        st.write(f"• {tip}")
                
                # Strategies and Other
                with st.expander("Strategies and Other", expanded=True):
                    for tip in brawler_tips.get('StrategiesAndOther', []):
                        st.write(f"• {tip}")
            else:
                st.info(f"No tips available for {st.session_state.selected_brawler_name}")

        # Nach der AI-Analyse Anzeige
        st.markdown(
            """
            <div style='text-align: right; font-size: 0.8em; color: #888;'>
                AI analysis powered by Together AI. 
                <a href='https://buymeacoffee.com/brawlerinsight' target='_blank'>Support this feature</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    def _show_brawler_details(self, brawler_id: str, brawler_name: str) -> None:
        """Shows detailed information for a selected brawler"""
        st.subheader(f"Details for {brawler_name}")
        
        # Load detailed brawler information
        brawler_details = self.api_client.get_brawler_info(brawler_id)
        
        if not brawler_details:
            st.error("Error loading brawler details")
            return
        
        # Create tabs for different information
        tab1, tab2 = st.tabs(["Abilities", "Global Ranking"])
        
        with tab1:
            # Display Star Powers
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
            
            # Display Gadgets
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
            # Load and display ranking information
            rankings = self.api_client.get_brawler_rankings(brawler_id)
            if rankings and 'items' in rankings:
                st.markdown("### Top 10 Players Global")
                ranking_data = []
                for idx, player in enumerate(rankings['items'][:10], 1):
                    ranking_data.append({
                        'Rank': idx,
                        'Player': player['name'],
                        'Trophies': player['trophies'],
                        'Club': player.get('club', {}).get('name', 'No Club')
                    })
                
                st.dataframe(
                    ranking_data,
                    column_config={
                        'Rank': st.column_config.NumberColumn(format="%d"),
                        'Trophies': st.column_config.NumberColumn(format="%d")
                    },
                    hide_index=True
                )
            else:
                st.warning("No ranking data available")

    def _load_club_info(self) -> Dict:
        """Loads information for all predefined clubs"""
        club_info = {}
        for name, tag in self.CLUB_TAGS.items():
            club_data = self.api_client.get_club_info(tag)
            if club_data:
                club_info[name] = club_data
        return club_info

    def _setup_player_selection(self, club_info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Creates the user interface for player selection"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Player 1")
            # Tab for selection method
            selection_mode1 = st.radio(
                "Selection method for Player 1",
                ["Select from Club", "Enter Player ID"],
                key="selection_mode1",
                horizontal=True
            )
            
            if selection_mode1 == "Select from Club":
                club1 = st.selectbox(
                    "Select Club (Player 1)",
                    options=list(club_info.keys()),
                    key="club1",
                    index=list(club_info.keys()).index("Venom Vipers")
                )
                if club1:
                    members1 = self.api_client.get_club_members(self.CLUB_TAGS[club1])
                    if members1:
                        member_list1 = [f"{m['name']} ({m['tag']})" for m in members1['items']]
                        default_index1 = next((i for i, m in enumerate(member_list1) 
                                            if "Spoony" in m), 0)
                        player1 = st.selectbox(
                            "Select Player 1",
                            options=member_list1,
                            key="player1",
                            index=default_index1
                        )
                        player1_tag = player1.split('(')[1].rstrip(')') if player1 else None
                    else:
                        player1_tag = None
                        st.error("Error loading club members")
            else:
                player1_tag = st.text_input(
                    "Enter Player ID (with #)",
                    placeholder="#2YJQ8LRCG",
                    key="player1_direct"
                )
                if player1_tag and not player1_tag.startswith('#'):
                    st.error("Player ID must start with #")
                    player1_tag = None

        with col2:
            st.subheader("Player 2")
            # Tab for selection method
            selection_mode2 = st.radio(
                "Selection method for Player 2",
                ["Select from Club", "Enter Player ID"],
                key="selection_mode2",
                horizontal=True
            )
            
            if selection_mode2 == "Select from Club":
                club2 = st.selectbox(
                    "Select Club (Player 2)",
                    options=list(club_info.keys()),
                    key="club2",
                    index=list(club_info.keys()).index("Venom Vipers")
                )
                if club2:
                    members2 = self.api_client.get_club_members(self.CLUB_TAGS[club2])
                    if members2:
                        member_list2 = [f"{m['name']} ({m['tag']})" for m in members2['items']]
                        default_index2 = next((i for i, m in enumerate(member_list2) 
                                            if "Creppy" in m), 0)
                        player2 = st.selectbox(
                            "Select Player 2",
                            options=member_list2,
                            key="player2",
                            index=default_index2
                        )
                        player2_tag = player2.split('(')[1].rstrip(')') if player2 else None
                    else:
                        player2_tag = None
                        st.error("Error loading club members")
            else:
                player2_tag = st.text_input(
                    "Enter Player ID (with #)",
                    placeholder="#2YJQ8LRCG",
                    key="player2_direct"
                )
                if player2_tag and not player2_tag.startswith('#'):
                    st.error("Player ID must start with #")
                    player2_tag = None

        # Validate player tags before returning
        if player1_tag and player2_tag:
            # Check if players exist
            test_player1 = self.api_client.get_player_info(player1_tag)
            test_player2 = self.api_client.get_player_info(player2_tag)
            
            if not test_player1:
                st.error(f"Player 1 with tag {player1_tag} not found.")
                return None, None
            
            if not test_player2:
                st.error(f"Player 2 with tag {player2_tag} not found.")
                return None, None

        return player1_tag, player2_tag

    def _display_player_comparison(self, player1_tag: str, player2_tag: str) -> None:
        """Shows the comparison between two players"""
        # Load player data
        player1_data = self.api_client.get_player_info(player1_tag)
        player2_data = self.api_client.get_player_info(player2_tag)

        if not player1_data or not player2_data:
            st.error("Error loading player data")
            return

        # Load club information
        club1_info = None
        club2_info = None
        if 'club' in player1_data and player1_data['club'].get('tag'):
            club1_info = self.api_client.get_club_info(player1_data['club']['tag'])
        if 'club' in player2_data and player2_data['club'].get('tag'):
            club2_info = self.api_client.get_club_info(player2_data['club']['tag'])

        # Display player statistics
        col1, col2 = st.columns(2)
        self.ui.display_player_stats(player1_data, club1_info, col1)
        self.ui.display_player_stats(player2_data, club2_info, col2)

        # Trophy comparison as bar chart with Plotly
        st.header("Trophy Comparison")
        trophy_data = {
            'Player': [player1_data['name'], player2_data['name']],
            'Trophies': [player1_data['trophies'], player2_data['trophies']]
        }
        trophy_df = pd.DataFrame(trophy_data)
        
        # Create a Plotly bar chart with dark blue and dark red
        fig = px.bar(
            trophy_df,
            x='Player',
            y='Trophies',
            color='Player',
            color_discrete_map={
                player1_data['name']: '#8B0000',  # Dark red for Player 1
                player2_data['name']: '#00008B'   # Dark blue for Player 2
            },
            text='Trophies'
        )
        
        # Adjust layout
        fig.update_traces(textposition='outside')  # Values above bars
        fig.update_layout(
            showlegend=False,  # Hide legend
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            height=400  # Chart height
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Victory comparison as bar chart
        st.header("Victory Comparison")
        
        # Prepare data for different victory types
        victories_data = {
            'Player': [
                player1_data['name'], player1_data['name'], player1_data['name'],
                player2_data['name'], player2_data['name'], player2_data['name']
            ],
            'Victory Type': ['3vs3', 'Solo', 'Duo'] * 2,
            'Count': [
                player1_data.get('3vs3Victories', 0),
                player1_data.get('soloVictories', 0),
                player1_data.get('duoVictories', 0),
                player2_data.get('3vs3Victories', 0),
                player2_data.get('soloVictories', 0),
                player2_data.get('duoVictories', 0)
            ]
        }
        victories_df = pd.DataFrame(victories_data)
        
        # Create a grouped bar chart for victories
        fig_victories = px.bar(
            victories_df,
            x='Victory Type',
            y='Count',
            color='Player',
            barmode='group',  # Grouped bars side by side
            color_discrete_map={
                player1_data['name']: '#8B0000',  # Dark red for Player 1
                player2_data['name']: '#00008B'   # Dark blue for Player 2
            },
            text='Count'  # Show values above bars
        )
        
        # Adjust layout
        fig_victories.update_traces(textposition='outside')
        fig_victories.update_layout(
            showlegend=True,  # Show legend for better distinction
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis_title="Game Mode",
            yaxis_title="Number of Victories"
        )
        
        st.plotly_chart(fig_victories, use_container_width=True)

        # Display brawler statistics
        st.header("Brawler Comparison")
        brawler_col1, brawler_col2 = st.columns(2)
        
        # Calculate and show brawler statistics
        brawler_stats1 = self.data_processor.calculate_brawler_statistics(player1_data)
        brawler_stats2 = self.data_processor.calculate_brawler_statistics(player2_data)
        
        self.ui.display_brawler_stats(brawler_stats1, brawler_col1)
        self.ui.display_brawler_stats(brawler_stats2, brawler_col2)
        
        # Add detailed brawler information
        detail_col1, detail_col2 = st.columns(2)
        
        # Format and display detailed brawler information
        brawler_details1 = self.data_processor.format_brawler_details(player1_data)
        brawler_details2 = self.data_processor.format_brawler_details(player2_data)
        
        self.ui.display_brawler_details(brawler_details1, detail_col1)
        self.ui.display_brawler_details(brawler_details2, detail_col2)

        # Display battle logs
        battles1 = self.api_client.get_battle_log(player1_tag)
        battles2 = self.api_client.get_battle_log(player2_tag)
        
        if battles1 and battles2:
            self._display_battle_logs(battles1, battles2, player1_tag, player2_tag)
            
            # Add AI analysis button
            st.header("AI Analysis")
            if st.button("Generate AI Analysis"):
                with st.spinner("Generating analysis..."):
                    # Calculate statistics for analysis
                    formatted_battles1, star_count1 = self.data_processor.format_battle_log(battles1, player1_tag)
                    formatted_battles2, star_count2 = self.data_processor.format_battle_log(battles2, player2_tag)
                    battle_stats1 = self.data_processor.calculate_battle_statistics(formatted_battles1)
                    battle_stats2 = self.data_processor.calculate_battle_statistics(formatted_battles2)
                    
                    # Generate AI analysis
                    analysis = self._generate_ai_comparison(
                        player1_data, player2_data,
                        brawler_stats1, brawler_stats2,
                        battle_stats1, battle_stats2,
                        star_count1, star_count2
                    )
                    
                    # Display analysis in a nice container
                    st.markdown("""
                        <style>
                            .analysis-container {
                                padding: 20px;
                                border-radius: 10px;
                                background-color: rgba(255, 255, 255, 0.05);
                                margin: 10px 0;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="analysis-container">{analysis}</div>', unsafe_allow_html=True)

        # Add Buy Me a Coffee info after AI analysis
        st.markdown(
            """
            <div style='text-align: right; font-size: 0.8em; color: #888;'>
                AI analysis powered by Together AI. 
                <a href='https://buymeacoffee.com/brawlerinsight' target='_blank'>Support this feature</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    def _display_battle_logs(self, battles1, battles2, player1_tag, player2_tag):
        """Displays battle logs for both players side by side"""
        player1_name = self._get_player_name(player1_tag)
        player2_name = self._get_player_name(player2_tag)
        
        # Trophy Progress Chart
        st.write("### Trophy Progression in Recent Games")
        
        if battles1 and battles2:
            # Process battle data for player 1
            formatted_battles1, star_count1 = self.data_processor.format_battle_log(battles1, player1_tag)
            df1 = pd.DataFrame(formatted_battles1)
            df1['Trophy_Change'] = pd.to_numeric(df1['Trophy Change'], errors='coerce').fillna(0)
            df1['Cumulative_Trophies'] = df1['Trophy_Change'].cumsum()
            
            # Process battle data for player 2
            formatted_battles2, star_count2 = self.data_processor.format_battle_log(battles2, player2_tag)
            df2 = pd.DataFrame(formatted_battles2)
            df2['Trophy_Change'] = pd.to_numeric(df2['Trophy Change'], errors='coerce').fillna(0)
            df2['Cumulative_Trophies'] = df2['Trophy_Change'].cumsum()
            
            # Create comparison data
            chart_data = pd.DataFrame({
                player1_name: df1['Cumulative_Trophies'].values,
                player2_name: df2['Cumulative_Trophies'].values
            })
            
            # Use native Streamlit line chart
            st.line_chart(
                chart_data,
                height=300
            )
        
        # Display battle logs in columns
        col1, col2 = st.columns(2)
        
        with col1:
            if formatted_battles1:
                stats1 = self.data_processor.calculate_battle_statistics(formatted_battles1)
                st.metric("Victories", f"{stats1['victories']}/{stats1['total_games']}")
                st.metric("Win Rate", f"{stats1['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count1}x ⭐")
                
                # Show link to extended statistics if available
                if self.data_processor.has_extended_statistics(player1_tag):
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 10px;'>
                            <a href="?page=extended_stats&player_tag={player1_tag.replace('#', '%23')}" target="_self">
                                📊 Advanced Battle Statistics available
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.dataframe(pd.DataFrame(formatted_battles1))
                
        with col2:
            if formatted_battles2:
                stats2 = self.data_processor.calculate_battle_statistics(formatted_battles2)
                st.metric("Victories", f"{stats2['victories']}/{stats2['total_games']}")
                st.metric("Win Rate", f"{stats2['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count2}x ⭐")
                
                # Show link to extended statistics if available
                if self.data_processor.has_extended_statistics(player2_tag):
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 10px;'>
                            <a href="?page=extended_stats&player_tag={player2_tag.replace('#', '%23')}" target="_self">
                                📊 Advanced Battle Statistics available
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.dataframe(pd.DataFrame(formatted_battles2))

    def _show_clubs_page(self) -> None:
        """Shows the club analysis page"""
        st.title("Club Analysis")

        # Two tabs for existing clubs and custom club ID
        tab1, tab2 = st.tabs(["Existing Clubs", "Enter Club ID"])

        with tab1:
            selected_club = st.selectbox(
                "Select Club",
                options=list(self.CLUB_TAGS.keys())
            )
            if selected_club:
                club_tag = self.CLUB_TAGS[selected_club]
                self._display_club_info(club_tag)

        with tab2:
            custom_tag = st.text_input(
                "Enter Club Tag (with #)",
                placeholder="#JOLVRPRP"
            )
            if custom_tag:
                if not custom_tag.startswith('#'):
                    st.error("Club tag must start with #")
                else:
                    self._display_club_info(custom_tag)

    def _display_club_info(self, club_tag: str) -> None:
        """Shows detailed information for a club"""
        club_info = self.api_client.get_club_info(club_tag)
        
        if not club_info:
            st.error("Club not found or error loading data")
            return

        # Club header with basic information
        st.header(club_info['name'])
        
        # Find president
        president = next((member for member in club_info.get('members', []) 
                         if member['role'].lower() == 'president'), None)
        president_name = president['name'] if president else "Unknown"
        
        # Calculate trophy statistics
        if club_info.get('members'):
            member_trophies = [member['trophies'] for member in club_info['members']]
            min_trophies = min(member_trophies)
            max_trophies = max(member_trophies)
            avg_trophies = sum(member_trophies) / len(member_trophies)
        else:
            min_trophies = max_trophies = avg_trophies = 0
        
        # Display club metrics in two rows
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trophies", f"{club_info['trophies']:,}")
        with col2:
            st.metric("Required Trophies", f"{club_info.get('requiredTrophies', 0):,}")
        with col3:
            st.metric("Members", f"{len(club_info.get('members', []))}/30")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("President", president_name)
        with col2:
            st.metric("Type", club_info.get('type', 'Unknown').replace('_', ' ').title())
        with col3:
            st.metric("Average Trophies", f"{int(avg_trophies):,}")
        
        # Trophy range info
        st.info(f"Trophy Range: {min_trophies:,} - {max_trophies:,} 🏆")

        # Rest of the club info display remains the same...
        if club_info.get('description'):
            st.markdown("### Description")
            st.write(club_info['description'])

        # Member list
        st.markdown("### Members")
        
        if 'members' in club_info:
            # Create DataFrame for members
            members_data = []
            for member in club_info['members']:
                members_data.append({
                    'Name': member['name'],
                    'Role': member['role'].capitalize(),
                    'Trophies': member['trophies'],
                    'Tag': member['tag']
                })
            
            df = pd.DataFrame(members_data)
            
            # Sort by trophies descending
            df = df.sort_values('Trophies', ascending=False)
            
            # Show table with adjusted styling
            st.dataframe(
                df,
                column_config={
                    'Name': st.column_config.TextColumn('Name'),
                    'Role': st.column_config.TextColumn('Role'),
                    'Trophies': st.column_config.NumberColumn('Trophies', format="%d"),
                    'Tag': st.column_config.TextColumn('Tag')
                },
                hide_index=True
            )

            # Trophy distribution as histogram
            st.markdown("### Trophy Distribution")
            fig = px.histogram(
                df,
                x='Trophies',
                nbins=20,
                title='Distribution of Member Trophies'
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Role distribution as pie chart
            st.markdown("### Role Distribution")
            role_counts = df['Role'].value_counts()
            fig_roles = px.pie(
                values=role_counts.values,
                names=role_counts.index,
                title='Distribution of Club Roles'
            )
            fig_roles.update_layout(height=400)
            st.plotly_chart(fig_roles, use_container_width=True)

    def _generate_ai_comparison(self, player1_data: Dict, player2_data: Dict,
                              brawler_stats1: Dict, brawler_stats2: Dict,
                              battle_stats1: Dict, battle_stats2: Dict,
                              star_count1: int, star_count2: int) -> str:
        """Generates an AI-based analysis of the player comparison"""
        
        prompt = f"""
        Compare these two Brawl Stars players based on their statistics:

        Player 1 ({player1_data['name']}):
        - Highest Trophies: {player1_data['highestTrophies']}
        - 3vs3 Victories: {player1_data.get('3vs3Victories', 0)}
        - Solo Victories: {player1_data.get('soloVictories', 0)}
        - Duo Victories: {player1_data.get('duoVictories', 0)}
        - Club Trophies: {player1_data.get('club', {}).get('trophies', 0)}
        - Total Brawlers: {brawler_stats1.get('total_brawlers', 0)}
        - Brawlers Power 9+: {brawler_stats1.get('high_level_brawlers', 0)}
        - Brawlers Power 11: {brawler_stats1.get('max_level_brawlers', 0)}
        - Recent Win Rate: {battle_stats1.get('win_rate', 0):.1f}%
        - Star Player Count: {star_count1}

        Player 2 ({player2_data['name']}):
        - Highest Trophies: {player2_data['highestTrophies']}
        - 3vs3 Victories: {player2_data.get('3vs3Victories', 0)}
        - Solo Victories: {player2_data.get('soloVictories', 0)}
        - Duo Victories: {player2_data.get('duoVictories', 0)}
        - Club Trophies: {player2_data.get('club', {}).get('trophies', 0)}
        - Total Brawlers: {brawler_stats2.get('total_brawlers', 0)}
        - Brawlers Power 9+: {brawler_stats2.get('high_level_brawlers', 0)}
        - Brawlers Power 11: {brawler_stats2.get('max_level_brawlers', 0)}
        - Recent Win Rate: {battle_stats2.get('win_rate', 0):.1f}%
        - Star Player Count: {star_count2}

        Create a concise analysis, in maximum 6-8 sentences, comparing these players.
        Highlight key differences and mention who is stronger in which areas.
        Just one paragraph in response.
        Classify the players based on their trophy count using this scale: Beginner (0 to 700), Novice (701 to 3,000), Intermediate (3,001 to 10,000), Proficient (10,001 to 20,000), Advanced (20,001 to 50,000), Expert (50,001+).
        Focus on the most significant stats that show the skill and progress level of each player.
        """

        try:
            # Using Together AI's completion endpoint
            response = together.Complete.create(
                prompt=f"<human>You are a Brawl Stars expert. {prompt}</human><assistant>",
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                temperature=0.3,
                max_tokens=300,
                top_k=40,
                top_p=0.5,
                repetition_penalty=1.1
            )
            
            # Debug logging
            logging.info(f"AI Response: {response}")
            
            # Extract the generated text from the response
            if isinstance(response, dict):
                # Navigate through the response structure
                if 'output' in response and 'choices' in response['output']:
                    choices = response['output']['choices']
                    if choices and len(choices) > 0 and 'text' in choices[0]:
                        return choices[0]['text'].strip()
            
            logging.error(f"Unexpected response structure: {response}")
            return "Error: Could not extract analysis from AI response"
            
        except Exception as e:
            error_msg = f"Error generating AI analysis: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def _load_brawler_tips(self, brawler_name: str) -> Dict:
        """Lädt die Tips für einen bestimmten Brawler aus der JSON-Datei"""
        try:
            with open('BrawlerTips.json', 'r', encoding='utf-8') as f:
                tips_data = json.load(f)
                
            # Suche den Brawler in den Tips (case-insensitive)
            for brawler in tips_data['brawlers']:
                if brawler['brawlerName'].lower() == brawler_name.lower():
                    return brawler['tips']
                    
            return {} # Leeres Dict falls Brawler nicht gefunden
        except Exception as e:
            logging.error(f"Error loading brawler tips: {e}")
            return {}

    def _show_extended_stats_page(self) -> None:
        """Shows the extended statistics page"""
        player_tag = st.query_params.get("player_tag")
        
        if not player_tag:
            st.error("No player selected")
            return
            
        # Convert URL-encoded player tag back to normal format
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag.replace('%23', '')}"
            
        player_name = self.data_processor.PLAYERS_WITH_EXTENDED_STATS.get(player_tag, "Unknown")
        st.title(f"Advanced Statistics: {player_name}")
        
        # Date Range Selection
        st.write("### 📅 Select Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=None,
                format="YYYY-MM-DD"
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=None,
                format="YYYY-MM-DD"
            )
            
        # Convert dates to ISO format if selected
        start_datetime = f"{start_date}T00:00:00" if start_date else None
        end_datetime = f"{end_date}T23:59:59" if end_date else None
        
        # Fetch and display extended statistics
        stats = self.data_processor.get_extended_statistics(
            player_tag,
            start_date=start_datetime,
            end_date=end_datetime
        )
        if stats:
            # Time Range
            st.write("### 📅 Time Range")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("First Battle", stats.get("first_battle", "Unknown"))
            with col2:
                st.metric("Last Battle", stats.get("last_battle", "Unknown"))
            
            st.markdown("---")  # Trennlinie
            
            # Battle Statistics
            st.write("### 🎮 Battle Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Battles", f"{stats.get('total_battles', 0):,}")
            with col2:
                total_victories = int(stats.get('total_battles', 0) * stats.get('win_rate', 0) / 100)
                st.metric("Total Victories", f"{total_victories:,}")
            with col3:
                st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
            
            st.markdown("---")  # Trennlinie
            
            # Daily Averages
            st.write("### 📈 Daily Averages")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Battles/Day", f"{stats.get('avg_battles_per_day', 0):.1f}")
            with col2:
                st.metric("Victories/Day", f"{stats.get('avg_victories_per_day', 0):.1f}")
            with col3:
                st.metric("Trophies/Day", f"{stats.get('avg_trophies_per_day', 0):.1f}")
                
            st.markdown("---")  # Trennlinie
            
            # Trophy Progress Chart
            st.write("### 🏆 Trophy Progress")
            progress_data = self.data_processor.get_trophy_progress(
                player_tag,
                start_date=start_datetime,
                end_date=end_datetime
            )
            
            if progress_data and 'daily_progress' in progress_data:
                # Convert data to DataFrame
                df = pd.DataFrame(progress_data['daily_progress'])
                df['date'] = pd.to_datetime(df['date']).dt.date
                
                # Calculate cumulative trophy progress
                df['cumulative_trophies'] = df['trophy_change'].cumsum()
                
                # Create cumulative trophy progress chart
                st.line_chart(
                    df,
                    x='date',
                    y='cumulative_trophies',
                    height=400
                )
                
                # Show total progress
                st.metric(
                    "Total Trophy Progress",
                    f"{progress_data.get('total_trophy_change', 0):+,}"
                )
        else:
            st.error("Could not load extended statistics")

        st.markdown("---")  # Trennlinie
        
        # Brawler Statistics
        st.write("### 🤖 Brawler Statistics")
        brawler_data = self.data_processor.get_brawler_statistics(
            player_tag,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        if brawler_data and 'brawler_statistics' in brawler_data:
            # Convert to DataFrame and sort by battles
            df = pd.DataFrame(brawler_data['brawler_statistics'])
            df = df.sort_values('battles', ascending=False)
            
            # Display as interactive table
            st.dataframe(
                df,
                column_config={
                    "brawler_name": st.column_config.TextColumn("Brawler", width="medium"),
                    "battles": st.column_config.NumberColumn("Battles", width="small"),
                    "victories": st.column_config.NumberColumn("Victories", width="small"),
                    "trophy_change": st.column_config.NumberColumn("Trophy Δ", width="small"),
                    "win_rate": st.column_config.NumberColumn("Win Rate", width="small", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add scatter plot for Brawler Performance
            st.write("#### Brawler Performance Analysis")
            fig = px.scatter(
                df,
                x='battles',
                y='win_rate',
                color='trophy_change',
                size='victories',
                hover_name='brawler_name',
                hover_data={
                    'brawler_name': False,  # Hide brawler_name (shown in hover_name)
                    'battles': True,
                    'win_rate': ':.1f',
                    'trophy_change': True,
                    'victories': True
                },
                height=400,
                labels={
                    'battles': 'Total Battles',
                    'win_rate': 'Win Rate (%)',
                    'trophy_change': 'Trophy Change',
                    'victories': 'Victories'
                }
            )
            
            # Update layout for better appearance
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(bgcolor="white", font_size=14)
            )
            
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")  # Trennlinie
        
        # Game Mode Statistics
        st.write("### 🎮 Game Mode Statistics")
        gamemode_data = self.data_processor.get_gamemode_statistics(
            player_tag,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        if gamemode_data and 'game_mode_statistics' in gamemode_data:
            # Convert to DataFrame and sort by battles
            df = pd.DataFrame(gamemode_data['game_mode_statistics'])
            df = df.sort_values('battles', ascending=False)
            
            # Format battle_mode names for better readability
            df['battle_mode'] = df['battle_mode'].apply(lambda x: ' '.join(
                word.capitalize() for word in x.split('_')
            ))
            
            # Display as interactive table
            st.dataframe(
                df,
                column_config={
                    "battle_mode": st.column_config.TextColumn("Game Mode", width="medium"),
                    "battles": st.column_config.NumberColumn("Battles", width="small"),
                    "victories": st.column_config.NumberColumn("Victories", width="small"),
                    "trophy_change": st.column_config.NumberColumn("Trophy Δ", width="small"),
                    "win_rate": st.column_config.NumberColumn("Win Rate", width="small", format="%.1f%%"),
                    "avg_duration": st.column_config.NumberColumn("Avg Duration", width="small", format="%.1f s"),
                    "avg_trophies_per_battle": st.column_config.NumberColumn("Trophies/Battle", width="small", format="%.2f"),
                    "seconds_per_trophy": st.column_config.NumberColumn("Seconds/Trophy", width="small", format="%.1f")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add Game Mode Performance Analysis
            st.write("#### Game Mode Performance Analysis")
            
            # Filter modes with at least 10 battles for better visualization
            df_filtered = df[df['battles'] >= 10].copy()
            
            # Create Plotly grouped bar chart
            fig = px.bar(
                df_filtered,
                x='battle_mode',
                y=['battles', 'victories'],
                barmode='group',
                height=400,
                labels={
                    'battle_mode': 'Game Mode',
                    'value': 'Count',
                    'variable': 'Type'
                }
            )
            
            # Rotate x-axis labels for better readability
            fig.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")  # Trennlinie
        
        # Map Statistics
        st.write("### 🗺️ Map Statistics")
        map_data = self.data_processor.get_map_statistics(
            player_tag,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        if map_data and 'map_statistics' in map_data:
            # Convert to DataFrame and sort by battles
            df = pd.DataFrame(map_data['map_statistics'])
            df = df.sort_values('battles', ascending=False)
            
            # Create compact most played brawler info
            df['most_played'] = df['most_played_brawler'].apply(
                lambda x: f"{x['brawler_name']} ({x['battles']})"
            )
            
            # Create compact most trophies brawler info
            df['most_trophies'] = df['most_trophy_brawler'].apply(
                lambda x: f"{x['brawler_name']} ({x['trophy_change']:+})"
            )
            
            # Display as interactive table
            st.dataframe(
                df,
                column_config={
                    "event_map": st.column_config.TextColumn("Map", width="medium"),
                    "battle_mode": st.column_config.TextColumn("Mode", width="small"),
                    "battles": st.column_config.NumberColumn("Battles", width="small"),
                    "victories": st.column_config.NumberColumn("Victories", width="small"),
                    "trophy_change": st.column_config.NumberColumn("Trophy Δ", width="small"),
                    "win_rate": st.column_config.NumberColumn("Win Rate", width="small", format="%.1f%%"),
                    "avg_duration": st.column_config.NumberColumn("Avg Duration", width="small", format="%.1f s"),
                    "avg_trophies_per_battle": st.column_config.NumberColumn("Trophies/Battle", width="small", format="%.2f"),
                    "most_played": st.column_config.TextColumn("Most Played", width="small"),
                    "most_trophies": st.column_config.TextColumn("Most Trophies By", width="small")
                },
                column_order=[
                    "event_map", "battle_mode", "battles", "victories", "trophy_change",
                    "win_rate", "avg_duration", "avg_trophies_per_battle", "most_played", "most_trophies"
                ],
                hide_index=True,
                use_container_width=True
            )

    def _get_player_name(self, player_tag: str) -> str:
        """Gets the player name from player tag"""
        player_data = self.api_client.get_player_info(player_tag)
        return player_data['name'] if player_data else "Unknown Player"

def main():
    """Hauptfunktion zum Starten der App"""
    app = BrawlStarsApp()
    app.run()

if __name__ == "__main__":
    main()
