from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path

# Bandcamp URL parameters
# --------------------------------------
# genre   - all
# sort_by - top = (best-selling),
#           rec = (artist-recommended),
#           new = (new arrivals)
# r       - most, latest

URL = 'https://bandcamp.com/?g={genre}&s={sort_by}&p=0&gn=0&f=all&w=0&r={r}'.format(
    genre="all", sort_by="rec", r="most")

# hide a warning about a bluetooth error...
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Driver setup
DRIVER_PATH = Path("./chromedriver.exe")
driver = webdriver.Chrome(executable_path=DRIVER_PATH)

# GET request
driver.get(URL)

# make soup
soup = BeautifulSoup(driver.page_source, 'html.parser')

artist_list = soup.find_all("a", {"class": "item-artist"})

for artist in artist_list:
    print(artist.text)

# close webdriver
driver.quit()
