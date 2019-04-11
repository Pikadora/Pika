import subprocess
import sys, re, os
import json, os.path
import argparse
import jsonschema
import traceback



#Проверка запущенных сервисов; вывод критических сервисов в оффлайн режиме.
def service_stat():
    crit_serv = ["naubuddy", "nautel", "nausipproxy",  "naufileservice", "naucm", "nauqpm"]
    command_line =["cat","/tmp/naucore"]
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
    with open('C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\nausipproxy.txt','r') as hope:
        lines = hope.read().splitlines()
    for line in lines:
        ris = re.findall(r'2[\d]{2}',line)
        if ris != []:
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
        res = re.findall(r'[(]\bclient',com)
        if len(res) > 0:
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

    # json файл
    data_json = {
        "checks": [
            {
                "name": "services",
                "command": "service_stat()",
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
    try:
        if os.path.isfile('C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\checks_script.json'):#проверка на имеющийся файл json
            print('File is here')
            # считывание проверяемого json файла
            with open("C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema) #проверка входных данных с помощью jsonschema
            print('Check is OK')
        else:
            # создание json файла
            with open("C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
            print('ya sozdal!')
    except jsonschema.exceptions.ValidationError:
         print('Ошибка в типе значений json файла:\n', traceback.format_exc())


def check():
    # проверка json файла
    check_json()
    #если аргумента нет - вывод подсказки обратиться в помощь
    if args_con.mode is None :
        print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')
        return
    #если аргумента объявлен - проверить проверку на включенность
    with open('C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\checks_script.json','r')as lafa:
        data = json.load(lafa)
    for i in range(len(data['checks'])):
        wtfk = data['checks'][i]
        #если обьявленный аргумент имеет имя проверки и она включена (имеет значение успеха - true):
        if args_con.mode == wtfk['name']:
            if data['checks'][i]['success'] == True:
                cod = data['checks'][i]['command']
                # выполнить проверку
                exec(cod)
            else:
                print('Please see the config_file (check success true/false)')
        else:
            continue





parser = argparse.ArgumentParser(description='Three check options.')
parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
args_con = parser.parse_args()

check()



