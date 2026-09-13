from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    request_contact = State()
    waiting_for_wallet = State()
    waiting_for_amount = State()
    waiting_for_support_message = State()
