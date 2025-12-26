from aiogram.fsm.state import State, StatesGroup


class SubscriptionStates(StatesGroup):
    """FSM состояния для подписок"""

    choosing_plan = State()
    """Выбор плана подписки"""

    confirming_subscription = State()
    """Подтверждение оформления подписки"""

    subscription_confirmed = State()
    """Подписка успешно оформлена"""


class PromoStates(StatesGroup):
    """FSM состояния для промокодов"""

    entering_promo = State()
    """Пользователь вводит промокод"""

    confirming_promo = State()
    """Подтверждение применения промокода"""

    promo_applied = State()
    """Промокод успешно применён"""


class PaymentStates(StatesGroup):
    """FSM состояния для платежей"""

    viewing_past_payments = State()
    """Просмотр прошедших платежей"""

    viewing_upcoming_payments = State()
    """Просмотр предстоящих платежей"""


class CancellationStates(StatesGroup):
    """FSM состояния для отмены подписки"""

    confirming_cancellation = State()
    """Подтверждение отмены подписки"""

    cancellation_confirmed = State()
    """Подписка успешно отменена"""
