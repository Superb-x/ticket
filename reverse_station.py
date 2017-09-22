from stations import stations
from pprint import pprint

stcode = {}
for station in stations:
    stcode[stations[station]] = station

pprint(dict(stcode), indent=4)