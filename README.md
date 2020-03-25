## Выключаем неиспользуемые порты коммутаторов 

Задача простая:  
пройтись по всем коммутаторам доступа и административно погасить те из них, которые не используются более определенного количества дней  

У нас в хозяйстве коммутаторы двух вендоров **Cisco** и **Huawei**  
А еще есть в наличии NMS - система мониторинга сетевого (и не только) оборудования *Observium* 
которая по SNMP собирает всю необходимую нам статистику и кладет в базу данных *MySQL*.  
Так же кроме *Observium* развернут *LibreNMS*, который является более продвинутым форком первого и на который мы видимо в итоге смигрируем. Поэтому решение должно поддерживать обе NMS системы.

Чтобы получить список неиспользуемых портов из базы *Observium* подойдет такой SQL запрос:
```sql
SELECT port_label,ifLastChange FROM ports WHERE device_id={ID}
 AND port_label LIKE '%Ethernet%' AND ifAdminStatus='up' AND ifOperStatus='down' 
 AND ifLastChange<=DATE_SUB(CURDATE(),INTERVAL {XX} DAY)
```
Для *LibreNMS* запрос получается немного другой:  
```sql
SELECT ifDescr, DATE_SUB(NOW(), INTERVAL ifLastChange/100 SECOND) as ifLastChange FROM ports \
WHERE device_id={ID} and ifDescr like '%Ethernet%' AND ifAdminStatus='up' AND ifOperStatus='down' AND ifLastChange >= 8640000*{XX}
```
Вот собственно и все решение. 
Под нашу задачу написан отдельный скрипт (*inventory.py*), который в зависимости от параметров выдает список неиспользуемых интерфейсов в консоль или формирует *host_vars* для сценариев *ansible*.

Дальше коротко:  
  * *inventory.py* - срипт на *pyhton* выполняет этот запрос для заданного коммутатора  
  * *inventory.yml* - ansible playbook выполняет скрипт для множества коммутаторов  
  * *cisco-shut.yml* - ansible playbook выключает неиспользуемые порты на коммутаторах **cisco**  
  * *hw-shut.yml* - ansible playbook выключает неиспользуемые порты на коммутаторах **huawei**  
  * *shut-down-unused-ports.yml* - ansible сценарий-обертка: запускает последовательно *cisco-shut.yml* и *hw-shut.yml* 

Сценарий *hw-shut.yml* использует кастомные модули *napalm-ansible*, которые необходимо предварительно установить командой 
> pip install napalm-ansible

Кроме того необходимо убедиться в том, что в *ansible.cfg* указан путь к модулю

Авторизация на коммутаторы происходит по логину/паролю.  
Эти параметры передаются в сценарии через переменные *{{ username }}* и *{{ password }}*  
параметры находятся в файлах *group_vars/cisco/vault.yml* и *group_vars/huawei/vault.yml*  
и зашифрованы механизмом **ansible-vault**

### Использование

Скрипт можно запустить как standalone так и в качесте inventory для ansible  
В любом случае предварительно нужно настроить скрипт под базу NMS.  
Настройки пописываются в *script/nmsargs.py*
```python
# the mysql DB creds
creds = {
"host": "127.0.0.1",
"user": "librenms",
"passwd": "password",
"database": "librenms"}
# and the nms that should be set to "observium" or "librenms"
nms="librenms"
```

Чтобы познакомиться с параметрами запускаем с ключом -h:  
```bash
11:45 $ python3 script/inventory.py -h
usage: inventory.py [-h] -H HOSTNAME -D DAYS [-A]

finds unused ports on a given switch

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTNAME, --hostname HOSTNAME
                        switch's hostname
  -D DAYS, --days DAYS  days ports being unused
  -A, --ansible         create ansible inventory file for farther network
                        automation operations (no output to stdout)
```

Теперь можно запросить любой, существующий в базе NMS коммутатор:
```bash
11:52 $ python3 script/inventory.py -H catalyst25 -D 20
device_id=33
+---------------------+----------------------------+
|        ifDesc       |        ifLastChange        |
+---------------------+----------------------------+
|  GigabitEthernet0/5 | 2019-08-01 14:32:08.002000 |
|  GigabitEthernet0/6 | 2019-07-31 11:00:04.004300 |
|  GigabitEthernet0/7 | 2020-02-21 12:50:46.003400 |
| GigabitEthernet0/16 | 2019-07-03 16:10:39.006100 |
| GigabitEthernet0/18 | 2020-02-04 19:07:35.003000 |
| GigabitEthernet0/22 | 2019-08-04 10:32:10.000500 |
| GigabitEthernet0/23 | 2019-07-26 13:09:18.009000 |
| GigabitEthernet0/25 | 2020-01-15 16:31:53.005500 |
| GigabitEthernet0/26 | 2019-03-27 08:42:41.003000 |
| GigabitEthernet0/27 | 2019-06-02 11:00:05.007100 |
| GigabitEthernet0/31 | 2019-07-03 11:30:49.009700 |
| GigabitEthernet0/34 | 2019-12-20 12:23:14.005200 |
+---------------------+----------------------------+
```

И то же самое с ключом **-A** чтоб создать *host_vars* для *ansible*
```bash
11:52 $ python3 script/inventory.py -H catalyst25 -D 20 -A
device_id=33

11:54 $ cat host_vars/catalyst25.yml 
interfaces:
  - GigabitEthernet0/5
  - GigabitEthernet0/6
  - GigabitEthernet0/7
  - GigabitEthernet0/16
  - GigabitEthernet0/18
  - GigabitEthernet0/22
  - GigabitEthernet0/23
  - GigabitEthernet0/25
  - GigabitEthernet0/26
  - GigabitEthernet0/27
  - GigabitEthernet0/31
  - GigabitEthernet0/34
```

#### Ansible ####

*Ansible* вышеперечисленное делает самостоятельно. Если предварительно настроен конечно.  
Как уже упоминалось, для поддежки *huawei* требуется поставить модуль *ansible-napalm*.  
Так же необходимо создать файлы **group_vars/cisco/vault.yml** и **group_vars/cisco/vault.yml** с содержимым:
```
username:cisco
password:cisco123
```
и зашифровать с помощью ansible-vault:
```bash
ansible-vault encrypt ansible-vault encrypt creds.yaml --vault-password-file vault/vault.txt
```
  
А далее просто прописываем в **hosts** нужные свичи в группы *cisco* и/или *huawei* и выполняем последовательно сценарии: 
 - inventory.yml<sup>1</sup>  
 - shut-down-unused-ports.yml

----
<sup>1</sup> ansible начитывает *inventory* в начале выполнения. поэтому сгенерированный inventory внутри сценария, в первой задаче, не передается во вторую и последующие.