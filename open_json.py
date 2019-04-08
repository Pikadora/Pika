import json
import argparse
import script_all

parser = argparse.ArgumentParser(description='Three check options.')
parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
args_con = parser.parse_args()


if args_con.mode is None :
    print('____________________')
    print('Please see the HELP: "python test.py -h" or "python test.py --help" and try again')
    print('____________________')

else:
    with open('/tmp/pika/checks.json','r')as lafa:
        data = json.load(lafa)
        for i in range(len(data['checks'])):
            wtfk = data['checks'][i]
            if args_con.mode == wtfk['name']:
                if data['checks'][i]['success'] == 'true':
                    cod = data['checks'][i]['command']
                    exec(cod)
                else:
                    print('Please see the config_file (check success true/false)')
            else:
                continue
