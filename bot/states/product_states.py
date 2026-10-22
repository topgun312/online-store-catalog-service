from aiogram.fsm.state import State, StatesGroup


class ProductCreate(StatesGroup):
    waiting_category = State()
    waiting_new_category = State()
    waiting_title_photo = State()


class ProductSelect(StatesGroup):
    choosing = State()


class ProductEdit(StatesGroup):
    waiting_title_photo = State()
    choosing_category = State()
    waiting_new_category = State()
