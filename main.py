import os
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import logging
import plotly.express as px
import together

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
        self.ui = BrawlStarsUI()

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
        selected_page = st.sidebar.radio(
            "Navigation",
            ["Player Comparison", "Brawlers", "Clubs"],
            index=0
        )

        if selected_page == "Player Comparison":
            self._show_player_comparison_page()
        elif selected_page == "Brawlers":
            self._show_brawler_page()
        else:
            self._show_clubs_page()

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
        
        # Load all brawlers
        brawlers_data = self.api_client.get_brawlers()
        
        if not brawlers_data or 'items' not in brawlers_data:
            st.error("Error loading brawler data")
            return

        # Get all brawlers and sort them alphabetically
        brawlers = sorted(brawlers_data.get('items', []), key=lambda x: x.get('name', ''))
        
        # Create two columns: one for the brawler list and one for details
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Select Brawler")
            # Create a list of brawlers as buttons
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
                                            if "Hydropi" in m), 0)
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

    def _display_battle_logs(self, battles1: Dict, battles2: Dict, 
                            player1_tag: str, player2_tag: str) -> None:
        """Shows the battle logs of both players"""
        st.header("Recent Games")
        
        # Trophy progression as line chart
        st.subheader("Trophy Progression in Recent Games")
        
        # Get player names from player info
        player1_data = self.api_client.get_player_info(player1_tag)
        player2_data = self.api_client.get_player_info(player2_tag)
        
        player1_name = player1_data['name'] if player1_data else "Player 1"
        player2_name = player2_data['name'] if player2_data else "Player 2"
        
        # Helper function to calculate cumulative trophies
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

        # Calculate cumulative trophies for both players
        trophies1 = calculate_cumulative_trophies(battles1, player1_tag)
        trophies2 = calculate_cumulative_trophies(battles2, player2_tag)
        
        # Create DataFrame for the line chart with actual names
        chart_data = pd.DataFrame({
            'Game': range(1, max(len(trophies1), len(trophies2)) + 1),
            player1_name: trophies1 + [None] * (len(trophies2) - len(trophies1)) if len(trophies2) > len(trophies1) else trophies1,
            player2_name: trophies2 + [None] * (len(trophies1) - len(trophies2)) if len(trophies1) > len(trophies2) else trophies2
        })
        
        # Create line chart with Plotly and actual names
        fig = px.line(
            chart_data,
            x='Game',
            y=[player1_name, player2_name],
            color_discrete_map={
                player1_name: '#8B0000',  # Dark red
                player2_name: '#00008B'   # Dark blue
            }
        )
        
        # Adjust layout
        fig.update_layout(
            xaxis_title="Game Number",
            yaxis_title="Cumulative Trophy Change",
            plot_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Original battle log display
        col1, col2 = st.columns(2)
        
        with col1:
            formatted_battles1, star_count1 = self.data_processor.format_battle_log(
                battles1, player1_tag)
            if formatted_battles1:
                stats1 = self.data_processor.calculate_battle_statistics(formatted_battles1)
                
                st.metric("Victories", f"{stats1['victories']}/{stats1['total_games']}")
                st.metric("Win Rate", f"{stats1['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count1}x ⭐")
                
                st.dataframe(pd.DataFrame(formatted_battles1))

        with col2:
            formatted_battles2, star_count2 = self.data_processor.format_battle_log(
                battles2, player2_tag)
            if formatted_battles2:
                stats2 = self.data_processor.calculate_battle_statistics(formatted_battles2)
                
                st.metric("Victories", f"{stats2['victories']}/{stats2['total_games']}")
                st.metric("Win Rate", f"{stats2['win_rate']:.1f}%")
                st.metric("Star Player", f"{star_count2}x ⭐")
                
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

        Create a concise analysis (4-6 sentences) comparing these players.
        Highlight key differences and mention who is stronger in which areas.
        Focus on the most significant stats that show the skill and progress level of each player.
        """

        try:
            # Using Together AI's completion endpoint
            response = together.Complete.create(
                prompt=f"<human>You are a Brawl Stars expert. {prompt}</human><assistant>",
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                max_tokens=300,
                temperature=0.7,
                top_k=50,
                top_p=0.7,
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

def main():
    """Hauptfunktion zum Starten der App"""
    app = BrawlStarsApp()
    app.run()

if __name__ == "__main__":
    main()
