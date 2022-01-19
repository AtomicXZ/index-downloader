from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import quote, unquote
from selenium.webdriver import Chrome
from multiprocessing import Process
from bs4 import BeautifulSoup
import os


link = input("Enter index link:  ")

if "https://" in link:
    prefix = "https://"
elif "http://" in link:
    prefix = "http://"
else:
    prefix = ""

# format link for usage with password
user = input("Enter username, if applicable, else leave empty:  ")
if user:
    password = input("Enter password:  ")
    link = link.replace(prefix, "")
    link = f"{prefix}{quote(user)}:{quote(password)}@{link}"

indexLink = link[:link.replace(prefix, "").index("/")+len(prefix)]


# start chrome driver (headless)
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = Chrome(options=options)


def getSoup(link):
    while True:
        driver.get(link)
        try:
            myElem = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".list-group-item.list-group-item-action")))
            break
        except TimeoutException:
            print("Connection Failed, retrying. Please Wait!")

    html = driver.page_source
    return BeautifulSoup(html, "html.parser")


def download(Sno, Dlist):
    for i in Dlist:
        dir = i[len(indexLink)+1:i.rfind('/')]
        file = i[len(indexLink)+1:]
        try:
            int(dir[0])
            dir = unquote(dir[3:])
            file = unquote(file[3:])
        except ValueError:
            pass
        while True:
            os.system(
                f"aria2c \"{i}\" -d\"{dir}\" --auto-file-renaming=false --save-session log-{Sno}.txt")
            if os.path.isfile(file):
                break
            elif os.stat(f"log-{Sno}.txt").st_size == 0:
                break

    # delete the generated log file
    try:
        os.remove(f"log-{Sno}.txt")
    except FileNotFoundError:
        pass


# fetch all links from the base url
soup = getSoup(link)
allFiles = soup.find_all("a", {"class": "list-group-item-action"}, href=True)

ddlLink = []
for i in allFiles:
    if not i["href"].replace('?a=view', '')[-1] == "/":
        # add link to list after formatting if it's a file
        ddlLink.append(
            f"{indexLink}{i['href'].replace('?a=view', '').replace(' ', '%20')}")
    else:
        # open the link if it's not a file and add it to allFiles var
        soup = getSoup(
            f"{indexLink}{i['href'].replace('?a=view', '').replace(' ', '%20')}")
        allFiles.extend(soup.find_all(
            "a", {"class": "list-group-item-action"}, href=True))

driver.close()

# separate the links list
k, m = divmod(len(ddlLink), 4)
ddlList = [ddlLink[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(4)]

# downloading starts here
if __name__ == '__main__':
    Process(target=download, args=(1, ddlList[0],)).start()
    Process(target=download, args=(2, ddlList[1],)).start()
    Process(target=download, args=(3, ddlList[2],)).start()
    Process(target=download, args=(4, ddlList[3],)).start()
