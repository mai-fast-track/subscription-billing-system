# Архитектура Billing Core API

## Обзор системы

---

## Технологический стек

### Backend
- **FastAPI** — веб-фреймворк для API
- **SQLAlchemy** — ORM для работы с БД (async и sync версии)
- **PostgreSQL** — основная база данных
- **Alembic** — миграции БД

### Фоновые задачи
- **Celery** — асинхронная обработка задач
- **Redis** — брокер сообщений и кэш

### Интеграции
- **YooKassa SDK** — платежный шлюз
- **Telegram Bot API** — уведомления пользователям



## Модели данных

### User (Пользователь)

```python
- id: int (PK)
- telegram_id: int (unique, indexed)
- role: UserRole (client/admin)
- saved_payment_method_id: str (nullable) # ID сохраненного метода оплаты
- created_at: datetime
- updated_at: datetime
```

### Subscription (Подписка)

```python
- id: int (PK)
- user_id: int (FK → users.id, indexed)
- plan_id: int (FK → subscription_plans.id)
- status: str # active, cancelled, cancelled_waiting, expired, pending_payment
- promotion_id: int (FK → promotions.id, nullable, indexed) # Связанный промокод
- start_date: datetime
- end_date: datetime
- created_at: datetime
- updated_at: datetime
```

**Статусы подписки:**
- `active` — активная подписка
- `cancelled` — отменена пользователем (финальный статус)
- `cancelled_waiting` — отменена, но активна до `end_date` (подписка остается активной до конца оплаченного периода)
- `expired` — истекла после неудачных попыток оплаты
- `pending_payment` — ожидает оплаты

**Важно о статусе `cancelled_waiting`:**
- Подписка остается активной до `end_date` (дата окончания не изменяется)
- Автоплатежи отключены (проверка статуса в логике автоплатежей)
- Платежный метод пользователя очищается (`saved_payment_method_id = None`)
- В конце дня задача `process_cancelled_waiting_subscriptions` переводит статус в `cancelled`
- Пользователь может создать новую подписку (не блокирует создание)

**Важно о статусе `cancelled`:**
- Финальный статус отмененной подписки
- `end_date` установлена в дату отмены (доступ прекращен)
- Автоплатежи отключены
- Платежный метод пользователя очищен
- Пользователь может создать новую подписку (не блокирует создание)
- При успешной оплате подписка может быть реактивирована и продлена

### SubscriptionPlan (Тарифный план)

```python
- id: int (PK)
- name: str
- price: float
- duration_days: int
- features: str (nullable)
- created_at: datetime
- updated_at: datetime
```

### Payment (Платеж)

```python
- id: int (PK)
- subscription_id: int (FK → subscriptions.id)
- user_id: int (FK → users.id)
- yookassa_payment_id: str (unique, indexed) # ID платежа в YooKassa
- amount: float
- currency: str (default: "RUB")
- status: str # pending, succeeded, failed, cancelled
- payment_method: str # auto_payment, manual
- attempt_number: int (default: 1) # Для retry логики
- next_retry_at: datetime (nullable)
- error_reason: str (nullable)
- idempotency_key: str (unique) # Защита от дублей
- created_at: datetime
- updated_at: datetime
```

**Статусы платежа:**
- `pending` — ожидает обработки
- `succeeded` — успешно завершен
- `failed` — неудачный платеж
- `cancelled` — отменен


**Идемпотентность:**
- `idempotency_key` гарантирует уникальность платежа
- Формат для автоплатежей: `auto_payment_{subscription_id}_{date}`

### Refund (Возврат)

```python
- id: int (PK)
- payment_id: int (FK → payments.id, CASCADE)
- yookassa_refund_id: str (unique, indexed) # ID возврата в YooKassa
- amount: float
- currency: str (default: "RUB")
- status: str # pending, succeeded, failed, cancelled
- reason: str (nullable) # Причина возврата
- created_at: datetime
- updated_at: datetime
```

**Статусы возврата:**
- `pending` — возврат создан, ожидает обработки
- `succeeded` — возврат успешно выполнен
- `failed` — возврат не удался
- `cancelled` — возврат отменен

**Особенности:**
- Один платеж может иметь только один возврат (проверка на уровне бизнес-логики)
- Связь с платежом через `payment_id` с каскадным удалением
- `yookassa_refund_id` уникален для связи с YooKassa API

### Promotion (Промокод)

```python
- id: int (PK)
- code: str (unique, indexed)
- name: str
- description: str (nullable)
- type: str # "bonus_days" (единственный поддерживаемый тип)
- valid_from: datetime
- valid_until: datetime (nullable)
- is_active: bool (default: True)
- max_uses: int (nullable) # None = unlimited
- current_uses: int (default: 0)
- value: int (nullable) # Количество бонусных дней
- assigned_user_id: int (nullable, FK → users.id) # Если указан, промокод доступен только этому пользователю
- created_at: datetime
- updated_at: datetime
```

**Типы промокодов:**
- `bonus_days` — добавляет бонусные дни к подписке (продлевает `end_date`)

**Особенности:**
- Промокоды могут быть общими (`assigned_user_id = None`) или персональными (`assigned_user_id` указан)
- Один пользователь может использовать промокод только один раз (отслеживается через `UserPromotionUsage`)
- Промокоды применяются к активным подпискам через `POST /api/v1/subscriptions/{subscription_id}/apply-promotion`

### UserPromotionUsage (Использование промокода)

```python
- id: int (PK)
- user_id: int (FK → users.id, CASCADE)
- promotion_id: int (FK → promotions.id, CASCADE)
- subscription_id: int (FK → subscriptions.id, nullable)
- created_at: datetime
- UniqueConstraint: (user_id, promotion_id) # Один пользователь может использовать промокод только один раз
```

**Особенности:**
- Отслеживает использование промокодов пользователями
- Связывает промокод с подпиской, к которой он был применен

---
## Бизнес-правила и ограничения:

### Подписки
- Один пользователь может иметь только одну активную подписку (статус `active`)
- Подписки со статусом `cancelled_waiting` или `cancelled` не блокируют создание новой подписки
- Подписка может иметь связанный промокод через `promotion_id`

### Промопериод (Trial Period)
- Новые пользователи могут получить промопериод (по умолчанию 7 дней, настраивается через `TRIAL_PERIOD_DAYS`)
- Промопериод доступен только один раз для каждого пользователя
- Промопериод не требует привязки карты
- Если пользователь не воспользовался промопериодом, а сразу оплатил, он не считается новым пользователем
- Промопериод создается через `POST /api/v1/subscriptions/create-trial`
- Платеж для промопериода имеет `yookassa_payment_id = "trial_period"` и статус `succeeded`
- Триал-платежи не возвращаются при отмене подписки

### Промокоды
- Промокоды типа `bonus_days` продлевают активную подписку на указанное количество дней
- Промокод можно применить только к активной подписке
- Один пользователь может использовать промокод только один раз
- Промокоды могут быть общими или персональными (назначенными конкретному пользователю)

## Архитектура обработки платежей

### Поток создания платежа

1. **Клиент** → `POST /api/v1/payments` или `/payments/two-stage`
2. **PaymentService** создает платеж в YooKassa
3. Сохраняет платеж в БД со статусом `pending`
4. Возвращает клиенту `confirmation_url` для оплаты
5. **Пользователь** переходит по ссылке и оплачивает
6. **YooKassa** отправляет webhook → `POST /api/v1/payments/webhook`
7. **PaymentService.process_webhook()** обновляет статус платежа
8. При успешном платеже продлевается подписка

### Webhook обработка

**Endpoint:** `POST /api/v1/payments/webhook`

**Логика:**
1. Получение webhook от YooKassa
2. Поиск платежа по `yookassa_payment_id`
3. Обновление статуса платежа в БД
4. Если статус `succeeded`:
   - Продление подписки (`end_date += duration_days`)
   - Обновление статуса подписки на `active`
   - Отправка уведомления пользователю

**Важно:** Webhook endpoint всегда возвращает `200 OK`, даже при ошибках (требование YooKassa).

### Webhook обработка возвратов

**Событие:** `refund.succeeded`

**Логика:**
1. Получение webhook от YooKassa с событием `refund.succeeded`
2. Поиск возврата по `yookassa_refund_id`
3. Обновление статуса возврата в БД на `succeeded`
4. Логирование успешного возврата

**Обработчик:** `PaymentService._process_refund_webhook()`

---

## Система отмены подписки и возвратов

### Обзор

Система поддерживает отмену подписки с сохранением доступа до конца оплаченного периода и автоматическую обработку возвратов средств.

### Архитектура отмены подписки

#### Компоненты

1. **SubscriptionService** (`app/services/subscription_service.py`)
   - Метод `cancel_subscription()` — основная логика отмены
   - Метод `_process_refunds_for_cancellation()` — обработка возвратов

2. **PaymentService** (`app/services/payment_service.py`)
   - Метод `calculate_refund_amount()` — расчет суммы возврата
   - Метод `create_refund()` — создание возврата через YooKassa API
   - Метод `_process_refund_webhook()` — обработка webhook о возврате

3. **YookassaClient** (`app/core/clients/yookassa_client.py`)
   - Метод `create_refund()` — создание возврата через YooKassa API

4. **RefundRepository** (`app/database/repositories/refund_repository.py`)
   - Управление возвратами в БД

### Поток отмены подписки

Система поддерживает **два сценария отмены подписки**:

1. **Отмена без возврата** (`with_refund=False`, по умолчанию)
2. **Отмена с возвратом** (`with_refund=True`)

#### Шаг 1: запрос отмены

**Endpoint:** `PATCH /api/v1/subscriptions/{subscription_id}/cancel`

**Параметры:**
- `with_refund: bool = False` — выполнить возврат средств

**Сценарий 1: Отмена без возврата (`with_refund=False`)**

**Логика:**
1. Проверка статуса подписки (нельзя отменить уже отмененную)
2. Установка статуса `cancelled_waiting` (не изменяется `end_date`)
3. Возврат **НЕ выполняется**
4. Очистка `saved_payment_method_id` пользователя

**Важно:**
- `end_date` **НЕ изменяется** — подписка остается активной до конца оплаченного периода
- Статус устанавливается в `cancelled_waiting`, а не `cancelled`
- Автоплатежи отключаются автоматически (проверка статуса в логике автоплатежей)
- Пользователь сохраняет доступ до `end_date`
- Пользователь может создать новую подписку сразу после отмены

**Сценарий 2: Отмена с возвратом (`with_refund=True`)**

**Логика:**
1. Проверка статуса подписки (нельзя отменить уже отмененную)
2. Расчет суммы возврата за неиспользованную часть (используя оригинальный `end_date`)
3. Создание возврата через YooKassa API
4. Установка статуса `cancelled`
5. Установка `end_date` в текущую дату (доступ прекращается сразу)
6. Очистка `saved_payment_method_id` пользователя

**Важно:**
- `end_date` устанавливается в текущую дату — доступ прекращается сразу
- Статус устанавливается в `cancelled` (финальный статус)
- Выполняется возврат за неиспользованную часть периода
- Автоплатежи отключаются автоматически
- Пользователь может создать новую подписку сразу после отмены

#### Шаг 2: Обработка возвратов (только для `with_refund=True`)

**Метод:** `SubscriptionService._process_refunds_for_cancellation()`

**Важно:** Этот метод вызывается только при `with_refund=True`. При `with_refund=False` возвраты не обрабатываются.

**Логика:**
1. Получение всех успешных платежей для подписки
2. Поиск последнего успешного платежа (не триал)
3. Проверка, не был ли уже создан возврат для этого платежа
4. Расчет суммы возврата через `PaymentService.calculate_refund_amount()` (используя оригинальный `end_date`)
5. Создание возврата через `PaymentService.create_refund()` (если сумма > 0)
6. После создания возврата устанавливается `end_date` в текущую дату

**Исключения:**
- Триал-платежи (`yookassa_payment_id == "trial_period"`) не возвращаются
- Если возврат уже создан — пропускается
- Если сумма возврата = 0 — возврат не создается

#### Шаг 3: Расчет суммы возврата

**Метод:** `PaymentService.calculate_refund_amount()`

**Политика возврата:**

1. **Полный возврат** (если платеж < 14 дней назад):
   - Возвращается полная сумма платежа
   - Пример: платеж 1000 ₽, отмена через 5 дней → возврат 1000 ₽

2. **Частичный возврат** (если платеж > 14 дней назад):
   - Возврат пропорционален неиспользованному периоду
   - Формула: `refund_amount = payment.amount * (days_remaining / total_days)`
   - Пример: платеж 1000 ₽ за 30 дней, отмена через 20 дней, осталось 10 дней → возврат 333.33 ₽

3. **Нет возврата**:
   - Если период подписки истек (`end_date` в прошлом)
   - Для триал-платежей

**Логика расчета:**
```python
days_since_payment = (now - payment.created_at).days
days_remaining = (subscription.end_date - now).days
total_days = plan.duration_days

if days_since_payment <= 14:
    refund_amount = payment.amount  # Полный возврат
else:
    refund_ratio = days_remaining / total_days
    refund_amount = payment.amount * refund_ratio  # Пропорциональный
```

#### Шаг 4: Создание возврата

**Метод:** `PaymentService.create_refund()`

**Логика:**
1. Валидация платежа (статус должен быть `succeeded`)
2. Проверка, что возврат еще не создан
3. Валидация суммы возврата (0 < amount <= payment.amount)
4. Создание возврата через YooKassa API (`YookassaClient.create_refund()`)
5. Сохранение возврата в БД со статусом `pending`
6. Логирование операции

**Обработка ошибок:**
- Если платеж не успешен → `ValueError`
- Если возврат уже создан → `ValueError`
- Если сумма некорректна → `ValueError`
- Ошибки YooKassa API → логируются и пробрасываются

#### Шаг 5: Обновление статуса возврата

**Webhook:** `POST /api/v1/payments/webhook` (событие `refund.succeeded`)

**Логика:**
1. Получение webhook от YooKassa с событием `refund.succeeded`
2. Поиск возврата по `yookassa_refund_id`
3. Обновление статуса возврата в БД на `succeeded`
4. Логирование успешного возврата

### Интеграция с автоплатежами

#### Защита от автоплатежей для отмененных подписок

**Проверка статуса в `AutoPaymentServiceSync.process_single_subscription_payment()`:**
```python
if locked_subscription.status in [
    SubscriptionStatus.cancelled.value,
    SubscriptionStatus.cancelled_waiting.value,
]:
    return {"success": False, "error": "subscription_cancelled"}
```

**Проверка статуса в `AutoPaymentServiceSync.retry_auto_payment_attempt()`:**
```python
if subscription.status in [
    SubscriptionStatus.cancelled.value,
    SubscriptionStatus.cancelled_waiting.value,
]:
    return {"success": False, "error": "subscription_cancelled"}
```

**Результат:**
- Подписки со статусом `cancelled_waiting` не обрабатываются автоплатежами
- Платежи не создаются для отмененных подписок
- Пользователь сохраняет доступ до `end_date`, но автоплатежи отключены

### Финальная обработка отмененных подписок

**Задача:** `process_cancelled_waiting_subscriptions` (23:00 UTC)

**Логика:**
1. Получение всех подписок со статусом `cancelled_waiting`
2. Для каждой подписки (с блокировкой):
   - Проверка, что `end_date` наступил или прошел
   - Обновление статуса на `cancelled`
3. Логирование результатов

**Результат:** Все подписки со статусом `cancelled_waiting` переведены в `cancelled`.

### Модель данных возвратов

**Таблица:** `refunds`

**Связи:**
- `payment_id` → `payments.id` (CASCADE DELETE)
- `yookassa_refund_id` → уникальный ID в YooKassa

**Индексы:**
- `ix_refunds_payment_id` — для быстрого поиска по платежу
- `ix_refunds_yookassa_refund_id` — для поиска по ID YooKassa (unique)

### Безопасность и валидация

#### Защита от дублей

1. **Проверка существующего возврата:**
   ```python
   existing_refund = await self.uow.refunds.get_by_payment_id(payment_id)
   if existing_refund:
       raise ValueError("Возврат уже создан")
   ```

2. **Идемпотентность YooKassa:**
   - Каждый возврат имеет уникальный `idempotency_key`
   - YooKassa гарантирует, что повторный запрос с тем же ключом вернет тот же возврат

#### Валидация данных

1. **Проверка статуса платежа:**
   - Только платежи со статусом `succeeded` могут быть возвращены

2. **Проверка суммы:**
   - `0 < refund_amount <= payment.amount`
   - Сумма округляется до 2 знаков после запятой

3. **Проверка статуса подписки:**
   - Нельзя отменить уже отмененную подписку
   - Проверка выполняется перед изменением статуса

---

## Система автоматических платежей

### Обзор

Система автоматически продлевает подписки пользователей, у которых есть сохраненный платежный метод (`saved_payment_method_id`).

### Архитектура (новая версия)

Система использует **одноразовый сбор подписок** в начале дня и **асинхронную обработку** с Redis для координации.

#### Компоненты

1. **Redis Client** (`app/core/redis_client.py`)
   - Хранение ID подписок для координации
   - Ключи: `auto_payment:subscriptions:{date}` → SET[subscription_id1, ...]
   - TTL: 24 часа

2. **Celery Tasks** (`app/tasks/auto_payment.py`)
   - `collect_subscriptions_for_payment` — сбор подписок в начале дня
   - `process_single_subscription_payment` — обработка одной подписки
   - `retry_auto_payment_attempt` — попытка автосписания
   - `process_cancelled_waiting_subscriptions` — финальная обработка в конце дня
   - `send_payment_reminders` — напоминания о платежах

3. **Service** (`app/services/auto_payment_service_sync.py`)
   - Бизнес-логика обработки платежей
   - Защиты от гонок (SELECT FOR UPDATE)
   - Идемпотентность

### Поток выполнения

#### День 1: Начало дня (02:00 UTC)

**Задача: `collect_subscriptions_for_payment`**

1. Читает из БД все активные подписки с `end_date` сегодня
2. Сохраняет ID подписок в Redis: `auto_payment:subscriptions:2024-01-15`
3. Для каждой подписки запускает отдельную задачу: `process_single_subscription_payment.delay(subscription_id)`

**Результат:** Список подписок сохранен в Redis, запущены задачи обработки.

#### День 1: Обработка подписок (параллельно)

**Задача: `process_single_subscription_payment(subscription_id)`**

1. Блокирует подписку: `SELECT FOR UPDATE`
2. Проверяет идемпотентность (есть ли платеж сегодня)
3. **Если есть `saved_payment_method_id`:**
   - Создает `Payment` в БД (status=pending, attempt_number=1)
   - Запускает первую попытку: `retry_auto_payment_attempt.apply_async(payment_id, attempt=1, countdown=0)`
   - Удаляет из Redis
4. **Если нет `saved_payment_method_id`:**
   - Создает `Payment` в БД (manual, со ссылкой)
   - Отправляет уведомление со ссылкой на оплату (1 раз)
   - Обновляет БД: `Subscription.status = cancelled`
   - Удаляет из Redis

**Результат:** Платежи созданы, попытки запущены (для подписок с методом), подписки без метода помечены как cancelled.

#### День 1: Попытки автосписания (асинхронно, с интервалом)

**Задача: `retry_auto_payment_attempt(payment_id, attempt)`**

1. Блокирует подписку и платеж: `SELECT FOR UPDATE`
2. Проверяет статус подписки (не cancelled)
3. Проверяет статус платежа в YooKassa
4. **Если успех:**
   - Обновляет БД: `Payment.status = succeeded`
   - Продлевает подписку: `Subscription.end_date += duration_days`, `status = active`
   - Отправляет финальное уведомление: "✅ Подписка продлена до..."
5. **Если неудача и `attempt < MAX_ATTEMPTS`:**
   - Обновляет БД: `Payment.attempt_number += 1`, `status = failed`
   - Запускает следующую попытку: `retry_auto_payment_attempt.apply_async(payment_id, attempt+1, countdown=INTERVAL)`
6. **Если неудача и `attempt == MAX_ATTEMPTS`:**
   - Обновляет БД: `Payment.status = failed`, `Subscription.status = cancelled_waiting`
   - Отправляет финальное уведомление: "❌ Не удалось продлить подписку..."

**Результат:** Платежи обработаны, подписки продлены или помечены как cancelled_waiting.

#### День 1: Конец дня (23:00 UTC)

**Задача: `process_cancelled_waiting_subscriptions`**

1. Читает из БД все подписки со статусом `cancelled_waiting`
2. Для каждой подписки (с блокировкой):
   - Обновляет БД: `Subscription.status = cancelled`
3. Redis не используется (читаем только из БД)

**Результат:** Все подписки со статусом cancelled_waiting переведены в cancelled.

#### API для управления настройками

**Получить текущие настройки:**
```
GET /api/v1/auto-payments/config
```

**Обновить настройки:**
```
PUT /api/v1/auto-payments/config
Body: {"retry_interval_seconds": 120, "max_attempts": 5}
```

**Сбросить к значениям по умолчанию:**
```
POST /api/v1/auto-payments/config/reset
```

#### Инициализация подписчика

При старте Celery worker автоматически запускается подписчик на настройки автоплатежей.

Инициализация происходит в `app/celery_app.py` через сигнал `worker_process_init`.

**Особенности реализации:**

- **Thread-safe инициализация**: использование `threading.Lock()` для защиты от race conditions
- **Автоматическое переподключение**: при разрыве соединения с Redis подписчик автоматически переподключается (до 5 попыток)
- **Валидация данных**: все конфигурации валидируются перед обновлением кеша
- **Graceful shutdown**: корректное завершение подписчика при остановке приложения (в `main.py` и `celery_app.py`)
- **Обработка ошибок**: при недоступности Redis система продолжает работать с кешированными или default значениями

### Защиты и идемпотентность

#### 1. Блокировки
- `SELECT FOR UPDATE` при обработке подписки/платежа
- Предотвращает гонки между автосписанием и отменой подписки

#### 2. Идемпотентность платежей
- `idempotency_key = f"auto_payment_{subscription_id}_{date}"`
- Гарантирует, что при retry будет использован тот же ключ
- Проверка существующих платежей перед созданием нового

#### 3. Проверка статуса подписки
- После блокировки проверяем статус (защита от отмены в день платежа)
- Если подписка cancelled — пропускаем платеж

#### 4. Проверка продления
- Перед продлением проверяем, не была ли подписка уже продлена
- Защита от двойных платежей при retry после timeout коммита


---

## Управление транзакциями

### Unit of Work Pattern

Система использует паттерн **Unit of Work** для управления транзакциями:

- **Async UoW** (`app/database/unit_of_work.py`) — для FastAPI endpoints
- **Sync UoW** (`app/database/sync_unit_of_work.py`) — для Celery задач

**Принципы:**
- Каждая операция выполняется в отдельной транзакции
- UoW управляет commit/rollback автоматически через контекстный менеджер
- При ошибке транзакция откатывается, изменения не сохраняются

### Подключения к БД

- **FastAPI:** Async engine с пулом соединений (pool_size=20)
- **Celery:** Sync engine с пулом соединений (pool_size=5 на worker)
- Каждый worker процесс имеет свой пул соединений

---

## Интеграции

### YooKassa

**Клиент:** `app/core/clients/yookassa_client.py`

**Методы:**
- `create_payment()` — одностадийный платеж
- `create_payment_two_stage()` — двухстадийный платеж
- `capture_payment()` — подтверждение двухстадийного платежа
- `cancel_payment()` — отмена платежа
- `get_payment()` — получение информации о платеже
- `create_refund()` — создание возврата платежа (полный или частичный)

**Особенности:**
- Retry логика для обработки временных ошибок (429, 500)
- Exponential backoff для повторных попыток
- Идемпотентность через `idempotency_key`

### Telegram

**Уведомления:** `app/core/telegram_notifier.py`

**Использование:**
- Уведомления о статусе платежей
- Напоминания о необходимости оплаты
- Уведомления о продлении подписки

---
### Идемпотентность

- Все платежи имеют уникальный `idempotency_key`
- Защита от двойных платежей на уровне БД (unique constraint)
- Идемпотентность API YooKassa

### Защита от гонок

- `SELECT FOR UPDATE` блокировки при обработке платежей
- Предотвращение параллельной обработки одной подписки

---

## Система промокодов и промопериода

### Обзор

Система поддерживает два типа промо-механик:

1. **Промопериод (Trial Period)** — бесплатный период для новых пользователей
2. **Промокоды (Promotions)** — бонусные дни для продления активных подписок

### Промопериод (Trial Period)

**Особенности:**
- Доступен только один раз для каждого пользователя
- Не требует привязки платежного метода
- Настраивается через `TRIAL_PERIOD_DAYS` (по умолчанию 7 дней)
- Создается через `POST /api/v1/subscriptions/create-trial`
- Платеж для промопериода имеет `yookassa_payment_id = "trial_period"` и статус `succeeded`
- Триал-платежи не возвращаются при отмене подписки

**Проверка доступности:**
- `GET /api/v1/subscriptions/check-trial-eligibility/{user_id}` — проверить, доступен ли промопериод
- Промопериод недоступен, если:
  - Пользователь уже использовал промопериод (есть платеж с `yookassa_payment_id = "trial_period"`)
  - У пользователя уже есть активная подписка

**Бизнес-правила:**
- Если пользователь не воспользовался промопериодом, а сразу оплатил, он не считается новым пользователем
- Промопериод создает активную подписку со статусом `active`
- После окончания промопериода подписка может быть продлена через автоплатежи или ручную оплату

### Промокоды (Promotions)

**Типы промокодов:**
- `bonus_days` — единственный поддерживаемый тип, добавляет бонусные дни к подписке

**Особенности:**
- Промокоды могут быть общими (`assigned_user_id = None`) или персональными (`assigned_user_id` указан)
- Один пользователь может использовать промокод только один раз (отслеживается через `UserPromotionUsage`)
- Промокод можно применить только к активной подписке
- Применение промокода продлевает `end_date` подписки на указанное количество дней

**API для промокодов:**
- `GET /api/v1/promotions/available` — получить доступные промокоды для текущего пользователя
- `POST /api/v1/subscriptions/{subscription_id}/apply-promotion` — применить промокод к активной подписке

**Валидация промокода:**
- Промокод должен быть активным (`is_active = True`)
- Промокод должен быть в периоде действия (`valid_from <= now`, `valid_until >= now` или `None`)
- Промокод не должен быть исчерпан (`current_uses < max_uses` или `max_uses = None`)
- Пользователь не должен был использовать промокод ранее
- Если промокод персональный, он должен быть назначен текущему пользователю

### Модель UserPromotionUsage

Отслеживает использование промокодов пользователями:
- Гарантирует, что один пользователь не может использовать промокод дважды
- Связывает промокод с подпиской, к которой он был применен
- Уникальное ограничение: `(user_id, promotion_id)`



## Примечания

- **API (FastAPI):** Использует async UoW и AsyncSession
- **Celery задачи:** Используют sync UoW и Session
- **Разделение:** Чёткое разделение async (API) и sync (Celery) частей
- 
   - Одноразовый сбор подписок вместо периодических проверок
   - Параллельная обработка подписок
   - Короткие задачи (< 30 секунд)
  
   - БД — единственный источник истины
   - Redis — только координация (можно очистить без потери данных)
   - Отказоустойчивость: если Redis упадет, данные в БД сохранятся
  
   - Можно добавить больше workers для параллельной обработки
   - Каждая подписка обрабатывается независимо
