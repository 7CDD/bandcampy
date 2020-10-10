from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path
import time

# Bandcamp URL parameters
# --------------------------------------
# genre   - all
# sort_by - top = (best-selling),
#           rec = (artist-recommended),
#           new = (new arrivals)
# r       - most, latest


def build_url(genre, sort_by, page):
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
URL = build_url("all", "rec", 0)
driver.get(URL)

# GET requests
for page in range(0, 2):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    print("Page: " + str(page) + " loading")
    artist_list = find_artist_list(soup)
    title_list = find_title_list(soup)

    driver.find_element_by_xpath(
        '//*[@id="discover"]/div[9]/div[1]/div[5]/div/a[11]').click()


for artist, title in zip(artist_list, title_list):
    print(artist.text + " - " + title.text)

# close webdriver
driver.quit()
