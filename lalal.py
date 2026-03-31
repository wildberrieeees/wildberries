import datetime as dt
import streamlit as st
import pandas as pd
import plotly.express as px
from pandas.core.frame import DataFrame

# Функция для суммирования с фильтром по датам
def get_a_value_of_column(excel: DataFrame, column_name: str) -> int:
    if not agree:
        if not pd.api.types.is_datetime64_any_dtype(excel["Дата продажи"]):
            excel["Дата продажи"] = pd.to_datetime(excel["Дата продажи"])
        filtered_df = excel[
            (excel["Дата продажи"] >= dt.datetime.strptime(str(one_time), '%Y-%m-%d')) &
            (excel["Дата продажи"] <= dt.datetime.strptime(str(last_time), '%Y-%m-%d'))
            ]
        return filtered_df[column_name].sum()
    else:
        return excel[column_name].sum()


# Основные настройки
one_time = 0
last_time = 0

st.title("📊 Финансовый отчет Wildberries")

agree = st.checkbox("Выбрать ВСЕ даты")
if not agree:
    st.subheader("Выберите период")
    one_time = st.date_input("С ")
    last_time = st.date_input("По ")

try:
    df = pd.read_excel(st.file_uploader("Выберите файл", type=["xlsx"]))
except Exception as e:
    st.subheader("Пожалуйста! Выберите файл!")
else:
    if not pd.api.types.is_datetime64_any_dtype(df["Дата продажи"]):
        df["Дата продажи"] = pd.to_datetime(df["Дата продажи"])

    st.subheader("Данные из файла")
    st.dataframe(df.head(15))

    cols = df.columns.tolist()

    # Метрики
    logistics = get_a_value_of_column(df, "Услуги по доставке товара покупателю")
    pribil = get_a_value_of_column(df, "Вайлдберриз реализовал Товар (Пр)")
    storage_pay = get_a_value_of_column(df, "Хранение")
    return_c = get_a_value_of_column(df, "Количество возврата")
    operating_profit = get_a_value_of_column(df, "К перечислению Продавцу за реализованный Товар")
    penalty = get_a_value_of_column(df, "Общая сумма штрафов")

    st.metric("Затраты на доставку", f"{logistics:,.2f} ₽")
    st.metric("Затраты на хранение товара", f"{storage_pay:,.2f} ₽")
    st.metric("Возвращенных товаров", f"{return_c} шт.")
    st.metric("Прибыль", f"{pribil:,.2f} ₽")
    st.metric("Операционная прибыль (чистая)", f"{operating_profit - storage_pay - logistics:,.2f} ₽")

    # Фильтрация по периоду
    if not agree:
        df_filtered = df[
            (df["Дата продажи"] >= pd.to_datetime(one_time)) &
            (df["Дата продажи"] <= pd.to_datetime(last_time))
            ]
    else:
        df_filtered = df.copy()

    # Графики
    with st.expander("📈 Выручка по датам"):
        revenue_by_date = df_filtered.groupby("Дата продажи")[
            "К перечислению Продавцу за реализованный Товар"].sum().reset_index()
        fig1 = px.line(revenue_by_date, x="Дата продажи", y="К перечислению Продавцу за реализованный Товар",
                       title="Выручка по датам")
        st.plotly_chart(fig1, use_container_width=True)

    with st.expander("🥧 Структура расходов"):
        expenses = {"Логистика": logistics, "Хранение": storage_pay, "Штрафы": penalty}
        fig2 = px.pie(names=expenses.keys(), values=expenses.values(), title="Распределение расходов")
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📊 Прибыль vs Затраты"):
        compare = pd.DataFrame({
            "Показатель": ["Прибыль", "Затраты"],
            "Сумма": [round(operating_profit - storage_pay - logistics, 2), round(logistics + storage_pay, 2)]
        })
        fig3 = px.bar(compare, x="Показатель", y="Сумма", text="Сумма", color="Показатель")
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📉 Штрафы по датам"):
        fines_by_date = df_filtered.groupby("Дата продажи")["Общая сумма штрафов"].sum().reset_index()
        if fines_by_date["Общая сумма штрафов"].sum() == 0:
            st.info("✅ В этом периоде штрафов не было")
        else:
            fig_fines = px.bar(fines_by_date, x="Дата продажи", y="Общая сумма штрафов",
                               title="Штрафы по дням", text="Общая сумма штрафов",
                               color="Общая сумма штрафов")
            st.plotly_chart(fig_fines, use_container_width=True)

    # Логистика и комиссия на товар
    st.subheader("🚚 Логистика и комиссия на товар")
    # Логистика на товар
    if "Услуги по доставке товара покупателю" in cols and "Количество доставок" in cols:
        df_filtered["Логистика на товар"] = df_filtered["Услуги по доставке товара покупателю"] / df_filtered[
            "Количество доставок"].replace(0, 1)
    else:
        df_filtered["Логистика на товар"] = df_filtered["Услуги по доставке товара покупателю"] / df_filtered[
            "Количество продаж"].replace(0, 1)

    # Комиссия на товар
    df_filtered["Комиссия на товар"] = df_filtered["Цена розничная"] - df_filtered[
        "К перечислению Продавцу за реализованный Товар"]

    with st.expander("🚚 Логистика на товар по дням"):
        logistics_trend = df_filtered.groupby("Дата продажи")["Логистика на товар"].mean().reset_index()
        fig5 = px.line(logistics_trend, x="Дата продажи", y="Логистика на товар", title="Логистика на товар по дням")
        st.plotly_chart(fig5, use_container_width=True)

    with st.expander("💰 Комиссия на товар по дням"):
        commission_trend = df_filtered.groupby("Дата продажи")["Комиссия на товар"].mean().reset_index()
        fig6 = px.line(commission_trend, x="Дата продажи", y="Комиссия на товар", title="Комиссия на товар по дням")
        st.plotly_chart(fig6, use_container_width=True)
