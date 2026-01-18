import csv

fn = 'tr_eikon_eod_data.csv'  # ← これ！この一行が抜けているのでエラーになります
csv_reader = csv.reader(open(fn, 'r'))

for row in csv_reader:
    print(row)

data = list(csv_reader)

data[:5]
