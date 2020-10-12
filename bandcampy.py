from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv


def get_auth():
    load_dotenv()
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    scope = 'user-library-read playlist-modify-public'
    auth = SpotifyOAuth(scope=scope, cache_path='user_cache',
                        client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI)

    return spotipy.Spotify(auth_manager=auth)


def build_url(genre, sort_by, page):
    # Bandcamp URL parameters
    # --------------------------------------
    # genre   - all
    # sort_by - top = (best-selling),
    #           rec = (artist-recommended),
    #           new = (new arrivals)
    # r       - most, latest
    r = "most"
    return f'https://bandcamp.com/?g={genre}&s={sort_by}&p={page}&gn=0&f=all&w=0&r={r}'


def get_soup(driver, url):
    driver.get(url)
    return BeautifulSoup(driver.page_source, 'html.parser')


def find_artist_list(soup):
    return soup.find_all("a", {"class": "item-artist"})


def find_title_list(soup):
    return soup.find_all("a", {"class": "item-title"})


def hide_warnings():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])


def init_driver():
    DRIVER_PATH = Path("./chromedriver.exe")
    return webdriver.Chrome(executable_path=DRIVER_PATH)


# hide a warning about a bluetooth error...
hide_warnings()

# Driver setup
driver = init_driver()

# GET request
URL = build_url(genre="all", sort_by="rec", page=0)
driver.get(URL)


# parse pages
for page in range(0, 2):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    print("Page: ".join([str(page), " loading"]))
    artist_list = find_artist_list(soup)
    title_list = find_title_list(soup)

    driver.find_element_by_xpath(
        '//*[@id="discover"]/div[9]/div[1]/div[5]/div/a[11]').click()


for artist, title in zip(artist_list, title_list):
    print(artist.text.join([" - ", title.text]))

# close webdriver
driver.quit()

# spotify api example use
sp = get_auth()

playlists = sp.user_playlists('7cdd')
while playlists:
    for i, playlist in enumerate(playlists['items']):
        print("%4d %s %s" %
              (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None
