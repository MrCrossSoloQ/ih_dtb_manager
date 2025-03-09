from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError
import teams
import player
import random
import time
from unidecode import unidecode
import re
import os
from dotenv import load_dotenv

class PlaywrightController:
    def __init__(self, dtb_data = None):
        self.dtb_data = dtb_data
        self.playwright = None
        self.browser = None
        self.page = None
        self.scraped_items = []

    def playwright_starter(self):
        ublock_path = r"C:\Users\tomas\Desktop\Python\ublock_origin_lite"
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        if self.browser is None:
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir="userdata",
                headless=False,
                args=[f"--disable-extensions-except={ublock_path}", f"--load-extension={ublock_path}"]
            )
        if self.page is None:
            self.page = self.browser.new_page()

    # def get_page_content(self, full_url):
    #     print(f"get_page_url - Testovací výpis: {full_url}")
    #     time.sleep(random.uniform(1.0, 5.0)) #kratší generovaná pauza, aby nás nezachytla ochrana proti webscrapingu
    #     for attempt in range(3):
    #         try:
    #             self.page.goto(full_url)
    #             html = self.page.content()
    #             return html
    #         except TimeoutError:
    #             print(f"Timeout při načítání: {full_url}; Pokus: {attempt + 1}")
    #         except Exception as e:
    #             print(f"Neočekávaná chyba při načítání stránky: {full_url}: {e}")
    #
    #     return None

    def load_page(self, full_url):
        print(f"get_page_url - Testovací výpis: {full_url}")
        time.sleep(random.uniform(1.0, 5.0)) #kratší generovaná pauza, aby nás nezachytla ochrana proti webscrapingu
        for attempt in range(3):
            try:
                """Hodnota load přiřazená argumentu wait_until zajišťuje, aby další interakce se stránkou byla provedena, až se načtou základní zdroje stránky (html, css, javascript) tím se minimalizují chyby"""
                self.page.goto(full_url, wait_until="load")
                return True
            except TimeoutError:
                print(f"Timeout při načítání: {full_url}; Pokus: {attempt + 1}")
            except Exception as e:
                print(f"Neočekávaná chyba při načítání stránky: {full_url}: {e}")

        return False

    def get_page_content(self):
        html = self.page.content()
        return html

    def playwright_termination(self):
        self.browser.close()
        self.playwright.stop()
        self.browser = None
        self.playwright = None

    def soup_maker(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return soup

    def get_url(self, url_content, chosen_league):
        for dtb_item in self.dtb_data:
            if dtb_item["league_id"] == chosen_league or chosen_league == 0:
                full_url = urljoin("https://www.eliteprospects.com/", dtb_item["elite_url"])
                page_result = self.load_page(full_url)
                if page_result is True:
                    returned_html_content = self.get_page_content()
                    returned_soup = self.soup_maker(returned_html_content)

                    if url_content == "league":
                        self.team_soup_parse(dtb_item["league_id"], returned_soup)
                    elif url_content == "team_roster":
                        self.team_roster_parse(returned_soup, dtb_item["league_id"], dtb_item["team_id"])
        return self.scraped_items

    def team_soup_parse(self, league_id, soup):
        """Metoda najde všechny týmy dané ligy na stránce. Získá jméno týmu a odkaz na profil týmu."""
        list_of_scraped_teams = soup.find_all("a", class_ = "TextLink_link__RhSiC LabelWithIcon_link__67DL_ TableBody_link__dfR3c TableBody_plainText__KuMY7")
        for team in list_of_scraped_teams:
            team_name = team.text
            team_url = team.get("href")
            team_full_url = "https://www.eliteprospects.com" + team_url
            new_team = teams.Teams(league_id, team_name, team_full_url)
            print(league_id, team_name, team_url)
            self.scraped_items.append(new_team)

    def team_roster_parse(self, soup, league_id, team_id):
        """Metoda najde všechny hráče týmu na stránce. Získá jejich jméno a odkaz na profil hráče."""
        roster_player_divs = soup.find_all("div", class_ = "Roster_player__e6EbP")
        for roster_player_div in roster_player_divs:
            roster_player_a = roster_player_div.find("a")
            roster_player_url = roster_player_a.get("href")
            full_url = urljoin("https://www.eliteprospects.com/", roster_player_url)
            returned_player = self.player_profile_parse(full_url, league_id, team_id)
            self.scraped_items.append(returned_player)

    def player_name_splitter(self, name_unformatted):
        """Metoda, která nám z jednoho řetězce s celým jménem, odstraní zbytečné znaky a vrátí křestní jméno a příjmení"""
        clean_name = name_unformatted.split(" (")[0]
        name_parts = clean_name.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])
        if last_name is None:
            last_name = first_name
            first_name = None
        return first_name, last_name

    def create_name_variants(self, player_fullname, player_surname, player_lastname):
        shorted_name = player_surname[:1] + ". " + player_lastname
        shorted_name_diacriticsless = unidecode(shorted_name)
        full_name_diacriticless = unidecode(player_fullname)
        list_of_variants = self.similarity_check(player_fullname, full_name_diacriticless, shorted_name, shorted_name_diacriticsless)
        return list_of_variants

    def similarity_check(self, full_name, full_name_diacriticsless, shorted_name, shorted_name_diacritics_less):
        """Funkce, která ověří, zda se varianty jmen s diakritikou a bez liší a na základě toho vytvoří seznam variací.
        Některé jména jsou již v originálu bez diakritiky, takže je není nutné vkládat znovu, když jméno proženeme funkcí, která odstraňuje diakritiku.
        """
        name_variations = []
        if full_name != full_name_diacriticsless:
            name_variations.append(full_name_diacriticsless)
        if shorted_name != shorted_name_diacritics_less:
            name_variations.append(shorted_name_diacritics_less)
        else:
            name_variations.append(shorted_name)
        return name_variations

    def player_profile_parse(self, full_url, league_id, team_id):
        page_result = self.load_page(full_url)
        if page_result is True:
            html_content = self.get_page_content()
            returned_soup = self.soup_maker(html_content)
            player_h1 = returned_soup.find("h1", class_ = "Profile_headerMain__WPgYE")
            print(f"H1 print: {player_h1}")
            player_fullname = player_h1.text
            player_surname, player_lastname = self.player_name_splitter(player_fullname)
            list_of_variants = self.create_name_variants(player_fullname, player_surname, player_lastname)

            player_card_ul = returned_soup.find("ul", class_ = "PlayerFacts_factsList__Xw_ID")
            list_of_player_facts = player_card_ul.find_all("li")
            player_nation = list_of_player_facts[3].find("a", class_="TextLink_link__RhSiC").text
            player_position = list_of_player_facts[5].text
            sliced_player_position = player_position[len("Position"):]
            player_date_of_birth = list_of_player_facts[0].text
            sliced_player_date_of_birth = player_date_of_birth[len("Date of Birth"):]

            decoded_url = unquote(full_url)

            new_player = player.Player(player_surname, player_lastname, player_nation, league_id, sliced_player_position, sliced_player_date_of_birth, team_id, decoded_url, name_variants = list_of_variants)
            print(player_surname, player_lastname, player_nation, league_id, sliced_player_position, sliced_player_date_of_birth, team_id, decoded_url, list_of_variants)
            return new_player

    def get_year(self, season_value):
        match = re.search(r"\d{4}", season_value)
        season = match.group(0)
        if season:
            return season

    def elite_prospects_get_player(self, searched_name, dtb_team):
        load_dotenv("dev.env")

        searched_name_parts = searched_name.split(". ")
        searched_name_first_letter = searched_name_parts[0]
        searched_player_last_name = searched_name_parts[1]
        time.sleep(random.uniform(1.0, 5.0))

        if self.page is not None:
            page_result = self.load_page("https://www.eliteprospects.com/login")
            if page_result is True and self.page.url != "https://www.eliteprospects.com/":
                """
                Pokud je page_result True, znamená to, že se nám stránka načetla. 
                Jestliže se self.page.url nerovná: https://www.eliteprospects.com/, musíme se přihlásit do účtu
                """
                self.page.fill("input[name='email']", os.getenv("EMAIL"))
                self.page.fill("input[name='password']", os.getenv("PASSWORD"))
                self.page.click("button[type='submit']")

        page_result = self.load_page("https://www.eliteprospects.com/search/player")
        if page_result is True:
            self.page.fill("input[class = 'form-control']", searched_player_last_name)
            self.page.click("input[class = 'btn green-sm']")

            table_locator = self.page.locator("css=.table.table-condensed.table-striped.players ")
            table_html = table_locator.inner_html()
            soup = self.soup_maker(table_html)
            all_tr = soup.find_all("tr")

            list_of_scraped_players = []
            for tr in all_tr[1:]:
                td_name = tr.find("td", class_ = "name")
                name_unformatted = td_name.text.strip()
                first_name, last_name = self.player_name_splitter(name_unformatted)
                print(name_unformatted)
                print(first_name, last_name)
                scraped_first_name_first_letter = first_name[0]

                a_span = td_name.find("span", class_="txt-blue")
                a = a_span.find("a")
                player_url = a.get("href")
                print(player_url)

                td_current_team = tr.find("td", class_="latest-team hidden-xs")
                span_season = td_current_team.find("span", class_="season")
                if span_season:
                    season_unformatted = span_season.text
                    season = self.get_year(season_unformatted)
                    print(season)
                else:
                    season = None

                if searched_name_first_letter == scraped_first_name_first_letter and season == "2025":
                    scraped_player = self.player_profile_parse(player_url, dtb_team["league_id"], dtb_team["team_id"])
                    list_of_scraped_players.append(scraped_player)
            print(list_of_scraped_players)

            return list_of_scraped_players