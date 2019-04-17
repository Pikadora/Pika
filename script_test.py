import subprocess
import sys, re, os
import json, os.path
import argparse
import jsonschema
import traceback
import paramiko

def service_stat(arg):
    crit_serv = arg
    command_line =["cat","/opt/naumen/nauphone/snmp/naucore"]
    call = subprocess.Popen(command_line,stdout=subprocess.PIPE)
    file_call = call.communicate()
    file_in = file_call[0].decode()
    lines = file_in.split()
    dict_out = {}
    for i in range(1,len(lines)):
        if lines[i] in crit_serv and lines[i + 2] == 'offline':
            dict_out[lines[i]] = lines[i + 2]
    if dict_out:
        print ('There are offline services:')
        for ser in dict_out:
            print (ser,':',dict_out[ser])
        return (2)

    print('There are no offline services!')
    return (0)

def sip_trunk():
    out_file = []
    with open("/opt/naumen/nauphone/snmp/nausipproxy","r") as fil:
        fines = fil.read().splitlines()
    for fine in fines:
        stat = re.findall(r'2[\d]{2}',fine)
        if stat != []:
            out_file.append(fine)
    if len(out_file) > 0:
        for ot in out_file:
            print(ot)
        return (0)

    print('There are all sip trunks have bad status')
    for fine in fines:
        print(fine)
    return (3)

def kolvo_oper():
    command = subprocess.Popen("sleep 1 | /opt/naumen/nauphone/bin/naucore show connections",shell = True,stdout = subprocess.PIPE).stdout
    dic_out = []
    n = 0
    for com in command:
        oper = re.findall(r'[(]\bclient',com)
        if oper != []:
            dic_out.append(com)
            n += 1
    print('Number of operators: ',n)
    if n > 0:
        for i in range(len(dic_out)):
            print (dic_out[i])
        return (0)

    return (1)

def check_json():
    schema = {
        "type": "object",
        "properties": {
                "service":{
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "server":{
                                "type":"object",
                                "properties": {
                                    "host": {"type": "string"},
                                    "user": {"type": "string"},
                                    "password": {"type": "string"},
                                    "port": {"type": "integer"},
                                    "crit_serv": {
                                        "type": "array",
                                        "items": {
                                            "type":"string"
                                        }
                                    },
                                    "checks": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "command": {"type": "string"},
                                                "success": {"type": "boolean"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
        }
    }

    data_json = {
        "servers": [
            {
                "server":
                    {
                        "host": "192.168.56.101",
                        "user": "root",
                        "password": "root123",
                        "port": 22,
                        "crit_serv": ["naubuddy","nautel","nausipproxy","naufileservice","naucm","nauqpm"],
                        "checks": [
                            {
                                "name": "services",
                                "command": "service_stat(arg)",
                                "success": False
                            },
                            {
                                "name": "sip_trunks",
                                "command": "sip_trunk()",
                                "success": True
                            },
                            {
                                "name": "operators",
                                "command": "kolvo_oper()",
                                "success": False
                            }
                        ]
                    }
                }
            ]
        }

    try:
        if os.path.isfile("/tmp/pika/checks_script.json"):
            print('File is here')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema)
            print('Check_json is OK')
        else:
            with open("/tmp/pika/checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
            print('Check_json now is here')
    except jsonschema.exceptions.ValidationError:
        print('json file:\n', traceback.format_exc())

def createParser():
    parser = argparse.ArgumentParser(description='Three check options.')
    parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
    parser.add_argument('-ip','--ip_add',action='append',dest='ip',help = 'Enter ip-address to connect to the server')
    args_con = parser.parse_args()

    return args_con

def main():
    args_con = createParser()
    check_json()
    lis = []
    with open("/tmp/pika/checks_script.json","r")as lafa:
        data = json.load(lafa)

    for i in range(len(data['servers'])):

        host = data['servers'][i]['server']['host']
        username = data['servers'][i]['server']['user']
        #password = data['servers'][i]['server']['password']
        port = data['servers'][i]['server']['port']


        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        privkey = paramiko.RSAKey.from_private_key_file('/root/.ssh/id_rsa')
        ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

        for j in range(len(data['servers'][i]['server']['checks'])):
            check = data['servers'][i]['server']['checks'][j]
            if check['success'] == True:
                cod = check['command']
                arg = data['servers'][i]['server']['crit_serv']
                cod_out = exec(cod)
                if cod_out == "2":
                    sys.exit(2)
                elif cod_out == "3":
                    sys.exit(3)
                elif cod_out == "1":
                    sys.exit(1)

        ssh.close()
    sys.exit(0)


main()
