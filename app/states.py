from aiogram.fsm.state import State, StatesGroup


class PcWizard(StatesGroup):
    usage = State()     #для чого ПК
    budget = State()    #бажаний бюджет
    cpu = State()       #AMD чи Intel


class TopUp(StatesGroup):
    amount = State()
