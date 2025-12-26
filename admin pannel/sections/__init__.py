"""
Секции админ-панели
"""

from sections.auto_payments import render_auto_payments_tab
from sections.promotions import render_promotions_tab

__all__ = ["render_auto_payments_tab", "render_promotions_tab"]
