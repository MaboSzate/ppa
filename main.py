import pandas as pd
from datetime import timedelta


class Fund:

    def __init__(self, date, investment):
        self.assets = pd.DataFrame() # az alapban lévő eszközök adatai, az oszlopok létrehozva az add_asset fv-ben
        self.date = pd.to_datetime(date) # az adott nap, kezdetben az input induló nap
        self.investment = investment # induló tőke
        self.n_assets = 0 # eszközök száma
        self.priceData = pd.read_csv("prices.csv", sep=";") # ÁKK historikus adatok MÁK-okra és DKJ-kra
        self.priceData["Settle Date"] = pd.to_datetime(self.priceData["Settle Date"]) # konvertálás dátummá
        self.problem = False # ez később igazra állítódik, ha valami gond van az alappal és közbe kell lépni
        self.nav = investment # netto eszközérték, kezdetben az induló tőkével megegyezik
        self.tradingDays = self.priceData["Settle Date"].drop_duplicates()
        self.tradingDays = pd.Series(self.tradingDays.values[self.tradingDays >= self.date])
        # csak azokat a napokat vesszük figyelembe, amihez van adat, és ami az induló dátum után van
        self.dateIndex = 0 # ez fogja követni, hogy hányadik napnál járunk

    def add_asset(self, name, nominal): # új eszköz felvétele az alapba
        self.n_assets += 1
        # bevezetésre kerül az assets DataFrame 4 oszlopa
        self.assets.loc[self.n_assets, "Name"] = name
        self.assets.loc[self.n_assets, "Maturity"] = self.priceData["Maturity"].loc[self.priceData["Security"] == name].values[0]
        self.assets.loc[self.n_assets, "Nominal"] = nominal # névérték
        df = self.priceData.loc[self.priceData["Security"] == name] # az árak leszűkítése a megfelelő eszközre
        self.assets.loc[self.n_assets, "Value"] = df["Ask Price"].loc[df["Settle Date"] ==
                                                                      self.date].values[0] * nominal /100
        # megkeressük a megfelelő dátumhoz tartozó ask price-t, és megszorozzuk a névértékkel

    def calc_remaining_cash(self): # az indulásnál a kezdőtőkéből megmaradt pénz készpénz lesz
        self.n_assets += 1
        self.assets.loc[self.n_assets, "Name"] = "cash"
        self.assets.loc[self.n_assets, "Maturity"] = self.date
        self.assets.loc[self.n_assets, "Value"] = self.investment - self.assets["Value"].sum()

    def check_maturity(self): # megnézzük, hogy a következő napon lejár-e valamelyik eszköz
        # ha csak ÁKK-terméket veszünk, erre nem lesz szükség, semmi nem jár le jún 30-ig
        next_day = self.tradingDays[self.dateIndex + 1]
        for date in self.assets["Maturity"]:
            if pd.to_datetime(date) == next_day:
                self.problem = True # jelezzük a problémát
                break

    def check_limits(self):
        pass # ide jönnek a limittesztek

    def calc_nav(self): # az eszközök újraárazása, majd összeadása, hogy meglegyen az új nav
        for index, row in self.assets.iterrows():
            price_date = self.date
            if row["Name"] != "cash": # a cash-t nem kell újraárazni, a többit hasonlóan árazzuk, mint az add_assetnél
                df = self.priceData.loc[self.priceData["Security"] == self.assets.loc[index, "Name"]]
                current_price = df["Bid Price"].loc[df["Settle Date"] == price_date] # mostmár bid price
                while current_price.size == 0: # van olyan nap, amikor valamelyik eszközhöz nincs adat, ezért kell ez
                    price_date -= timedelta(days=1) # ekkor a legutolsó elérhető áron árazzuk
                    current_price = df["Bid Price"].loc[df["Settle Date"] == price_date]
                self.assets.loc[index, "Value"] = current_price.values[0] * self.assets.loc[index, "Nominal"] / 100
        self.nav = self.assets["Value"].sum() # a nav az új értékek összege

    def trade(self, data):
        # data egy df, első oszlopban a dátumok ("Date"), második oszlopban a nettó forgalmazás ("Trading")
        # feladat még data leszimulálása a feladatkiírás 4. pontja alapján
        trading_today = data["Trading"].loc[data["Date"] == self.date]
        self.assets["Value"].loc[self.assets["Name"] == "cash"] += trading_today

    def tomorrow(self):
        self.check_maturity()
        self.dateIndex += 1
        self.date = self.tradingDays[self.dateIndex]
        self.assets["Maturity"].loc[self.assets["Name"] == "cash"] = self.date
        self.calc_nav()
        # self.trade()
        self.check_limits()
        print(self.date, self.nav)



