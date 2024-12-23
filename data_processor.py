from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd

class BrawlStarsDataProcessor:
    """
    Verarbeitet und formatiert Daten aus der Brawl Stars API.
    """

    def calculate_battle_statistics(self, battles: List[Dict]) -> Dict[str, Any]:
        """
        Berechnet Statistiken aus den Battle-Log-Daten.

        Args:
            battles (List[Dict]): Liste der formatierten Kämpfe

        Returns:
            Dict[str, Any]: Berechnete Statistiken
        """
        if not battles:
            return {
                'total_games': 0,
                'victories': 0,
                'win_rate': 0.0
            }

        total_games = len(battles)
        victories = sum(1 for b in battles if b['Ergebnis'] == 'Sieg')
        win_rate = (victories / total_games * 100) if total_games > 0 else 0

        return {
            'total_games': total_games,
            'victories': victories,
            'win_rate': win_rate
        }

    def format_battle_log(self, battles: Dict[str, Any], player_tag: str) -> Tuple[List[Dict], int]:
        """
        Formatiert das Battle-Log und zählt Star Player Auszeichnungen.

        Args:
            battles (Dict[str, Any]): Rohdaten des Battle-Logs
            player_tag (str): Tag des Spielers für Star Player Vergleich

        Returns:
            Tuple[List[Dict], int]: (Formatierte Battles, Anzahl Star Player Auszeichnungen)
        """
        if not battles or 'items' not in battles:
            return [], 0

        formatted_battles = []
        star_player_count = 0

        for battle in battles['items'][:20]:  # Begrenzt auf die letzten 20 Spiele
            try:
                battle_info = self._format_single_battle(battle, player_tag)
                if battle_info.get('Star Player'):
                    star_player_count += 1
                formatted_battles.append(battle_info)
            except Exception as e:
                print(f"Fehler bei der Verarbeitung eines Kampfes: {e}")
                continue

        return formatted_battles, star_player_count

    @staticmethod
    def _format_single_battle(battle: Dict[str, Any], player_tag: str) -> Dict[str, Any]:
        """
        Formatiert die Daten eines einzelnen Kampfes.

        Args:
            battle (Dict[str, Any]): Rohdaten eines einzelnen Kampfes
            player_tag (str): Tag des Spielers

        Returns:
            Dict[str, Any]: Formatierte Kampfdaten
        """
        return {
            'Zeit': BrawlStarsDataProcessor._format_battle_time(battle.get('battleTime', '')),
            'Modus': BrawlStarsDataProcessor._get_battle_mode(battle),
            'Typ': BrawlStarsDataProcessor._get_battle_type(battle),
            'Ergebnis': BrawlStarsDataProcessor._get_battle_result(battle),
            'Trophäen': BrawlStarsDataProcessor._format_trophy_change(battle),
            'Star Player': BrawlStarsDataProcessor._check_star_player(battle, player_tag),
            'Brawler': BrawlStarsDataProcessor._get_player_brawler(battle, player_tag),
            'Power Level': BrawlStarsDataProcessor._get_power_level(battle, player_tag)
        }

    @staticmethod
    def _format_battle_time(battle_time: str) -> str:
        """
        Formatiert den Zeitstempel eines Kampfes.

        Args:
            battle_time (str): Roher Zeitstempel

        Returns:
            str: Formatierter Zeitstempel
        """
        try:
            return datetime.strptime(battle_time, '%Y%m%dT%H%M%S.000Z').strftime('%d.%m.%Y %H:%M')
        except (ValueError, TypeError):
            return 'Unbekannt'

    @staticmethod
    def _get_battle_mode(battle: Dict[str, Any]) -> str:
        """
        Ermittelt den Spielmodus eines Kampfes.

        Args:
            battle (Dict[str, Any]): Kampfdaten

        Returns:
            str: Spielmodus
        """
        return battle.get('battle', {}).get('mode', 'Unbekannt')

    @staticmethod
    def _get_battle_type(battle: Dict[str, Any]) -> str:
        """
        Ermittelt den Kampftyp.

        Args:
            battle (Dict[str, Any]): Kampfdaten

        Returns:
            str: Kampftyp
        """
        return battle.get('battle', {}).get('type', 'Unbekannt')

    @staticmethod
    def _get_battle_result(battle: Dict[str, Any]) -> str:
        """
        Ermittelt das Kampfergebnis und formatiert es einheitlich.

        Args:
            battle (Dict[str, Any]): Kampfdaten

        Returns:
            str: Formatiertes Kampfergebnis ('Sieg', 'Niederlage' oder 'Unentschieden')
        """
        result = battle.get('battle', {}).get('result', '').lower()
        result_mapping = {
            'victory': 'Sieg',
            'defeat': 'Niederlage',
            'draw': 'Unentschieden'
        }
        return result_mapping.get(result, 'Keine Wertung')

    @staticmethod
    def _format_trophy_change(battle: Dict[str, Any]) -> str:
        """
        Formatiert die Trophäenänderung.

        Args:
            battle (Dict[str, Any]): Kampfdaten

        Returns:
            str: Formatierte Trophäenänderung
        """
        trophy_change = battle.get('battle', {}).get('trophyChange', 0)
        if trophy_change > 0:
            return f"+{trophy_change}"
        return str(trophy_change)

    @staticmethod
    def _check_star_player(battle: Dict[str, Any], player_tag: str) -> str:
        """
        Prüft, ob der Spieler Star Player war.

        Args:
            battle (Dict[str, Any]): Kampfdaten
            player_tag (str): Spieler-Tag

        Returns:
            str: Star Player Symbol oder leer
        """
        star_player = battle.get('battle', {}).get('starPlayer', {})
        if star_player and star_player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
            return '⭐'
        return ''

    @staticmethod
    def _get_player_brawler(battle: Dict[str, Any], player_tag: str) -> str:
        """
        Ermittelt den verwendeten Brawler des Spielers.

        Args:
            battle (Dict[str, Any]): Kampfdaten
            player_tag (str): Spieler-Tag

        Returns:
            str: Name des Brawlers
        """
        try:
            for player in battle.get('battle', {}).get('players', []):
                if player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
                    return player.get('brawler', {}).get('name', 'Unbekannt')
        except Exception:
            pass
        return 'Unbekannt'

    @staticmethod
    def _get_power_level(battle: Dict[str, Any], player_tag: str) -> int:
        """
        Ermittelt das Power Level des verwendeten Brawlers.

        Args:
            battle (Dict[str, Any]): Kampfdaten
            player_tag (str): Spieler-Tag

        Returns:
            int: Power Level des Brawlers
        """
        try:
            for player in battle.get('battle', {}).get('players', []):
                if player.get('tag', '').replace('#', '') == player_tag.replace('#', ''):
                    return player.get('brawler', {}).get('power', 0)
        except Exception:
            pass
        return 0

    def calculate_brawler_statistics(self, player_data: Dict) -> Dict:
        """Berechnet Statistiken über die Brawler eines Spielers"""
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
        
        # Zähle Brawler mit Power 9 oder höher
        high_level_brawlers = sum(1 for b in brawlers if b.get('power', 0) >= 9)
        
        # Zähle Brawler mit Power 11
        max_level_brawlers = sum(1 for b in brawlers if b.get('power', 0) == 11)
        
        return {
            'total_brawlers': total_brawlers,
            'high_level_brawlers': high_level_brawlers,
            'max_level_brawlers': max_level_brawlers,
            'avg_trophies': total_trophies / total_brawlers if total_brawlers > 0 else 0
        }
