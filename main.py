import pandas as pd
from datetime import timedelta
import numpy.random
import matplotlib.pyplot as plt


class Fund:

    def __init__(self, date, end_date, investment):
        self.assets = pd.DataFrame()  # az alapban lévő eszközök adatai, az oszlopok létrehozva az add_asset fv-ben
        self.date = pd.to_datetime(date)  # az adott nap, kezdetben az input induló nap
        self.end_date = pd.to_datetime(end_date)
        self.investment = investment  # induló tőke
        self.n_assets = 0  # eszközök száma
        self.priceData = pd.read_csv("prices2.csv", sep=";")  # ÁKK historikus adatok MÁK-okra és DKJ-kra
        self.priceData["Settle Date"] = pd.to_datetime(self.priceData["Settle Date"])  # konvertálás dátummá
        self.problem = False  # ez később igazra állítódik, ha valami gond van az alappal és közbe kell lépni
        self.nav = investment  # netto eszközérték, kezdetben az induló tőkével megegyezik
        self.tradingDays = self.priceData["Settle Date"].drop_duplicates()
        self.tradingDays = pd.Series(self.tradingDays.values[self.date <= self.tradingDays])
        self.tradingDays = pd.Series(self.tradingDays.values[self.end_date >= self.tradingDays])
        # csak azokat a napokat vesszük figyelembe, amihez van adat, és ami az induló dátum után van
        self.dateIndex = 0  # ez fogja követni, hogy hányadik napnál járunk
        self.num_of_shares = 10_000  # befektetési jegyek száma
        self.nav_per_shares = self.nav / self.num_of_shares
        self.calc_nav_per_shares()  # egy jegyre jutó nav
        self.interest_rate = 0.0001 / 12  # havi kamatláb (interneten ez volt a leggyakoribb)
        self.trajectory = self.generate_trajectory()
        self.zerokupon = pd.read_csv("zerokupon.csv", sep=";", usecols=[0,1])
        self.zerokupon["Date"] = pd.to_datetime(self.zerokupon["Date"])

    def add_asset(self, name, nominal): # új eszköz felvétele az alapba
        self.n_assets += 1
        # bevezetésre kerül az assets DataFrame 4 oszlopa
        self.assets.loc[self.n_assets, "Name"] = name
        self.assets.loc[self.n_assets, "Maturity"] = self.priceData["Maturity Date"].loc[self.priceData["Security"] == name].values[0]
        self.assets.loc[self.n_assets, "Nominal"] = nominal # névérték
        df = self.priceData.loc[self.priceData["Security"] == name] # az árak leszűkítése a megfelelő eszközre
        df = df.loc[df["Settle Date"] == self.date]
        self.assets.loc[self.n_assets, "Value"] = (df["Ask Price"].values[0] + df["Accrued"].values[0]) * nominal / 100
        # megkeressük a megfelelő dátumhoz tartozó ask price-t, és megszorozzuk a névértékkel

    def add_bank_deposit(self, nominal):
        # 1 hét lejáratú lekötött bankbetét
        premium = 1 # a zéró kupon hozamot ennyivel csökkentve kapott érték lesz a kamatunk
        self.zerokupon["Hozam"] -= premium
        self.zerokupon["Price"] = 100 / (1 + self.zerokupon["Hozam"] / 100) ** (7 / 365)
        self.n_assets += 1
        self.assets.loc[self.n_assets, "Name"] = "Bank Deposit"
        self.assets.loc[self.n_assets, "Maturity"] = self.date + timedelta(weeks=1)
        self.assets.loc[self.n_assets, "Nominal"] = nominal
        self.assets.loc[self.n_assets, "Value"] = self.zerokupon["Price"].loc[self.zerokupon["Date"] ==
                                                                              self.date].values[0] * nominal / 100

    def calc_nav_per_shares(self):
        self.nav_per_shares = self.nav / self.num_of_shares

    def generate_trajectory(self):
        length = self.tradingDays.size
        out_low, out_high = -150, 50
        in_low, in_high = -50, 150
        if self.date < pd.to_datetime("2023.06.01"):
            trajectory = numpy.random.randint(out_low, out_high, length)
        else:
            trajectory = numpy.random.randint(in_low, in_high, length)
        return pd.Series(trajectory)

    def calc_remaining_cash(self): # az indulásnál a kezdőtőkéből megmaradt pénz készpénz lesz
        self.n_assets += 1
        self.assets.loc[self.n_assets, "Name"] = "cash"
        self.assets.loc[self.n_assets, "Maturity"] = self.date
        self.assets.loc[self.n_assets, "Value"] = self.investment - self.assets["Value"].sum()

    def check_maturity(self): # megnézzük, hogy a mai napon lejár-e valamelyik eszköz
        for index, row in self.assets.iterrows():
            date = row["Maturity"]
            if pd.to_datetime(date) == self.date and row["Name"] != "cash":
                self.assets["Value"].loc[self.assets["Name"] == "cash"] += row["Nominal"]
                self.assets = self.assets.drop([index])

    def check_limits(self):
        pass # ide jönnek a limittesztek

    def calc_nav(self): # az eszközök újraárazása, majd összeadása, hogy meglegyen az új nav
        for index, row in self.assets.iterrows():
            price_date = self.date
            if row["Name"] != "cash" and row["Name"] != "Bank Deposit": # a cash-t nem kell újraárazni, a többit hasonlóan árazzuk, mint az add_assetnél
                df_original = self.priceData.loc[self.priceData["Security"] == self.assets.loc[index, "Name"]]
                df = df_original.loc[df_original["Settle Date"] == price_date]
                while df.size == 0: # van olyan nap, amikor valamelyik eszközhöz nincs adat, ezért kell ez
                    price_date -= timedelta(days=1) # ekkor a legutolsó elérhető áron árazzuk
                    df = df_original.loc[df_original["Settle Date"] == price_date]
                current_price = df["Bid Price"].loc[df["Settle Date"] == price_date] + \
                                    df["Accrued"].loc[df["Settle Date"] == price_date]
                self.assets.loc[index, "Value"] = current_price.values[0] * self.assets.loc[index, "Nominal"] / 100
            if row["Name"] == "Bank Deposit":
                hozam = self.zerokupon["Hozam"].loc[self.zerokupon["Date"] == self.date].values[0]
                lejarat = (row["Maturity"] - self.date).days
                self.assets.loc[index, "Value"] = 100 / (1 + hozam / 100) ** (lejarat / 365) * row["Nominal"] / 100
        self.nav = self.assets["Value"].sum() # a nav az új értékek összege

    def trade(self):
        trade_today = self.trajectory[self.dateIndex - 1]
        self.num_of_shares += trade_today
        print(self.assets.loc[self.n_assets, "Value"])
        self.assets.loc[self.n_assets, "Value"] += trade_today * self.nav_per_shares
        print(self.assets.loc[self.n_assets, "Value"])

    def tomorrow(self):
        self.dateIndex += 1
        self.check_maturity()
        self.date = self.tradingDays[self.dateIndex]
        self.assets["Maturity"].loc[self.assets["Name"] == "cash"] = self.date
        self.calc_nav()
        self.trade()
        self.check_limits()
        self.calc_nav()
        self.calc_nav_per_shares()
        print(self.date.date(), self.nav, self.assets)



