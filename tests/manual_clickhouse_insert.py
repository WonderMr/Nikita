from clickhouse_driver import Client
from datetime import datetime
import sys
da = '20200229000012'
r3 = '24384443947d0'
r3h = int('0x'+r3, 16)
r3a = '3033'
r3ah = int('0x'+r3a, 16)
r15 = '1234'
ta = da[0:4]+"-"+da[4:6]+'-'+da[6:8]+' '+da[8:10]+':'+da[10:12]+':'+da[12:14]
print(ta)
ts = int(datetime.fromisoformat(ta).timestamp())
print(ts)
#sys.exit(0)
client = Client(host='m1-1c-sme-bi', user='default', password='')
ta = da[0:4]+"-"+da[4:6]+'-'+da[6:8]+' '+da[8:10]+':'+da[10:12]+':'+da[12:14]
ts = int(datetime.fromisoformat(ta).timestamp())
ret = client.execute("insert into nikita.logs(r1,r2,r3,r3a,r15,) values ("+str(ts)+",'C',0x"+r3+",0x"+r3a+","+r15+")" )
print(ret)