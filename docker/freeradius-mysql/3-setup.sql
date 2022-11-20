CREATE USER 'raduser'@'%' IDENTIFIED BY 'radpass';
GRANT ALL ON raddb.* TO 'raduser'@'%';
