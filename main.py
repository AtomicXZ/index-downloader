from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from os import path, remove, stat, system
from urllib.parse import quote, unquote
from selenium.webdriver import Chrome
from argparse import ArgumentParser
from multiprocessing import Pool
from bs4 import BeautifulSoup
from time import sleep
from json import load

parser = ArgumentParser(
    description="Simple script to download folders/files from cloudflare gdrive index links.")
parser.add_argument(
    "-l", "--link", help="Link. Put multiple links with no space or by enclosing them in inverted commas (\"\").")
parser.add_argument("-u", "--user", help="Username for auth, if required.")
parser.add_argument("-p", "--password",
                    help="Password for auth, if username is entered.")
parser.add_argument("-s", "--sessions",
                    help="Number of simultaneous downloades.")
args = vars(parser.parse_args())

if not args["link"]:
    link = input("Enter index link:  ")
else:
    link = args["link"]

link = list(filter(None, link.strip().split(",")))
for i in link:
    link[link.index(i)] = i.strip()

try:
    if not args["sessions"]:
        raise ValueError
    else:
        MULTIPROCESSING_SESSIONS = int(args["sessions"])
except ValueError:
    MULTIPROCESSING_SESSIONS = 2

if "https://" in link[0]:
    prefix = "https://"
elif "http://" in link[0]:
    prefix = "http://"
else:
    prefix = ""

# format link for usage with password
creds = load(open(f"{path.dirname(__file__)}/creds.json"))

for i in creds:
    if args["user"] and args["password"]:
        user = args["user"]
        password = args["password"]
        break
    elif i in link[0]:
        user = creds[i]["user"]
        password = creds[i]["password"]
        break
else:
    user = input("Enter username, if applicable, else leave empty:  ")

if user:
    if not password:
        password = input("Enter password:  ")
    for i in link:
        credentials = f"{quote(user)}:{quote(password)}"
        if not credentials in i:
            nlink = f"{prefix}{credentials}@{i.replace(prefix, '')}"
            link[link.index(i)] = nlink

# get index base url
index_link = link[0][:link[0].replace(prefix, "").index("/")+len(prefix)]


# start chrome driver (headless)
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = Chrome(options=options)


def get_soup(link):
    while True:
        driver.get(link)

        last_height = driver.execute_script(
            "return document.body.scrollHeight")
        while True:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        try:
            my_elem = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".list-group-item.list-group-item-action")))
            break
        except TimeoutException:
            print("Connection Failed, retrying. Please Wait!")

    html = driver.page_source
    return BeautifulSoup(html, "html.parser")


# get file name and path
def get_path(i):
    if index_link in i:
        dir = i[len(index_link)+1:i.rfind('/')]
        file = i[len(index_link)+1:]
    else:
        dir = i[:i.rfind('/')]
        file = i
    try:
        int(dir[0])
        dir = unquote(dir[3:])
        file = unquote(file[3:])
    except ValueError:
        try:
            int(dir[1])
            dir = unquote(dir[4:])
            file = unquote(file[4:])
        except ValueError:
            dir = unquote(dir)
            file = unquote(file)

    return [dir, file]


def download(Sno, data_list):
    for i in data_list:
        dir, file = get_path(i)[0], get_path(i)[1]
        while True:
            if dir:
                system(
                    f"aria2c \"{i}\" -d\"{dir}\" --auto-file-renaming=false --save-session log-{Sno}.txt")
            else:
                system(
                    f"aria2c \"{i}\" --auto-file-renaming=false --save-session log-{Sno}.txt")
            if path.isfile(file) and not path.isfile(f"{file}.aria2"):
                break
            elif stat(f"log-{Sno}.txt").st_size == 0:
                break

    # delete the generated log file
    try:
        remove(f"log-{Sno}.txt")
    except FileNotFoundError:
        pass


# fetch all links from the base url
dl_link = []
all_files = ""  # set empty var to avoid iteration error in for loop

for i in link:
    if i[-1] == "/":
        soup = get_soup(i)
        if link.index(i) == 0:
            all_files = soup.find_all(
                "a", {"class": "list-group-item-action"}, href=True)
        else:
            all_files.extend(soup.find_all(
                "a", {"class": "list-group-item-action"}, href=True))
    else:
        dl_link.append(i)

for i in all_files:
    rem_view = i["href"].replace('?a=view', '')
    # check if link is a file or folder
    if not rem_view[-1] == "/":
        if path.isfile(get_path(rem_view)[1]) and path.isfile(f"{get_path(rem_view)[1]}.aria2"):
            # check if file already exists and only add if *.aria2 also exists
            dl_link.append(
                f"{index_link}{rem_view.replace(' ', '%20')}")
        elif not path.isfile(get_path(rem_view)[1]):
            # if file doesn't exist then just add it
            dl_link.append(
                f"{index_link}{rem_view.replace(' ', '%20')}")
    else:
        # open the link if it's not a file and add it to all_files var
        soup = get_soup(
            f"{index_link}{i['href'].replace('?a=view', '').replace(' ', '%20')}")
        all_files.extend(soup.find_all(
            "a", {"class": "list-group-item-action"}, href=True))

driver.close()

# separate the links list
k, m = divmod(len(dl_link), MULTIPROCESSING_SESSIONS)
dl_list = [dl_link[i*k+min(i, m):(i+1)*k+min(i+1, m)]
           for i in range(MULTIPROCESSING_SESSIONS)]

multiprocessing_sessions_dl_list = []
for i in range(MULTIPROCESSING_SESSIONS):
    multiprocessing_sessions_dl_list.append((i + 1, dl_list[i]))

# downloading starts here
dl = Pool(MULTIPROCESSING_SESSIONS).starmap(download, multiprocessing_sessions_dl_list)
