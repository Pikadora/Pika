import subprocess
import sys, re, os
import json, os.path
import argparse
import jsonschema
import traceback
import paramiko



def service_stat(arg):

    crit_serv = arg
    command_line ="cat /opt/naumen/nauphone/snmp/naucore"
    stdin, stdout, stderr = ssh.exec_command(command_line)
    file_call = stdout.read().decode().split()
    dict_out = {}
    for i in range(1,len(file_call)):
        if file_call[i] in crit_serv and file_call[i + 2] == 'offline':
            dict_out[file_call[i]] = file_call[i + 2]
    if dict_out:
        print ('There are offline services:')
        for ser in dict_out:
            print (ser,':',dict_out[ser])
        return 2

    print('There are no offline services!')
    return 0

def sip_trunk():

    cmnd_line ="cat /opt/naumen/nauphone/snmp/nausipproxy "
    stdin, stdout, stderr = ssh.exec_command(cmnd_line)
    file_in = stdout.read().decode().splitlines()
    out_file = []
    #with open("/tmp/pika/nausipproxy","r") as fil:
        #fines = fil.read().splitlines()
    for fine in file_in:
        stat = re.findall(r'2[\d]{2}',fine)
        if stat != []:
            out_file.append(fine)
    if len(out_file) > 0:
        for ot in out_file:
            print(ot)
        return 0

    print('There are all sip trunks have bad status')
    for fine in file_in:
        print(fine)
    return 3

def kolvo_oper():

    cmnd_line = "sleep 1 | /opt/naumen/nauphone/bin/naucore show connections"
    stdin, stdout, stderr = ssh.exec_command(cmnd_line)
    lines = stdout.read().decode().splitlines()
    dic_out = []
    n = 0
    for line in lines:
        oper = re.findall(r'[(]\bclient',line)
        if oper != []:
            dic_out.append(line)
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
                        "host": "172.16.200.250",
                        "user": "root",
                        "password": "root123",
                        "port": 22,
                        "crit_serv": ["naubuddy","nautel","nausipproxy","naufileservice","naucm","nauqpm"],
                        "checks": [
                            {
                                "name": "services",
                                "command": "service_stat(arg)",
                                "success": True
                            },
                            {
                                "name": "sip_trunks",
                                "command": "sip_trunk()",
                                "success": True
                            },
                            {
                                "name": "operators",
                                "command": "kolvo_oper()",
                                "success": True
                            }
                        ]
                    }
                }
            ]
        }

def createParser():

    parser = argparse.ArgumentParser(description='Three check options.')
    parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
    parser.add_argument('-ip','--ip_add',action='append',dest='ip',help = 'Enter ip-address to connect to the server')
    args_con = parser.parse_args()

    return args_con

def keys_check ():

    tor = args_con.ip[0]
    for i in range(len(data['servers'])):
        if tor == data['servers'][i]['server']['host']:
            host = data['servers'][i]['server']['host']
            username = data['servers'][i]['server']['user']
            #password = data['servers'][i]['server']['password']
            port = data['servers'][i]['server']['port']
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
            ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

            for j in range(len(data['servers'][i]['server']['checks'])):
                wtfk = data['servers'][i]['server']['checks'][j]
                if args_con.mode == wtfk['name']:
                    lis.append(args_con.mode)
                    if wtfk['success'] == True:
                        cod = wtfk['command']
                        if cod == 'service_stat(arg)':
                            arg = data['servers'][i]['server']['crit_serv']
                        cod_key = eval(cod)
                    else:
                        print('Please see the config_file (check success true/false)')
                else:
                    continue



            ssh.close()
    return cod_key


if __name__ == "__main__":

    args_con = createParser()
    check_json()


    with open("/tmp/pika/checks_script.json","r")as lafa:
        data = json.load(lafa)

    if args_con.ip is None and args_con.mode is None:
        for i in range(len(data['servers'])):
            host = data['servers'][i]['server']['host']
            username = data['servers'][i]['server']['user']
            #password = data['servers'][i]['server']['password']
            port = data['servers'][i]['server']['port']

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
            ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

            for j in range(len(data['servers'][i]['server']['checks'])):
                check = data['servers'][i]['server']['checks'][j]
                if check['success'] == True:
                    cod = check['command']
                    arg = data['servers'][i]['server']['crit_serv']
                    cod_out = eval(cod)

            ssh.close()
    elif args_con.ip is not None and args_con.mode is not None :
        cod_out = keys_check()

    else:
        print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')

    if cod_out == "2":
        sys.exit(2)
    elif cod_out == "3":
        sys.exit(3)
    elif cod_out == "1":
        sys.exit(1)
    else:
        sys.exit(0)
