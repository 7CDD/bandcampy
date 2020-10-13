from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time


def get_auth():
    load_dotenv()
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    scope = 'user-read-private user-library-read playlist-modify-public'
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
soup = BeautifulSoup(driver.page_source, 'html.parser')
artist_list = []
title_list = []
# parse pages
for page in range(0, 30):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    print(" ".join(("Page:", str(page + 1), "loading")))
    driver.find_element_by_xpath(
        '//*[@id="discover"]/div[9]/div[1]/div[5]/div/a[11]').click()
    if page % 3 == 0:
        artist_list = artist_list + find_artist_list(soup)
        title_list = title_list + find_title_list(soup)
    time.sleep(1)
for artist, title in zip(artist_list, title_list):
    print(" - ".join((artist.text, title.text)))
# close webdriver
driver.quit()

# spotify api example use
sp = get_auth()

exists = None
playlists = sp.user_playlists('7cdd')
while playlists:
    for i, playlist in enumerate(playlists['items']):
        if playlist['name'] == "test playlist":
            playlist_id = playlist['uri']
            exists = 1
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None

if exists is None:
    sp.user_playlist_create(user="7cdd", name="test playlist",
                            public=True, collaborative=False, description="robots")
    print("created playlist!")
    playlists = sp.user_playlists('7cdd')
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%4d %s %s" %
                  (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
            if playlist['name'] == "test playlist":
                playlist_id = playlist['uri']
            if playlists['next']:
                playlists = sp.next(playlists)
            else:
                playlists = None
else:
    print("playlist already exists")


track_list = []
for artist, title in zip(artist_list, title_list):
    result = sp.search(q=" ".join(
        (artist.text, title.text)), type="album", market="from_token")
    # print(result)
    if len(result.get("albums").get("items")) > 0:
        uri = result.get("albums").get("items")[0].get("uri")
        tracks = sp.album_tracks(album_id=uri, limit=50, offset=0, market=None).get(
            "items")
        for track in tracks:
            track_list.append(track.get("uri"))

print(" ".join(("loading:", str(len(track_list)), "tracks...")))
chunk_size = 100
track_chunks = [track_list[x:x+chunk_size]
                for x in range(0, len(track_list), chunk_size)]

for i in range(0, len(track_chunks), chunk_size):
    chunk = track_chunks[i:i+chunk_size]
    for c in chunk:
        sp.user_playlist_add_tracks(
            user="7cdd", playlist_id=playlist_id, tracks=c, position=None)
