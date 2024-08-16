## not needed for local development
## TODO: get mysqlclient to install on prod -- and remove all references to pymysql

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception as e:
    pass
