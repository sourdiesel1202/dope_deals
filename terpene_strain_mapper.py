#!/app/virtualenv/bin/python3
import csv
import traceback
import cx_Oracle, json, pprint, sys, time
from datetime import datetime
from tabulate import tabulate
from functions import write_csv, read_csv, obtain_db_connection, load_module_config, file_suffix, is_venv


logging = False
creds = None
# module_config = load_module_config(__file__.split("/")[-1].split(".py")[0])
def strip_special_chars(string):
    for x in "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~":
        string=string.replace(x,'')
    return string
if __name__ == "__main__":
    start_time = time.time()

    # connection = obtain_db_connection(module_config['connection'])

    result = []

    try:
        with open("extracts/Terpene.json", "r") as f:
            terpene_json = json.loads(f.read())
        with open("extracts/strain_data.json", "r") as f:
            strain_json = json.loads(f.read())
        terpene_aromas = ["Pear"]
        for terpene, terpene_data in terpene_json.items():
            for aroma in terpene_data['aromas']:
                if aroma not in terpene_aromas:
                    terpene_aromas.append(aroma)
        strain_list = [x for x in strain_json.keys()]
        for strain, strain_data in strain_json.items():
            # print(f"Processing Strain {strain}")
            #first,cleanup existing terpenes
            for i in range(0, len(strain_data['terpenes'])):
                if  "(" in strain_data['terpenes'][i]:
                    # print(f"Cleaning {strain} terpene: {strain_json[strain]['terpenes'][i]} ==> {strain_data['terpenes'][i].split('(')[0].strip()}")
                    strain_json[strain]['terpenes'][i]=strain_data['terpenes'][i].split("(")[0].strip()
                    strain_data['terpenes'][i] = strain_data['terpenes'][i].split("(")[0].strip()
            #ok so now we need to make sure we aren't missing any terpenes in the description
            for terpene in terpene_json.keys():
                if terpene.lower() in strain_data['description'].lower():
                    if terpene not in strain_data['terpenes']:
                        # print(f"Found extra terpene for {strain} (lol @ leafly): {terpene}")
                        strain_json[strain]['terpenes'].append(terpene)
            #ok this went so smoothly that i'd like to try to find the missing parents
            tmp_descripton = strain_data['description'].split("imilar")[0].split("like")[0]
            for _strain in strain_json.keys():
                if _strain in ['Cream','Or', "Euphoria","Flo", "Humboldt", "Ice", "Boost", "22", "Spice", "Lucky", "Decent", "Haze"] or _strain in terpene_aromas:
                    continue
                if (f" {_strain} " in strip_special_chars(tmp_descripton) or f" {_strain}x" in strip_special_chars(tmp_descripton)) and _strain.lower() not in strain.lower() and _strain!= 'Or' and _strain !=strain:
                    if  _strain not in strain_data['parents']:
                        ignore_strain =False
                        for parent in strain_data['parents']:
                            if _strain in parent or parent in _strain:
                                ignore_strain=True
                                break
                        if not ignore_strain:
                            if len(strain_data['parents']) < 2:
                                strain_json[strain]['parents'].append(_strain)
                                print(f"Found missing parent for {strain}: {_strain}: New Parents: {','.join(strain_json[strain]['parents'])}")
                            else:
                                for parent in strain_data['parents']:
                                    if parent in _strain:
                                        print(f"Replacing parent for {strain}:New Parent- {_strain} Old Parent-{parent}: New Parents: {','.join(strain_json[strain]['parents'])}")
                                        strain_json[strain]['parents'][strain_json[strain]['parents'].index(parent)]=_strain
            if 'haze' in strain.lower() and len(strain_data['parents']) <2:
                strain_json[strain]['parents'].append('Haze')
                print(f"Found missing parent for {strain}: Haze: New Parents: {','.join(strain_json[strain]['parents'])}")
        with open("extracts/Strain.json", "w+") as f :
            f.write(json.dumps(strain_json))

    except:
        traceback.print_exc()
    #
    # write_csv(f"extracts/output_{file_suffix}.csv", result)

    # connection.close()

    print(
        f"\nCompleted in {int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds")

