import json
import os
import pprint

import dotenv
import requests
from dotenv import load_dotenv
from riotwatcher import ApiError, LolWatcher

load_dotenv()
RIOT_KEY = os.getenv("RIOT_KEY")
watcher = LolWatcher(RIOT_KEY)


class dataDragon:
    # Atributos compartilhados entre todas as instâncias de dataDragon
    my_region = "BR1"
    lang_code = "pt_BR"

    # Emojis das Roles
    EMOJI_TOP = "<:TOP:817472045087457280>"
    EMOJI_JUNGLE = "<:JUNGLE:817472044878921810>"
    EMOJI_MIDDLE = "<:MIDDLE:817472045062291497>"
    EMOJI_BOTTOM = "<:ADC:817472146799460433>"
    EMOJI_UTILITY = "<:SUPPORT:817472045130186812>"

    def __init__(self):

        # Métodos do construtor
        def get_current_version():
            response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
            league_versions = response.json()
            return league_versions[0]

        def get_all_champions_json():
            all_champions_url = (
                f"http://ddragon.leagueoflegends.com/cdn/{self.latest_version}/data/{self.lang_code}/champion.json"
            )
            all_response = requests.get(all_champions_url)
            return all_response.json()

        # Atributos do construtor
        self.latest_version = get_current_version()
        self.all_champions = get_all_champions_json()

    # Métodos da classe
    def get_profile_icon(self, iconID: int):
        return f"http://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/profileicon/{iconID}.png"

    def get_champion_name(self, championID: int):
        champion_name = ""
        all_champions = self.all_champions
        for item in all_champions["data"]:
            row = all_champions["data"][item]
            if row["key"] == str(championID):
                champion_name = row["name"]
        return champion_name
