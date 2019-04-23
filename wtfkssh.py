import subprocess
import sys, re, os
import json, os.path
import argparse
import jsonschema
import traceback
import paramiko
import threading

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
        return 20

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

def sum_oper():

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
        return 0

    return 100

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
                        "host": "172.16.201.18",
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
                                "command": "sum_oper()",
                                "success": True
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

class CheckThread(threading.Thread):

    def init(self,cod):
        
        self.result = None
        threading.Thread.init(self)

    def run(self):

        if cod == 'service_stat(arg)':
            arg = data['servers'][i]['server']['crit_serv']
        self.result = eval(cod)

    def join(self, *args):
        
        threading.Thread.join(self)
        return self.result

if __name__ == '__main__':

    args_con = createParser()
    check_json()

    cod_out = []
    lis = []

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
                    myThread = CheckThread()
                    myThread.start()

                    result = myThread.join()
                    cod_out.append(result)
                else:
                    continue

            ssh.close()
    

    elif args_con.ip is not None and args_con.mode is not None :

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
                        cod = wtfk['command']
                        myThread = CheckThread()
                        myThread.start()

                        result = myThread.join()
                        cod_out.append(result)
                   else:
                        continue

                ssh.close()

        if args_con.mode not in lis:
            print('Check is not founded')

    else:
        print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')

    for c in cod_out:
        n = int(c)
        sys.exit(c)
                                                     
