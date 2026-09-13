from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_plus_amount = State()
    waiting_for_minus_amount = State()
    waiting_for_mandatory_channel = State()
    waiting_for_payment_channel = State()
    waiting_for_payment_system_name = State()
    waiting_for_taklif_price = State()
    waiting_for_currency_name = State()
    waiting_for_min_withdrawal = State()
    waiting_for_admin_user = State()
    waiting_for_button_code = State()
    waiting_for_button_value = State()
    waiting_for_text_code = State()
    waiting_for_text_value = State()
    waiting_for_broadcast_text = State()
    waiting_for_broadcast_forward = State()
    waiting_for_direct_user_id = State()
    waiting_for_direct_message = State()
    waiting_for_earn_photo = State()
