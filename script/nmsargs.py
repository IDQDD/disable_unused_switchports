# nmsargs is a place to configure an NMS that is being used as a source of
# truth of switches ports state
# there are two variables to modify:
# the mysql DB creds
creds = {
"host": "127.0.0.1",
"user": "librenms",
"passwd": "nga4Lomo",
"database": "librenms"}
# and the nms that should be set to "observium" or "librenms"
nms="librenms"

# don't modify the templates below
query_device_tpl="SELECT device_id FROM devices WHERE hostname='{}'"

query_unused_ports_tpl = { 
	"observium": 
	"SELECT port_label,ifLastChange FROM ports \
WHERE device_id={} and port_label like '%Ethernet%' and ifAdminStatus='up' and ifOperStatus='down' and ifLastChange<=DATE_SUB(CURDATE(),INTERVAL {} DAY)", 
	"librenms": 
	"SELECT ifDescr, DATE_SUB(NOW(), INTERVAL ifLastChange/100 SECOND) as ifLastChange FROM ports \
WHERE device_id={} and ifDescr like '%Ethernet%' AND ifAdminStatus='up' AND ifOperStatus='down' AND ifLastChange >= 8640000*{}"
}
