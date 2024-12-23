from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd

class BrawlStarsDataProcessor:
    """
    Processes and formats data from the Brawl Stars API.
    """

    def calculate_battle_statistics(self, battles: List[Dict]) -> Dict[str, Any]:
        """
        Calculates statistics from battle log data.

        Args:
            battles (List[Dict]): List of formatted battles

        Returns:
            Dict[str, Any]: Calculated statistics
        """
        if not battles:
            return {
                'total_games': 0,
                'victories': 0,
                'win_rate': 0.0
            }

        total_games = len(battles)
        victories = sum(1 for b in battles if b['Result'] == 'Victory')
        win_rate = (victories / total_games * 100) if total_games > 0 else 0

        return {
            'total_games': total_games,
            'victories': victories,
            'win_rate': win_rate
        }

    def format_battle_log(self, battles: Dict[str, Any], player_tag: str) -> Tuple[List[Dict], int]:
        """
        Formats the battle log and counts star player awards.

        Args:
            battles (Dict[str, Any]): Raw battle log data
            player_tag (str): Player tag for star player comparison

        Returns:
            Tuple[List[Dict], int]: (Formatted battles, Number of star player awards)
        """
        if not battles or 'items' not in battles:
            return [], 0

        formatted_battles = []
        star_player_count = 0

        for battle in battles['items'][:20]:  # Limited to last 20 games
            try:
                battle_info = self._format_single_battle(battle, player_tag)
                if battle_info.get('Star Player'):
                    star_player_count += 1
                formatted_battles.append(battle_info)
            except Exception as e:
                print(f"Error processing battle: {e}")
                continue

        return formatted_battles, star_player_count

    @staticmethod
    def _format_single_battle(battle: Dict[str, Any], player_tag: str) -> Dict[str, Any]:
        """
        Formats the data of a single battle.

        Args:
            battle (Dict[str, Any]): Raw data of a single battle
            player_tag (str): Player tag

        Returns:
            Dict[str, Any]: Formatted battle data
        """
        return {
            'Time': BrawlStarsDataProcessor._format_battle_time(battle.get('battleTime', '')),
            'Mode': BrawlStarsDataProcessor._get_battle_mode(battle),
            'Type': BrawlStarsDataProcessor._get_battle_type(battle),
            'Result': BrawlStarsDataProcessor._get_battle_result(battle),
            'Trophies': BrawlStarsDataProcessor._format_trophy_change(battle),
            'Star Player': BrawlStarsDataProcessor._check_star_player(battle, player_tag),
            'Brawler': BrawlStarsDataProcessor._get_player_brawler(battle, player_tag),
            'Power Level': BrawlStarsDataProcessor._get_power_level(battle, player_tag)
        }

    @staticmethod
    def _format_battle_time(battle_time: str) -> str:
        """
        Formats the timestamp of a battle.

        Args:
            battle_time (str): Raw timestamp

        Returns:
            str: Formatted timestamp
        """
        try:
            return datetime.strptime(battle_time, '%Y%m%dT%H%M%S.000Z').strftime('%d.%m.%Y %H:%M')
        except (ValueError, TypeError):
            return 'Unknown'

    @staticmethod
    def _get_battle_mode(battle: Dict[str, Any]) -> str:
        """
        Determines the game mode of a battle.

        Args:
            battle (Dict[str, Any]): Battle data

        Returns:
            str: Game mode
        """
        return battle.get('battle', {}).get('mode', 'Unknown')

    @staticmethod
    def _get_battle_type(battle: Dict[str, Any]) -> str:
        """
        Determines the battle type.

        Args:
            battle (Dict[str, Any]): Battle data

        Returns:
            str: Battle type
        """
        return battle.get('battle', {}).get('type', 'Unknown')

    @staticmethod
    def _get_battle_result(battle: Dict[str, Any]) -> str:
        """
        Determines the battle result and formats it uniformly.

        Args:
            battle (Dict[str, Any]): Battle data

        Returns:
            str: Formatted battle result ('Victory', 'Defeat' or 'Draw')
        """
        result = battle.get('battle', {}).get('result', '').lower()
        result_mapping = {
            'victory': 'Victory',
            'defeat': 'Defeat',
            'draw': 'Draw'
        }
        return result_mapping.get(result, 'No Result')

    @staticmethod
    def _format_trophy_change(battle: Dict[str, Any]) -> str:
        """
        Formats the trophy change.

        Args:
            battle (Dict[str, Any]): Battle data

        Returns:
            str: Formatted trophy change
        """
        trophy_change = battle.get('battle', {}).get('trophyChange', 0)
        if trophy_change > 0:
            return f"+{trophy_change}"
        return str(trophy_change)

    @staticmethod
    def _check_star_player(battle: Dict[str, Any], player_tag: str) -> str:
        """
        Checks if the player was star player.

        Args:
            battle (Dict[str, Any]): Battle data
            player_tag (str): Player tag

        Returns:
            str: Star player symbol or empty
        """
        star_player = battle.get('battle', {}).get('starPlayer', {})
        if star_player and star_player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
            return '⭐'
        return ''

    @staticmethod
    def _get_player_brawler(battle: Dict[str, Any], player_tag: str) -> str:
        """
        Determines the brawler used by the player.

        Args:
            battle (Dict[str, Any]): Battle data
            player_tag (str): Player tag

        Returns:
            str: Name of the brawler
        """
        try:
            for player in battle.get('battle', {}).get('players', []):
                if player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
                    return player.get('brawler', {}).get('name', 'Unknown')
        except Exception:
            pass
        return 'Unknown'

    @staticmethod
    def _get_power_level(battle: Dict[str, Any], player_tag: str) -> int:
        """
        Determines the power level of the used brawler.

        Args:
            battle (Dict[str, Any]): Battle data
            player_tag (str): Player tag

        Returns:
            int: Power level of the brawler
        """
        try:
            for player in battle.get('battle', {}).get('players', []):
                if player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
                    return player.get('brawler', {}).get('power', 0)
        except Exception:
            pass
        return 0

    def calculate_brawler_statistics(self, player_data: Dict) -> Dict:
        """
        Calculates statistics about a player's brawlers.

        Args:
            player_data (Dict): Player data containing brawler information

        Returns:
            Dict: Dictionary containing brawler statistics
        """
        if 'brawlers' not in player_data:
            return {
                'total_brawlers': 0,
                'high_level_brawlers': 0,
                'max_level_brawlers': 0,
                'avg_trophies': 0
            }

        brawlers = player_data['brawlers']
        total_brawlers = len(brawlers)
        total_trophies = sum(b['trophies'] for b in brawlers)
        
        # Count brawlers with power 9 or higher
        high_level_brawlers = sum(1 for b in brawlers if b.get('power', 0) >= 9)
        
        # Count brawlers with power 11
        max_level_brawlers = sum(1 for b in brawlers if b.get('power', 0) == 11)
        
        return {
            'total_brawlers': total_brawlers,
            'high_level_brawlers': high_level_brawlers,
            'max_level_brawlers': max_level_brawlers,
            'avg_trophies': total_trophies / total_brawlers if total_brawlers > 0 else 0
        }
