"""
Вспомогательные функции для работы с API и отображения данных
"""

import json
from typing import Any, Optional

import streamlit as st


def parse_response(response: Any) -> Optional[dict]:
    """
    Парсит ответ от API клиента в словарь для отображения.

    Args:
        response: Ответ от API (может быть parsed объектом или dict)

    Returns:
        Dict с данными или None
    """
    if response is None:
        return None

    if isinstance(response, dict):
        return response

    if hasattr(response, "to_dict"):
        return response.to_dict()

    if hasattr(response, "__dict__"):
        return response.__dict__

    return {"result": str(response)}


def handle_api_error(response: Any, status_code: int) -> None:
    """
    Обрабатывает ошибки API и отображает их в Streamlit.

    Args:
        response: Ответ от API
        status_code: HTTP статус код
    """
    st.error(f"❌ Ошибка: {status_code}")

    if hasattr(response, "content"):
        try:
            error_data = json.loads(response.content.decode("utf-8"))
            st.json(error_data)
        except:
            st.text(response.content.decode("utf-8", errors="ignore"))
    elif hasattr(response, "text"):
        try:
            st.json(response.text)
        except:
            st.text(response.text)
    elif hasattr(response, "parsed"):
        parsed = parse_response(response.parsed)
        if parsed:
            st.json(parsed)


def display_success_message(message: str = "✅ Операция выполнена успешно!", data: Any = None) -> None:
    """
    Отображает сообщение об успехе и опциональные данные.

    Args:
        message: Текст сообщения
        data: Данные для отображения (опционально)
    """
    st.success(message)
    if data:
        parsed = parse_response(data)
        if parsed:
            st.json(parsed)
