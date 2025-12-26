"""
Секция управления промокодами
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st

# Добавляем путь к папке admin pannel для корректных импортов
admin_pannel_path = Path(__file__).parent.parent
if str(admin_pannel_path) not in sys.path:
    sys.path.insert(0, str(admin_pannel_path))

# Добавляем путь к проекту для импорта billing_core_api_client
project_root = admin_pannel_path.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Используем относительные импорты
import config
import utils

from billing_core_api_client.api.promotions import (
    create_promotion_api_v1_promotions_post,
    delete_promotion_api_v1_promotions_promotion_id_delete,
    get_all_promotions_api_v1_promotions_get,
    get_promotion_api_v1_promotions_promotion_id_get,
    update_promotion_api_v1_promotions_promotion_id_patch,
)
from billing_core_api_client.models import PromotionCreate, PromotionUpdate


def render_promotions_tab():
    """Отрисовать вкладку управления промокодами"""
    try:
        st.header("🎁 Управление промокодами")

        # Вкладки для разных операций
        tab_list, tab_create, tab_edit, tab_delete = st.tabs(
            ["📋 Список промокодов", "➕ Создать промокод", "✏️ Редактировать", "🗑️ Удалить"]
        )

        with tab_list:
            _render_promotions_list()

        with tab_create:
            _render_create_promotion()

        with tab_edit:
            _render_edit_promotion()

        with tab_delete:
            _render_delete_promotion()
    except Exception as e:
        import traceback

        st.error(f"❌ Критическая ошибка при загрузке вкладки промокодов: {str(e)}")
        st.code(traceback.format_exc())


def _render_promotions_list():
    """Отобразить список всех промокодов"""
    st.subheader("Список всех промокодов")

    try:
        client = config.get_client()
        with client:
            response = get_all_promotions_api_v1_promotions_get.sync_detailed(client=client, skip=0, limit=1000)

            if response.status_code == 200:
                promotions = response.parsed
                if not promotions:
                    st.info("📭 Промокодов пока нет. Создайте первый промокод во вкладке 'Создать промокод'.")
                    return

                st.success(f"✅ Найдено промокодов: {len(promotions)}")

                # Отображаем промокоды в виде карточек
                for promo in promotions:
                    # Безопасная проверка description
                    description = None
                    if hasattr(promo, "description") and promo.description is not None:
                        from billing_core_api_client.types import UNSET

                        if promo.description is not UNSET:
                            description = promo.description

                    # Безопасная проверка valid_until
                    valid_until = None
                    if hasattr(promo, "valid_until") and promo.valid_until is not None:
                        from billing_core_api_client.types import UNSET

                        if promo.valid_until is not UNSET:
                            valid_until = promo.valid_until

                    # Безопасная проверка max_uses
                    max_uses = None
                    if hasattr(promo, "max_uses") and promo.max_uses is not None:
                        from billing_core_api_client.types import UNSET

                        if promo.max_uses is not UNSET:
                            max_uses = promo.max_uses

                    # Безопасная проверка assigned_user_id
                    assigned_user_id = None
                    if hasattr(promo, "assigned_user_id") and promo.assigned_user_id is not None:
                        from billing_core_api_client.types import UNSET

                        if promo.assigned_user_id is not UNSET:
                            assigned_user_id = promo.assigned_user_id

                    with st.expander(
                        f"🎁 {promo.code} - {promo.name} {'✅' if promo.is_active else '❌'}",
                        expanded=False,
                    ):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**ID:** {promo.id}")
                            st.markdown(f"**Код:** `{promo.code}`")
                            st.markdown(f"**Название:** {promo.name}")
                            if description:
                                st.markdown(f"**Описание:** {description}")
                            st.markdown(f"**Тип:** {promo.type_}")
                            st.markdown(f"**Бонусных дней:** {promo.value}")

                        with col2:
                            st.markdown(f"**Активен:** {'✅ Да' if promo.is_active else '❌ Нет'}")
                            st.markdown(f"**Использований:** {promo.current_uses}")
                            if max_uses:
                                st.markdown(f"**Макс. использований:** {max_uses}")
                            else:
                                st.markdown("**Макс. использований:** Без ограничений")
                            st.markdown(f"**Действует с:** {promo.valid_from.strftime('%d.%m.%Y %H:%M')}")
                            if valid_until:
                                st.markdown(f"**Действует до:** {valid_until.strftime('%d.%m.%Y %H:%M')}")
                            else:
                                st.markdown("**Действует до:** Без ограничений")
                            if assigned_user_id:
                                st.markdown(f"**Назначен пользователю:** {assigned_user_id}")
                            else:
                                st.markdown("**Назначен пользователю:** Общий промокод")

            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        import traceback

        st.error(f"❌ Ошибка при загрузке промокодов: {str(e)}")
        st.code(traceback.format_exc())


def _render_create_promotion():
    """Форма создания нового промокода"""
    st.subheader("Создать новый промокод")

    st.markdown(
        """
        **Информация:**
        - Тип промокода: только `bonus_days` (бонусные дни)
        - Код автоматически приводится к верхнему регистру
        - Промокод создается активным по умолчанию
        """
    )

    with st.form("create_promotion_form"):
        col1, col2 = st.columns(2)

        with col1:
            code = st.text_input(
                "Код промокода *", help="Уникальный код промокода (будет приведен к верхнему регистру)"
            )
            name = st.text_input("Название *", help="Название промокода")
            description = st.text_area("Описание", help="Описание промокода (необязательно)")

        with col2:
            value = st.number_input(
                "Количество бонусных дней *", min_value=1, step=1, help="Сколько дней добавить к подписке"
            )
            valid_from = st.date_input("Действует с *", value=datetime.now(timezone.utc).date())
            valid_until = st.date_input("Действует до", value=None, help="Оставьте пустым для бессрочного действия")

        col3, col4 = st.columns(2)

        with col3:
            max_uses = st.number_input(
                "Максимальное количество использований",
                min_value=1,
                step=1,
                value=None,
                help="Оставьте пустым для неограниченного использования",
            )

        with col4:
            assigned_user_id = st.number_input(
                "ID пользователя (персональный промокод)",
                min_value=1,
                step=1,
                value=None,
                help="Оставьте пустым для общего промокода",
            )

        submitted = st.form_submit_button("Создать промокод", use_container_width=True, type="primary")

        if submitted:
            if not code or not name or not value:
                st.error("❌ Заполните все обязательные поля (отмечены *)")
                return

            _handle_create_promotion(
                code, name, description, value, valid_from, valid_until, max_uses, assigned_user_id
            )


def _handle_create_promotion(
    code: str,
    name: str,
    description: str,
    value: int,
    valid_from,
    valid_until,
    max_uses: Optional[int],
    assigned_user_id: Optional[int],
):
    """Обработать создание промокода"""
    try:
        # Подготавливаем данные
        valid_from_dt = datetime.combine(valid_from, datetime.min.time().replace(tzinfo=timezone.utc))
        valid_until_dt = None
        if valid_until:
            valid_until_dt = datetime.combine(valid_until, datetime.max.time().replace(tzinfo=timezone.utc))

        promotion_data = PromotionCreate(
            code=code.upper().strip(),
            name=name.strip(),
            type_="bonus_days",
            value=value,
            valid_from=valid_from_dt,
            description=description.strip() if description else None,
            valid_until=valid_until_dt,
            max_uses=max_uses if max_uses else None,
            assigned_user_id=assigned_user_id if assigned_user_id else None,
        )

        client = config.get_client()
        with client:
            response = create_promotion_api_v1_promotions_post.sync_detailed(client=client, body=promotion_data)

            if response.status_code == 200:
                utils.display_success_message("✅ Промокод успешно создан!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при создании промокода: {str(e)}")


def _render_edit_promotion():
    """Форма редактирования промокода"""
    st.subheader("Редактировать промокод")

    st.markdown(
        """
        **Информация:**
        - Можно изменить только: название, описание, дату окончания, активность, лимит использований
        - Код и тип промокода изменить нельзя
        - Лимит использований не может быть меньше текущего количества использований
        """
    )

    with st.form("edit_promotion_form"):
        promotion_id = st.number_input(
            "ID промокода *", min_value=1, step=1, help="Введите ID промокода для редактирования"
        )

        if st.form_submit_button("Загрузить промокод", use_container_width=True):
            _load_promotion_for_edit(promotion_id)

        # Если промокод загружен в session_state, показываем форму редактирования
        if "edit_promotion" in st.session_state and st.session_state.edit_promotion:
            promo = st.session_state.edit_promotion

            st.divider()
            st.markdown(f"**Редактирование промокода:** `{promo.code}` (ID: {promo.id})")

            name = st.text_input("Название", value=promo.name)

            # Безопасная обработка description
            from billing_core_api_client.types import UNSET

            promo_description = ""
            if hasattr(promo, "description") and promo.description is not None:
                if promo.description is not UNSET:
                    promo_description = promo.description or ""

            description = st.text_area("Описание", value=promo_description)

            col1, col2 = st.columns(2)

            with col1:
                # Безопасная обработка valid_until
                from billing_core_api_client.types import UNSET

                valid_until_value = None
                if hasattr(promo, "valid_until") and promo.valid_until is not None:
                    if promo.valid_until is not UNSET:
                        valid_until_value = promo.valid_until.date() if hasattr(promo.valid_until, "date") else None

                valid_until = st.date_input(
                    "Действует до",
                    value=valid_until_value,
                    help="Оставьте пустым для бессрочного действия",
                )
                is_active = st.checkbox("Активен", value=promo.is_active)

            with col2:
                # Безопасная обработка max_uses
                from billing_core_api_client.types import UNSET

                max_uses_value = None
                if hasattr(promo, "max_uses") and promo.max_uses is not None:
                    if promo.max_uses is not UNSET:
                        max_uses_value = promo.max_uses

                max_uses = st.number_input(
                    "Максимальное количество использований",
                    min_value=promo.current_uses,
                    step=1,
                    value=max_uses_value,
                    help=f"Текущее использование: {promo.current_uses}",
                )

            submitted = st.form_submit_button("Сохранить изменения", use_container_width=True, type="primary")

            if submitted:
                _handle_update_promotion(promotion_id, name, description, valid_until, is_active, max_uses)


def _load_promotion_for_edit(promotion_id: int):
    """Загрузить промокод для редактирования"""
    try:
        client = config.get_client()
        with client:
            response = get_promotion_api_v1_promotions_promotion_id_get.sync_detailed(
                promotion_id=promotion_id, client=client
            )

            if response.status_code == 200:
                st.session_state.edit_promotion = response.parsed
                st.success(f"✅ Промокод загружен: {response.parsed.code}")
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        import traceback

        st.error(f"❌ Ошибка при загрузке промокода: {str(e)}")
        st.code(traceback.format_exc())


def _handle_update_promotion(
    promotion_id: int, name: str, description: str, valid_until, is_active: bool, max_uses: Optional[int]
):
    """Обработать обновление промокода"""
    try:
        valid_until_dt = None
        if valid_until:
            valid_until_dt = datetime.combine(valid_until, datetime.max.time().replace(tzinfo=timezone.utc))

        update_data = PromotionUpdate(
            name=name.strip(),
            description=description.strip() if description else None,
            valid_until=valid_until_dt,
            is_active=is_active,
            max_uses=max_uses if max_uses else None,
        )

        client = config.get_client()
        with client:
            response = update_promotion_api_v1_promotions_promotion_id_patch.sync_detailed(
                promotion_id=promotion_id, client=client, body=update_data
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Промокод успешно обновлен!", response.parsed)
                # Очищаем session_state
                if "edit_promotion" in st.session_state:
                    del st.session_state.edit_promotion
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при обновлении промокода: {str(e)}")


def _render_delete_promotion():
    """Форма удаления промокода"""
    st.subheader("Удалить промокод")

    st.warning(
        """
        ⚠️ **Внимание!**
        
        Удалить можно только промокоды, которые **никогда не использовались**.
        
        Если промокод уже использовался, его нужно **деактивировать** (установить `is_active = False`) 
        через вкладку "Редактировать".
        """
    )

    with st.form("delete_promotion_form"):
        promotion_id = st.number_input(
            "ID промокода для удаления *",
            min_value=1,
            step=1,
            help="Введите ID промокода для удаления",
        )

        confirm = st.checkbox(
            "Я понимаю, что удалить можно только неиспользованные промокоды",
            help="Подтвердите, что понимаете ограничения",
        )

        submitted = st.form_submit_button("🗑️ Удалить промокод", use_container_width=True, type="primary")

        if submitted:
            if not confirm:
                st.error("❌ Подтвердите удаление, установив галочку")
                return

            _handle_delete_promotion(promotion_id)


def _handle_delete_promotion(promotion_id: int):
    """Обработать удаление промокода"""
    try:
        client = config.get_client()
        with client:
            response = delete_promotion_api_v1_promotions_promotion_id_delete.sync_detailed(
                promotion_id=promotion_id, client=client
            )

            if response.status_code == 200:
                utils.display_success_message("✅ Промокод успешно удален!", response.parsed)
            else:
                utils.handle_api_error(response, response.status_code)
    except Exception as e:
        st.error(f"❌ Ошибка при удалении промокода: {str(e)}")
