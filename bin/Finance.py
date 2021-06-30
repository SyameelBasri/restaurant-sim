from bin import *
import json


class Finance:
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.latestEntry = None
        self.cashFlow = {'daily': [], 'monthly': [], 'yearly': []}

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.evManager.RegisterListener(self)

    def FirstDay(self, cash):
        self.NewDay(cash)
        self.NewMonth(cash)
        self.NewYear(cash)

    def NewDay(self, cash):
        if Date.day == self.latestEntry:
            return

        self.latestEntry = Date.day

        cashFlow = dict()

        cashFlow[FIN_SALES] = 0
        cashFlow[FIN_INVENTORY] = 0
        cashFlow[FIN_MARKETING] = 0
        cashFlow[FIN_RENOVATION] = 0
        cashFlow[FIN_SALARY] = 0
        cashFlow[FIN_MISC] = 0
        cashFlow[FIN_CASH] = cash
        cashFlow['Profit'] = 0
        cashFlow['Expense'] = 0
        cashFlow['Day'] = Date.day
        cashFlow['Month'] = Date.month
        cashFlow['Year'] = Date.year

        self.cashFlow['daily'].append(cashFlow)

    def NewMonth(self, cash):
        cashFlow = dict()
        cashFlow[FIN_SALES] = 0
        cashFlow[FIN_INVENTORY] = 0
        cashFlow[FIN_MARKETING] = 0
        cashFlow[FIN_RENOVATION] = 0
        cashFlow[FIN_SALARY] = 0
        cashFlow[FIN_MISC] = 0
        cashFlow[FIN_CASH] = cash
        cashFlow['Profit'] = 0
        cashFlow['Expense'] = 0
        cashFlow['Month'] = Date.month
        cashFlow['Year'] = Date.year

        self.cashFlow['monthly'].append(cashFlow)

    def NewYear(self, cash):
        cashFlow = dict()
        cashFlow[FIN_SALES] = 0
        cashFlow[FIN_INVENTORY] = 0
        cashFlow[FIN_MARKETING] = 0
        cashFlow[FIN_RENOVATION] = 0
        cashFlow[FIN_SALARY] = 0
        cashFlow[FIN_MISC] = 0
        cashFlow[FIN_CASH] = cash
        cashFlow['Profit'] = 0
        cashFlow['Expense'] = 0
        cashFlow['Year'] = Date.year

        self.cashFlow['yearly'].append(cashFlow)

    def CashFlow(self, value, category, cash):
        self.CashFlowDay(value, category, cash)
        self.CashFlowMonth(value, category, cash)
        self.CashFlowYear(value, category, cash)

    def CashFlowDay(self, value, category, cash):

        i = Date.dayNumber
        self.cashFlow['daily'][i][FIN_CASH] = cash
        self.cashFlow['daily'][i][category] += value

        if category in [FIN_INVENTORY, FIN_MARKETING, FIN_RENOVATION, FIN_SALARY, FIN_MISC]:
            self.cashFlow['daily'][i]['Expense'] += value

        self.cashFlow['daily'][i]['Profit'] = self.cashFlow['daily'][i]['Sales'] - self.cashFlow['daily'][i]['Expense']

    def CashFlowMonth(self, value, category, cash):

        i = Date.monthNumber
        self.cashFlow['monthly'][i][FIN_CASH] = cash
        self.cashFlow['monthly'][i][category] += value

        if category in [FIN_INVENTORY, FIN_MARKETING, FIN_RENOVATION, FIN_SALARY, FIN_MISC]:
            self.cashFlow['monthly'][i]['Expense'] += value

        self.cashFlow['monthly'][i]['Profit'] = self.cashFlow['monthly'][i]['Sales'] - self.cashFlow['monthly'][i]['Expense']

    def CashFlowYear(self, value, category, cash):

        i = Date.yearNumber
        self.cashFlow['yearly'][i][FIN_CASH] = cash
        self.cashFlow['yearly'][i][category] += value

        if category in [FIN_INVENTORY, FIN_MARKETING, FIN_RENOVATION, FIN_SALARY, FIN_MISC]:
            self.cashFlow['yearly'][i]['Expense'] += value

        self.cashFlow['yearly'][i]['Profit'] = self.cashFlow['yearly'][i]['Sales'] - self.cashFlow['yearly'][i]['Expense']

    def CashBook(self, fiscalTerm):
        statementList = []

        if fiscalTerm == FIN_TERM_DAILY:
            i = Date.dayNumber

            if len(self.cashFlow[fiscalTerm]) >= 3:
                statementList.append(self.cashFlow[fiscalTerm][i])
                statementList.append(self.cashFlow[fiscalTerm][i - 1])
                statementList.append(self.cashFlow[fiscalTerm][i - 2])

            else:
                for x in range(len(self.cashFlow[fiscalTerm])):
                    statementList.append(self.cashFlow[fiscalTerm][i - x])

        elif fiscalTerm == FIN_TERM_MONTHLY:
            i = Date.monthNumber

            if len(self.cashFlow[fiscalTerm]) >= 3:
                statementList.append(self.cashFlow[fiscalTerm][i])
                statementList.append(self.cashFlow[fiscalTerm][i - 1])
                statementList.append(self.cashFlow[fiscalTerm][i - 2])

            else:
                for x in range(len(self.cashFlow[fiscalTerm])):
                    statementList.append(self.cashFlow[fiscalTerm][i - x])

        elif fiscalTerm == FIN_TERM_YEARLY:
            i = Date.yearNumber

            if len(self.cashFlow[fiscalTerm]) >= 3:
                statementList.append(self.cashFlow[fiscalTerm][i])
                statementList.append(self.cashFlow[fiscalTerm][i - 1])
                statementList.append(self.cashFlow[fiscalTerm][i - 2])

            else:
                for x in range(len(self.cashFlow[fiscalTerm])):
                    statementList.append(self.cashFlow[fiscalTerm][i - x])

        return statementList

    # get daily or monthly or yearly
    # check date
    # pass the value in the dict

    def Notify(self, event):
        if isinstance(event, RequestFinanceWindowEvent):
            ev = UpdateFinanceWindowEvent(self.CashBook(event.fiscalTerm))
            self.evManager.Post(ev)

