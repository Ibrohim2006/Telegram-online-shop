from aiogram.fsm.state import State, StatesGroup

class UserRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class ProductSelection(StatesGroup):
    browsing_categories = State()
    viewing_product = State()
    selecting_color = State()

class CartManagement(StatesGroup):
    viewing_cart = State()
    removing_item = State()

class OrderCreation(StatesGroup):
    entering_address = State()
    entering_phone = State()
    confirming_order = State()