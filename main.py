from __init__ import *

link = input("Enter index link:  ")
try:
    simulDownloadNumber = int(
        input("Enter number of simultaneous downloads (default 4):  "))
except ValueError:
    print("Continuing with default (4).")
    simulDownloadNumber = 4

if "https://" in link:
    prefix = "https://"
elif "http://" in link:
    prefix = "http://"
else:
    prefix = ""

# format link for usage with password
creds = {"helios": ["helios", "mirror@"], "hash": ["hash", "mirror"],
         "ghost": ["ghost", "mirror"]}  # credentials for known index links

for i, j in creds.items():
    if i in link:
        user = j[0]
        password = j[1]
        break
else:
    user = input("Enter username, if applicable, else leave empty:  ")

if user:
    if not password:
        password = input("Enter password:  ")
    link = link.replace(prefix, "")
    link = f"{prefix}{quote(user)}:{quote(password)}@{link}"

# get index base url
indexLink = link[:link.replace(prefix, "").index("/")+len(prefix)]


# start chrome driver (headless)
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = Chrome(options=options)


def getSoup(link):
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
            myElem = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".list-group-item.list-group-item-action")))
            break
        except TimeoutException:
            print("Connection Failed, retrying. Please Wait!")

    html = driver.page_source
    return BeautifulSoup(html, "html.parser")


# get file name and path
def getPath(i):
    if indexLink in i:
        dir = i[len(indexLink)+1:i.rfind('/')]
        file = i[len(indexLink)+1:]
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


def download(Sno, Dlist):
    for i in Dlist:
        dir, file = getPath(i)[0], getPath(i)[1]
        while True:
            system(
                f"aria2c \"{i}\" -d\"{dir}\" --auto-file-renaming=false --save-session log-{Sno}.txt")
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
soup = getSoup(link)
allFiles = soup.find_all("a", {"class": "list-group-item-action"}, href=True)

ddlLink = []
for i in allFiles:
    remView = i["href"].replace('?a=view', '')
    # check if link is a file or folder
    if not remView[-1] == "/":
        if path.isfile(getPath(remView)[1]) and path.isfile(f"{getPath(remView)[1]}.aria2"):
            # check if file already exists and only add if *.aria2 also exists
            ddlLink.append(
                f"{indexLink}{remView.replace(' ', '%20')}")
        elif not path.isfile(getPath(remView)[1]):
            # if file doesn't exist then just add it
            ddlLink.append(
                f"{indexLink}{remView.replace(' ', '%20')}")
    else:
        # open the link if it's not a file and add it to allFiles var
        soup = getSoup(
            f"{indexLink}{i['href'].replace('?a=view', '').replace(' ', '%20')}")
        allFiles.extend(soup.find_all(
            "a", {"class": "list-group-item-action"}, href=True))

driver.close()

# separate the links list
k, m = divmod(len(ddlLink), simulDownloadNumber)
ddlList = [ddlLink[i*k+min(i, m):(i+1)*k+min(i+1, m)]
           for i in range(simulDownloadNumber)]

simulDownloadList = []
for i in range(simulDownloadNumber):
    simulDownloadList.append((i + 1, ddlList[i]))

# downloading starts here
dl = Pool(simulDownloadNumber).starmap(download, simulDownloadList)
