import requests
import re
import datetime
import subprocess
import logging
import os
import sqlite3


def regex_extract(pattern, string):
    #Fucntion takes a value and a regex and returns a Dictionary
    logging.info('Attempting to extract values via regex')

    try:
        pattern = re.compile(pattern)
        regex_extracted = re.search(pattern,string)
        regex_dict = regex_extracted.groupdict()
        logging.info('Successful')
        return regex_dict
    except Exception as E:
        logging.error('Regex Failed with Error: {}'.format(E))

def http_get_data(path):
    #performs get request and returns text data
    full_url = 'http://'+url+path

    logging.info('Performing GET Request on {}'.format(full_url))
    try:
        data = requests.get(full_url,auth=(user,pw))
        logging.info('Successful')
        return data.text

    except Exception as E:
        logging.error('Get Request Failed with {}'.format(E))


def Run_command(path, command):
    ##performs pst request against ddwrt command page and retruns results
    full_url = 'http://'+url+path

    logging.info('Performing custom command "{0}" via a POST Request on {1}'.format(command,full_url))

    try:
        headers_post = {'Referer':'http://{}/Diagnostics.asp'.format(url)}
        command = 'submit_button=Ping&action=ApplyTake&submit_type=start&change_action=gozila_cgi&next_page=Diagnostics.asp&ping_ip='+command.replace(' ','+')
        data = requests.post(full_url,data = command, headers=headers_post,auth=(user,pw))
        return data.text
    except Exception as E:
        logging.error('Custom Command POST Request Failed with {}'.format(E))


def db_insert(Record):
    ##Inserts Data into SQL lite Database
    logging.info('Connecting to SQLLite DB')

    try:
        connection = sqlite3.connect(os.path.join(script_path, database_name))
        cursor = connection.cursor()
        try:
            logging.info('Inserting Record into Database')

            COLUMNS = ', '.join(list(Record.keys()))
            VALUES = re.sub('([\w]+,?)',':\g<1>',COLUMNS)

            insert_statement = "INSERT INTO DDWRT_MONITOR ({0}) VALUES ({1})".format(COLUMNS,VALUES)
            cursor.execute(insert_statement,Record)
            connection.commit()
            logging.info('Record Inserted Successfully')
        except Exception as E:
            logging.error('Error Inserting Data: {}'.format(E))

        connection.close()

    except Exception as E:
        logging.error('Error Connecting to SQLite DB: {}'.format(E))




def main():

    global user, pw, url, database_name, script_path
    user = os.environ.get('DDWRT_USER')
    pw = os.environ.get('DDWRT_PW')
    url = os.environ.get('DDWRT_SERVER')

    if user == None or pw == None or url == None:
        logging.error('Environmental Variables are not set.')
        raise Exception('Environmental Variables set to None')


    database_name = 'DDWRT_MONITOR'
    script_path = os.path.dirname(__file__)

    logging.basicConfig(level=logging.ERROR, format=' %(asctime)s -  %(levelname)s -  %(message)s', filename=os.path.join(script_path, 'DD-WRT_Health_Pull.log'))

    logging.info('Initializing Script')





    DDWRT_DATA = {}

    logging.info('Capturing Current datetime')
    Current_time = datetime.datetime.now()
    DDWRT_DATA['current_time'] = Current_time.strftime('%Y-%m-%d %H:%M:%S')

    ### Fetch mem_total, mem_free, system_load_1min, system_load_5min, system_load_15min, active_connections, cpu_temp, nvram_used, nvram_total from Status Router Url ###
    Status_Router = http_get_data('/Status_Router.live.asp')

    DDWRT_DATA.update(regex_extract("('MemTotal:','(?P<mem_total>[\d]+)','[\w]+','MemFree:','(?P<mem_free>[\d]+)').*((?P<system_load_1min>[\d]+.[\d]+), (?P<system_load_5min>[\d]+.[\d]+), (?P<system_load_15min>[\d]+.[\d]+)})({ip_conntrack::(?P<active_connections>[0-9]+)}).*({cpu_temp::CPU (?P<cpu_temp>[0-9]{0,3}\.[0-9]{0,2})\s.*?}).*({nvram::(?P<nvram_used>[\d]+) KB \/ (?P<nvram_total>[\d]+) KB})",Status_Router))

    ## Fetch traffic_in and traffic_out from Status Internet Url ###
    Status_Internet = http_get_data('/Status_Internet.live.asp')
    DDWRT_DATA.update(regex_extract("{ttraff_in::(?P<traffic_in>[\d]+)}{ttraff_out::(?P<traffic_out>[\d]+)}",Status_Internet))

    ###Calcuate Uptime ###
    #Run Command via Webpage and extract results
    Uptime = Run_command('/apply.cgi', 'uptime -s')
    Uptime_Dict = regex_extract('new Array\( "(?P<uptime>[\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2})',Uptime)

    # #calcuate uptime in seconds based off current time and last reboot
    Uptime = Current_time - datetime.datetime.strptime(Uptime_Dict['uptime'],'%Y-%m-%d %H:%M:%S')
    DDWRT_DATA['uptime'] = Uptime.total_seconds()

    ## Perform Ping test from Router to Google ####
    External_Ping = Run_command('/apply.cgi', 'ping -c 10 www.google.com')

    DDWRT_DATA.update(regex_extract("(?P<external_packet_loss>[\d]+)% packet loss\"\n,\"round-trip min/avg/max = (?P<external_ping_roundtrip_min>[\d]+.[\d]+)/(?P<external_ping_roundtrip_avg>[\d]+.[\d]+)/(?P<external_ping_roundtrip_max>[\d]+.[\d]+)",External_Ping))

    ## Perform Ping test from Test machine to router ####
    ping_command = 'ping -c 10 {}'.format(url)
    logging.info('Performing internal ping command "{}"'.format(ping_command))

    try:
        Internal_Ping = subprocess.check_output(ping_command,shell=True)
        logging.info('Successful')
        DDWRT_DATA.update(regex_extract("(?P<internal_packet_loss>[\d]+)% packet loss, time [\d]+ms\nrtt min/avg/max/mdev = (?P<internal_ping_roundtrip_min>[\d]+.[\d]+)/(?P<internal_ping_roundtrip_avg>[\d]+.[\d]+)/(?P<internal_ping_roundtrip_max>[\d]+.[\d]+)",Internal_Ping.decode()))
    except Exception as E:
        logging.error('Internal ping command Failed with {}'.format(E))

    db_insert(DDWRT_DATA)



if __name__ == "__main__":
    main()
