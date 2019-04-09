import subprocess
import sys, re, os
import argparse
import json




#Проверка запущенных сервисов; вывод критических сервисов в оффлайн режиме.
def service_stat():
    crit_serv = ["naubuddy", "nautel", "nausipproxy",  "naufileservice", "naucm", "nauqpm"]#список критических сервисов
    command_line =["cat","/tmp/naucore"]
    call = subprocess.Popen(command_line,stdout=subprocess.PIPE) #создание процесса запуска команды просмотра файла состояний процессов 
    filet = call.communicate()
    file_in = filet[0].decode()
    lines = file_in.split()
    sl_out = {}
    for i in range(1,len(lines)):
        if lines[i] in crit_serv and lines[i + 2] == 'offline': # поиск оффлайн сервисов и есть ли среди них критические
            sl_out[lines[i]] = lines[i + 2]
    if len(sl_out) < 1: 
        print('There are no offline services!') 
        sys.exit(0) #вывод код завершения 0 - ошибок не найдено
    else:
        print ('There are offline services:')
        for ser in sl_out:
            print (ser,':',sl_out[ser]) #вывод: имена критических сервисов в оффлайн режиме
            sys.exit(2) #вывод код завершения 2 - критичный сервис недоступен
    
#Проверка состояния внешних sip транков                       
def sip_trunk():
    out_f = []
    with open('/opt/naumen/nauphone/snmp/nausipproxy','r') as hope:
        lines = hope.read().splitlines() #считывание файла 
    for line in lines:
        ris = re.findall(r'2[\d]{2}',line) #поиск кода, начинающегося на 2
        if ris != []:
            out_f.append(line)
    if len(out_f) > 0:
        for ot in out_f: 
            print(ot) #вывод работающих успешных транков
        sys.exit(0) #вывод код завершения 0 - ошибок не найдено
    else:
        print('There are all sip trunks have bad status')
        for line in lines:
            print(line)  # вывод всех неработающих транков, т.к. ни одного работающего нет.
        sys.exit(3)  #вывод код завершения 3 - SIP-транки не работают
       
#Проверка количества авторизованных пользователей на шине (опционально)           
def kolvo_oper():
    command = os.popen("sleep 1 | /opt/naumen/nauphone/bin/naucore show connections") #выполнение команды 
    slov_out = []
    n = 0
    for com in command:
        res = re.findall(r'[(]\bclient',com) #поиск операторов .client
        if len(res) > 0:
            slov_out.append(com)
            n += 1 #подсчет количества операторов
    print('Number of operators: ',n) # вывод количества операторов
    if n > 0:
        for i in range(len(slov_out)):
            print (slov_out[i]) #вывод списка операторов
        sys.exit(0)  #вывод код завершения 0 - ошибок не найдено
    else:
        sys.exit(1) #вывод код завершения 1 - отсутсвуют операторы
   

parser = argparse.ArgumentParser(description='Three check options.') #создание ключей и аргументов
parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
args_con = parser.parse_args()


if args_con.mode is None :
    print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again') #если нет ключей - подсказка отправит в справку

else:
    with open('/tmp/pika/checks.json','r')as lafa:
        data = json.load(lafa) #считывание json файла вкл/выкл проверок
        for i in range(len(data['checks'])):
            wtfk = data['checks'][i]
            if args_con.mode == wtfk['name']: #если аргумент ключа есть в проверках
                if data['checks'][i]['success'] == 'true': #если включена проверка
                    cod = data['checks'][i]['command'] #считывание функции проверки
                    exec(cod) # запуск функции
                else:
                    print('Please see the config_file (check success true/false)') # значит поверка отключена false и необходимо просмотреть json файл
            else:
                continue





        
