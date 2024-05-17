import warnings
import numpy as np
import pandas as pd 
import streamlit as st
import geopandas as gpd

import contextily as ctx
import plotly.express as px
import matplotlib.pyplot as plt

from tesspy import Tessellation
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from shapely.geometry import Point, Polygon

# carregando arquivos #
## Df lat lon ##
df_lat_lon = pd.read_csv('D:\AEY HELTH\harquivos_streamlit\df_lat_lon.csv', sep = ';')

## Df zona ##
df_zona = pd.read_csv('D:\AEY HELTH\harquivos_streamlit\df_zona_cnae.csv', sep = ';', index_col=False)
df_zona.set_index('Unnamed: 0', inplace=True)

## df nome fantazia ##
df_nomes_fantazia = df_lat_lon[['CNAE FISCAL PRINCIPAL', 'TIPO']]
df_nomes_fantazia['CNAE FISCAL PRINCIPAL'] = df_nomes_fantazia['CNAE FISCAL PRINCIPAL'].astype(str).tolist()

## carregando mapa de fortaleza ##
Fortaleza = Tessellation("Fortaleza")
Fortaleza_polygon = Fortaleza.get_polygon()

## df hexagon ##
df_fortaleza_hexagons = gpd.read_file(r'D:\AEY HELTH\harquivos_streamlit\Fortaleza_hexagons.shp')

# inicio da pagina #
st.set_page_config(
    page_title="AEY_HELTH.app",
    page_icon="🌎",
)

# Titulo da pagina #
st.sidebar.header("Pesquisar Endereço")

# Titulo da pagina #

# caixa de texto input #
endereco = st.sidebar.text_input("Digite o endereço aqui:", "")

## Botao de pesquizar ##
search_button = st.sidebar.button("🔍 Pesquisar")
## teste do botao ##
if search_button:
    st.sidebar.write(f"Você pesquisou pelo endereço: {endereco}")
    df_zona2 = df_zona.drop(df_zona.index[-1])
    media=df_zona2.mean().values
    std=df_zona2.std()  

    ## Verificando se foi acahdo ##
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(endereco)
    if location:
        latitude = location.latitude
        longitude = location.longitude
        ponto = Point(longitude, latitude)
        for index, row in df_fortaleza_hexagons[['geometry','Zonas']].iterrows():
                if row['geometry'].contains(ponto):
                    st.sidebar.write(f'O emderco esta contido na Zona {row['Zonas']}')
                    zona_encontrada = row['geometry']
                    # nome_zona = row['Zonas']
                    break
                    
        df_filtrado_zona = df_lat_lon[df_lat_lon['Zonas'] == row['Zonas']]
        cnae = len(df_filtrado_zona['CNAE FISCAL PRINCIPAL'].drop_duplicates())
        st.sidebar.write(f"No denreco selecionado contem {cnae} CNAIS(s) distintos")
        cnpj = len(df_filtrado_zona['CNPJ BÁSICO'].drop_duplicates())
        st.sidebar.write("No denreco selecionado contem {} CNPJ(s) Básicos distintos".format(cnpj))

        fig2, ax = plt.subplots(figsize=(10,15))
        df_fortaleza_hexagons[df_fortaleza_hexagons['geometry'] == row['geometry']]['geometry'].to_crs("EPSG:3857").plot(ax=ax, facecolor='none', edgecolor="k", lw=1)
        # df_fortaleza_hexagons['geometry'].to_crs("EPSG:3857")
        ctx.add_basemap(ax=ax, source=ctx.providers.CartoDB.Voyager)
        ax.set_axis_off()
        ax.set_title("Fortaleza", fontsize=20)
        st.pyplot(fig2)
        ## Grafico Barras ##
        x = df_zona[df_zona.index == row['Zonas']]
        resultado=(x-media)/std
        daux = pd.DataFrame(resultado).T
        daux = daux.rename(columns={daux.columns[0]: 'Z'}).sort_values('Z')
        daux['CNAE FISCAL PRINCIPAL'] = list(daux.index)
        daux = pd.merge(daux, df_nomes_fantazia, how = 'right', on = 'CNAE FISCAL PRINCIPAL').drop_duplicates()
        lista_nomes = list(daux['TIPO'])
        lista_valores = list(daux['Z'])
        fig3 = px.bar(x=lista_nomes, y=lista_valores)
        fig3.update_xaxes(tickangle=90, showticklabels=False)  # Remove os rótulos do eixo x
        fig3.update_layout(
            title=f'Gráfico de Barras dos CNAIs Mais Utilizados em {endereco}',
            xaxis_title='Lista de CNAIs',
            yaxis_title='Quantidades')
        st.plotly_chart(fig3)   


else: 
    st.sidebar.write("Você pesquisou pelo endereço: Forataleza")
    ### Pegando as quantidades de cnae destitos ###
    cnae = len(df_lat_lon['CNAE FISCAL PRINCIPAL'].drop_duplicates())
    st.sidebar.write(f"No endereço selecionado contém **{cnae}** CNAES(s) distintos")
    ### Pegando as quantidades de cnpj destitos ###
    cnpj = len(df_lat_lon['CNPJ BÁSICO'].drop_duplicates())
    st.sidebar.write(f"No endereço selecionado contém **{cnpj}** CNPJ(s) Basicos distintos")

    ## plotando grafico ##
    fig, ax = plt.subplots(figsize=(10,15))

    Fortaleza_polygon.to_crs("EPSG:3857").plot(ax=ax, facecolor="none", edgecolor="k", lw=3)
    ctx.add_basemap(ax=ax, source=ctx.providers.CartoDB.Voyager)
    ax.set_axis_off()
    ax.set_title("Fortaleza", fontsize=20)
    st.pyplot(fig)

    ## Inicio do grafico de barras ##

    ###Preparando dados do grafico ##
    df_totais_fortaleza = pd.DataFrame(df_zona.iloc[-1].astype(str).sort_values(ascending=False))
    df_totais_fortaleza['CNAE FISCAL PRINCIPAL'] = list(df_totais_fortaleza.index)
    df_totais = pd.merge(df_totais_fortaleza, df_nomes_fantazia, how = 'right', on = 'CNAE FISCAL PRINCIPAL').drop_duplicates()
    df_totais.sort_values( ascending=False, by='Total', inplace = True)
    lista_nomes = list(df_totais['TIPO'])
    lista_quantidades = list(df_totais['Total'])
    fig2 = px.bar(x=lista_nomes, y=lista_quantidades)
    fig2.update_xaxes(tickangle=90, showticklabels=False)  # Remove os rótulos do eixo x
    fig2.update_layout(
        title='Gráfico de Barras dos CNAIs Mais Utilizados em Fortaleza',
        xaxis_title='Lista de CNAIs',
        yaxis_title='Quantidades'
    )
    st.plotly_chart(fig2)


# fim da Pagina

