from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from os import path, remove, stat, system
from urllib.parse import quote, unquote
from selenium.webdriver import Chrome
from multiprocessing import Pool
from bs4 import BeautifulSoup
from time import sleep
from json import load