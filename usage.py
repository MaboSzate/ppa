import main as m
import pandas as pd
import matplotlib.pyplot as plt


def start_fund():
    # kezdetben kiválasztottam 6 random állampapírt, 2 DKJ 4 MÁK, mindegyik 30 milla névértéken
    # a maradék készpénz, ami kiadja a 15% heti lejáratú terméket
    SafeHarbor.add_bank_deposit(15)
    SafeHarbor.add_asset("D230517", 30)
    SafeHarbor.add_asset("A230823C20", 30)
    SafeHarbor.add_asset("D230920", 30)
    SafeHarbor.add_asset("A231124A07", 30)
    SafeHarbor.add_asset("D231018", 25)
    SafeHarbor.add_asset("D231227", 25)
    SafeHarbor.calc_remaining_cash()


SafeHarbor = m.Fund("2023-05-02", "2023-06-30", 200)
start_fund()
SafeHarbor.generate_trajectory()
end_date = pd.to_datetime("2023-06-30")

# egyelőre a program addig megy amíg nincs probléma (vagy az end date-ig)
# a tomorrow fv. minden nap szépen kiírja a nav-ot
SafeHarbor.calc_nav()
SafeHarbor.calc_share_of_assets()
print(SafeHarbor.date, SafeHarbor.nav, SafeHarbor.assets)
while not SafeHarbor.problem and SafeHarbor.date < end_date:
    SafeHarbor.tomorrow()
    # print(SafeHarbor.assets)

print(SafeHarbor.df_shares)
SafeHarbor.plot_values()
plt.show()
