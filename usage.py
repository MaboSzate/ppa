import main as m
import pandas as pd


def start_fund():
    # kezdetben kiválasztottam 6 random állampapírt, 2 DKJ 4 MÁK, mindegyik 30 milla névértéken
    # a maradék készpénz, ami kiadja a 15% heti lejáratú terméket
    SafeHarbor.add_asset("A241024C18", 30)
    SafeHarbor.add_asset("D230920", 30)
    SafeHarbor.add_asset("A231124A07", 30)
    SafeHarbor.add_asset("D240221", 30)
    SafeHarbor.add_asset("A240626B15", 30)
    SafeHarbor.add_asset("A261222D17", 30)
    SafeHarbor.calc_remaining_cash()


SafeHarbor = m.Fund("2023-05-02", 200)
start_fund()
end_date = pd.to_datetime("2023-06-30")

# egyelőre a program addig megy amíg nincs probléma (vagy az end date-ig)
# a tomorrow fv. minden nap szépen kiírja a nav-ot
while not SafeHarbor.problem and SafeHarbor.date < end_date:
    SafeHarbor.tomorrow()

