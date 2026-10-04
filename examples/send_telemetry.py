"""Replace sample power with measured sensor output. Shadow mode only."""
import json,time,urllib.request
for i in range(30):
    data={'device_id':'smart-plug-01','timestamp_s':time.time(),'power_w':300+i%3,'max_power_w':1000}
    req=urllib.request.Request('http://127.0.0.1:8080/api/telemetry',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=5) as r:print(r.read().decode())
    time.sleep(.05)
