import pandas as pd

df = pd.read_csv('updated_list.csv')

# health = df[df['Subject'] == 'Health']
# health.to_csv('health.csv', index=False)

# plnr = df[df['Subject'] == 'Public Lands and Natural Resources']
# plnr.to_csv('plnr.csv', index=False)

# env = df[df['Subject'] == 'Environmental Protection']
# env.to_csv('env.csv', index=False)

# govops = df[df['Subject'] == 'Government Operations and Politics']
# govops.to_csv('csvs/govops.csv', index=False)

tpw = df[df['Subject'] == 'Transportation and Public Works']
tpw.to_csv('csv_files/tpw.csv', index=False)

econ = df[df['Subject'] == 'Economics and Public Finance']
econ.to_csv('csv_files/econ.csv', index=False)

stc = df[df['Subject'] == 'Science, Technology, Communications']
stc.to_csv('csv_files/stc.csv', index=False)

water = df[df['Subject'] == 'Water Resources Development']
water.to_csv('csv_files/water.csv', index=False)

food = df[df['Subject'] == 'Agriculture and Food']
food.to_csv('csv_files/food.csv', index=False)

energy = df[df['Subject'] == 'Energy']
energy.to_csv('csv_files/energy.csv', index=False)