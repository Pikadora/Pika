import subprocess
import sys, re, os
import json, os.path
import argparse
import jsonschema
import traceback
import paramiko

#Проверка запущенных сервисов; вывод критических сервисов в оффлайн режиме.
def service_stat(arg):
    crit_serv = arg
    command_line =["cat","/opt/naumen/nauphone/snmp/naucore"]
    call = subprocess.Popen(command_line,stdout=subprocess.PIPE)
    filet = call.communicate()
    file_in = filet[0].decode()
    lines = file_in.split()
    sl_out = {}
    for i in range(1,len(lines)):
        if lines[i] in crit_serv and lines[i + 2] == 'offline':
            sl_out[lines[i]] = lines[i + 2]
    if sl_out:
        print ('There are offline services:')
        for ser in sl_out:
            print (ser,':',sl_out[ser])
        sys.exit(2)

    print('There are no offline services!')
    sys.exit(0)

#Проверка состояния внешних sip транков
def sip_trunk():
    out_f = []
    with open("/opt/naumen/nauphone/snmp/nausipproxy","r") as fi:
        lines = fi.read().splitlines()
    for line in lines:
        stat = re.findall(r'2[\d]{2}',line)
        if stat != []:
            out_f.append(line)
    if len(out_f) > 0:
        for ot in out_f:
            print(ot)
        sys.exit(0)

    print('There are all sip trunks have bad status')
    for line in lines:
        print(line)
    sys.exit(3)

#Проверка количества авторизованных пользователей на шине (опционально)
def kolvo_oper():
    command = subprocess.Popen("sleep 1 | /opt/naumen/nauphone/bin/naucore show connections",shell = True,stdout = subprocess.PIPE).stdout
    slov_out = []
    n = 0
    for com in command:
        oper = re.findall(r'[(]\bclient',com)
        if len(oper) > 0:
            slov_out.append(com)
            n += 1
    print('Number of operators: ',n)
    if n > 0:
        for i in range(len(slov_out)):
            print (slov_out[i])
        sys.exit(0)

    sys.exit(1)
# проверка json файла
def check_json():
    # схема проверки json файла
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
 # json файл
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
        #проверка на имеющийся файл json
        if os.path.isfile("/tmp/pika/checks_script.json"):
            print('File is here')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            #проверка входных данных с помощью jsonschema
            jsonschema.validate(numb, schema)
            print('Check_json is OK')
        else:
            # создание json файла
            with open("/tmp/pika/checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
            print('Check_json now is here')
    except jsonschema.exceptions.ValidationError:
        print('json file:\n', traceback.format_exc()) # !!!

# создание ключей запуска скрипта
def createParser():
    parser = argparse.ArgumentParser(description='Three check options.')
    parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
    parser.add_argument('-ip','--ip_add',action='append',dest='ip',help = 'Enter ip-address to connect to the server')
    args_con = parser.parse_args()

    return args_con

# главная
def main():
    # считывание аргументов
    args_con = createParser()
    # проверка json файла
    check_json()
    lis = []
    with open("/tmp/pika/checks_script.json","r")as lafa:
        data = json.load(lafa)

    for i in range(len(data['servers'])):
        # наличие ключей при запуске скрипта
        if args_con.ip is None:
            print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')
            return

        elif args_con.mode is None:
            print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')
            return
        tor = args_con.ip[0]
        # ssh подключение к серверу
        if tor == data['servers'][i]['server']['host']:
            host = data['servers'][i]['server']['host']
            username = data['servers'][i]['server']['user']
            password = data['servers'][i]['server']['password']
            port = data['servers'][i]['server']['port']

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=username, password=password, port=port)

            # смотрим какие проверки на этом сервере включены
            for j in range(len(data['servers'][i]['server']['checks'])):
                wtfk = data['servers'][i]['server']['checks'][j]
                if args_con.mode == wtfk['name']:
                    lis.append(args_con.mode)
                    if wtfk['success'] == True:
                        cod = wtfk['command']
                        if cod == 'service_stat(arg)':
                            arg = data['servers'][i]['server']['crit_serv']
                        # выполнение ф-ции
                        exec(cod)
                    else:
                        print('Please see the config_file (check success true/false)')
                else:
                    continue
        else:
            continue

        if args_con.mode not in lis:
            print('Check is not founded')

main()
