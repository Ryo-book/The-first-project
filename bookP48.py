import csv

fn = 'tr_eikon_eod_data.csv'

csv_reader = csv.DictReader(open(fn, 'r'))

for row in csv_reader:
    print(row)


data = list(csv_reader)

data[:3]
