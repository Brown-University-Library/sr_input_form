try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception as e:
    pass
