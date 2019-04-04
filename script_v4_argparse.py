import argparse
import subprocess
import sys
import re
import os



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
    if len(sl_out) < 1:
        print('There are no offline services!')
        sys.exit(0)
    else:
        print ('There are offline services:')
        for ser in sl_out:
            print (ser,':',sl_out[ser])
        sys.exit(2)
    
#Проверка состояния внешних sip транков                       
def sip_trunk():
    out_f = []
    with open('/opt/naumen/nauphone/snmp/nausipproxy','r') as hope:
        lines = hope.read().splitlines()
    for line in lines:
        ris = re.findall(r'2[\d]{2}',line)
            if ris != []:
                out_f.append(line)
    if len(out_f) > 0:
        for ot in out_f:
            print(ot)
        sys.exit(0)
    else:
        print('There are all sip trunks have bad status')
        for line in lines:
            print(line)
        sys.exit(3)
       
#Проверка количества авторизованных пользователей на шине (опционально)           
def kolvo_oper():
    command = os.popen("sleep 1 | /opt/naumen/nauphone/bin/naucore show connections")
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
    else:
        sys.exit(1)

parser = argparse.ArgumentParser(description='Parsing some files.')
parser.add_argument('-s','--services',help = 'Check services',action = 'store_true')
parser.add_argument('-t','--trunks',help = 'Check status of sip trunks',action = 'store_true')
parser.add_argument('-u','--users',help = 'Check number of authorized users ',action = 'store_true')
args = parser.parse_args()

if args.services:
        service_stat()
elif args.trunks:
        sip_trunk()
elif args.users:
        kolvo_oper()
else:
        print('Please see th HELP: "python test.py -h" or "python test.py --help" and try again')


