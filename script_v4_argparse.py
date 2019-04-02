import argparse
import subprocess

#Проверка запущенных сервисов; вывод критических сервисов в оффлайн режиме.
def off_1():
    with open('/tmp/pika/crit_serv.txt') as life:
        crit_serv = life.read().split()
    command_line =["cat","/tmp/naucore"]
    call = subprocess.Popen(command_line,stdout=subprocess.PIPE)
    filet = call.communicate()
    file_in = filet[0]
    lines = file_in.split()
    n = len(lines)
    sl_out = {}
    for i in range(1,n):
        if lines[i] in crit_serv and lines[i + 2] == 'offline':
                sl_out[lines[i]] = lines[i + 2]
    if len(sl_out) < 1:
        print('There are no offline services')
    else:
        print ('Attention!!! There is offline services:')
        for ser in sl_out:
            print ser,':',sl_out[ser]

#Проверка состояния внешних sip транков                       
def off_2():

            
#Проверка количества авторизованных пользователей на шине (опционально)           
def off_3():
        
                 

parser = argparse.ArgumentParser(description='Parsing some files.')
parser.add_argument('-1','--one',help = 'offline services',action = 'store_true')
parser.add_argument('-2','--two',help = 'only critical offline services',action = 'store_true')
parser.add_argument('-3','--three',help = 'online services',action = 'store_true')
args = parser.parse_args()

if args.one:
        off_1()
elif args.two:
        #off_2()
elif args.three:
        #off_3()
else:
        print('Please see th HELP: "python test.py -h" or "python test.py --help" and try again')


