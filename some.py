
"""
Модуль содержит три функции проверки сервисов для серверов Naumen Contact Center.
Код завершения работы модуля отправляется в Consul для дальнейших действий.
Информация о серверах и проверках, необходимых для этих серверов, прописана в конфигурационном файле в формате json.
Конфигурационный файл настраивается сисадмином.
Путь к файлу регистрации критичных уведомлений, а также уведомлений об ошибках, прописан также в конфигурационном файле.
Каждое уведомление имеет структуру: дата и время - главный процесс - подпроцесс - адрес сервера - сообщение.

Есть возможность запуска модуля в трех вариантах:
1. режим *Демон*,запуск модуля в фоновом режиме с повтором через некоторое время(согласно концигурационному файлу);
2. режим *Стандарт*, запуск модуля в обычном режиме, для выполнения одного прогона и завершение.
3. режим *Один-ко-одному*, запуск на определенном сервере одной из проверок.

Код завершения программы:
0 - Модуль выполнил все проверки на серверах и завершился без ошибок.
1 - При выполнении проверки возникла ошибка: отсутсвие авторизованных операторов на шине.
2 - При выполнении проверки возникла ошибка: недоступен важный критический сервис.
3 - При выполнении проверки возникла ошибка: все SIP-транки не работают.

"""
import sys, re, os
import json, os.path
import argparse, jsonschema, paramiko
import threading, logging
import time, signal

# Функция выявления статуса критических сервисов.
'''
В конфигурационном файле у каждого сервера прописан список установленных на нем критических сервисов.
Сервис naucore запускает остальные сервисы, зависящие от него. При незапуске, пытается запустить еще раз.
Информацию о наименовании и статусе сервиса хранит в текстовом файле.

Функция просматривает текстовый файл и проверяет выполнение двух условий:
1. Наличие имени сервиса в списке критических сервисов, указанном в конфигурационном файле.
2. Статус *отключен*.
Все сервисы при статусе *отключен* выводит в критичное сообщение на консоль и регистрирует уведомление в файл
регистрации критичных уведомлений.
А так же отправляет код выхода 2 в Consul для дальнейших действий.

При невыявлении недоступных критических сервисов, выводит в консоль уведомление, а также в Consul отправляется 0.

'''

def service_stat(arg,host):

    logger.debug('{} - Check services started.'.format(host))

    crit_serv = arg
    host = host
    offserv = []
    command_line ="cat /tmp/pika/naucore"
    stdin, stdout, stderr = ssh.exec_command(command_line)
    file_call = stdout.read().decode().split()
    dict_out = {}
    for i in range(1,len(file_call)):
        if file_call[i] in crit_serv and file_call[i + 2] == 'offline':
            dict_out[file_call[i]] = file_call[i + 2]

    if dict_out:
        for ser in dict_out:
            doc = ":".join([ser,dict_out[ser]])
            offserv.append(doc)
        logger.critical(f'{host} - There are offline important services!{offserv}')
        logger.debug("Thread of function services_stat{}.".format(threading.currentThread()))

        return 2

    logger.info(f'{host} - There are no offline services!')
    logger.debug("Thread of function services_stat{}.".format(threading.currentThread()))

    return 0

# Функция выявления доуступности SIP-trunkов.
'''
Сервис sipproxy
Информацию о наименовании и код статуса канала хранит в текстовом файле.
Функция просматривает построчно текстовый файл и выполняет поиск кода 2хх, что означает доступный SIP trunk.
Для удобного поиска используем метод импортируемой библиотеки re, для осуществления поиска в строке, использования
регулярных выражений.
Для поиска используется метод  re.findall, потому что у него нет ограничений на осуществления поиска в начеле строки или конце.
В конце поиска возвращает список всех совпадений, найденных в строке.

При отсутсвия каналов с таким кодом - выводит критичное сообщение на консоль и регистрирует его в файл регистрации
критичных уведомлений.
А так же отправляет код выхода 3 в Consul для дальнейших действий.
При выявлении одного и более доступных SIP trunkов, выводит адрес хоста и список SIP trunkов, а также в Consul отправляется 0.

'''

def sip_trunk(host):

    logger.debug('{} - Check sip_trunks started.'.format(host))
    host = host

    command ="cat /tmp/pika/nausipproxy "
    stdin, stdout, stderr = ssh.exec_command(command)
    file_in = stdout.read().decode().splitlines()
    out_file = []
    answ = []
    for fine in file_in:
        stat = re.findall(r'2[\d]{2}',fine)
        offstat = re.findall(r'[^2,\s][\d]{2}',fine)
        if stat != []:
            out_file.append(fine)
        elif offstat != []:
            answ.append(fine)
    if len(out_file) > 0:
        if len(answ) > 0:
            logger.info(f'{host} - There are some good sip trunks. But this are bad:{answ}')
        else:
            logger.info(f'{host} - There are all sip trunks have good status')

        logger.debug("Thread of def sip_trunk{}.".format(threading.currentThread()))

        return 0

    logger.critical(f'{host} - There are all sip trunks have bad status!{answ}')
    logger.debug("Thread of def sip_trunk{}.".format(threading.currentThread()))

    return 3

# Функция подсчета количества авторизованных операторов на шине(опционально)
'''
Выводим список подключений на сервере с помощью команды : *sleep 1 | /opt/naumen/nauphone/bin/naucore show connections*
Информация выводится на консоль.

Функция просматривает техстовый файл и выполняет поиск, основанный на использовании регулярных выражений, ключа *client*,
что означает авторизованный пользователь.

Для удобного поиска используем метод импортируемой библиотеки re, для осуществления поиска в строке, использования
регулярных выражений.
Для поиска используется метод  re.findall, потому что у него нет ограничений на осуществления поиска в начеле строки или конце.
В конце поиска возвращает список всех совпадений, найденных в строке.

При отсутсви авторизованных пользователей - выводит критичное сообщение, на консоль и регистрирует его в файл регистрации
критичных уведомлений.
А так же отправляет код выхода 1 в Consul для дальнейших действий.

При выявлении одного и более авторизованных операторов, выводит адрес хоста и количество авторизованных операторов,
а также в Consul отправляется 0.

'''

def sum_oper(host):

    logger.debug('{} - Check sum_oper started.'.format(host))
    host = host

    cmnd_line = "cat /tmp/pika/naucoreshowconnections"
    stdin, stdout, stderr = ssh.exec_command(cmnd_line)
    lines = stdout.read().decode().splitlines()
    dic_out = []
    n = 0
    for line in lines:
        oper = re.findall(r'[(]\bclient',line)
        if oper != []:
            dic_out.append(line)
            n += 1

    logger.info(f'{host} - Number of operators: {n}.')
    logger.debug("Thread of def sum_oper{}".format(threading.currentThread()))

    if n > 0:
        return 0

    logger.critical(f'{host} - There are no operators!')
    logger.debug("Thread of def sum_oper{}".format(threading.currentThread()))

    return 1

# Функция проверки файла конфигурации на наличие,правильную конструкцию, или , при отсутствии  - создания файла конфигурации.
def check_json():
    # Схема, с помощью которой производится проверка построение конфигурационного файла.
    schema = {
        "type": "object",
        "properties": {
            "is_demon":{"type": "boolean"},
            "interval":{"type": "integer"},
            "file_log":{"type":"string"},
            "servers":{
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
    # Шаблон конфигурационного файла для модуля.
    data_json = {
        "is_demon": False,
        "interval": 15,
        "file_log":"/tmp/pika/log_info.log",
        "servers": [
            {
                "server": {
                    "host": "172.16.201.101",
                    "user": "root",
                    "password": "root123",
                    "port": 22,
                    "crit_serv": [
                        "naubuddy",
                        "nautel",
                        "nausipproxy",
                        "naufileservice",
                        "naucm",
                        "nauqpm"
                    ],
                    "checks": [
                        {
                            "name": "services",
                            "command": "service_stat(arg,host)",
                            "success": False
                        },
                        {
                            "name": "sip_trunks",
                            "command": "sip_trunk(host)",
                            "success": False
                        },
                        {
                            "name": "operators",
                            "command": "sum_oper(host)",
                            "success": False
                        }
                    ]
                }
            },
            {
                "server": {
                    "host": "172.16.200.211",
                    "user": "root",
                    "password": "root123",
                    "port": 22,
                    "crit_serv": [
                        "naubuddy",
                        "nausipproxy",
                        "naufileservice",
                        "naucm",
                        "nauqpm"
                    ],
                    "checks": [
                        {
                            "name": "services",
                            "command": "service_stat(arg,host)",
                            "success": False

                       },

                       {
                            "name": "sip_trunks",
                            "command": "sip_trunk(host)",
                            "success": False
                        },
                        {
                            "name": "operators",
                            "command": "sum_oper(host)",
                            "success": False
                        }
                    ]
                }
            }
        ]
    }

    '''
    Проверка на наличие файла конфигурации. Используем метод s.path.isfile из подмодуля os.path, встроенного в библиотеку os.
    Метод проверяет наличие файла по указанному пути и возвращает булевое значение True - при наличии, False - при отсутствии.

    При присутсвии - проверка на конструкцию. Используем метод валидации библиотеки jsonschema, т.к. работаем с форматом json.
    Метод сначала проверит, что предоставленная схема сама по себе действительна, во избежание других ошибок или сбоя, а далее
    проверит необходимый объект по данной схеме.

    При отсутсвии - создание и проверки.

    '''

    try:
        if os.path.isfile("/tmp/pika/checks_script.json"):
            logger.debug('File is here')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema)
            logger.info('Checks config json is OK.')
        else:
            with open("/tmp/pika/checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
                logger.debug('Check config json now is here.')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema)
            logger.info('Checks config json is OK.')

    except jsonschema.exceptions.ValidationError:
        logger.error(f'There are some mistakes in config json.')
        logger.exception('ValidationError in json.')
        sys.exit()
    except jsonschema.exceptions.SchemaError:
        logger.error(f'There are some mistakes in shema for validation.')
        logger.exception('SchemaError in module.')
        sys.exit()

# Создание ключей, для запуска модуля режиме одной определенной проверки на определенном сервере.
'''
Использовали библиотеку argparse, импортирование которой позволяет легко описать интерфейс командной строки, а именно
описать аргументы, которые должны быть указаны, как их обработать, автоматически генерирует справочную страницу, а также
выводит сообщения и ошибки, когда пользователи используют недопустимые аргументы.

'''

def createParser():

    parser = argparse.ArgumentParser(description='Three check options.')
    parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
    parser.add_argument('-ip','--ip_add',action='append',dest='ip',help = 'Enter ip-address to connect to the server')
    args_con = parser.parse_args()

    return args_con

# Проверим на наличие файла регистрации критичных уведомлений и, если нет, создадим новый.
'''
Проверка на наличие файла регистрации критичных уведомлений. Используем метод s.path.isfile из подмодуля os.path, встроенного в библиотеку os.
Метод проверяет наличие файла по указанному пути и возвращает булевое значение True - при наличии, False - при отсутствии.
При отсутсвии - создание.

'''

def check_logFile():

    file_log = data['file_log']
    if os.path.isfile(file_log):
        logger.debug('Log file is here.')
    else:
        with open(file_log, "w") as new:
            new.write('')
        logger.debug('Now Log file created.')

    return file_log

# Создание класса потоков для запуска выполнения функций в параллельных потоках.
'''
Класс состоит из метода, выполняющего роль конструктора класса, метод описывающий функции объекта данного класса,
которые он будет иметь после его создания, метод ожидания реализации объекта,для получения результата функций объекта,
и метод завершения существования объекта.

В конструкторе описаны все обязательные поля, без которых объект класса не будет создан.
В методе функций объекта указываем функцию модуля, которую он должен реализовать.
В методе ожидания реализации объекта указываем, что необходимо дождаться окончания выполнения действий указанной функции,
описанной выше, и получить результат.

В методе завершения существования объекта указываем, что после всего выполнения и получения рехультата, закрываем поток.

Результат объекта класса - результат функции модуля.

'''

class CheckThread(threading.Thread):

    def __init__(self,cod,host,arg):

        threading.Thread.__init__(self)
        self.result = None
        self.cod = cod
        self.arg = arg
        self.host = host

    def run(self):

        arg = self.arg
        host = self.host
        self.result = eval(self.cod)
        logger.debug('Cod started.')

    def join(self, *args):

        threading.Thread.join(self)

        return self.result

    def exit(self):

        self.killed = True

# Создание класса сигналов, для прекращения выполнения модуля как демона.
'''
Класс состоит из метода, выполняющего роль конструктора класса и два метода, осуществляющего действия при определенном сигнале.
Конструктор класса содержит в себе объявленные сигналы:
1. kill -SIGTERM *pid_процесса*
2. ctrl + C

При объявлении одного из двух сигналов, прекращается работа модуля и выводится сообщение на консоль
об окончании работы модуля в связи с сигналом.

'''

class Signal_daemon:

    kill_daemon = False

    def __init__(self):

        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT,  self.KeyboardInterrupt)

    def exit_gracefully(self, signum, frame):

        self.kill_daemon = True

    def KeyboardInterrupt(self, signum, frame):

       self.kill_daemon = True

# Главная функция анализирования аргументов, указанных при запуске модуля, выполнение ssh - поключений и запуска потоков.
'''
В связи с наличием или отсутсвием аргументов, указанных при запуске модуля, зависит дальнейшая работа модуля:
с аргументами выполняется ssh - подключение к указанному серверу и выполняется только одна указанная проверка(функция),
без аргументов, подключение происходит поочередно ко всем серверам и выполнение проверок, указанным в конфигурационном файле.

'''
def main():

    global ssh
    # Вариант запуска функций, если аргументы не указаны.
    if args_con.ip is None and args_con.mode is None:
         # Считывание адреса сервера для осеществления подключения
        for i in range(len(data['servers'])):
            host = data['servers'][i]['server']['host']
            username = data['servers'][i]['server']['user']
            password = data['servers'][i]['server']['password']
            port = data['servers'][i]['server']['port']

            logger.debug('{} - SSH started.'.format(host))

            try:
                # Подключение к серверу
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
                ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

                for j in range(len(data['servers'][i]['server']['checks'])):
                    check = data['servers'][i]['server']['checks'][j]
                    if check['success'] == True:
                        cod = check['command']
                        arg = data['servers'][i]['server']['crit_serv']

                        myThread = CheckThread(cod,host,arg)
                        logger.debug('Thread started.')
                        myThread.start()

                        logger.debug('Thread stoped.')
                        result = myThread.join()

                        myThread.exit()

                        logger.debug('Thread exit.')
                        cod_out.append(result)

                    else:
                        continue
                ssh.close()
                logger.debug('{} - SSH stopped.'.format(host))

                for c in cod_out:
                    if c > 0 :
                        sys.exit(c)

            except paramiko.ssh_exception.NoValidConnectionsError:
                logger.warning("Unable to connect {}".format(host))
                logger.exception("NoValidConnectionsError(paramiko). Unable to connect {}".format(host))

    # Вариант подключения к серверу и запуска функции, если аргументы указаны.
    elif args_con.ip is not None and args_con.mode is not None :

        tor = args_con.ip[0]
        # Считывание адреса сервера для осеществления подключения
        for i in range(len(data['servers'])):
            if tor == data['servers'][i]['server']['host']:
                host = data['servers'][i]['server']['host']
                username = data['servers'][i]['server']['user']
                #password = data['servers'][i]['server']['password']
                port = data['servers'][i]['server']['port']

                logger.debug('{} - SSH started.'.format(host))

                try:
                    # Подключение к серверу
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
                    ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

                    for j in range(len(data['servers'][i]['server']['checks'])):
                        checks = data['servers'][i]['server']['checks'][j]
                        if args_con.mode == checks['name']:
                            lis.append(args_con.mode)
                            cod = checks['command']
                            arg = data['servers'][i]['server']['crit_serv']

                            myThread = CheckThread(cod,host,arg)
                            logger.debug('Thread started.')
                            myThread.start()

                            logger.debug('Thread stoped.')
                            result = myThread.join()

                            myThread.exit()

                            logger.debug('Thread exit.')
                            cod_out.append(result)

                        else:
                            continue

                    ssh.close()
                    logger.debug('{} - SSH stopped.'.format(host))

                except paramiko.ssh_exception.NoValidConnectionsError:
                    logger.warning("Unable to connect {}".format(host))
                    logger.exception("NoValidConnectionsError(paramiko). Unable to connect {}".format(host))

                if args_con.mode not in lis:
                    logger.info(f'{host} - Check is not founded.')
    else:
        logger.info('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')

    return cod_out

#Действия, если модуль запущен
'''
Подключение логирование.
Настройка вывода сообщения в консоль.
Считывание аргументов.
Проверка конфигурационного файла.
Настройка вывода сообщения в файл.
Запуск прослушивания сигнала остановки.
Проверка режима запуска.
Запуск главной функции.
Возвращение кода выхода ( 1 - 2 - 3 - 0 )
'''

if __name__ == '__main__':

    try:
        logger = logging.getLogger (__name__)
        logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S %d.%m.%Y')
        console.setFormatter(formatter)

        logger.addHandler(console)

        args_con = createParser()
        check_json()

        with open("/tmp/pika/checks_script.json","r")as lafa:
            data = json.load(lafa)

        file_logger = check_logFile()
        fil_hand = logging.FileHandler(file_logger, mode = "a")
        fil_hand.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S %d.%m.%Y')

        fil_hand.setFormatter(formatter)
        logger.addHandler(fil_hand)

        cod_out = []
        lis = []

        signal = Signal_daemon()

        while data['is_demon'] == True:
            cod_out = main()

            logger.info('Programm sleep {}'.format(data['interval']))
            time.sleep(data['interval'])
            if signal.kill_daemon:
                logger.warning('The program is closed by a signal.')
                break
        else:
            cod_out = main()
            logger.info('Complete!')

        for c in cod_out:
            if c > 0 :
                sys.exit(c)

        sys.exit(0)

    except KeyError:
        logger.error("There are some mistakes in config json, module doesn't find key.")
        logger.exception("KeyError")
    except FileNotFoundError:
        logger.error("No such file or directory.")
        logger.exception("FileNotFoundError")
    except json.decoder.JSONDecodeError:
        logger.error("There are some mistakes in config json, module mustn't read check_script.json")
        logger.exception("JSONDecodeError")
    except KeyboardInterrupt:
        logger.error("Module suspended by KeyboardInterrupt")
        logger.exception("KeyboardInterrupt")
    except TimeoutError:
        logger.error("Connection timed out")
        logger.exception("TimeoutError")
    except paramiko.ssh_exception.SSHException:
        logger.error("Error reading SSH protocol banner")
        logger.exception("Time to connect timed out")
    except Exception:
        logger.error("Oh, new error")
        logger.exception("Error")
    except:
        logger.exception("sys")
