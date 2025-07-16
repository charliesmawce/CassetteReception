import json

data = json.load(open('C:/cygwin64/home/charl/25CERN/CassetteReception/report_ECOND_chip_1014308_2025-04-12_05-18-11.json'))

test_list = data['tests']

for t in test_list:
    print(t['nodeid']) #prints the name of the test
    print(t['outcome']) #outcome of the test, passed/failed/skipped, etc.