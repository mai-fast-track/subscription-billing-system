"""
Streamlit приложение для админ-панели
"""

import sys
from pathlib import Path

import streamlit as st

admin_pannel_path = Path(__file__).parent
if str(admin_pannel_path) not in sys.path:
    sys.path.insert(0, str(admin_pannel_path))

project_root = admin_pannel_path.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sections import render_auto_payments_tab, render_promotions_tab

st.set_page_config(page_title="Админ-панель", page_icon="⚙️", layout="wide")

st.title("⚙️ Админ-панель")
st.divider()

tab1, tab2 = st.tabs(["🔄 Автосписания", "🎁 Промокоды"])

with tab1:
    render_auto_payments_tab()

with tab2:
    render_promotions_tab()
