import os
import requests
import streamlit as st
from typing import Optional, Dict, Any
from time import sleep
import logging

@st.cache_data(ttl=300)
def cached_api_request(url: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Gecachte API-Anfrage"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API-Fehler: {str(e)}")
        return None

class BrawlStarsAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://api.brawlstars.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    def _clean_tag(self, tag: str) -> str:
        """Bereinigt einen Spieler- oder Club-Tag."""
        if not tag.startswith('#'):
            tag = f'#{tag}'
        return tag.upper().replace('#', '%23').replace(' ', '')

    def get_player_info(self, player_tag: str) -> Optional[Dict[str, Any]]:
        """Ruft Spielerinformationen ab."""
        clean_tag = self._clean_tag(player_tag)
        url = f"{self.base_url}/players/{clean_tag}"
        return cached_api_request(url, self.headers)

    def get_battle_log(self, player_tag: str) -> Optional[Dict[str, Any]]:
        """Ruft das Battle-Log eines Spielers ab."""
        clean_tag = self._clean_tag(player_tag)
        url = f"{self.base_url}/players/{clean_tag}/battlelog"
        return cached_api_request(url, self.headers)

    def get_club_info(self, club_tag: str) -> Optional[Dict[str, Any]]:
        """Ruft Club-Informationen ab."""
        clean_tag = self._clean_tag(club_tag)
        url = f"{self.base_url}/clubs/{clean_tag}"
        return cached_api_request(url, self.headers)

    def get_club_members(self, club_tag: str) -> Optional[Dict[str, Any]]:
        """Ruft Club-Mitglieder ab."""
        clean_tag = self._clean_tag(club_tag)
        url = f"{self.base_url}/clubs/{clean_tag}/members"
        return cached_api_request(url, self.headers)

    def get_brawler_list(self) -> Optional[Dict[str, Any]]:
        """Ruft die Liste aller Brawler ab."""
        url = f"{self.base_url}/brawlers"
        return cached_api_request(url, self.headers)

    def get_brawler_info(self, brawler_id: int) -> Optional[Dict[str, Any]]:
        """Ruft Brawler-Informationen ab."""
        url = f"{self.base_url}/brawlers/{brawler_id}"
        return cached_api_request(url, self.headers)

    def get_brawlers(self) -> Optional[Dict[str, Any]]:
        """Holt die Liste aller verfügbaren Brawler"""
        return self._get_brawlers_cached(self.headers, self.base_url)

    @staticmethod
    @st.cache_data(ttl=300)
    def _get_brawlers_cached(_headers: Dict[str, str], _base_url: str) -> Optional[Dict[str, Any]]:
        """Gecachte Version der Brawler-Abfrage"""
        url = f"{_base_url}/brawlers"
        return cached_api_request(url, _headers)

    def get_brawler_rankings(self, brawler_id: str) -> Optional[Dict[str, Any]]:
        """Ruft das globale Ranking für einen bestimmten Brawler ab."""
        url = f"{self.base_url}/rankings/global/brawlers/{brawler_id}"
        return cached_api_request(url, self.headers)
