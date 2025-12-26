"""
Секция управления автосписаниями
"""

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

admin_pannel_path = Path(__file__).parent.parent
if str(admin_pannel_path) not in sys.path:
    sys.path.insert(0, str(admin_pannel_path))

project_root = admin_pannel_path.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import config
import utils

from billing_core_api_client.api.auto_payments import (
    collect_subscriptions_for_payment_api_v1_auto_payments_collect_subscriptions_post,
    get_auto_payment_config_api_v1_auto_payments_config_get,
    get_redis_status_api_v1_auto_payments_redis_status_get,
    process_auto_payments_today_api_v1_auto_payments_process_today_post,
    process_cancelled_waiting_api_v1_auto_payments_process_cancelled_waiting_post,
    process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post,
    retry_auto_payment_api_v1_auto_payments_retry_payment_payment_id_attempt_post,
    simulate_subscription_ending_api_v1_auto_payments_simulate_subscription_ending_subscription_id_post,
    test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post,
)
from billing_core_api_client.api.payments import (
    get_user_payments_api_v1_payments_user_user_id_get,
)
from billing_core_api_client.api.subscriptions import (
    get_subscription_api_v1_subscriptions_subscription_id_get,
)


def _convert_payments_to_dicts(payments: Any) -> list[dict]:
    """Преобразует список платежей в список словарей"""
    if not payments:
        return []
    
    if not isinstance(payments, list):
        return []
    
    result = []
    for payment in payments:
        if isinstance(payment, dict):
            result.append(payment)
        elif hasattr(payment, "to_dict"):
            result.append(payment.to_dict())
        elif hasattr(payment, "model_dump"):
            result.append(payment.model_dump())
        elif hasattr(payment, "dict"):
            result.append(payment.dict())
        elif hasattr(payment, "__dict__"):
            result.append(payment.__dict__)
        else:
            try:
                result.append(dict(payment))
            except (TypeError, ValueError):
                continue
    
    return result


def render_auto_payments_tab():
    """Отрисовать вкладку управления автосписаниями"""
    st.header("🔄 Управление автосписаниями")

    _render_process_subscription_section()
    st.divider()
    _render_test_subscription_section()
    st.divider()
    _render_retry_payment_section()
    st.divider()
    _render_simulate_ending_section()
    st.divider()
    _render_process_all_subscriptions_section()
    st.divider()
    _render_full_demo_cycle_section()
    _render_final_processing_button()


def _render_process_subscription_section():
    """Секция обработки подписки по ID"""
    st.subheader("Обработка подписки")
    st.markdown("Запускает Celery задачу для обработки одной подписки по её ID")
    with st.form("process_subscription_form"):
        subscription_id = st.number_input(
            "ID подписки",
            min_value=1,
            step=1,
            key="process_subscription_id",
            help="Введите ID подписки для обработки",
        )
        submitted = st.form_submit_button("Обработать подписку", use_container_width=True)

        if submitted and subscription_id:
            _handle_process_subscription(subscription_id)


def _handle_process_subscription(subscription_id: int):
    """Обработка запроса на обработку подписки"""
    try:
        client = config.get_client()
        with client:
            response = process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Задача запущена успешно!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при обработке подписки: {str(e)}")


def _render_test_subscription_section():
    """Секция тестирования автоплатежа"""
    st.subheader("Тестирование автоплатежа")
    st.markdown("Синхронно тестирует автоплатеж для подписки и возвращает результат")
    with st.form("test_subscription_form"):
        test_subscription_id = st.number_input(
            "ID подписки",
            min_value=1,
            step=1,
            key="test_subscription_id",
            help="Введите ID подписки для тестирования автоплатежа",
        )
        submitted = st.form_submit_button("Протестировать автоплатеж", use_container_width=True)

        if submitted and test_subscription_id:
            _handle_test_subscription(test_subscription_id)


def _handle_test_subscription(subscription_id: int):
    """Обработка запроса на тестирование подписки"""
    try:
        client = config.get_client()
        with client:
            response = test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Тест выполнен успешно!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при тестировании: {str(e)}")


def _render_retry_payment_section():
    """Секция повторной попытки платежа"""
    st.subheader("Повторная попытка платежа")
    st.markdown("Запускает повторную попытку автосписания для уже созданного платежа")
    with st.form("retry_payment_form"):
        col1, col2 = st.columns(2)
        with col1:
            payment_id = st.number_input(
                "ID платежа",
                min_value=1,
                step=1,
                key="retry_payment_id",
                help="Введите ID платежа",
            )
        with col2:
            attempt = st.number_input(
                "Номер попытки",
                min_value=1,
                step=1,
                value=1,
                key="retry_attempt",
                help="Номер попытки (начинается с 1)",
            )
        submitted = st.form_submit_button("Повторить платеж", use_container_width=True)

        if submitted and payment_id and attempt:
            _handle_retry_payment(payment_id, attempt)


def _handle_retry_payment(payment_id: int, attempt: int):
    """Обработка запроса на повторную попытку платежа"""
    try:
        client = config.get_client()
        with client:
            response = retry_auto_payment_api_v1_auto_payments_retry_payment_payment_id_attempt_post.sync_detailed(
                payment_id=int(payment_id),
                attempt=int(attempt),
                client=client,
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Задача повторной попытки запущена!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при повторной попытке: {str(e)}")


def _render_simulate_ending_section():
    """Секция симуляции окончания подписки"""
    st.subheader("Симуляция окончания подписки")
    st.markdown("Устанавливает дату окончания подписки на сегодня для тестирования. ⚠️ Изменяет реальную дату в БД!")
    with st.form("simulate_ending_form"):
        simulate_subscription_id = st.number_input(
            "ID подписки",
            min_value=1,
            step=1,
            key="simulate_subscription_id",
            help="Введите ID подписки для симуляции окончания (end_date будет установлен на сегодня)",
        )
        submitted = st.form_submit_button("Симулировать окончание", use_container_width=True)

        if submitted and simulate_subscription_id:
            _handle_simulate_ending(simulate_subscription_id)


def _handle_simulate_ending(subscription_id: int):
    """Обработка запроса на симуляцию окончания подписки"""
    try:
        client = config.get_client()
        with client:
            response = simulate_subscription_ending_api_v1_auto_payments_simulate_subscription_ending_subscription_id_post.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Симуляция выполнена успешно!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при симуляции: {str(e)}")


def _render_process_all_subscriptions_section():
    """Секция обработки всех подписок на сегодня"""
    st.subheader("Обработка всех подписок на сегодня")
    st.markdown("Запускает обработку автоплатежей для всех подписок, заканчивающихся сегодня")
    if st.button("Обработать все подписки на сегодня", use_container_width=True, type="primary"):
        _handle_process_all_subscriptions()


def _handle_process_all_subscriptions():
    """Обработка запроса на обработку всех подписок"""
    try:
        client = config.get_client()
        with client:
            response = process_auto_payments_today_api_v1_auto_payments_process_today_post.sync_detailed(
                client=client,
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Задача запущена успешно!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при обработке: {str(e)}")


def _render_full_demo_cycle_section():
    """Секция полного демо-цикла автоплатежей"""
    st.subheader("🚀 Полный демо-цикл автоплатежей")
    st.markdown(
        """
        Запускает полный цикл автоплатежей: устанавливает end_date на сегодня, добавляет в Redis, 
        запускает обработку и отслеживает попытки. ⚠️ Изменяет реальную дату окончания подписки!
        """
    )

    with st.form("full_demo_form"):
        demo_subscription_id = st.number_input(
            "ID подписки для демо",
            min_value=1,
            step=1,
            key="demo_subscription_id",
            help="Введите ID подписки для полного демо-цикла",
        )

        st.info("Интервал между попытками берется из конфига Redis")

        submitted = st.form_submit_button("🚀 Запустить полный демо-цикл", use_container_width=True, type="primary")

        if submitted and demo_subscription_id:
            _handle_full_demo_cycle(demo_subscription_id)


def _handle_full_demo_cycle(subscription_id: int):
    """Обработка запроса на запуск полного демо-цикла"""
    try:
        client = config.get_client()
        with client:
            progress_bar = st.progress(0)
            status_text = st.empty()

            config_response = get_auto_payment_config_api_v1_auto_payments_config_get.sync_detailed(client=client)
            retry_interval = 60
            if config_response.status_code == 200:
                config_data = utils.parse_response(config_response.parsed)
                if config_data:
                    retry_interval = config_data.get("retry_interval_seconds", 60)

            status_text.text("📅 Шаг 1/6: Устанавливаю end_date на сегодня...")
            response = simulate_subscription_ending_api_v1_auto_payments_simulate_subscription_ending_subscription_id_post.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )
            if response.status_code != 200:
                utils.handle_api_error(response, response.status_code)
                st.stop()
            progress_bar.progress(15)

            status_text.text("🔍 Шаг 2/6: Получаю информацию о подписке...")
            subscription_response = get_subscription_api_v1_subscriptions_subscription_id_get.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )
            if subscription_response.status_code != 200:
                utils.handle_api_error(subscription_response, subscription_response.status_code)
                st.stop()

            subscription_data = utils.parse_response(subscription_response.parsed)
            user_id = subscription_data.get("user_id") if subscription_data else None

            if not user_id:
                st.error("❌ Не удалось получить user_id из подписки")
                st.stop()

            progress_bar.progress(30)

            status_text.text("📦 Шаг 3/6: Добавляю подписку в Redis...")
            collect_response = (
                collect_subscriptions_for_payment_api_v1_auto_payments_collect_subscriptions_post.sync_detailed(
                    client=client,
                )
            )
            if collect_response.status_code != 200:
                utils.handle_api_error(collect_response, collect_response.status_code)
                st.stop()

            redis_status = get_redis_status_api_v1_auto_payments_redis_status_get.sync_detailed(client=client)
            if redis_status.status_code == 200:
                redis_data = utils.parse_response(redis_status.parsed)
                st.success(f"✅ Подписка #{subscription_id} добавлена в Redis!")
                with st.expander("📊 Статус Redis", expanded=True):
                    st.json(redis_data)
            progress_bar.progress(45)

            status_text.text("🔄 Шаг 4/6: Запускаю обработку подписки...")
            process_response = process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post.sync_detailed(
                subscription_id=int(subscription_id),
                client=client,
            )
            if process_response.status_code != 200:
                utils.handle_api_error(process_response, process_response.status_code)
                st.stop()

            task_id = None
            if process_response.parsed:
                parsed_data = utils.parse_response(process_response.parsed)
                task_id = parsed_data.get("task_id") if parsed_data else None

            st.success(f"✅ Задача обработки запущена! Task ID: `{task_id or 'N/A'}`")
            st.info(f"Интервал из конфига: {retry_interval} сек")
            progress_bar.progress(55)

            status_text.text("⏳ Шаг 5/6: Отслеживание попыток автосписания...")

            max_attempts = 3
            total_wait_time = retry_interval * (max_attempts - 1)

            st.info(f"Ожидание попыток: ~{total_wait_time} секунд ({total_wait_time / 60:.1f} минут)")

            attempts_container = st.container()
            attempts_placeholder = st.empty()

            attempts_seen = set()
            payment_id = None
            start_time = time.time()
            max_wait_time = total_wait_time + 60

            with attempts_container:
                st.markdown("### 📊 Статус попыток:")

                while time.time() - start_time < max_wait_time:
                    payments_response = get_user_payments_api_v1_payments_user_user_id_get.sync_detailed(
                        user_id=user_id,
                        client=client,
                        limit=10,
                    )

                    if payments_response.status_code == 200:
                        payments_raw = payments_response.parsed
                        if isinstance(payments_raw, list):
                            payments = _convert_payments_to_dicts(payments_raw)
                        else:
                            payments = []

                        current_payment = None
                        for payment in payments:
                            if isinstance(payment, dict) and payment.get("subscription_id") == subscription_id:
                                current_payment = payment
                                if not payment_id:
                                    payment_id = payment.get("id")
                                break

                        if current_payment:
                            attempt_num = current_payment.get("attempt_number", 0)
                            status = current_payment.get("status", "unknown")

                            if attempt_num > 0 and attempt_num not in attempts_seen:
                                attempts_seen.add(attempt_num)
                                attempts_placeholder.markdown(
                                    f"**Попытка {attempt_num}/{max_attempts}:** Статус: `{status}`, "
                                    f"Время: {datetime.now().strftime('%H:%M:%S')}, "
                                    f"Payment ID: {current_payment.get('id')}"
                                )

                            attempts_placeholder.markdown(
                                f"**Текущий статус:** Попытка {attempt_num}/{max_attempts}, "
                                f"Статус: `{status}`, Payment ID: {current_payment.get('id')}, "
                                f"Время: {datetime.now().strftime('%H:%M:%S')}"
                            )

                            if status == "succeeded":
                                st.success("✅ Платеж успешно выполнен! Подписка продлена.")
                                break
                            elif status == "failed" and attempt_num >= max_attempts:
                                st.warning("⚠️ Все попытки провалились. Подписка в статусе cancelled_waiting.")
                                break

                    time.sleep(5)

                    if len(attempts_seen) >= max_attempts:
                        time.sleep(10)
                        break

                if payments_response.status_code == 200:
                    payments_raw = payments_response.parsed
                    if isinstance(payments_raw, list):
                        payments = _convert_payments_to_dicts(payments_raw)
                    else:
                        payments = []
                    
                    for payment in payments:
                        if isinstance(payment, dict) and payment.get("subscription_id") == subscription_id:
                            final_status = payment.get("status", "unknown")
                            final_attempt = payment.get("attempt_number", 0)
                            attempts_placeholder.markdown(
                                f"### ✅ Финальный статус: Попытка {final_attempt}/{max_attempts}, "
                                f"Статус: `{final_status}`, Payment ID: {payment.get('id')}"
                            )
                            break

            progress_bar.progress(85)

            status_text.text("🔄 Шаг 6/6: Готово к финальной обработке")

            st.info("Если все попытки провалились, подписка будет в статусе `cancelled_waiting`. "
                   "Используйте кнопку ниже для финальной обработки.")

            st.session_state.demo_launched = True
            st.session_state.demo_sub_id = subscription_id

            progress_bar.progress(100)
            status_text.text("✅ Демо-цикл завершен!")

            st.success(
                f"✅ Демо-цикл успешно выполнен! Подписка #{subscription_id} обработана. "
                f"Если все попытки провалились, используйте кнопку ниже для финальной обработки."
            )

    except Exception as e:
        st.error(f"❌ Ошибка при запуске демо-цикла: {str(e)}")
        st.code(traceback.format_exc())


def _render_final_processing_button():
    """Кнопка для финальной обработки"""
    if st.session_state.get("demo_launched", False):
        st.divider()
        st.subheader("🔄 Финальная обработка")
        st.markdown("Обработка подписок со статусом `cancelled_waiting`")
        if st.button(
            "🔄 Запустить финальную обработку cancelled_waiting",
            use_container_width=True,
            key="final_process_btn_outside",
        ):
            _handle_final_processing()


def _handle_final_processing():
    """Обработка запроса на финальную обработку cancelled_waiting"""
    try:
        client = config.get_client()
        with client:
            response = process_cancelled_waiting_api_v1_auto_payments_process_cancelled_waiting_post.sync_detailed(
                client=client
            )
            if response.status_code == 200:
                utils.display_success_message("✅ Финальная обработка завершена!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при финальной обработке: {str(e)}")
