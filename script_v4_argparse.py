import argparse
import subprocess
import sys
import re



#Проверка запущенных сервисов; вывод критических сервисов в оффлайн режиме.
def service_stat():
    with open('/tmp/pika/crit_serv.txt') as life:
        crit_serv = life.read().split()
    command_line =["cat","/tmp/naucore"]
    call = subprocess.Popen(command_line,stdout=subprocess.PIPE)
    filet = call.communicate()
    file_in = filet[0]
    lines = file_in.split()
    sl_out = {}
    for i in range(1,len(lines)):
        if lines[i] in crit_serv and lines[i + 2] == 'offline':
                sl_out[lines[i]] = lines[i + 2]
    if len(sl_out) < 1:
        print('There are no offline services')
        sys.exit(0)
    else:
        print ('Attention!!! There is offline services:')
        for ser in sl_out:
            print ser,':',sl_out[ser]
        sys.exit(2)
#Проверка состояния внешних sip транков                       
def sip_trunk():
    #sys.exit(3)
            
#Проверка количества авторизованных пользователей на шине (опционально)           
def kolvo_oper():
    with open('/tmp/pika/users.txt','r') as fol:
        users = fol.read().splitlines()
        print (users)
        slov_out = []
        for user in users:
                res = re.findall(r'\bclient',user)
                if len(res) > 0:
                        slov_out.append(user)
        if slov_out != '':
            for i in range(len(slov_out)):
                print slov_out[i]
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
        #sip_trunk()
elif args.users:
        #kolvo_oper()
else:
        print('Please see th HELP: "python test.py -h" or "python test.py --help" and try again')


