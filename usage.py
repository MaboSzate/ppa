import main as m
import pandas as pd
import matplotlib.pyplot as plt
import random


def start_fund():
    # kezdetben kiválasztottam 6 random állampapírt, 2 DKJ 4 MÁK, mindegyik 30 milla névértéken
    # a maradék készpénz, ami kiadja a 15% heti lejáratú terméket
    SafeHarbor.add_bank_deposit(20)
    SafeHarbor.add_asset("D230517", 22)
    SafeHarbor.add_asset("D231129", 22)
    SafeHarbor.add_asset("D230920", 22)
    SafeHarbor.add_asset("A231124A07", 60)
    SafeHarbor.add_asset("D231018", 22)
    SafeHarbor.add_asset("D231227", 22)
    SafeHarbor.calc_remaining_cash()


SafeHarbor = m.Fund("2023-05-02", "2023-06-30", 200)
start_fund()

SafeHarbor.generate_trajectory()
end_date = pd.to_datetime("2023-06-30")

SafeHarbor.calc_nav()
SafeHarbor.calc_share_of_assets()
print(SafeHarbor.date, SafeHarbor.nav, SafeHarbor.assets)
while not SafeHarbor.problem and SafeHarbor.date < end_date:
    SafeHarbor.tomorrow()
    # print(SafeHarbor.assets)


SafeHarbor.plot_values()
plt.show()
SafeHarbor.save_to_excel()