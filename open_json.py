import json
import script


with open('/tmp/pika/checks.json','r')as lafa:
    data = json.load(lafa)
    for i in range(len(data['checks'])):
        if data['checks'][i]['name'] == 'services' and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.service_stat()
        elif data['checks'][i]['name'] == 'sip_trunks' and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.sip_trunk()
        elif data['checks'][i]['name'] == 'operators' and data['checks'][i]['success'] == 'true':
            print(data['checks'][i])
            print("__________________")
            script.kolvo_oper()
