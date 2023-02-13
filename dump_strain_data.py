#!/app/virtualenv/bin/python3
import csv
import os
import traceback
import cx_Oracle, json, pprint, sys, time
from datetime import datetime
from tabulate import tabulate
from functions import write_csv, read_csv, obtain_db_connection, load_module_config, file_suffix, is_venv
from bs4 import BeautifulSoup
logging = False
creds = None
module_config = load_module_config(__file__.split("/")[-1].split(".py")[0])
from classes import Leafly,Connection
from functions import process_list_concurrently
def load_strain_data(pages):
    driver = Leafly(Connection(module_config['url']))
    driver.build_webdriver()
    driver.load_strains(pages)
def combine_outputs():
    bigass_json={}
    os.chdir('extracts')

    for file in os.listdir():
        with open(file, 'r') as f:
            data = json.loads(f.read())
            for k,v in data.items():
                bigass_json[k]=v

        # os.remove(file)

    with open("strain_data.json", 'w') as f:
        f.write(json.dumps(bigass_json))
if __name__ == "__main__":
    # initialize()
    start_time = time.time()
    driver = Leafly(Connection(module_config['url']))

    driver.build_webdriver()
    pages = driver.load_pages()
    process_list_concurrently(pages,load_strain_data,30)
    combine_outputs()
    # driver.build_webdriver()
    # driver.load_strains()
    print()
    # with open(module_config['html_source']) as f:
    #
    #     soup = BeautifulSoup(f.read())
    #     # print()[x for x in soup.find_all('div', {'class':"wp-show-posts-inner"})[0].children]
    #
    #     for strain_row in soup.find_all('div', {'class':"wp-show-posts-inner"}):
    #         print(strain_row.text.splitlines()[1])
            # for child in strain_row.children:
            #     print(child.text)
    # connection = obtain_db_connection(module_config['connection'])

    result = []

    try:
        pass
        # cursor = connection.cursor()



    except:
        traceback.print_exc()
    #
    write_csv(f"extracts/output_{file_suffix}.csv", result)

    # connection.close()

    print(
        f"\nCompleted in {int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds")

