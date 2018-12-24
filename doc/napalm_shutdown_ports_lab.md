---


```python
from napalm import get_network_driver
import yaml

cmd_template="""
interface {}
shutdown"""

driver = get_network_driver("ce")

hostname="192.168.99.201"
username="ansible"
password="ansible123"
with driver(hostname,username,password) as device:   

    with open("host_vars/OOB_Switch1.yml") as host_vars:
        for interface in yaml.load(host_vars)["interfaces"]:
            device.load_merge_candidate(config=cmd_template.format(interface))
            
        device.commit_config()
print("Done")
```

    Done


---
Смотрим со cтороны коммутатора

```bash
<OOB_switch1>display interface brief 

*down: administratively down
Interface                   PHY   Protocol  InUti OutUti   inErrors  outErrors
GigabitEthernet0/0/1        *down down         0%     0%          0          0
GigabitEthernet0/0/2        down  down         0%     0%          0          0
GigabitEthernet0/0/3        *down down         0%     0%          0          0
GigabitEthernet0/0/4        *down down         0%     0%          0          0
GigabitEthernet0/0/5        *down down         0%     0%          0          0
GigabitEthernet0/0/6        *down down         0%     0%          0          0
```

## Получилось!  

---

