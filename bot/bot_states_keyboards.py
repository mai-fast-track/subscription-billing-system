from aiogram.fsm.state import State, StatesGroup


class SubscriptionStates(StatesGroup):
    """Состояния для работы с подписками"""

    choosing_plan = State()
    confirming_subscription = State()
    subscription_confirmed = State()


class PromoStates(StatesGroup):
    """Состояния для работы с промокодами"""

    entering_promo = State()
    confirming_promo = State()
    promo_applied = State()


class PaymentStates(StatesGroup):
    """Состояния для просмотра платежей"""

    viewing_past_payments = State()
    viewing_upcoming_payments = State()


class CancellationStates(StatesGroup):
    """Состояния для отмены подписки"""

    confirming_cancellation = State()
    cancellation_confirmed = State()
