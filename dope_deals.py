#!/app/virtualenv/bin/python3
import csv
import itertools
import multiprocessing
import os
import traceback
import re

import cx_Oracle, json, pprint, sys, time
from datetime import datetime
import pandas as pd
from pandas import ExcelWriter
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from functions import  load_module_config,strip_special_chars,strip_alphabetic_chars,read_csv, write_csv as _write_csv
from tabulate import tabulate
# from ready_up import  initialize
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
module_config = load_module_config(__file__.split("/")[-1].split(".py")[0])
# logging = False
# creds = None
#
# def is_venv():
#     return (hasattr(sys, 'real_prefix') or
#             (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
file_suffix = f"{datetime.now().strftime('%m-%d-%Y')}"
global_items_of_interest=[]
from selenium.common.exceptions import TimeoutException
# "strain_keywords": ["haze", "skywalker", "sky walker", "afghan","pakistan", "hindu", "maui","afgoo" ,"hindi","diesel","crack", "cheese","dixie","khalifa", "syrup" ]
class Workbook:
    def __init__(self, name):
        self.sheets =[]
        self.workbook_name=f'{name}'
    def write_workbook(self):

        writer = ExcelWriter(self.workbook_name)

        for filename in self.sheets:
            df_csv = pd.read_csv(filename)

            (_, f_name) = os.path.split(filename)
            (f_shortname, _) = os.path.splitext(f_name)
            df_csv.to_excel(writer,filename.split('/')[-1].split('__')[0], index=False)
        writer.save()
global_workbook = Workbook(module_config['report_file'].replace('{date}', file_suffix).replace("{location}", module_config['location'].split(',')[0]))
class DealType:
    FLOWER="flower"
    EDIBLES="edibles"
    PREROLLS="prerolls"
    VAPORIZERS="vaporizers"
    CONCENTRATES="concentrates"
    SPECIALS="specials"
class THCObject:
    dispensary = ""
    producer = ""
    name = ""
    type = ""
    thc = ""
    quantity = ""
    price = ""
    raw = ""
    def is_cost(self,str_cost):
        pattern = re.compile(r"^\$\d*\.?\d*$", re.IGNORECASE)
        return pattern.match(str_cost)
    def convert_to_grams(self,quantity):
        # quantity=
        if 'oz' in quantity:
            quantity=quantity.lower().split('o')[0].strip()
            if quantity =='1/8':
                quantity=3.5
            elif quantity=='1/4':
                quantity = 7
            elif quantity=='1/2':
                quantity = 14
            elif quantity=='1':
                quantity = 28
            else:
                raise Exception(f"cannot calculate ounce price for {str(self)}")
        else:
            try:
                quantity = float(quantity.replace('g', '').strip())
            except:
                traceback.print_exc()
                print(f"Could not convert quantity to grams")
                pass
        return float(quantity)

    def smooth_quantity(self):
        return self.quantity.replace('-', '').strip()
    def thc_content(self):
        return float(self.thc.replace("%",'').strip()) if isinstance(self.thc,str) else self.thc
    def cost(self):
        try:

            if '$' not in self.price:
                found_costs =[]
                for item in self.raw:
                    if self.is_cost(item):
                        found_costs.append(int(item.replace('$','').strip()))
                try:
                    if len(found_costs)>0:
                        self.price=f"${max(found_costs)}"
                    else:
                        print(f"Found no cost data for {' '.join(self.raw)}")
                        return 9999
                except:
                    traceback.print_exc()
                    print(f"COuld not generate cost data for {' '.join(self.raw)}: {self.dispensary}")
                    return 9999

            val = float(self.price.replace("$", '').strip())
            return val
        except:
            traceback.print_exc()
            print(f"COuld not generate cost data for {' '.join(self.raw)}: {self.dispensary}")
            return 9999

    def calculate_gram_cost(self):
        quantity=self.smooth_quantity()
        quantity = self.convert_to_grams(quantity)
        if quantity > 1:
            return self.cost()/quantity
        elif quantity < 1:
            return (1/quantity)*self.cost()
        else:
            return self.cost()


    def calculate_oz_cost(self):
        quantity = self.quantity.replace('-','').strip()
        # self.
        #conver1t to grams
        quantity= self.convert_to_grams(quantity)
        try:
            _cost = self.cost()
        except:
            traceback.print_exc()
            print(f"COuld not calculate data to OZ for {self.name}: {self.dispensary}")
            pass
        return _cost*(28/quantity)
class Edible(THCObject):
    def is_dosage(self, string):
        pattern = re.compile(r"^.*mg$", re.IGNORECASE)
        return pattern.match(string)

    def smooth_edible_data(self):
        dosages = []
        for string in self.name.split(" "):
            if self.is_dosage(string):
                dosages.append(strip_special_chars(string).replace('mg',''))
                if 'x' in  dosages[-1]:
                    data = dosages[-1].lower().split('x')
                    dosages[-1] = int(strip_alphabetic_chars(data[0])) * int(strip_alphabetic_chars(data[1]))
                else:
                    dosages[-1]=int(strip_alphabetic_chars(dosages[-1]))
        if len(dosages) >0:
            self.thc=max(dosages)
        else:
            self.thc=0 #zero out

    def calculate_10mg_cost(self):
        # dose = 200
        # price = 1/0
        self.smooth_edible_data()
        divider = self.thc / 10
        print(divider)
        return self.cost() / divider

        pass
class Special(THCObject):

    type="Special"
    thc="n/a"
    producer = ""
    discount_percentage=""
    full_name=""
    def parse_name(self):
        data = self.name.replace(" %", "%").split(" ")
        for i in range(0, len(data)):
            if data[i].lower()=='for':
                self.price=data[i+1].strip().replace("$", "")
                self.name=' '.join(data[:i-1])
                self.quantity = data[i-1].strip()
                return
            if "/" in data[i]:
                if i==0:
                    self.price=data[i].split("/")[-1].strip()
                    self.quantity=data[i].split("/")[0].strip()
                    self.name=' '.join(data[i+1:])
                    return
                elif i==len(data)-1:
                    self.price = data[i].split("/")[-1].strip()
                    self.quantity = data[i].split("/")[0].strip()
                    self.name = ' '.join(data[:i-1])
                    return
                else:
                    self.price = data[i].split("/")[-1].strip()
                    self.quantity = data[i].split("/")[0].strip()
                    return
            if "%" in data[i]:
                if i==0:
                    self.name=' '.join(data[i+2:])
                    self.discount_percentage=data[i].replace("%",'')
                    return
                elif i==len(data)-1:
                    self.name = ' '.join(data[:i-1])
                    self.discount_percentage = data[i].replace("%", '')
                    return

class VaporizerConcentrate(THCObject):

    def __str__(self):
        return f"Producer: {self.producer} Name: {self.name} THC Content: {self.thc}% Cost Listed: {self.price}/{self.quantity} Cost: ${self.calculate_gram_cost()}/g"
class Flower(THCObject):


    def __str__(self):
        return f"Grower: {self.producer} Name: {self.name} THC Content: {self.thc}% Cost: {self.price}/{self.quantity} OZ Cost: ${self.calculate_oz_cost()}/OZ"
def combine_outputs(pids, type):
    '''
    This function combines a series of output csvs into a single file. This is required as this script is multi-processed and issues can occur writing to the same file
    :param pids: the list of child processes that have written files
    :param environment: the environment the files are written in. this corresponds to a directory name in extracts/
    :return:
    '''
    print(f"Combining {len(pids)} .csv files from child processes into a singular extract")
    pass
    rows = []
    for i in range(0, len(pids)):
        print(f"Processing {type}{pids[i]}.csv")
        if i==0:
            #base case
            if f"{type}{pids[i]}.csv" in os.listdir():
                rows=read_csv(f"{type}{pids[i]}.csv")
        else:
            print(f"reading from temp file {type}{pids[i]}.csv")
            if f"{type}{pids[i]}.csv" in os.listdir():
                tmp_rows = read_csv(f"{type}{pids[i]}.csv")
                for i in range(1, len(tmp_rows)):
                    rows.append(tmp_rows[i])


    print(f"writing extraction file to {type}.csv")
    write_csv(f'{type}.csv',rows)
def write_csv(filename, rows):
    with open(filename  , 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Wrote file {filename}")
    global_workbook.sheets.append(filename)

def scrape_data(data):
    results = []
    for element in data:
        try:
            results.append(element.text.replace("\n",module_config['delimiter']))
        except:
            traceback.print_exc()
            print(f"could not load data for element {element.text}")
            pass
    return results
#     pass
def is_flower_ignore_type(flower):
    for ignore_type in module_config['ignore_types_flower']:
        if ignore_type.lower() in ' '.join(flower.raw).lower():
            return True
def is_vaporizer_ignore_type(thc_object):
    for ignore_type in module_config['ignore_types_vaporizers']:
        if ignore_type in thc_object.name.lower():
            return True
def is_edible_type_ignore(thc_object):
    for ignore_type in module_config['ignore_types_edibles']:
        if ignore_type in thc_object.name.lower():
            return True
def is_concentrate_ignore_type(thc_object):
    for ignore_type in module_config['ignore_types_concentrates']:
        if ignore_type in thc_object.name.lower():
            return True
def generate_special_report(special_dict):

    # _specials = itertools.chain([x for x in special_dict.values()])
    _specials=[]
    for _list in special_dict.values():
        for x in _list:
            _specials.append(x)
    results = [["Dispensary", "Full Name", "Name", "Quantity As Sold", "Price As Sold"]]
    for special in _specials:
        results.append([special.dispensary, special.full_name, special.name, special.quantity, special.cost()])
    return results

def generate_vaporizer_concentrate_report(deal_dict,type):
    #ok so first things first lets sort this out soley by THC content and price
    full_inventory= []
    _report = []
    for dispo, deals in deal_dict.items():
        try:
            deal_list=[]
            if type==DealType.VAPORIZERS:
                # deal_list = [x for x in deals if x.calculate_gram_cost() <= module_config['cost_limit_vaporizers'] and x.thc_content() >=module_config['thc_limit_vaporizers'] and not is_vaporizer_ignore_type(x) ]
                for x in deals:
                    try:
                        if x.calculate_gram_cost() <= module_config['cost_limit_vaporizers'] and x.thc_content()  >= module_config['thc_limit_vaporizeres'] and  not is_vaporizer_ignore_type(x):
                            deal_list.append(x)
                    except:
                        traceback.print_exc()
                        print(f"Could not generate deal for {x.name}")
            elif type==DealType.CONCENTRATES:
                deal_list = [x for x in deals if x.calculate_gram_cost() <= module_config['cost_limit_concentrates'] and x.thc_content() >=module_config['thc_limit_concentrates'] and not is_concentrate_ignore_type(x) ]
                for x in deals:
                    try:
                        if x.calculate_gram_cost() <= module_config['cost_limit_concentrates'] and x.thc_content() >=module_config['thc_limit_concentrates'] and not is_concentrate_ignore_type(x):
                            deal_list.append(x)
                    except:
                        traceback.print_exc()
                        print(f"Could not generate deal for {x.name}")
        except:
            traceback.print_exc()
            print(f"Could not generate deals for {dispo}")
            continue
        full_inventory = full_inventory+deal_list
        # print(f"")
        deal_list.sort(key=lambda x: x.thc_content(), reverse=True)
        deal_list_str = '\n'.join([str(x) for x in deal_list])
        print(f"Deals sorted by THC: {dispo}\n{deal_list_str}")
        print("\n")
        # print(f"")
        deal_list.sort(key=lambda x: x.calculate_gram_cost(), reverse=False)
        deal_list_str = '\n'.join([str(x) for x in deal_list])
        print(f"Deals sorted by Price: {dispo}\n{deal_list_str}")
        print("\n")

    full_inventory.sort(key=lambda x: x.thc_content(), reverse=True)
    print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by THC Content")
    print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    print("\n")
    full_inventory.sort(key=lambda x: x.calculate_gram_cost(), reverse=False)
    print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by Cost")
    print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    print("\n")

    _report.append(["Dispensary", "Producer", "Name", "Type", "THC Content", "Quantity As Sold", "Price As Sold", "Price Per Gram"])
    for thc_object in full_inventory[:150]:
        _report.append([thc_object.dispensary, thc_object.producer, thc_object.name, thc_object.type, thc_object.thc_content(), thc_object.smooth_quantity(), thc_object.cost(), thc_object.calculate_gram_cost()])
    return _report
def generate_interesting_finds_report():
    _report = [["Dispensary", "Producer", "Name", "Type", "THC Content", "Quantity As Sold", "Price As Sold",
                    "Price Per Gram", "Price Per Ounce"]]
    for thc_object in global_items_of_interest:
        try:
            _report.append([thc_object.dispensary, thc_object.producer, thc_object.name, thc_object.type, thc_object.thc,thc_object.smooth_quantity(), thc_object.cost(), thc_object.calculate_gram_cost(), thc_object.calculate_oz_cost()])
        except:
            traceback.print_exc()
            print(f"Could not process interesting find: {thc_object.name}")
    return _report
def generate_edible_report(deal_dict):
    #ok so first things first lets sort this out soley by THC content and price
    full_inventory= []
    _report = []
    for dispo, deals in deal_dict.items():
        try:
            deal_list=[]
            for x in deals:
                try:
                    x.smooth_edible_data()
                    if x.calculate_10mg_cost() <= module_config['cost_limit_edibles'] and x.thc_content() >= module_config['thc_limit_edibles'] and not is_edible_type_ignore(x):
                        deal_list.append(x)
                except:
                    print(f"Could not generate deal for {x.name}")
                    traceback.print_exc()
                    pass
            # deal_list = [x for x in deals if x.calculate_oz_cost() <= module_config['cost_limit_flower'] and x.thc_content() >=module_config['thc_limit_flower'] and not is_flower_ignore_type(x) ]
        except:
            traceback.print_exc()
            print(f"Could not generate deals for {dispo}")
            continue
        full_inventory = full_inventory+deal_list
        # print(f"")
    #     deal_list.sort(key=lambda x: x.thc_content(), reverse=True)
    #     deal_list_str = '\n'.join([str(x) for x in deal_list])
    #     print(f"Deals sorted by THC: {dispo}\n{deal_list_str}")
    #     print("\n")
    #     # print(f"")
    #     deal_list.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
    #     deal_list_str = '\n'.join([str(x) for x in deal_list])
    #     print(f"Deals sorted by Price: {dispo}\n{deal_list_str}")
    #     print("\n")
    #
    # full_inventory.sort(key=lambda x: x.thc_content(), reverse=True)
    # print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by THC Content")
    # print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    # print("\n")
    # full_inventory.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
    # print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by Cost")
    # print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    # print("\n")

    _report.append(["Dispensary", "Producer", "Name", "Type", "THC Content", "Quantity As Sold", "Price As Sold", "Price Per Gram"])
    for edible in full_inventory[:150]:
        _report.append([edible.dispensary, edible.producer, edible.name, edible.type, edible.thc_content(), edible.smooth_quantity(), edible.cost(), edible.calculate_10mg_cost()])
    return _report
def generate_flower_report(deal_dict):
    #ok so first things first lets sort this out soley by THC content and price
    full_inventory= []
    _report = []
    for dispo, deals in deal_dict.items():
        try:
            deal_list=[]
            for x in deals:
                try:
                    if x.calculate_oz_cost() <= module_config['cost_limit_flower'] and x.thc_content() >= module_config['thc_limit_flower'] and not is_flower_ignore_type(x):
                        deal_list.append(x)
                except:
                    print(f"Could not generate deal for {x.name}")
                    traceback.print_exc()
                    pass
            # deal_list = [x for x in deals if x.calculate_oz_cost() <= module_config['cost_limit_flower'] and x.thc_content() >=module_config['thc_limit_flower'] and not is_flower_ignore_type(x) ]
        except:
            traceback.print_exc()
            print(f"Could not generate deals for {dispo}")
            continue
        # deal_list =[]
        # # try:
        # for x in deals:
        #     try:
        #         if x.calculate_oz_cost() <= module_config['cost_limit_flower'] and x.thc_content() >=module_config['thc_limit_flower'] and not is_flower_ignore_type(x):
        #             deals.append(x)
        #     except:
        #         traceback.print_exc()
        #         print(f"Could not generate deals for {dispo}")
        #         continue

        full_inventory = full_inventory+deal_list
        # print(f"")
        deal_list.sort(key=lambda x: x.thc_content(), reverse=True)
        # deal_list_str = '\n'.join([str(x) for x in deal_list])
        # print(f"Deals sorted by THC: {dispo}\n{deal_list_str}")
        # print("\n")
        # print(f"")
        deal_list.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
        # deal_list_str = '\n'.join([str(x) for x in deal_list])
        # print(f"Deals sorted by Price: {dispo}\n{deal_list_str}")
        # print("\n")

    # full_inventory.sort(key=lambda x: x.thc_content(), reverse=True)
    # print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by THC Content")
    # print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    # print("\n")
    # full_inventory.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
    # print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by Cost")
    # print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    # print("\n")

    _report.append(["Dispensary", "Grower", "Name", "Type", "THC Content", "Quantity As Sold", "Price As Sold", "Price Per Ounce"])
    for flower in full_inventory[:150]:
        _report.append([flower.dispensary, flower.producer, flower.name, flower.type, flower.thc_content(), flower.smooth_quantity(), flower.cost(), flower.calculate_oz_cost()])
    return _report

def process_special_deals(deals,dispensary):
    _specials = []
    for deal in deals:
        special = Special()
        special.name=deal
        special.full_name=deal
        special.parse_name()
        special.dispensary=dispensary
        _specials.append(special)

    return _specials


def process_thc_deals(deals, dispensary):
    thc_objects = []
    for deal in deals:
        if 'thc' not in deal.lower():
            continue
        # print(deal)

        data = deal.split(module_config['delimiter'])
        if type == DealType.FLOWER:
            # print('\n'.join(deals))
            thc_object = Flower()
            # print('\n'.join([str(x) for x in strains]))
            # scrape_flower_deals(products)
        if type == DealType.PREROLLS:
            thc_object=THCObject()
        # if:
        #     thc_object=THCObject()
        if type == DealType.VAPORIZERS or  type == DealType.CONCENTRATES:
            thc_object=VaporizerConcentrate()
        if type == DealType.EDIBLES:
            thc_object=Edible()
        else:
            thc_object=THCObject()
        thc_object.raw =data
        while data[0] in ['Staff Pick','Special offer'] or '$' in data[0]:
            del data[0]
        thc_object.dispensary=dispensary
        thc_object.producer = data[0]
        thc_object.name=data[1]
        for key in module_config['strain_keywords']:
            if  key.lower() in ' '.join(thc_object.raw).lower() and thc_object not in global_items_of_interest:
                global_items_of_interest.append(thc_object)
                print(f"Found interesting item: {' '.join(thc_object.raw)} at dispensary: {dispensary}")
        try:
            if data[2].lower() not in ['indica','sativa','hybrid', 'high cbd']:
                data.insert(2,'n/a')
                # print('hmm')
            thc_object.type = data[2]
        except:
            traceback.print_exc()

            continue #skip if this is the case
        try:
            if "|" in data[3]:
                thc_object.thc= data[3].split('|')[0].strip().split("THC: ")[-1]
            else:
                thc_object.thc = data[3].strip().split("THC: ")[-1]
        except:
            traceback.print_exc()
            pass
        # if '%'data[-1]:

        if '%' in data[-1]:
            thc_object.price=data[-2]
            if type==DealType.EDIBLES:
                thc_object.quantity='1'
            else:
                thc_object.quantity = data[-3] if '$' not in data[-3] else data[-4]

        else:
            thc_object.price=data[-1]
            if type==DealType.EDIBLES:
                thc_object.quantity='1'
            else:
                thc_object.quantity = data[-2]
        # print(deal)
        # print(thc_object)
        if type==DealType.EDIBLES:
            try:
                thc_object.smooth_edible_data()
            except:
                traceback.print_exc()
                pass
        thc_objects.append(thc_object)

    # thc_object.calculate_10mg_cost()
    return thc_objects


def load_specials(driver):
    # pass
    # 'class="bogo-menu-card__TextContainer-sc-1grazy4-3 sZXzD"'
    time.sleep(2.5)
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    html = driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]')

    for i in range(0, 5):
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(1.5)
    # time.sleep(2.5)
    elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="bogo-menu-card__TextContainer-sc-1grazy4-3 sZXzD"]')
    return elements
def find_specials(driver, dispensary):
    specials =scrape_data(load_specials(driver))
    # driver.quit()
    return process_special_deals(specials, dispensary)
    pass
def load_products(driver):
    # time.sleep(5)
    # driver.implicitly_wait(5)
    wait = WebDriverWait(driver,180)
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="product-list-item"]')
    elements = []
    for i in range(0,20):
        # for element  in driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]'):
        driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]').send_keys(Keys.PAGE_DOWN)
        # html.send_keys(Keys.PAGE_DOWN)
        # time.sleep(2)
    try:
        images = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[class="product-image__LazyLoad-sc-16rwjkk-0 busNCP desktop-product-list-item__Image-sc-8wto4u-2 ipJspp lazyloaded"]')))
    except TimeoutException:
        images = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[class="product-image__LazyLoad-sc-16rwjkk-0 busNCP desktop-product-list-item__Image-sc-8wto4u-2 ipJspp lazyloaded"]')))
        # images = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[class="product-image__LazyLoad-sc-16rwjkk-0 busNCP desktop-product-list-item__Image-sc-8wto4u-2 ipJspp lazyloaded"]')))
    print(f"Found {len(images)} product images on this page")
    # time.sleep(3)
    # return elements
    return driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="product-list-item"]')
    # return products

def find_deals(driver,dispensary, type=DealType.FLOWER):
    deals = []
    try:
        products = load_products(driver)
        # ?page = 2
        deals = scrape_data(products)
        gt_100 = len(products) > 99
        pages  = WebDriverWait(driver, 20).until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="media-query__ContentDiv-sc-18mweoi-0 hrGTDA"]')))
        del pages[0]
        del pages[-1]
        # page =2
        product_url=driver.current_url
        # while gt_100:
        for i in range(2,max([int(x.text) for x in pages])+1):
            page=i
            print(f"Loading page {page} for {type} deals at {dispensary}")
            driver.get(f"{product_url}?page={page}")
            _products=load_products(driver)
            products = _products+products
            deals += scrape_data(_products)

    except:
        traceback.print_exc()
        print(f"Could not load products for {dispensary}")
        pass

    # driver.quit()
    return process_thc_deals(deals,dispensary)
    #     # print('\n'.join([str(x) for x in strains]))
    #     # scrape_flower_deals(products)
    # if type==DealType.PREROLLS:
    #     pass
    # if type==DealType.CONCENTRATES:
    #     pass
    # if type==DealType.VAPORIZERS:
    #     return process_thc_deals(deals,dispensary)
    # if type==DealType.EDIBLES:
    #     pass

def scrape_dispensary(dispensary,url):

    deals = {}
    for type in module_config['types']:
        driver= build_webdriver()
        print(f"Loading {type} deals for {dispensary}")
        _url=f"{url}{module_config['urls'][type]}"
        driver.get(_url)
        if type!=DealType.SPECIALS:
            deals[dispensary]=find_deals(driver,dispensary, type=type)
        else:
            deals[dispensary] = find_specials(driver, dispensary)
        if type==DealType.FLOWER:
            _write_csv(f"{type}{os.getpid()}.csv",generate_flower_report(deals))
        if type==DealType.VAPORIZERS or  type == DealType.CONCENTRATES:
            _write_csv(f"{type}{os.getpid()}.csv",generate_vaporizer_concentrate_report(deals, type))
        if type==DealType.SPECIALS:
            _write_csv(f"{type}{os.getpid()}.csv", generate_special_report(deals))
        if type==DealType.EDIBLES:
            _write_csv(f"{type}{os.getpid()}.csv", generate_edible_report(deals))
    _write_csv(f"interesting_finds{os.getpid()}.csv",generate_interesting_finds_report())
def build_webdriver():
    CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    CHROMEDRIVER_PATH ='../chromedriver'
    WINDOW_SIZE = "1920,1080"

    chrome_options = Options()
    # chrome_options.headless=True
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--start-minimized")
    chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

    driver = webdriver.Chrome(executable_path='../chromedriver', chrome_options=chrome_options)
    # driver = webdriver.Chrome('../chromedriver')
    driver.get("https://dutchie.com/")
    age_restriction_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-test="age-restriction-yes"]')
    age_restriction_btn.click()
    return driver
def load_dispensaries(driver):
    wait = WebDriverWait(driver, 10)
    search_bar = driver.find_element(By.CSS_SELECTOR, 'input[data-testid="homeAddressInput"]')
    search_bar.send_keys(module_config['location'])

    # locations = driver.find_elements(By.CSS_SELECTOR, 'div[class="option__Container-sc-1e884xj-0 khOZsM"]')
    search_bar.click()
    # class="dispensary-card__Image-sc-1wd9p5b-2 fKTDvr"
    # time.sleep(10)
    location = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'li[data-testid="addressAutocompleteOption"]')))[0]
    location.click()
    time.sleep(2)
    # soup = BeautifulSoup(driver.page_source)
    # results = soup.find_all("li", {"data-testid":"addressAutocompleteOption"})
    # results = soup.find("a", data-testid='listbox--1')
    images = wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[class="dispensary-card__Image-sc-1wd9p5b-2 fKTDvr"]')))
    for image in images:
        print(image.get_attribute('src'))
    dispensary_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="dispensary-card"]')
    dispensaries = {}
    for i in range(0, len(dispensary_links)):# in dispensary_links:
        link = dispensary_links[i]
        dispensaries[link.text.split("\n")[0] if  link.text.split("\n")[0] != 'Closed' else link.text.split("\n")[1]]={"url":link.get_attribute('href'),"distance":link.text.split("\n")[-2].split(" Mile")[0], "image":images[i].get_attribute('src')}
        # dis = [x.get_attribute('href') for x in dispensaries]
    print(f"Found {len(dispensaries.keys())} dispenaries in {module_config['location']}")
    return dispensaries
def update_run_history(runtime, dispensary_count):
    with open(module_config['run_history_file'], "a+") as f:
        f.write(f"{datetime.now().strftime('%m-%d-%Y %H:%M:%S')}: Scraped {dispensary_count} dispensaries ({module_config['location']}) in {runtime}\n")

if __name__ == "__main__":
    # print(is_venv())
    # _input= read_csv('encodings_are_dumb.csv')
    # initialize()
    start_time = time.time()
    # do_work(None, _input)
    # args =sys.argv[1:]
    #
    # # sql =args[0]\


    try:
        driver = build_webdriver()
        # driver.get("https://dutchie.com/")
        # age_restriction_btn = driver.find_element(By.CSS_SELECTOR,'button[data-test="age-restriction-yes"]')
        # age_restriction_btn.click()


        # dispo_str = '\n'.join(dispensaries.keys())
        # print(f"{dispo_str}\n")
        # driver.quit()
        dispensaries = load_dispensaries(driver)
        # dispensaries = {}
        # dispensaries={'3Fifteen':{"url":"https://dutchie.com/dispensary/3fifteen"}}
        # dispensaries={'jade':{"url":"https://dutchie.com/dispensary/jade-collection"}}
        # dispensaries={'Gage':{"url":'https://dutchie.com/dispensary/gage-cannabis-co-adrian'}}
        # dispensaries={'Gage':{"url":'https://dutchie.com/dispensary/gage-cannabis-co-adrian'}}
        # dispensaries={'Rush':{"url":'https://dutchie.com/dispensary/rush-cannabis'}}
        # dispensaries={'amazing-budz':{"url":'https://dutchie.com/dispensary/amazing-budz'}}
        # dispensaries={'heads-monroe':{"url":'https://dutchie.com/dispensary/heads-monroe'}}
        # for k, v in dispensaries.items():
        # dispos = [x for x in dispensaries.keys()]

        n=module_config['process_load_size']
        _dispensarys = [x for x in dispensaries.keys()]
        task_loads = [_dispensarys[i:i + n] for i in range(0, len(_dispensarys), n)]
        # for k,v in dispensaries.items():
        processes = {}
        print(f"Processing {len(dispensaries.keys())} in {len(task_loads)} load(s)")
        for i in range(0,len(task_loads)):
            print(f"Blowing {i + 1}/{len(task_loads)} Loads")
            load=task_loads[i]
            for ii in range(0,len(load)):

                p = multiprocessing.Process(target=scrape_dispensary, args=(load[ii],dispensaries[load[ii]]['url']))
                p.start()

                processes[str(p.pid)] = p
            while any(processes[p].is_alive() for p in processes.keys()):
                # print(f"Waiting for {len([x for x in processes if x.is_alive()])} processes to complete. Going to sleep for 10 seconds")
                process_str = ','.join([str(v.pid) for v in processes.values() if v.is_alive()])
                time_str = f"{int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds"
                print(f"Waiting on {len(processes.keys())} processes to finish in load {i + 1}/{len(task_loads)}\nElapsed Time: {time_str}")
                time.sleep(10)

        print(f"All loads have been blown, generating your report")
        module_config['types'].append('interesting_finds')
        for type in module_config['types']:
            combine_outputs([x for x in processes.keys()],type)
            for pid in processes.keys():
                if f"{type}{pid}.csv" in os.listdir():
                    os.remove(f"{type}{pid}.csv")
        driver.quit()

        global_workbook.write_workbook()
    except:
        traceback.print_exc()
    #
    # write_csv(f"extracts/output_{file_suffix}.csv", result)

    # cursor.close()
    # sp_connection.close()
    update_run_history(f"{int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds", len(dispensaries.keys()))
    print(f"\nCompleted in {int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds")


