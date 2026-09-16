from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    request_contact = State()
    waiting_for_pubg_id = State()
    waiting_for_wallet = State()
    waiting_for_amount = State()
    waiting_for_support_message = State()

    # UC sotib olish bosqichlari
    buy_waiting_for_pubg_id = State()
    buy_waiting_for_receipt = State()

    # UC yechish bosqichlari
    withdraw_waiting_for_pubg_id = State()
    withdraw_waiting_for_amount = State()
