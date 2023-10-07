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
        self.n_assets = 2  # eszközök száma
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
        self.zerokupon = pd.read_csv("zerokupon.csv", sep=";", usecols=[0, 1])
        self.zerokupon["Date"] = pd.to_datetime(self.zerokupon["Date"])
        self.new_asset_index = 0

        # plotokhoz szükséges listák/dataframe-ek
        self.date_list = [self.date]
        self.nav_list = [self.nav]
        self.nav_per_shares_list = [self.nav_per_shares]
        self.df_shares = pd.DataFrame()

    def add_asset(self, name, nominal):  # új eszköz felvétele az alapba
        self.n_assets += 1
        # bevezetésre kerül az assets DataFrame 4 oszlopa
        self.assets.loc[self.n_assets, "Name"] = name
        self.assets.loc[self.n_assets, "Maturity"] = pd.to_datetime(self.priceData["Maturity Date"].loc[self.priceData["Security"] == name].values[0])
        self.assets.loc[self.n_assets, "Nominal"] = nominal # névérték
        price_date = self.date
        df_original = self.priceData.loc[self.priceData["Security"] == name]
        df = df_original.loc[df_original["Settle Date"] == price_date]
        while df.size == 0:  # van olyan nap, amikor valamelyik eszközhöz nincs adat, ezért kell ez
            price_date -= timedelta(days=1)  # ekkor a legutolsó elérhető áron árazzuk
            df = df_original.loc[df_original["Settle Date"] == price_date]
            print(df_original)
        current_price = df["Bid Price"].loc[df["Settle Date"] == price_date] + \
                            df["Accrued"].loc[df["Settle Date"] == price_date]
        self.assets.loc[self.n_assets, "Value"] = current_price.values[0] * \
                                                  self.assets.loc[self.n_assets, "Nominal"] / 100
        # megkeressük a megfelelő dátumhoz tartozó ask price-t, és megszorozzuk a névértékkel

    def add_bank_deposit(self, nominal):
        # 1 hét lejáratú lekötött bankbetét
        self.assets.loc[1, "Name"] = "Bank Deposit"
        self.assets.loc[1, "Maturity"] = self.date + timedelta(weeks=1)
        self.assets.loc[1, "Nominal"] = nominal
        self.assets.loc[1, "Value"] = nominal

    # def calc_bank_deposit_value(self, method="alapkamat"):
    #     df = self.assets.loc[self.assets["Name"] == "Bank Deposit"]
    #     if df.size != 0:
    #         nominal = df["Nominal"].values[0]
    #         maturity = df["Maturity"].values[0]
    #         if method == "dkj":
    #             self.zerokupon["Price"] = 100 / (1 + self.zerokupon["Hozam"] / 100) ** (7 / 365)
    #             self.assets.loc[1, "Value"] = self.zerokupon["Price"].loc[self.zerokupon["Date"] ==
    #                                                                                   self.date].values[0] * nominal / 100
    #         if method == "alapkamat":
    #             alapkamat = 13
    #             premium = 1
    #             price = 100 / (1 + (alapkamat-1) / 100) ** ((maturity - self.date).days / 365)
    #             self.assets.loc[1, "Value"] = price * nominal / 100

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
        day_of_shock = numpy.random.randint(0, length)
        trajectory[day_of_shock] = numpy.random.randint(4 * out_low, 2 * out_low)
        return pd.Series(trajectory)

    def calc_remaining_cash(self): # az indulásnál a kezdőtőkéből megmaradt pénz készpénz lesz
        self.assets.loc[2, "Name"] = "cash"
        self.assets.loc[2, "Maturity"] = self.date
        self.assets.loc[2, "Value"] = self.investment - self.assets["Value"].sum()
        df = self.assets
        df.loc[2], df.loc[2] = df.loc[2].copy(), df.loc[2].copy()
        self.assets = df

    def break_deposit(self, nominal):
        self.assets.loc[1, "Value"] -= nominal
        self.assets.loc[1, "Nominal"] -= nominal
        self.assets.loc[2, "Value"] += nominal

    def sell_assets(self, sell_ratio):
        nominal_loss = self.assets["Nominal"].loc[self.assets.index > 2] * sell_ratio
        value_loss = self.assets["Value"].loc[self.assets.index > 2] * sell_ratio
        self.assets["Nominal"].loc[self.assets.index > 2] -= nominal_loss
        self.assets["Value"].loc[self.assets.index > 2] -= value_loss
        self.assets.loc[2, "Value"] += value_loss.sum()

    def check_maturity(self): # megnézzük, hogy a mai napon lejár-e valamelyik eszköz
        for index, row in self.assets.iterrows():
            date = row["Maturity"]
            if date <= self.date and index > 2:
                self.assets.loc[2, "Value"] += row["Nominal"]
                self.assets = self.assets.drop([index])
            if date <= self.date and index == 1:
                alapkamat = 0.13
                premium = 0.01
                kamat = (alapkamat - premium) * (7/365) * row["Nominal"]
                self.assets.loc[2, "Value"] += kamat
                self.add_bank_deposit(row["Nominal"])
                print("Betét lejárt, kamatazott " + str(kamat) + " mFt-t")

    def check_limits(self):
        # self.problem = True helyett korrekció
        # legalább 7,5% napi lejáratú
        if self.assets['Share'][self.assets['Maturity'] - self.date <= timedelta(days=1)].sum() < 0.075:
            print('Napi lejárat 7,5% alatt')
            self.not_enough_cash()
        # legalább 15% heti lejáratú
        if self.assets['Share'][self.assets['Maturity'] - self.date <= timedelta(days=7)].sum() < 0.15:
            print('Heti lejárat 15% alatt')
            self.not_enough_deposit()
        # Kell MÁK és DKJ is
        DKJ, MAK = False, False
        for name in self.assets['Name']:
            if name[0] == 'D':
                DKJ = True
            elif name[0] == 'A':
                MAK = True
        if not DKJ or not MAK:
            print('Nincs DKJ vagy MÁK')
            self.problem = True
        # maximum 30% egy sorozatba
        if any(self.assets['Share'][(self.assets['Name'] != 'cash') & (self.assets['Name'] != 'Bank Deposit')] > 0.3):
            print('Több, mint 30% egy sorozatban')
            self.problem = True
        # legalább 6 sorozat
        if self.assets[(self.assets['Name'] != 'cash') & (self.assets['Name'] != 'Bank Deposit')].shape[0] < 6:
            print('Kevesebb, mint 6 sorozat')
            self.not_enough_assets()

    def not_enough_cash(self):
        if self.assets['Share'][self.assets['Maturity'] - self.date <= timedelta(days=7)].sum() >= 0.2:
            while self.assets.loc[2, 'Share'] < 0.1:
                self.break_deposit(0.2)
                self.calc_share_of_assets()
            print("Betörtem betétet úgy, hogy 10% cash legyen")
        else:
            while self.assets.loc[2, "Share"] < 0.1:
                self.sell_assets(0.01)
                self.calc_share_of_assets()
            print("Eladtam eszközöket úgy, hogy 10% cash legyen")

    def not_enough_deposit(self):
        while self.assets.loc[1, 'Share'] + self.assets.loc[2, 'Share'] < 0.2:
            self.sell_assets(0.01)
            self.calc_share_of_assets()
        print("Eladtam eszközöket úgy, hogy 20% cash+deposit legyen")
        half_of_cash = self.assets.loc[2, "Value"] / 2
        current_deposit = self.assets.loc[1, "Value"]
        self.add_bank_deposit(half_of_cash + current_deposit)
        self.assets.loc[2, "Value"] -= half_of_cash
        self.check_limits()

    def not_enough_assets(self):
        if self.assets.loc[2, 'Value'] < 0.1:
            print("Kevesebb, mint 6 eszköz, nincs pénzem újat venni")
            self.problem = True
        available_assets = ["D240221", "D240430"]
        new_asset = available_assets[self.new_asset_index]
        self.new_asset_index += 1
        nominal = 1
        nominal_increment = 1
        old_value = 0
        while self.assets.loc[2, 'Share'] >= 0.1:
            self.add_asset(new_asset, nominal)
            new_value = self.assets.loc[self.n_assets, "Value"]
            value_change = new_value - old_value
            self.assets.loc[2, "Value"] -= value_change
            self.n_assets -= 1
            self.calc_nav()
            self.calc_share_of_assets()
            old_value = new_value
            nominal += nominal_increment
        self.check_limits()

    def calc_nav(self): # az eszközök újraárazása, majd összeadása, hogy meglegyen az új nav
        for index, row in self.assets.iterrows():
            price_date = self.date
            if index != 1 and index !=2: # a cash-t nem kell újraárazni, a többit hasonlóan árazzuk, mint az add_assetnél
                df_original = self.priceData.loc[self.priceData["Security"] == row["Name"]]
                df = df_original.loc[df_original["Settle Date"] == price_date]
                while df.size == 0: # van olyan nap, amikor valamelyik eszközhöz nincs adat, ezért kell ez
                    price_date -= timedelta(days=1) # ekkor a legutolsó elérhető áron árazzuk
                    df = df_original.loc[df_original["Settle Date"] == price_date]
                current_price = df["Bid Price"].loc[df["Settle Date"] == price_date] + \
                                    df["Accrued"].loc[df["Settle Date"] == price_date]
                self.assets.loc[index, "Value"] = current_price.values[0] * self.assets.loc[index, "Nominal"] / 100
        # self.calc_bank_deposit_value()
        self.nav = self.assets["Value"].sum() # a nav az új értékek összege

    # eszközök arányának kiszámítása a portfólióban
    def calc_share_of_assets(self):
        self.assets['Share'] = self.assets['Value'] / self.nav

    def trade(self):
        trade_today = self.trajectory[self.dateIndex - 1]
        self.num_of_shares += trade_today
        # print(self.assets.loc[2, "Value"])
        self.assets.loc[2, "Value"] += trade_today * self.nav_per_shares
        # print(self.assets.loc[2, "Value"])
        print("Mai pénzmozgás: " + str(trade_today * self.nav_per_shares))

    def tomorrow(self):
        # első nap a df_shares
        if self.dateIndex == 0:
            self.df_shares = self.assets.copy()
        self.dateIndex += 1
        self.date = self.tradingDays[self.dateIndex]
        self.check_maturity()
        self.assets.loc[2, "Maturity"] = self.date
        self.trade()

        # nem tudom, hogy elé vagy mögé kéne, vagy mindkettő
        self.calc_nav()
        self.calc_share_of_assets()

        self.check_limits()

        self.calc_nav()
        self.calc_share_of_assets()

        self.calc_nav_per_shares()

        self.add_items()
        print(self.date.date(), self.nav, self.assets)

    def add_items(self):
        self.date_list.append(self.date)
        self.nav_list.append(self.nav)
        self.nav_per_shares_list.append(self.nav_per_shares)
        self.df_shares = self.df_shares.merge(self.assets, 'outer', 'Name')

    def plot_values(self):
        df_nav = pd.DataFrame({'Net Asset Value': self.nav_list},
                              index=self.date_list)

        df_nav_per_shares = pd.DataFrame({'Net Asset Value per Shares': self.nav_per_shares_list}, index=self.date_list)

        self.df_shares.index = self.df_shares['Name']
        self.df_shares = self.df_shares.filter(like='Share', axis=1)
        self.df_shares.columns = self.date_list

        df_nav.plot()
        df_nav_per_shares.plot()
        self.df_shares.T.plot()
