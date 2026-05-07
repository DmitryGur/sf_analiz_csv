import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import io

# Настройка страницы
st.set_page_config(page_title="CSV Анализатор", layout="wide")


# Кеширование загрузки данных
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        return df
    return None


# Функция для статистического анализа
@st.cache_data
def get_statistics(column):
    stats = {}
    if pd.api.types.is_numeric_dtype(column):
        stats['Среднее'] = column.mean()
        stats['Медиана'] = column.median()
        stats['Cреднеквадратичное отклонение'] = column.std()
    else:
        stats['Уникальных значений'] = column.nunique()
        stats['Наиболее частое'] = column.mode().iloc[0] if not column.mode().empty else 'Нет'
        stats['Всего значений'] = len(column)
    return stats


# Функция построения графиков
def create_plot(df, x_col, y_col=None, plot_type='line'):
    fig, ax = plt.subplots(figsize=(10, 6))

    if plot_type == 'line':
        if y_col:
            df.plot(x=x_col, y=y_col, kind='line', ax=ax)
        else:
            df[x_col].plot(kind='line', ax=ax)
    elif plot_type == 'scatter':
        df.plot.scatter(x=x_col, y=y_col, ax=ax)
    elif plot_type == 'histogram':
        df[x_col].hist(bins=20, ax=ax, alpha=0.7)
        ax.set_title(f'Распределение {x_col}')
    elif plot_type == 'box':
        df.boxplot(column=x_col, ax=ax)
        ax.set_title(f'Box plot {x_col}')
    ax.set_xlabel(x_col)
    if y_col:
        ax.set_ylabel(y_col)
    plt.tight_layout()
    return fig


# Заголовок приложения
st.title("📊 Анализатор CSV-файлов")
st.markdown("Загрузите CSV-файл для анализа и исследования данных.")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите CSV-файл", type=['csv'])

if uploaded_file is not None:
    # Загрузка данных
    df = load_data(uploaded_file)
    st.success("Файл успешно загружен!")

    # Отображение данных
    st.subheader("Просмотр данных")
    with st.expander("Показать таблицу данных", expanded=True):
        st.dataframe(df.head(20))
        st.write(f"**Размер данных:** {df.shape[0]} строк, {df.shape[1]} столбцов")

    # Выбор столбцов
    st.subheader("Анализ данных")
    col1, col2 = st.columns(2)
    with col1:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        all_cols = df.columns.tolist()
        selected_column = st.selectbox("Выберите столбец для статистического анализа", all_cols)
    with col2:
        x_axis = st.selectbox("Ось X для графика", all_cols, key='x_axis')
        y_axis_options = [col for col in all_cols if col != x_axis]
        y_axis = st.selectbox("Ось Y для графика (опционально)", ['None'] + y_axis_options, key='y_axis')

    # Статистический анализ
    st.subheader("Статистический анализ")
    column_to_analyze = df[selected_column]
    stats = get_statistics(column_to_analyze)
    stats_df = pd.DataFrame(list(stats.items()), columns=['Показатель', 'Значение'])
    st.table(stats_df)

    # Построение графиков
    st.subheader("Визуализация данных")
    plot_col1, plot_col2 = st.columns(2)
    with plot_col1:
        plot_type = st.radio(
            "Тип графика",
            ['line', 'scatter', 'histogram', 'box'],
            format_func=lambda x: {
                'line': 'Линейный график',
                'scatter': 'Диаграмма рассеяния',
                'histogram': 'Гистограмма распределения',
                'box': 'Box plot'
            }[x]
        )
    with plot_col2:
        st.markdown("&nbsp;")  # Пустое пространство
        download_btn = st.button("Скачать график")
    # Построение основного графика
    if y_axis != 'None':
        fig = create_plot(df, x_axis, y_axis, plot_type)
    else:
        fig = create_plot(df, selected_column, None, plot_type)
    st.pyplot(fig)
    # Кнопка загрузки графика
    if download_btn:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        st.download_button(
            label="Скачать график",
            data=buf,
            file_name=f"plot_{plot_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )
        st.success("График готов к загрузке!")
    # Дополнительная статистика
    st.subheader("Дополнительная визуализация")
    expander = st.expander("Дополнительные графики")
    with expander:
        col_a, col_b = st.columns(2)
        with col_a:
            if numeric_cols:
                dist_col = st.selectbox("Столбец для распределения", numeric_cols, key='dist_col')
                fig_dist = plt.figure(figsize=(9, 4))
                sns.histplot(df[dist_col], kde=True, alpha=0.7)
                plt.title(f"Распределение {dist_col}")
                st.pyplot(fig_dist)
        with col_b:
            if len(numeric_cols) >= 2:
                pair_cols = st.multiselect("Пары столбцов для взаимного распределения", numeric_cols,
                                           default=numeric_cols[:2], key='pair_cols')
                if len(pair_cols) == 2:
                    fig_pair = plt.figure(figsize=(9, 4))
                    sns.scatterplot(data=df, x=pair_cols[0], y=pair_cols[1])
            plt.title(f"Взаимное распределение {pair_cols[0]} и {pair_cols[1]}")
            st.pyplot(fig_pair)
else:
    st.info("Загрузите CSV-файл.")
