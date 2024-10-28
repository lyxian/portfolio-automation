# portfolio-automation

**Learnings**
<!-- - asyncio -->
- sqlalchemy X marshmallow

Description: ..

### Issues
- (mariadb.InterfaceError) Lost connection to server during query
  - https://stackoverflow.com/questions/1884859/lost-connection-to-mysql-server-during-query
  - https://bobcares.com/blog/mariadb-lost-connection-during-query/
  - Can't reconnect until invalid transaction is rolled back.  Please rollback() fully before proceeding 

### DB Design

Table 1: currency
- shortName, fullName, sgdConversion, updatedAt

Table 2: region
- name, `currencyId`

Table 3: stock
- ticker, name, industry, price, altUrl, updatedAt, `currencyId`

Table 4: marketOrder
- buyDate, cumulativeUnits, units, price, fees, `regionId`, `stockId`

Table 5: portfolio
- costValue, marketValue, marketDiff, sgdConversion, costValueSGD, marketValueSGD, marketDiffSGD, updatedAt, `regionId`

FK links
- currency -> region
- currency -> stock
- region/stock -> marketOrder
- region -> portfolio

**init**

- workflow
  - currency 
  - region
  - orders.csv -> stocks -> orders
    - buyDate,stock,units,price,fees,region
  - portfolio


### ERROR

sqlalchemy.exc.ProgrammingError: (raised as a result of Query-invoked autoflush; consider using a session.no_autoflush block if this flush is occurring prematurely)
(mariadb.ProgrammingError) Invalid parameter type at row 3, column 1
[SQL: UPDATE currency SET `sgdConversion`=? WHERE currency.id = ?]
[parameters: [(0.5824818656891039, 1), (0.78, 2), (1, 3)]]
(Background on this error at: https://sqlalche.me/e/20/f405)

### References

- currency mapping [https://widget-yahoo.ofx.com/resources/current/data/localizations/USA.json]

```
##Packages (list required packages & run .scripts/python-init.sh)
cryptography==37.0.4
requests==2.28.1
pendulum==2.1.2
flask==2.2.2
Werkzeug==2.2.2
pyyaml==6.0
pytest==7.1.2

APScheduler==3.10.1
SQLAlchemy==2.0.17
marshmallow==3.20.0
mariadb==1.1.5
##Packages
```
