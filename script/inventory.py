#!/usr/bin/python3
# python script that fetch data from observium/LibreNMS DB and forms inventory files for the following ansible play

import argparse
import mysql.connector
from prettytable import PrettyTable
from nmsargs import creds, nms, query_device_tpl, query_unused_ports_tpl

parser = argparse.ArgumentParser(description="finds unused ports on a given switch")
parser.add_argument('-H','--hostname', help="switch's hostname",required=True)
parser.add_argument('-D','--days',help='days ports being unused', required=True)
parser.add_argument('-A','--ansible',help='create ansible inventory file for farther network automation operations (no output to stdout)', required=False, action='store_true')
args = parser.parse_args()

hostname = args.hostname
days = args.days
ansible = args.ansible

try:
    cnx = mysql.connector.connect(**creds)
    cursor = cnx.cursor()
    query_device = query_device_tpl.format(hostname)
    cursor.execute(query_device)
    res=cursor.fetchone()

    try:
        device_id=int(res[0])
        print("device_id={}".format(device_id))
    except TypeError:
        print ("""
Error:
there is no hostname -- {} -- found in Observium's database
----------------------------------------------------------------""".format(hostname))
        exit(0)

    query_unused_ports = query_unused_ports_tpl[nms].format(device_id, days)
    cursor.execute(query_unused_ports)
    res=cursor.fetchall()

    if ansible:
        filename='host_vars/' + hostname + '.yml'

        with open(filename, 'w') as w:
            w.write("interfaces:\n")

            for row in res:
                ifDesc = row[0]
                ansible_var="  - " + ifDesc + "\n"
                w.write(ansible_var) 

    else:
        t = PrettyTable(['ifDesc','ifLastChange'])

        try:
            for row in res:
                ifDesc,LastChange = row
                l=[ifDesc,LastChange]
                t.add_row(l)

            print(t)

        except TypeError:
            print("""
Seems like all enabled ports on the switch -- {} -- were being used at least once in last {} days
-------------------------------------------------------------------------------------------------""".format(hostname,days))


except mysql.connector.Error as e :
    print("Error while connecting to MySQL", e)

finally:
    if(cnx.is_connected()):
        cnx.close()
        print("connection is closed")


