import json
import os
import string
import traceback
import json
import traceback
# from products.classes import ProductType
from selenium.common import TimeoutException
from functions import process_list_concurrently
import requests
# from products.classes import ProductType
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
# from functions import  load_module_config,strip_special_chars,strip_alphabetic_chars,read_csv, write_csv as _write_csv
from tabulate import tabulate
# from ready_up import  initialize
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class Connection:
    def __init__(self, hostname):
        self.host=hostname
    host=""

class ProductType:
    FLOWER="flower"
    EDIBLES="edibles"
    PREROLLS="prerolls"
    VAPORIZERS="vaporizers"
    CONCENTRATES="concentrates"
    SPECIALS="specials"
class APIConnector:
    POST='POST'
    GET='GET'
    PATCH='PATCH'
    PUT='PUT'
    def __init__(self,connection):
        self.request = None
        self.connection = connection
        pass
    def call_api(self,url_path='/', method='GET', headers={}, data={}, verify=False, proxies={},params={},json={}):
        print(f"Calling: {self.connection.host}{url_path}")
        if method=='GET':
            self.request = requests.get(f"{self.connection.host}{url_path}", data=data, headers=headers, verify=verify, proxies=proxies,params=params,json=json)
        elif method=='POST':
            self.request = requests.post(f"{self.connection.host}{url_path}", data=data, headers=headers, verify=verify,proxies=proxies,params=params,json=json)
        elif method=='PATCH':
            self.request = requests.patch(f"{self.connection.host}{url_path}", data=data, headers=headers, verify=verify,proxies=proxies,params=params,json=json)
        elif method=='PUT':
            self.request = requests.put(f"{self.connection.host}{url_path}", data=data, headers=headers, verify=verify,proxies=proxies,params=params,json=json)
        else:
            raise NotImplementedError("Unrecognized HTTP Method")

class WebSource:
    driver = None
    connection =None
    def __init__(self, connection):
        self.connection = connection
    def test_connection(self):
        raise NotImplementedError
    def build_webdriver(self):
        raise NotImplementedError
    def scrap_data(self):
        raise NotImplementedError

class StrainWebSource(WebSource):

    def load_strain_details(self, strain_url):
        pass

    def load_strains(self, pages=None):
        pass
class ProductWebSource(WebSource):

    def load_dispensaries(self, location):
        raise NotImplementedError

    def load_products(self):
        raise NotImplementedError
    def process_thc_deals(self,  products, dispensary, product_type=ProductType.FLOWER):
        raise NotImplementedError
class Leafly(StrainWebSource):
    def build_webdriver(self):
        CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        CHROMEDRIVER_PATH = '../chromedriver'
        WINDOW_SIZE = "1920,1080"
        print()
        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.add_argument("--start-minimized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        self.driver = webdriver.Chrome(executable_path='../chromedriver', chrome_options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        # driver = webdriver.Chrome('../chromedriver')
        self.driver.get(self.connection.host)
        wait  = WebDriverWait(self.driver,30)
        age_restriction_btn = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="age-gate-yes-button"]')))
        age_restriction_btn.click()

    def load_pages(self):
        # self.build_webdriver()
        wait = WebDriverWait(self.driver, 30)
        pages = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="page"]')))
        # print(f"{pages.text}")
        return [x for x in range(1, int(pages.text.split(" of ")[-1]) + 1)]
    def load_lineage(self):
        data={}
        data['parents']=[]
        data['children']=[]
        #no parent care
        # try:
        #
        wait = WebDriverWait(self.driver, 3)
        #     if len(wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="jsx-1e374a6fd2e6bf7b lineage__strain--no-parents text-center flex flex-col items-center"]')))) > 0:
        #         data['parents']=[]
        #
        # except TimeoutException:
        #     pass
        #single parent case
        try:
             data['parents']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8ff675a0409ea4f5 lineage__center-parent"]'))).text.split("\n")[0]]
             # data['parents']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8ff675a0409ea4f5 lineage__center-parent"]'))).text.split("\n")[0]]
        except:
            pass
        try:
             data['parents']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[jsx-8af313c9106c9319 lineage__center-child--no-parents"]'))).text.split("\n")[0]]
             # data['parents']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8ff675a0409ea4f5 lineage__center-parent"]'))).text.split("\n")[0]]
        except:
            pass
        # jsx-8af313c9106c9319 lineage__center-child--no-parents
        #both parent case
        try:
            parent1 = wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[class="jsx-9131a7ef0b491b54 lineage__right-parent"]'))).text.split("\n")[0]
            parent2 = wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[class="jsx-9131a7ef0b491b54 lineage__left-parent"]'))).text.split("\n")[0]
            data['parents'] = [parent1, parent2]
        except:
            pass
        #both child case no parents
        try:

            child1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__left-child--no-parents"]'))).text.split("\n")[0]
            child2 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__right-child--no-parents"]'))).text.split("\n")[0]
            data['children']=[child1,child2]
        except:
            pass

        #single child no parents
        try:
            data['children']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__center-child--no-parents"]'))).text.split("\n")[0]]
        except:
            pass
        #single child both parents
        try:
            data['children']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8af313c9106c9319 lineage__center-child--two-parents"]'))).text.split("\n")[0]]
        except:
            pass
        #both children both parents
        try:
            data['children']=[wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__left-child--two-parents"]'))).text.split("\n")[0]]
            data['children'].append(wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__right-child--two-parents"]'))).text.split("\n")[0])
        except:
            pass
        return data
        # try:
        #     parent1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-9131a7ef0b491b54 lineage__right-parent"]'))).text.split("\n")[0]
        #     parent2 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-9131a7ef0b491b54 lineage__left-parent"]'))).text.split("\n")[0]
        #     data['children']=[child1,child2]
        # except:
            #try these again later
            # data['parents']=[]
            # data['children']=[]

            # try:
        # child2 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__right-child--two-parents"]'))).text.split("\n")[0]
        # child1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-97479fdfc5156e78 lineage__left-child--two-parents"]'))).text.split("\n")[0]
        # data['parents']=[parent1,parent2]
            #     parent1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8ff675a0409ea4f5 lineage__center-parent"]'))).text.split("\n")[0]
            #     child1 = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[class="jsx-8ff675a0409ea4f5 lineage__center-child"]'))).text.split("\n")[0]
            #     data['parents'] = [parent1]
            #     data['children'] = [child1]
            # except:
            #     traceback.print_exc()
            #     print(f"Could not load lineage for {data['name']}")
            #     data['children']=[]
            #     data['parents']=[]
    def load_strains(self, pages=None):
        json_data = {}
        urls = []
        with open('extracts/strain_data.json', 'r') as f:
            for item in json.loads(f.read()).values():
                urls.append(item['url'])
        print(f"Preloaded data for {len(urls)} strain(s)")
        for page_number in pages:
            wait = WebDriverWait(self.driver, 50)
            print(f"Processing {pages.index(page_number)+1}/{len(pages)} strain pages")
            #ok so first load the page
            self.driver.get(f"{self.connection.host}?page={page_number}")
            print(f"Loading strains on page {self.connection.host}?page={page_number}")
            time.sleep(2)
            for i in range(0, 10):
                # for element  in driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]'):
                self.driver.find_element(By.CSS_SELECTOR, 'body[class="transition-[padding-top] motion-reduce:transition-none"]').send_keys(
                    Keys.PAGE_DOWN)

            strain_links = [x.get_attribute("href") for x in wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-testid="strain-card"]')))]
            for strain_link in strain_links:
                if strain_link in urls:
                    print(f"Found existing data loaded for {strain_link}")
                    continue
                print(f"Processing strain {strain_links.index(strain_link)+1}/{len(strain_links)} {strain_link} on page {pages.index(page_number)+1}/{len(pages)}")
                try:
                    data= self.load_strain_details(strain_link)
                    json_data[data['name']]=data
                except:
                    traceback.print_exc()
                    print(f"Could not load data for {strain_link}")
                # print(strain_link.get_attribute("href"))
                with open(f"extracts/strain_{os.getpid()}.json", "w") as f:
                    f.write(json.dumps(json_data))
                self.driver.get(f"{self.connection.host}?page={page_number}")
                print(f"Loading strains on page {self.connection.host}?page={page_number}")
                wait = WebDriverWait(self.driver, 50)
        # process_list_concurrently(total_pages,self.load_leafly_strain_pages, 30)
        #so basically the idea here is that we will load our strains in a multi processed fashion here
        #first get list of pages

        pass
    # def load_leafly_strain_pages(self, pages):
    #     print(f"{os.getpid()}: Processing pages {','.join(pages)}")
        # for page_number in pages:
        #     pass
        pass
    def load_strain_details(self, strain_url):
        #name
        #description
        #source
        #images
        #type
        #parents
        #children
        #terpenes
        #terpenes
        #aliases

        self.driver.get(strain_url)
        wait  = WebDriverWait(self.driver,15)
        for i in range(0, 10):
            # for element  in driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]'):
            self.driver.find_element(By.CSS_SELECTOR,
                                     'body[class="transition-[padding-top] motion-reduce:transition-none"]').send_keys(
                Keys.PAGE_DOWN)

        data = {"url":strain_url}
        data["name"] = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'h1[class="heading--l mb-xs"]'))).text
        # print(f"Processing strain: {data['name']}")
        data['description'] = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop="description"]'))).text
        data['image'] = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[data-testid="image-picture-image"]')))[0].get_attribute('srcset').split(",")[0]
        lineage =self.load_lineage()
        wait = WebDriverWait(self.driver, 15)
        data['parents']=lineage['parents']
        data['children']=lineage['children']
        try:
            data['type'] = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'span[class="inline-block text-xs px-sm rounded font-bold text-default bg-leafly-white py-xs"]')))[0].text.split("?")[0]
        except:
            pass
        try:
            data['type'] = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'span[class="inline-block text-xs px-sm rounded font-bold text-default bg-white border border-light-grey py-0"]')))[0].text.split("?")[0]
        except:
            pass
        try:
            data['type'] = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'span[class="inline-block text-xs px-sm rounded font-bold text-default bg-white border border-light-grey py-0"]')))[0].text.split("?")[0]
        except:
            pass
        try:
            data['aliases']=[x.strip() for x in wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,'h2[class="text-xs font-normal truncate text-secondary"]'))).text.replace('aka ', '').split(',')]
        except TimeoutException:
            data['aliases']=[]
        try:


            data['terpenes']= [x.text for x in wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'p[class="mb-none"]')))]

            print()
        except:

            data['terpenes']=[]
            pass
        # self.driver.get(self.connection.host)

        return data

class AllBud(StrainWebSource):
    def build_webdriver(self):
        #ok so here we build the webdriver to do some shit? idk man
        CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        CHROMEDRIVER_PATH = '../chromedriver'
        WINDOW_SIZE = "1920,1080"
        print()
        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.add_argument("--start-minimized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        self.driver = webdriver.Chrome(executable_path='../chromedriver', chrome_options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        # driver = webdriver.Chrome('../chromedriver')
        self.driver.get(self.connection.host)
        wait  = WebDriverWait(self.driver,30)
        #no age restriction for allbud lol
        # age_restriction_btn = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="age-gate-yes-button"]')))
        # age_restriction_btn.click()

    def load_pages(self):
        # self.build_webdriver()
        # wait = WebDriverWait(self.driver, 30)
        # pages = wai/t.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="page"]')))
        # print(f"{pages.text}")
        return list(string.ascii_uppercase)

    def load_strains(self, pages=None):
        json_data = {}
        _strains = []
        with open('extracts/strain_data.json', 'r') as f:
            for item in json.loads(f.read()).keys():
                # print(item)
                # urls.append(item['url'])/
                _strains.append(item)
        print(f"Preloaded data for {len(_strains)} strain(s)")
        for page_letter in pages:
            wait = WebDriverWait(self.driver, 50)
            print(f"Processing {pages.index(page_letter)+1}/{len(pages)} strain pages")
            #ok so first load the page
            self.driver.get(f"{self.connection.host}&letter={page_letter}&results=5000")
            print(f"Loading strains on page {self.connection.host}&page={page_letter}&results=5000")
            wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'li[class="pull-left hidden-xs"]')))
            strains = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[class="infocard strain"]')))
            new_strains = {}
            for strain_card in strains:
                link = strain_card.find_element(By.CSS_SELECTOR,'section[class="object-title"]').find_element(By.CSS_SELECTOR,'a').get_attribute('href')
                name = strain_card.find_element(By.CSS_SELECTOR,'section[class="object-title"]').find_element(By.CSS_SELECTOR,'a').find_element(By.CSS_SELECTOR,'h3[class="visible-lg"]').text
                img = strain_card.find_element(By.CSS_SELECTOR,'header').find_element(By.CSS_SELECTOR,'img').get_attribute('data-src').strip()
                if name not in _strains:
                    print(f"Found new strain: {name}")
                    new_strains[name]={"url":link, "img":img, "name":name}
                # link = strain_card
                # print(link)
                # print(img)

            print(f"Found {len(new_strains)} new strains on page {page_letter}")
            parsed_strains = {}
            for tmp_strain_data  in new_strains.values():
                
                #load the strain data itself now
                try:
                    self.driver.get(tmp_strain_data['url'])
                    type = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'h4[class="variety"]'))).find_element(By.CSS_SELECTOR,'a').text
                    description = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'div[id="strain-info"]'))).find_elements(By.CSS_SELECTOR,'span')[-1].text
                    effects = [x.text for x in wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'section[id="positive-effects"]'))).find_element(By.CSS_SELECTOR,'div[class="panel-body well tags-list"').find_elements(By.CSS_SELECTOR, 'a')]
                    relieves = [x.text for x in wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'section[id="relieved"]'))).find_element(By.CSS_SELECTOR,'div[class="panel-body well tags-list"').find_elements(By.CSS_SELECTOR, 'a')]
                    aromas = [x.text for x in wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'section[id="aromas"]'))).find_element(By.CSS_SELECTOR,'div[class="panel-body well tags-list"').find_elements(By.CSS_SELECTOR, 'a')]
                    flavors = [x.text for x in wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'section[id="flavors"]'))).find_element(By.CSS_SELECTOR,'div[class="panel-body well tags-list"').find_elements(By.CSS_SELECTOR, 'a')]
                    print(f"{type}: {relieves} {aromas} {flavors} {effects}")
                    new_strains[tmp_strain_data['name']]['description']=description
                    new_strains[tmp_strain_data['name']]['effects']=effects
                    new_strains[tmp_strain_data['name']]['aromas']=aromas
                    new_strains[tmp_strain_data['name']]['flavors']=flavors
                    new_strains[tmp_strain_data['name']]['relieves']=flavors
                    new_strains[tmp_strain_data['name']]['type']=type
                    new_strains[tmp_strain_data['name']]['children']=[]
                    new_strains[tmp_strain_data['name']]['parents']=[]
                    new_strains[tmp_strain_data['name']]['aliases']=[]
                    new_strains[tmp_strain_data['name']]['terpenes']=[]
                    parsed_strains[tmp_strain_data['name']]=new_strains[tmp_strain_data['name']]
                    with open(f"extracts/strain_{os.getpid()}.json", "w") as f:
                        f.write(json.dumps(parsed_strains))
                    time.sleep(5) #try to be human?
                except:
                    traceback.print_exc()
                    print(f"Could not load data for {tmp_strain_data['name']}")

            # once we are here we can pretty much just write the json and move on
            #disregard below
            #presusmably now, we have a page full of strains to parse and load the data for

            # #ok so THIS is where shit is going to get fuuuuuuucky
            # #these are endless scroll, so basially do a while the more results button is visible
            # while len(self.driver.find_elements(By.CSS_SELECTOR, 'a[class="endless_more"]')) > 0:
            #     self.driver.find_element(By.CSS_SELECTOR, 'a[class="endless_more"]').click()
            #     try:
            #         wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'a[class="endless_more"]')))
            #     except TimeoutException as e:
            #         print(f"Reached the bottom?")
            #         break
        #     for i in range(0, 10):
        #         # for element  in driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]'):
        #         self.driver.find_element(By.CSS_SELECTOR, 'body[class="transition-[padding-top] motion-reduce:transition-none"]').send_keys(Keys.PAGE_DOWN)
        #
        #     strain_links = [x.get_attribute("href") for x in wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-testid="strain-card"]')))]
        #     for strain_link in strain_links:
        #         if strain_link in urls:
        #             print(f"Found existing data loaded for {strain_link}")
        #             continue
        #         print(f"Processing strain {strain_links.index(strain_link)+1}/{len(strain_links)} {strain_link} on page {pages.index(page_number)+1}/{len(pages)}")
        #         try:
        #             data= self.load_strain_details(strain_link)
        #             json_data[data['name']]=data
        #         except:
        #             traceback.print_exc()
        #             print(f"Could not load data for {strain_link}")
        #         # print(strain_link.get_attribute("href"))
        #         with open(f"extracts/{os.getpid()}.json", "w") as f:
        #             f.write(json.dumps(json_data))
        #         self.driver.get(f"{self.connection.host}?page={page_number}")
        #         print(f"Loading strains on page {self.connection.host}?page={page_number}")
        #         wait = WebDriverWait(self.driver, 50)
        # # process_list_concurrently(total_pages,self.load_leafly_strain_pages, 30)
        # #so basically the idea here is that we will load our strains in a multi processed fashion here
        # #first get list of pages

        pass
    # def load_leafly_strain_pages(self, pages):
    #     print(f"{os.getpid()}: Processing pages {','.join(pages)}")
        # for page_number in pages:
        #     pass
        pass