#!/app/virtualenv/bin/python3
import csv
import itertools
import os
import traceback

import cx_Oracle, json, pprint, sys, time
from datetime import datetime
import pandas as pd
from pandas import ExcelWriter
from selenium.webdriver.common.by import By
from functions import  load_module_config
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
                pass
        return float(quantity)
    def smooth_quantity(self):
        return self.quantity.replace('-', '').strip()
    def thc_content(self):
        return float(self.thc.replace("%",'').strip())
    def cost(self):
        try:
            return float(self.price.replace("$", '').strip())
        except:
            return ""

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

        #convert to grams
        quantity= self.convert_to_grams(quantity)
        try:
            cost = self.cost()
        except:
            pass
        return cost*(28/quantity)

class Special(THCObject):
    raw = ""
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
            pass
    return results
#     pass
def is_flower_ignore_type(flower):
    for ignore_type in module_config['ignore_types_flower']:
        if ignore_type in flower.name.lower():
            return True
def is_vaporizer_ignore_type(thc_object):
    for ignore_type in module_config['ignore_types_vaporizers']:
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
        _report.append([thc_object.dispensary, thc_object.producer, thc_object.name, thc_object.type, thc_object.thc_content(),thc_object.smooth_quantity(), thc_object.cost(), thc_object.calculate_gram_cost(), thc_object.calculate_oz_cost()])
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
        deal_list_str = '\n'.join([str(x) for x in deal_list])
        print(f"Deals sorted by THC: {dispo}\n{deal_list_str}")
        print("\n")
        # print(f"")
        deal_list.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
        deal_list_str = '\n'.join([str(x) for x in deal_list])
        print(f"Deals sorted by Price: {dispo}\n{deal_list_str}")
        print("\n")

    full_inventory.sort(key=lambda x: x.thc_content(), reverse=True)
    print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by THC Content")
    print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    print("\n")
    full_inventory.sort(key=lambda x: x.calculate_oz_cost(), reverse=False)
    print(f"A full inventory listing is below (sorted to your liking), limited to the first 100 by Cost")
    print('\n'.join([f"{x.dispensary}- {str(x)}" for x in full_inventory[:100]]))
    print("\n")

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
            thc_object=THCObject()
        thc_object.raw =data
        while data[0] in ['Staff Pick','Special offer'] or '$' in data[0]:
            del data[0]
        thc_object.dispensary=dispensary
        thc_object.producer = data[0]
        thc_object.name=data[1]
        try:
            if data[2].lower() not in ['indica','sativa','hybrid', 'high cbd']:
                data.insert(2,'n/a')
                # print('hmm')
            thc_object.type = data[2]
        except:
            continue #skip if this is the case
        try:
            if "|" in data[3]:
                thc_object.thc= data[3].split('|')[0].strip().split("THC: ")[-1]
            else:
                thc_object.thc = data[3].strip().split("THC: ")[-1]
        except:
            pass
        # if '%'data[-1]:

        if '%' in data[-1]:
            thc_object.price=data[-2]
            thc_object.quantity = data[-3] if '$' not in data[-3] else data[-4]

        else:
            thc_object.price=data[-1]
            thc_object.quantity = data[-2]
        # print(deal)
        # print(thc_object)
        thc_objects.append(thc_object)
        for key in module_config['strain_keywords']:
            if  key.lower() in thc_object.name.lower():
                global_items_of_interest.append(thc_object)

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
    return process_special_deals(specials, dispensary)
    pass
def load_products(driver):
    time.sleep(2.5)
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    html = driver.find_element(By.CSS_SELECTOR, 'html[data-js-focus-visible=""]')

    for i in range(0, 15):
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(1.5)
    time.sleep(2.5)
    return driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="product-list-item"]')
    # return products

def find_deals(driver,dispensary, type=DealType.FLOWER):
    products =load_products(driver)
    # ?page = 2
    deals = scrape_data(products)
    gt_100 = len(products)>99
    page =2
    product_url=driver.current_url
    while gt_100:
        driver.get(f"{product_url}?page={page}")
        _products=load_products(driver)
        products = _products+products
        deals += scrape_data(_products)
        if len(_products)<100:
            gt_100=False
        else:
            page+=1
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
        driver = webdriver.Chrome('./chromedriver')
        driver.get("https://dutchie.com/")
        age_restriction_btn = driver.find_element(By.CSS_SELECTOR,'button[data-test="age-restriction-yes"]')
        age_restriction_btn.click()
        # search_bar = driver.find_element(By.CSS_SELECTOR, 'input[data-testid="homeAddressInput"]')
        # search_bar.send_keys(module_config['location'])
        #
        # # locations = driver.find_elements(By.CSS_SELECTOR, 'div[class="option__Container-sc-1e884xj-0 khOZsM"]')
        # search_bar.click()
        # time.sleep(2)
        # location = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="addressAutocompleteOption"]')[0]
        # location.click()
        # time.sleep(3)
        # soup = BeautifulSoup(driver.page_source)
        # # results = soup.find_all("li", {"data-testid":"addressAutocompleteOption"})
        # # results = soup.find("a", data-testid='listbox--1')
        # dispensary_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="dispensary-card"]')
        # dispensaries = {}
        # for link in dispensary_links:
        #     dispensaries[link.text.split("\n")[0] if  link.text.split("\n")[0] != 'Closed' else link.text.split("\n")[1]]={"url":link.get_attribute('href'),"distance":link.text.split("\n")[-2].split(" Mile")[0]}
        #     # dis = [x.get_attribute('href') for x in dispensaries]
        # print(f"Found {len(dispensaries.keys())} dispenaries in {module_config['location']}")
        # dispo_str = '\n'.join(dispensaries.keys())
        # print(f"{dispo_str}\n")
        dispensaries={'3Fifteen':{"url":"https://dutchie.com/dispensary/3fifteen"}}
        # dispensaries={'Gage':{"url":'https://dutchie.com/dispensary/gage-cannabis-co-adrian'}}
        # dispensaries={'amazing-budz':{"url":'https://dutchie.com/dispensary/amazing-budz'}}
        # dispensaries={'heads-monroe':{"url":'https://dutchie.com/dispensary/heads-monroe'}}
        # for k, v in dispensaries.items():
        dispos = [x for x in dispensaries.keys()]

        for type in module_config['types']:
            deals = {}
            for i in range(0,len(dispos)):

                print(f"Loading {type} deals for {dispos[i]} {i+1}/{len(dispos)}")
                driver.get(f"{dispensaries[dispos[i]]['url']}{module_config['urls'][type]}")
                if type!=DealType.SPECIALS:
                    deals[dispos[i]]=find_deals(driver,dispos[i], type=type)
                else:
                    deals[dispos[i]] = find_specials(driver, dispos[i])
            if type==DealType.FLOWER:
                write_csv(f"{type}.csv",generate_flower_report(deals))
            if type==DealType.VAPORIZERS or  type == DealType.CONCENTRATES:
                write_csv(f"{type}.csv",generate_vaporizer_concentrate_report(deals, type))
            if type==DealType.SPECIALS:
                write_csv(f"{type}.csv", generate_special_report(deals))
        write_csv(f"interesting_finds.csv",generate_interesting_finds_report())
        global_workbook.write_workbook()
    except:
        traceback.print_exc()
    #
    # write_csv(f"extracts/output_{file_suffix}.csv", result)

    # cursor.close()
    # sp_connection.close()
    print(f"\nCompleted in {int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds")

