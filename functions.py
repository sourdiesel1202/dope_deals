#!/app/virtualenv/bin/python3
import csv
import json
import multiprocessing
import telnetlib
import time,os
import traceback
from random import randint
import sys
# import ready_up
from auth import *
from datetime import datetime
import cx_Oracle
from subprocess import Popen, PIPE, STDOUT, call
# import psycopg2
import platform    # For getting the operating system name
import re

# import subprocess  # For executing a shell command
start_time = time.time()
file_suffix = f"{datetime.now().strftime('%m%d%Y_%H%M')}"
MODE_ENCRYPT='encrypt'
MODE_DECRYPT='decrypt'

from encryption_tool import encrypt_message, decrypt_message
from cron_descriptor import get_description as get_cron_description

with open('./configs/project.json', 'r') as f:
    config = json.loads(f.read())
def strip_alphabetic_chars(string):
    return re.sub('[^0-9]', '', string)
def strip_special_chars(string):
    for x in "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~":
        string=string.replace(x,'')
    return string
def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return call(command) == 0

def write_csv(filename, rows):
    with open(filename  , 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"output file written to {filename}")
    # global_workbook.sheets.append('reports/sheets/'+filename)
def read_csv(filename):
    result = []
    with open(filename,'r', newline='', encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

        for row in spamreader:
            result.append([x for x in row])
    return  result
def obtain_db_connection(env):
    if 'service' in creds[env].keys():
        connection = cx_Oracle.connect(creds[env]['username'], decrypt_message(creds[env]['password']),
                                       cx_Oracle.makedsn(creds[env]['host'], creds[env]['port'],
                                                         service_name=creds[env]['service']))
    else:
        connection = cx_Oracle.connect(creds[env]['username'], creds[env]['password'],
                                       cx_Oracle.makedsn(creds[env]['host'], creds[env]['port'],
                                                         sid=creds[env]['sid']))
    print(f"connection obtained to {env}: {creds[env]['host']}")
    return connection

def execute_query(connection,sql, verbose=True):
    cursor = connection.cursor()
    try:
        if verbose:
            print(f"Executing\n{sql}")
        cursor.execute(sql)
        result= []
        result.append([row[0] for row in cursor.description])
        for row in cursor.fetchall():
            result.append([str(x) for x in row])
        if verbose:
            print(f"{len(result)-1} rows returned")
        cursor.close()
        return result

    except:
        cursor.close()
        traceback.print_exc()

def execute_update(connection,sql, auto_commit=True, verbose=True):
    if verbose:
        print(sql)
    cursor = connection.cursor()
    try:
        # pass
        cursor.execute(sql)

        if auto_commit:
            try:
                cursor.commit()
            except:
                pass
            connection.commit()
        cursor.close()
        pass
    except:
        cursor.close()
        traceback.print_exc()

def start_clock():
    start_time = time.time()

def stop_clock():
    print(f"\nCompleted in {int((int(time.time()) - start_time) / 60)} minutes and {int((int(time.time()) - start_time) % 60)} seconds")

def random_int_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)

def process_list_concurrently(data, process_function, batch_size):
    '''
    Process a list concurrently
    :param data: the list to process
    :param process_function: the function to pass to the multiprocessing module
    :param batch_size: the number of records to process at a time
    :return: None
    '''
    _keys = [x for x in data]
    n = batch_size
    loads = [_keys[i:i + n] for i in range(0, len(_keys), n)]
    # for load in loads:
    #     load.insert(0, data[0])
    # for load in loads:
    #     print(f"Load size: {len(load)}")
    # return
    processes = {}
    for load in loads:
        p = multiprocessing.Process(target=process_function, args=(load,))
        p.start()

        processes[str(p.pid)] = p
    pids = [x for x in processes.keys()]
    while any(processes[p].is_alive() for p in processes.keys()):
        # print(f"Waiting for {len([x for x in processes if x.is_alive()])} processes to complete. Going to sleep for 10 seconds")
        process_str = ','.join([str(v.pid) for v in processes.values() if v.is_alive()])
        print(f"The following child processes are still running: {process_str}")
        time.sleep(10)
    return pids
    # combine_outputs(pids, "extracts", f"extracts/leaver_defects_{file_suffix}.csv")

def load_module_config(module):
    print(f"Loading config file for {module}")
    with open(f"configs/{module}.json", "r") as f:
        return json.loads(f.read())
def combine_csv_reports(report1, report2, combine_key):
    '''
    Use this to add fields to reports
    :param report1:
    :param report2:
    :param combine_key:
    :return:
    '''
    #check if both have combine field

    if combine_key in report1[0] and combine_key in report2[0]:
        #add the headers first
        _added_fields=  0
        for i in range(0, len(report2[0])):
            if report2[0][i] not in report1[0]:
                report1[0].append(report2[0][i])
                _added_fields = _added_fields+1


        for i in range(1, len(report1)):
            #add the additional columns to the row

            report1[i] = report1[i]+['' for x in range(0, _added_fields)]
            for ii in range(1, len(report2)):
                if report2[ii][report2[0].index(combine_key)] == report1[i][report1[0].index(combine_key)]:
                    for iii in range(_added_fields*-1, 0):
                        report1[i][report1[0].index(report1[0][iii])]=report2[ii][report2[0].index(report1[0][iii])]
