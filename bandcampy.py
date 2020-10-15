from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time
from collections import namedtuple


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


def scrape_albums(soup, page_count):
    Albums = namedtuple('Albums', 'artists titles')
    artist_list = []
    title_list = []
    for page in range(0, page_count):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        print(f"Page: {page + 1} loading")
        driver.find_element_by_xpath(
            '//*[@id="discover"]/div[9]/div[1]/div[5]/div/a[11]').click()
        if page % 3 == 0:
            artist_list = artist_list + find_artist_list(soup)
            title_list = title_list + find_title_list(soup)
    return Albums(artists=artist_list, titles=title_list)


def hide_warnings():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])


def init_driver():
    DRIVER_PATH = Path("./chromedriver.exe")
    return webdriver.Chrome(executable_path=DRIVER_PATH)


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


def find_playlist(auth, playlist_name):
    Playlist = namedtuple('Playlist', 'name uri')
    user = get_username(auth)
    playlists = auth.user_playlists(user)
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] == playlist_name:
                return Playlist(name=playlist['name'], uri=playlist['uri'])
        if playlists['next']:
            playlists = auth.next(playlists)
        else:
            playlists = None
    else:
        return Playlist(name=None, uri=None)


def get_username(auth):
    return auth.current_user().get("display_name")


# hide a warning about a bluetooth error...
hide_warnings()

# Driver setup
driver = init_driver()

# GET request
URL = build_url(genre="all", sort_by="rec", page=0)
driver.get(URL)
soup = BeautifulSoup(driver.page_source, 'html.parser')

# parse pages
pages = 2
albums = scrape_albums(soup, pages)

# print all albums in format: ARTIST - TITLE
for artist, title in zip(*albums):
    print(f"{artist.text} - {title.text}")

# close webdriver
driver.quit()

# spotify api example use
sp = get_auth()
user = get_username(auth=sp)
playlist_name = "test playlist"

# find spotify playlist to use
playlist = find_playlist(auth=sp, playlist_name=playlist_name)

# create playlist if not found
if playlist.uri is None:
    sp.user_playlist_create(user=user, name=playlist_name,
                            public=True, collaborative=False, description="robots")
    # update playlist with newly created playlist
    playlist = find_playlist(auth=sp, playlist_name=playlist_name)
    print(f"created playlist: {playlist.name}")

else:
    print(f"using existing playlist: {playlist.name}")

# use album data from bandcamp to find correlated spotify track URIs
track_list = []
for artist, title in zip(*albums):
    # search spotify for album
    result = sp.search(q=f"{artist.text} {title.text}",
                       type="album", market="from_token")

    # if album found
    if len(result.get("albums").get("items")) > 0:
        # get album uri
        uri = result.get("albums").get("items")[0].get("uri")
        # get list of album tracks
        tracks = sp.album_tracks(album_id=uri, limit=50, offset=0, market=None).get(
            "items")
        # add track URI to list
        for track in tracks:
            track_list.append(track.get("uri"))

# print "loading: {TOTAL_COUNT} tracks..."
print(f"adding: {len(track_list)} tracks...")


# user_playlist_add_tracks() can only add up to 100 tracks per call
chunk_size = 100

# split track list to chunks for user_playlist_add_tracks()
track_chunks = [track_list[x:x+chunk_size]
                for x in range(0, len(track_list), chunk_size)]

# add tracks to playlist
for i in range(0, len(track_chunks), chunk_size):
    chunk = track_chunks[i:i+chunk_size]
    for tracks in chunk:
        sp.user_playlist_add_tracks(
            user=user, playlist_id=playlist.uri, tracks=tracks, position=None)
