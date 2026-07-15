from aiogram.fsm.state import State, StatesGroup


class SetWeightStates(StatesGroup):
    waiting_for_weight = State()


class SetFtpStates(StatesGroup):
    waiting_for_ftp = State()
