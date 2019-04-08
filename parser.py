import argparse
import script

parser = argparse.ArgumentParser(description='Three check options.')
parser.add_argument('-m','--mode',help = 'Check Modes: services,sip_trunks or operators')
args = parser.parse_args()


if args.mode == "services":
    script.service_stat()
elif args.mode == "sip_trunks":
    script.sip_trunk()
elif args.mode == "operators":
    script.kolvo_oper()
else:
    print('Please see th HELP: "python test.py -h" or "python test.py --help" and try again')
