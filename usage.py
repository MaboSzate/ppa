import main as m
import pandas as pd


def start_fund():
    # kezdetben kiválasztottam 6 random állampapírt, 2 DKJ 4 MÁK, mindegyik 30 milla névértéken
    # a maradék készpénz, ami kiadja a 15% heti lejáratú terméket
    SafeHarbor.add_asset("D230517", 20)
    SafeHarbor.add_asset("A241024C18", 20)
    SafeHarbor.add_asset("D230920", 20)
    SafeHarbor.add_asset("A231124A07", 20)
    SafeHarbor.add_asset("A240626B15", 20)
    SafeHarbor.add_asset("A261222D17", 20)
    SafeHarbor.add_bank_deposit(20)
    SafeHarbor.calc_remaining_cash()


SafeHarbor = m.Fund("2023-05-02", "2023-06-30", 200)
start_fund()
SafeHarbor.generate_trajectory()
end_date = pd.to_datetime("2023-06-30")

# egyelőre a program addig megy amíg nincs probléma (vagy az end date-ig)
# a tomorrow fv. minden nap szépen kiírja a nav-ot
while not SafeHarbor.problem and SafeHarbor.date < end_date:
    SafeHarbor.tomorrow()
    # print(SafeHarbor.assets)
