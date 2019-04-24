import sys, re, os
import json, os.path
import argparse, jsonschema, paramiko
import threading, logging

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

        logger.critical('There are offline important services!')
        for ser in dict_out:
            print (ser,':',dict_out[ser])
        return 2

    logger.info('There are no offline services!')
    return 0

def sip_trunk():

    logger.debug('Check sip_trunks started')

    cmnd_line ="cat /opt/naumen/nauphone/snmp/nausipproxy "
    stdin, stdout, stderr = ssh.exec_command(cmnd_line)
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

    logger.critical('There are all sip trunks have bad status!')
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

    logger.info('Number of operators: {}'.format(n))

    if n > 0:
        for i in range(len(dic_out)):
            print (dic_out[i])
        return 0

    logger.critical('There are no operators!')
    return 1

def check_json():

    schema = {
        "type": "object",
        "properties": {
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
                                "file_log" :{"type":"string"},
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
                        "file_log" : "/tmp/pika/some_info.log",
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
            logger.info('File is here')
            with open("/tmp/pika/checks_script.json", "r") as lop:
                numb = json.load(lop)
            jsonschema.validate(numb, schema)
            logger.info('Checks_json is OK')
        else:
            with open("/tmp/pika/checks_script.json", "w") as spr:
                json.dump(data_json, spr,indent=4)
            logger.info('Check_json now is here')

    except jsonschema.exceptions.ValidationError:
        logger.error('There are some mistakes in check_script.json', exc_info = True)
        sys.exit()

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
        logger.debug('Cod started.')

    def join(self, *args):

        threading.Thread.join(self)

        return self.result

if __name__ == '__main__':

    try:

        logger = logging.getLogger (__name__)
        logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        
        logger.addHandler(console)
        
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

                file_log =  data['servers'][i]['server']['file_log']
                fil_hand = logging.FileHandler(file_log)
                fil_hand.setLevel(logging.WARNING)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                fil_hand.setFormatter(formatter)
                logger.addHandler(fil_hand)

                logger.debug('ssh started.')
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                privkey = paramiko.RSAKey.from_private_key_file('/tmp/pika/ssh/id_rsa')
                ssh.connect(hostname=host, username=username, port=port, pkey=privkey)

                for j in range(len(data['servers'][i]['server']['checks'])):
                    check = data['servers'][i]['server']['checks'][j]
                    if check['success'] == True:
                        cod = check['command']
                        
                        myThread = CheckThread()
                        logger.debug('thread started.')
                        myThread.start()

                        logger.debug('thread stoped.')
                        result = myThread.join()
                        
                        cod_out.append(result)

                    else:
                        continue

                ssh.close()
                logger.debug('ssh stopped.')

        elif args_con.ip is not None and args_con.mode is not None :

            tor = args_con.ip[0]
            for i in range(len(data['servers'])):
                if tor == data['servers'][i]['server']['host']:
                    host = data['servers'][i]['server']['host']
                    username = data['servers'][i]['server']['user']
                    #password = data['servers'][i]['server']['password']
                    port = data['servers'][i]['server']['port']

                    file_log =  data['servers'][i]['server']['file_log']
                    fil_hand = logging.FileHandler(file_log)
                    fil_hand.setLevel(logging.WARNING)
                    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                    fil_hand.setFormatter(formatter)
                    logger.addHandler(fil_hand)

                    logger.debug('ssh started.')
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
                            logger.debug('thread started.')
                            myThread.start()
                            
                            logger.debug('thread stoped.')
                            result = myThread.join()
                            
                            cod_out.append(result)

                        else:
                            continue

                    ssh.close()
                    logger.debug('ssh stopped.')

                    if args_con.mode not in lis:
                        logger.info('Check is not founded')

        else:
            logger.info('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')

        for c in cod_out:
            if c > 0 :
                n = c
                sys.exit(n)

        sys.exit(0)
        
    except KeyError:
        logger.error("There are some mistakes in check_script.json, module doesn't find key", exc_info = True)
    except FileNotFoundError:
        logger.error("No such file or directory", exc_info = True)
    except json.decoder.JSONDecodeError:
        logger.error("There are some mistakes in check_script.json, module mustn't read check_script.json", exc_info = True)
    except paramiko.ssh_exception.NoValidConnectionsError:
        logger.error("Unable to connect",exc_info = True)



                    

                        
        


