import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Population & Development Analysis", layout="wide")

def load_data():
    military_df = pd.read_csv('data/military_spending.csv')
    hdi_df = pd.read_csv('data/hdi.csv')
    gdp_df = pd.read_csv('data/gdp.csv')
    population_df = pd.read_csv('data/population.csv')
    area_df = pd.read_csv('data/area.csv')
    
    df = pd.merge(military_df, hdi_df, on='country', how='outer')
    df = pd.merge(df, gdp_df, on='country', how='outer')
    df = pd.merge(df, population_df, on='country', how='outer')
    df = pd.merge(df, area_df, on='country', how='outer')
    
    df = df.dropna(subset=['population', 'hdi'])
    
    df['density'] = df['population'] / df['area']
    df['gdp_per_capita'] = df['gdp'] / df['population']
    df['gdp_share'] = (df['gdp'] / df['gdp'].sum()) * 100
    df['hdi_category'] = pd.qcut(df['hdi'], q=4, labels=['Low', 'Medium', 'High', 'Very High'])
    
    return df

def create_dashboard():
    st.title("Population and Development Analysis")
    
    df = load_data()

    # Сайдбар с фильтрами
    st.sidebar.header("Filters")
    
    # Фильтр по HDI категориям
    hdi_categories = st.sidebar.multiselect(
        "HDI Category",
        options=df['hdi_category'].unique(),
        default=df['hdi_category'].unique()
    )
    
    # Фильтр по размеру населения
    pop_range = st.sidebar.slider(
        "Population Range (millions)",
        min_value=float(df['population'].min()/1e6),
        max_value=float(df['population'].max()/1e6),
        value=(float(df['population'].min()/1e6), float(df['population'].max()/1e6))
    )
    
    # Фильтр по количеству стран для отображения
    top_n = st.sidebar.slider(
        "Number of countries to display",
        min_value=5,
        max_value=50,
        value=30
    )
    
    # Фильтр по континентам (если есть данные)
    if 'continent' in df.columns:
        continents = st.sidebar.multiselect(
            "Continents",
            options=df['continent'].unique(),
            default=df['continent'].unique()
        )
        df_filtered = df[
            (df['hdi_category'].isin(hdi_categories)) &
            (df['population'] >= pop_range[0]*1e6) &
            (df['population'] <= pop_range[1]*1e6) &
            (df['continent'].isin(continents))
        ]
    else:
        df_filtered = df[
            (df['hdi_category'].isin(hdi_categories)) &
            (df['population'] >= pop_range[0]*1e6) &
            (df['population'] <= pop_range[1]*1e6)
        ]
    
    # Метрики
    st.sidebar.header("Key Metrics")
    col1_side, col2_side = st.sidebar.columns(2)
    with col1_side:
        st.metric("Total Countries", len(df_filtered))
        st.metric("Avg HDI", f"{df_filtered['hdi'].mean():.3f}")
    with col2_side:
        st.metric("Total Population", f"{df_filtered['population'].sum()/1e9:.2f}B")
        st.metric("Avg GDP per capita", f"${df_filtered['gdp_per_capita'].mean():,.0f}")

    # Основные графики с фильтрованными данными
    # Корреляционная матрица
    columns_for_corr = ['population', 'density', 'gdp_per_capita', 'hdi', 
                       'area', 'gdp', 'gdp_share', 'military_spending']
    corr = df_filtered[columns_for_corr].corr()
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr,
        x=corr.columns,
        y=corr.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        text=np.around(corr, decimals=2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    fig_corr.update_layout(title='Correlation Matrix', width=800, height=800)
    st.plotly_chart(fig_corr)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Bubble Chart
        top_n_countries = df_filtered.nlargest(top_n, 'population')
        fig_bubble = px.scatter(
            top_n_countries,
            x='population',
            y='gdp',
            size='gdp_per_capita',
            color='hdi',
            hover_name='country',
            title=f'Population vs GDP (top {top_n} countries)',
            log_x=True,
            log_y=True
        )
        st.plotly_chart(fig_bubble)
        
        # 2. Violin Plot
        fig_violin = px.violin(
            df_filtered,
            x='hdi_category',
            y='density',
            title='Population Density Distribution by HDI Level',
            color='hdi_category',
            box=True
        )
        st.plotly_chart(fig_violin)
        
        # 3. Parallel Coordinates
        fig_parallel = px.parallel_coordinates(
            top_n_countries,
            dimensions=['population', 'density', 'gdp_per_capita', 'hdi'],
            color='hdi',
            title=f'Multi-dimensional Analysis (top {top_n} countries)'
        )
        st.plotly_chart(fig_parallel)
        
    with col2:
        # 4. Treemap
        fig_treemap = px.treemap(
            top_n_countries.head(15),
            path=[px.Constant("World"), 'country'],
            values='population',
            color='hdi',
            title='Population Distribution (Top 15)',
            hover_data=['gdp_per_capita']
        )
        st.plotly_chart(fig_treemap)
        
        # 5. Scatter Matrix
        fig_scatter_matrix = px.scatter_matrix(
            top_n_countries,
            dimensions=['population', 'density', 'gdp_per_capita', 'hdi'],
            color='hdi',
            title=f'Scatter Matrix (top {top_n} countries)'
        )
        st.plotly_chart(fig_scatter_matrix)
        
        # 6. Sunburst
        fig_sunburst = px.sunburst(
            top_n_countries.head(15),
            path=['hdi_category', 'country'],
            values='population',
            color='gdp_per_capita',
            title='Population Distribution by HDI Category',
            hover_data=['density']
        )
        st.plotly_chart(fig_sunburst)

    # Таблица с данными
    st.subheader("Filtered Data")
    st.dataframe(df_filtered)

if __name__ == "__main__":
    create_dashboard()