import pandas as pd
from datetime import timedelta
import numpy.random
import numpy as np
import random
import matplotlib.pyplot as plt
from openpyxl.workbook import Workbook


class Fund:

    def __init__(self, date, end_date, investment):
        self.assets = pd.DataFrame()  # az alapban lévő eszközök adatai, az oszlopok létrehozva az add_asset fv-ben
        self.date = pd.to_datetime(date)  # az adott nap, kezdetben az input induló nap
        self.end_date = pd.to_datetime(end_date)
        self.investment = investment  # induló tőke
        self.n_assets = 1  # eszközök száma
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
        # self.zerokupon = pd.read_csv("zerokupon.csv", sep=";", usecols=[0, 1])
        # self.zerokupon["Date"] = pd.to_datetime(self.zerokupon["Date"])
        # self.zerokupon['Hozam'] = self.zerokupon['Hozam'] / 100
        self.new_asset_index = 0
        self.deposit_index = 1
        self.walm = 0

        # plotokhoz szükséges listák/dataframe-ek
        self.date_list = [self.date]
        self.nav_list = [self.nav]
        self.nav_per_shares_list = [self.nav_per_shares]
        self.num_of_shares_list = [self.num_of_shares / 50]
        self.df_all = pd.DataFrame()
        self.returns = pd.DataFrame()
        self.walm_list = []

        # tranzakciós lista
        self.transactions = pd.DataFrame(
            columns=['Date', 'Transaction', 'Reason',
                     'Value_of_Transaction_per_Asset (mFt)'])
        self.transaction_value_per_shares = 0

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
        current_price = df["Bid Price"] + df["Accrued"]
        self.assets.loc[self.n_assets, "Value"] = current_price.values[0] * \
                                                  self.assets.loc[self.n_assets, "Nominal"] / 100
        # megkeressük a megfelelő dátumhoz tartozó ask price-t, és megszorozzuk a névértékkel

    def add_bank_deposit(self, nominal):
        # 1 hét lejáratú lekötött bankbetét
        self.assets.loc[10 + self.deposit_index, "Name"] = "Bank Deposit " + str(self.deposit_index)
        self.assets.loc[10 + self.deposit_index, "Maturity"] = self.date + timedelta(weeks=1)
        self.assets.loc[10 + self.deposit_index, "Nominal"] = nominal
        self.assets.loc[10 + self.deposit_index, "Value"] = nominal

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
        np.random.seed(69420)
        length = int(self.tradingDays.size / 2)
        out_low, out_high = -150, 50
        in_low, in_high = -50, 100
        trajectory = numpy.random.randint(out_low, out_high, length)
        trajectory = np.append(trajectory, numpy.random.randint(in_low, in_high, length))
        day_of_shock = numpy.random.randint(0, length)
        trajectory[day_of_shock] = numpy.random.randint(4 * out_low, 2 * out_low)
        return pd.Series(trajectory)

    def calc_remaining_cash(self): # az indulásnál a kezdőtőkéből megmaradt pénz készpénz lesz
        self.assets.loc[1, "Name"] = "cash"
        self.assets.loc[1, "Maturity"] = self.date
        self.assets.loc[1, "Value"] = self.investment - self.assets["Value"].sum()
        df = self.assets
        df.loc[1], df.loc[1] = df.loc[1].copy(), df.loc[1].copy()
        self.assets = df

    def break_deposit(self, nominal):
        furthest_maturity_deposit = self.assets.loc[self.assets.index > 10]["Maturity"].idxmax()
        self.assets.loc[furthest_maturity_deposit, "Value"] -= nominal
        self.assets.loc[furthest_maturity_deposit, "Nominal"] -= nominal
        self.assets.loc[1, "Value"] += nominal

    def sell_assets(self, sell_ratio):
        securities = self.assets.index[self.assets.index < 10]
        securities = securities[securities > 1]
        nominal_loss = self.assets.loc[securities, "Nominal"] * sell_ratio
        value_loss = self.assets.loc[securities, "Value"] * sell_ratio
        self.assets.loc[securities, "Nominal"] -= nominal_loss
        self.assets.loc[securities, "Value"] -= value_loss
        self.assets.loc[1, "Value"] += value_loss.sum()

        # a tranzakció értékét összegezzük
        # bank deposit nincs az eszközökbe beleszámolva
        self.transaction_value_per_shares += \
            value_loss.sum() / (self.n_assets - 1)

    def check_maturity(self): # megnézzük, hogy a mai napon lejár-e valamelyik eszköz
        for index, row in self.assets.iterrows():
            date = row["Maturity"]
            if date <= self.date and 10 > index > 1:
                self.assets.loc[1, "Value"] += row["Nominal"]
                self.assets = self.assets.drop([index])
            if date <= self.date and index > 10:
                alapkamat = 0.13
                premium = 0.01
                kamat = (alapkamat - premium) * (7/365) * row["Nominal"]
                self.assets.loc[1, "Value"] += kamat
                self.deposit_index = index - 10
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
        if any(self.assets['Share'][(self.assets['Name'] != 'cash') & (self.assets.index < 10)] > 0.3):
            print('Több, mint 30% egy sorozatban')
            self.above_30()
        # legalább 6 sorozat
        if self.assets[(self.assets['Name'] != 'cash') & (self.assets.index < 10)].shape[0] < 6:
            print('Kevesebb, mint 6 sorozat')
            self.not_enough_assets()
        # WAM legfeljebb 6 hónap
        if self.walm > 180:
            print("Wal túl magas")
            self.problem = True
        # ha túl sok a cash, vegyünk még valamit
        # if self.assets.loc[1, "Share"] > 0.2:
         #   self.not_enough_assets()

    def not_enough_cash(self):
        if self.assets['Share'][self.assets.index > 10].sum() >= 0.2:
            while self.assets.loc[1, 'Share'] < 0.1:
                self.break_deposit(0.2)
                self.calc_share_of_assets()
            print("Betörtem betétet úgy, hogy 10% cash legyen")
        else:
            while self.assets.loc[1, "Share"] < 0.1:
                self.sell_assets(0.01)
                self.calc_share_of_assets()
            self.add_transaction('Selling assets in equal ratio',
                                 'Daily liquidity below 7.5%')
            print(self.transactions)
            print("Eladtam eszközöket úgy, hogy 10% cash legyen")

    def not_enough_deposit(self):
        while self.assets.loc[1, 'Share'] + self.assets['Share'].loc[self.assets.index > 10].sum() < 0.2:
            self.sell_assets(0.01)
            self.calc_share_of_assets()
        self.add_transaction('Selling assets in equal ratio',
                             'Weekly liquidity below 15%')
        print("Eladtam eszközöket úgy, hogy 20% cash+deposit legyen")
        half_of_cash = self.assets.loc[1, "Value"] / 2
        self.deposit_index += 1
        self.add_bank_deposit(half_of_cash)
        print("Most van bd 2")
        self.assets.loc[1, "Value"] -= half_of_cash
        self.check_limits()

    def not_enough_assets(self):
        if self.assets.loc[1, 'Value'] < 0.1:
            print("Kevesebb, mint 6 eszköz, nincs pénzem újat venni")
            self.problem = True
        available_assets = ["D240221", "D240430"]
        new_asset = available_assets[self.new_asset_index]
        self.new_asset_index += 1
        nominal = 10
        nominal_increment = 1
        old_value = 0
        while self.assets.loc[1, 'Share'] >= 0.1:
            self.add_asset(new_asset, nominal)
            new_value = self.assets.loc[self.n_assets, "Value"]
            value_change = new_value - old_value
            self.assets.loc[1, "Value"] -= value_change
            self.n_assets -= 1
            self.calc_nav()
            self.calc_share_of_assets()
            old_value = new_value
            nominal += nominal_increment

            self.transaction_value_per_shares += value_change
        self.add_transaction(f'Buying asset {new_asset}.',
                             'Number of assets below 6.')
        print(self.transactions)
        self.check_limits()

    def above_30(self):
        idx = self.assets["Share"].idxmax()
        name = self.assets.loc[idx, "Name"]
        old_value = self.assets.loc[idx, "Value"]
        old_n_assets = self.n_assets
        self.n_assets = idx - 1
        self.add_asset(name, 50)
        new_value = self.assets.loc[idx, "Value"]
        self.assets.loc[1, "Value"] += old_value - new_value
        self.n_assets = old_n_assets

        self.transaction_value_per_shares += old_value - new_value
        self.add_transaction(f'Selling from asset {name}.',
                             f'Share of asset {name} above 30%.')
        print(self.transactions)

    def calc_nav(self): # az eszközök újraárazása, majd összeadása, hogy meglegyen az új nav
        for index, row in self.assets.iterrows():
            price_date = self.date
            if index != 1 and index < 10: # a cash-t nem kell újraárazni, a többit hasonlóan árazzuk, mint az add_assetnél
                df_original = self.priceData.loc[self.priceData["Security"] == row["Name"]]
                df = df_original.loc[df_original["Settle Date"] == price_date]
                while df.size == 0: # van olyan nap, amikor valamelyik eszközhöz nincs adat, ezért kell ez
                    price_date -= timedelta(days=1) # ekkor a legutolsó elérhető áron árazzuk
                    df = df_original.loc[df_original["Settle Date"] == price_date]
                current_price = df["Bid Price"] + df["Accrued"]
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
        self.assets.loc[1, "Value"] += trade_today * self.nav_per_shares
        # print(self.assets.loc[2, "Value"])
        print("Mai pénzmozgás: " + str(trade_today * self.nav_per_shares))

    def tomorrow(self):
        # első nap a df_shares
        if self.dateIndex == 0:
            self.df_all = self.assets.copy()
            self.walm_list = [np.dot(self.assets["Maturity"] - self.date, self.assets["Share"]).days]
        self.dateIndex += 1
        self.date = self.tradingDays[self.dateIndex]
        self.check_maturity()
        self.assets.loc[1, "Maturity"] = self.date
        self.trade()

        # nem tudom, hogy elé vagy mögé kéne, vagy mindkettő
        self.calc_nav()
        self.calc_share_of_assets()
        self.walm = np.dot(self.assets["Maturity"] - self.date, self.assets["Share"]).days
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
        self.df_all = self.df_all.merge(self.assets, how='outer', on='Name', suffixes=(str(self.date), str(self.date)))
        self.walm_list.append(self.walm)

    def plot_values(self):
        df_nav = pd.DataFrame({'Net Asset Value': self.nav_list}, index=self.date_list)

        df_nav_per_shares = pd.DataFrame({'Net Asset Value per Shares': self.nav_per_shares_list}, index=self.date_list)

        self.df_all.index = self.df_all['Name']
        df_shares = self.df_all.filter(like='Share', axis=1)
        df_shares.columns = self.date_list

        df_nav.plot()
        df_nav_per_shares.plot()
        df_shares.T.plot()

    def calculate_return_and_volatility(self):
        df_nav = pd.DataFrame({'Net Asset Value': self.nav_list}, index=self.date_list)
        df_nav_per_shares = pd.DataFrame({'Net Asset Value per Shares': self.nav_per_shares_list}, index=self.date_list)
        self.returns = df_nav_per_shares / df_nav_per_shares.shift(1) - 1
        volatility = self.returns.std() * np.sqrt(252)

    def save_to_excel(self):
        self.calculate_return_and_volatility()
        self.df_all.index = self.df_all['Name']
        df_shares = self.df_all.filter(like='Share', axis=1)
        df_shares.columns = self.date_list
        df_maturity = self.df_all.filter(like='Maturity', axis=1)
        df_maturity.columns = self.date_list
        self.returns.to_excel("returns.xlsx")
        df_shares.to_excel("shares.xlsx")
        df_maturity.to_excel("maturity.xlsx")
        self.walm_list = pd.DataFrame(self.walm_list, index=self.date_list)
        self.walm_list.to_excel("walm.xlsx")
        self.nav_list = pd.DataFrame(self.nav_list, index=self.date_list)
        self.nav_list.to_excel("nav.xlsx")
        self.transactions.to_excel('transaction_list.xlsx')

    def add_transaction(self, transaction, reason):
        new_transaction = pd.DataFrame([{
            'Date': self.date, 'Transaction': transaction, 'Reason': reason,
            'Value_of_Transaction_per_Asset (mFt)':
                self.transaction_value_per_shares
        }])
        self.transactions = pd.concat([self.transactions, new_transaction],
                                      ignore_index=True)
        self.transaction_value_per_shares = 0
