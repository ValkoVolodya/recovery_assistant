from aiogram.fsm.state import State, StatesGroup


class SetWeightStates(StatesGroup):
    waiting_for_weight = State()
