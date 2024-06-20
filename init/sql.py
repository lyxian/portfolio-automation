from init.const import currencyMap

currencies = ['GBP', 'USD']

test = {
    'currency': [{'shortName':i, 'fullName': currencyMap[i]} for i in currencies],
    'stock': ['RPI.L', 'NVDA'],
    # 'region': ['gb', 'us'],   # not required
    'order': [{   # dependent: region, cumulative, sgdConversion
        'stock': 'RPI.L', 'buyDate': '2/28/2022', 'units': 5, 'price': 485, 'fees': 0, 'region': 'GB'
    }, {
        'stock': 'NVDA', 'buyDate': '3/28/2022', 'units': 5, 'price': 185, 'fees': 1, 'region': 'US'
    }],
    # 'portfolio': [],   # not required
}

def loadData(filePath='init/data.csv'):
    import pendulum
    with open(filePath) as file:
        csv = [i.strip() for i in file.readlines()]
        header, data = csv[0], csv[1:]
        orders = []
        for row in data:
            d = dict(zip(header.split(','), row.split(',')))
            if d['region'] == 'SG':
                d['stock'] = d['stock'] + '.SI'
            elif d['region'] == 'GB':
                d['stock'] = d['stock'] + '.L'
            d['price'] = float(d['price'])
            d['units'] = float(d['units'])
            d['fees'] = float(d['fees']) if d['fees'] else 0
            orders += [d]
        stocks = set([i['stock'] for i in orders])
        return {'stock': stocks, 'order': orders}

currencies = ['GBP', 'USD', 'SGD']
   
prod = {
    'currency': [{'shortName':i, 'fullName': currencyMap[i]} for i in currencies],
    **loadData()
}

data = {
    'test': test,
    'prod': prod,
}