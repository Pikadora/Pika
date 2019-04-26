import sys, re, os
import json, os.path
import argparse, jsonschema, paramiko
import threading, logging
import time, signal
import socket

def service_stat(arg):

    logger.debug('Check services started')

    crit_serv = arg
    command_line ="cat /opt/naumen/nauphone/snmp/naucore"
    stdin, stdout, stderr = ssh.exec_command(command_line)
    file_call = stdout.read().decode().split()
    dict_out = {}
    for i in range(1,len(file_call)):
        if file_call[i] in crit_serv and file_call[i + 2] == 'offline':
            dict_out[file_call[i]] = file_call[i + 2]

    if dict_out:

        logger.critical(f'There are offline important services!{dict_out.items()}')
        logger.debug("thread of def services_stat{}".format(threading.currentThread()))

        for ser in dict_out:
            print(ser,':',dict_out[ser])
        return 2

    logger.info('There are no offline services!')
    return 0
    
def sip_trunk():

    logger.debug('Check sip_trunks started')

    command ="cat /opt/naumen/nauphone/snmp/nausipproxy "
    stdin, stdout, stderr = ssh.exec_command(command)
    file_in = stdout.read().decode().splitlines()
    out_file = []
    for fine in file_in:
        stat = re.findall(r'2[\d]{2}',fine)
        if stat != []:
            out_file.append(fine)
    if len(out_file) > 0:
        for ot in out_file:
            print(ot)

        logger.info('There are some good sip_trunks.')
        return 0

    logger.critical(f'There are all sip trunks have bad status!{file_in}')
    logger.debug("thread of def sip_trunk{}".format(threading.currentThread()))
    for fine in file_in:
        print(fine)
    return 3
    
def sum_oper():

    logger.debug('Check sum_oper started')

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

    logger.info(f'Number of operators: {n}')
    if n > 0:
        for i in range(len(dic_out)):
            print (dic_out[i])
        return 0

    logger.critical(f'There are no operators!')
    logger.debug("thread of def sum_oper{}".format(threading.currentThread()))
    return 1
    
def check_json():

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

    data_json = {
        "is_demon": true,
        "interval": 15,
        "file_log":"/tmp/pika/log_info.log",
        "servers": [
            {
                "server": {
                    "host": "172.16.201.18",
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
                            "command": "service_stat(arg)",
                            "success": true
                        },
                        {
                            "name": "sip_trunks",
                            "command": "sip_trunk()",
                            "success": true
                        },
                        {
                            "name": "operators",
                            "command": "sum_oper()",
                            "success": true
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
                            "command": "service_stat(arg)",
                            "success": true
                        },
                        {
                            "name": "sip_trunks",
                            "command": "sip_trunk()",
                            "success": true
                        },
                        {
                            "name": "operators",
                            "command": "sum_oper()",
                            "success": true
                        }
                    ]
                }
            }
        ]
    }

    try:
        if os.path.isfile("/tmp/pika/checks_script.json"):
            logger.debug('File is here')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema)
            logger.info('Checks_json is OK')
        else:
            with open("/tmp/pika/checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
                logger.debug('Check_json now is here')
                numb = json.load(spr)
            jsonschema.validate(numb, schema)
            logger.info('Checks_json is OK')

    except jsonschema.exceptions.ValidationError:
        logger.error(f'There are some mistakes in check_script.json')
        logger.exception('ValidationError in json')
        sys.exit()

def createParser():

    parser = argparse.ArgumentParser(description='Three check options.')
    parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
    parser.add_argument('-ip','--ip_add',action='append',dest='ip',help = 'Enter ip-address to connect to the server')
    args_con = parser.parse_args()

    return args_con

def check_logFile():

    file_log = data['file_log']

    if os.path.isfile(file_log):
        logger.debug('log_file is here.')
    else:
        with open(file_log, "w") as new:
            new.write('')
        logger.debug('Now log_file is here.')

    return file_log

class CheckThread(threading.Thread):

    def __init__(self,cod,arg):

        threading.Thread.__init__(self)
        self.result = None
        self.cod = cod
        self.arg = arg

    def run(self):

        if self.cod == 'service_stat(arg)':
            arg = self.arg
        self.result = eval(self.cod)
        logger.debug('Cod started.')

    def exit(self):
        self.killed = True

    def join(self, *args):

        threading.Thread.join(self)

        return self.result

class Signal_daemon:

    kill_daemon = False

    def __init__(self):

        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT,  self.KeyboardInterrupt)

    def exit_gracefully(self, signum, frame):

        self.kill_daemon = True

    def KeyboardInterrupt(self, signum, frame):

       self.kill_daemon = True

def main():

    if args_con.ip is None and args_con.mode is None:

        for i in range(len(data['servers'])):
            host = data['servers'][i]['server']['host']
            username = data['servers'][i]['server']['user']
            #password = data['servers'][i]['server']['password']
            port = data['servers'][i]['server']['port']

            file_logger = check_logFile()

            fil_hand = logging.FileHandler(file_logger, mode = "w")
            fil_hand.setLevel(logging.WARNING)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fil_hand.setFormatter(formatter)
            logger.addHandler(fil_hand)

            logger.debug('ssh started.')

            try:

                global ssh

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
                ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

                for j in range(len(data['servers'][i]['server']['checks'])):
                    check = data['servers'][i]['server']['checks'][j]
                    if check['success'] == True:
                        cod = check['command']
                        if cod == 'service_stat(arg)':
                            arg = data['servers'][i]['server']['crit_serv']

                        myThread = CheckThread(cod,arg)
                        logger.debug('thread started.')
                        myThread.start()

                        logger.debug('thread stoped.')
                        result = myThread.join()

                        myThread.exit()

                        logger.debug('thread exit.')
                        cod_out.append(result)

                    else:
                        continue

                ssh.close()
                logger.debug('ssh stopped.')

            except paramiko.ssh_exception.NoValidConnectionsError:
                logger.error("Unable to connect")
                logger.exception("NoValidConnectionsError(paramiko)")

    elif args_con.ip is not None and args_con.mode is not None :

        tor = args_con.ip[0]
        for i in range(len(data['servers'])):
            if tor == data['servers'][i]['server']['host']:
                host = data['servers'][i]['server']['host']
                username = data['servers'][i]['server']['user']
                #password = data['servers'][i]['server']['password']
                port = data['servers'][i]['server']['port']

                file_logger = check_logFile()

                fil_hand = logging.FileHandler(file_logger, mode = "w")
                fil_hand.setLevel(logging.WARNING)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                fil_hand.setFormatter(formatter)
                logger.addHandler(fil_hand)

                logger.debug('ssh started.')

                try:

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
                    ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

                    for j in range(len(data['servers'][i]['server']['checks'])):
                        wtfk = data['servers'][i]['server']['checks'][j]
                        if args_con.mode == wtfk['name']:
                            lis.append(args_con.mode)
                            cod = wtfk['command']
                            if cod == 'service_stat(arg)':
                                arg = data['servers'][i]['server']['crit_serv']

                            myThread = CheckThread(cod,arg)
                            logger.debug('thread started.')
                            myThread.start()

                            logger.debug('thread stoped.')
                            result = myThread.join()

                            myThread.exit()

                            logger.debug('thread exit.')
                            cod_out.append(result)

                        else:
                            continue

                    ssh.close()
                    logger.debug('ssh stopped.')

                except paramiko.ssh_exception.NoValidConnectionsError:
                    logger.error("Unable to connect")
                    logger.exception("NoValidConnectionsError(paramiko)")


                if args_con.mode not in lis:
                    logger.info('Check is not founded')

    else:
        logger.info('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')

    return cod_out

if __name__ == '__main__':

    try:
        logger = logging.getLogger (__name__)
        logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)

        logger.addHandler(console)

        args_con = createParser()
        check_json()

        cod_out = []
        lis = []

        signal = Signal_daemon()

        with open("/tmp/pika/checks_script.json","r")as lafa:
            data = json.load(lafa)

        while data['is_demon'] == True:
            cod_out = main()
            logger.info('Programm sleep {}'.format(data['interval']))
            time.sleep(data['interval'])
            if signal.kill_daemon:
                logger.info('The program is closed by a signal')
                break
        else:
            cod_out = main()
            logger.info('Complete!')

        for c in cod_out:
            if c > 0 :
                n = c
                sys.exit(n)

        sys.exit(0)

    except KeyError:
        logger.error("There are some mistakes in check_script.json, module doesn't find key")
        logger.exception("KeyError")
    except FileNotFoundError:
        logger.error("No such file or directory")
        logger.exception("FileNotFoundError")
    except json.decoder.JSONDecodeError:
        logger.error("There are some mistakes in check_script.json, module mustn't read check_script.json")
        logger.exception("JSONDecodeError")
        logger.exception("NoValidConnectionsError(paramiko)")
    except KeyboardInterrupt:
        logger.error("Module suspended by KeyboardInterrupt")
        logger.exception("KeyboardInterrupt")




    





