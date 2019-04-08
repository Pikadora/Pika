import json
import argparse
import script

parser = argparse.ArgumentParser(description='Three check options.')
parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
args = parser.parse_args()

with open('/tmp/pika/checks.json','r')as lafa:
    data = json.load(lafa)
    for i in range(len(data['checks'])):
        if args.mode in data['checks'][i]['name'] == "services"  and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.service_stat()
        elif args.mode in data['checks'][i]['name'] == "sip_trunks" and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.sip_trunk()
        elif args.mode in data['checks'][i]['name'] == "operators" and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.kolvo_oper()
