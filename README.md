## Выключаем неиспользуемые порты коммутаторов 

Задача простая:  
пройтись по всем коммутаторам доступа и административно погасить те из них, которые не используются более определнонго количества дней  

У нас в хозяйстве коммутаторы двух вендоров **Cisco** и **Huawei**  
так же есть в наличии система мониторинга сетевого (и не только) оборудования *Observium* <sup>1</sup>  
которая по SNMP собирает всю необходимую нам статистику и кладет в базу данных *MySQL*

Таким образом, задача по выявлению неиспользуемых портов решается простым запросом в базу:
```sql
SELECT port_label,ifLastChange FROM ports WHERE device_id={ID}
 AND port_label LIKE '%Ethernet%' AND ifAdminStatus='up' AND ifOperStatus='down' 
 AND ifLastChange<=DATE_SUB(CURDATE(),INTERVAL {XX} DAY)
```

Ну а дальше коротко:  
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
параметры находятся в файлах group_vars/cisco/vault.yml и group_vars/huawei/vault.yml  
и зашифрованы механизмом **ansible-vault**

----
<sup>1</sup> возможно будет работать с LibreNMS

