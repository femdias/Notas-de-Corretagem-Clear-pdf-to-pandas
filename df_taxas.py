import pandas as pd
import numpy as np
import re
import time

# funções para ajudar na criação do dataframe de taxas
def cond(l,s):
    df = pd.DataFrame(l)
    condição = (df.iloc[:,0].str.contains(s))
    return condição

def get_value(l,c):
    df = pd.DataFrame(l)
    df = df.loc[c][0].iloc[0]
    return df

def build_dftx(text):
    start_time = time.time()
    # dataframe de taxas
    colunas = ['data',
               'corretora',
               'taxa_liquidação',
               'taxa_registro',
               'taxa_termo/opções',
               'taxa_ANA',
               'emolumentos',
               'taxa_operacional',
               'execução',
               'taxa_custódia/exec_casa',
               'impostos',
               'outros']

    df_taxas = pd.DataFrame(columns = colunas)
    df_taxas['data'] = [text[i][2].split(' ')[-1] for i in range(0,len(text))]
    df_taxas['corretora'] = [get_value(l=text[i],c=cond(l=text[i],s='CM CAPITAL')|cond(l=text[i],s='CLEAR CORRETORA')) for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_liquidação'] = [get_value(l=text[i],c=cond(l=text[i],s='Taxa de liquidação')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_registro'] = [get_value(l=text[i],c=cond(l=text[i],s='Taxa de registro')|cond(l=text[i],s='Taxa de Registro')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_termo/opções'] = [get_value(l=text[i],c=cond(l=text[i],s='termo/opções')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_ANA'] = [get_value(l=text[i],c=cond(l=text[i],s='A.N.A')|cond(l=text[i],s='ANA')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'emolumentos'] = [get_value(l=text[i],c=cond(l=text[i],s='Emolumentos')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_operacional'] = [get_value(l=text[i],c=cond(l=text[i],s=' Clearing ')|cond(l=text[i],s='Taxa Operacional')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'execução'] = [get_value(l=text[i],c=cond(l=text[i],s='Execução')).replace(' D','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'taxa_custódia/exec_casa'] = [get_value(l=text[i],c=cond(l=text[i],s='Execução Casa')|cond(l=text[i],s='Taxa de Custódia')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'impostos'] = [get_value(l=text[i],c=cond(l=text[i],s='ISS \(')|cond(l=text[i],s='Impostos')).replace(' D','').replace(' C','').split(' ')[-1] for i in range(0,len(text))]
    df_taxas.loc[:,'outros'] = [get_value(l=text[i],c=cond(l=text[i],s='Outr')).split('Outr')[1].split(' ')[-2] for i in range(0,len(text))]

    df_taxas = df_taxas.melt(id_vars=['data','corretora'], var_name='taxa', value_name='valor')
    df_taxas['valor'] = df_taxas['valor'].replace('[~R\$)]','', regex=True).str.replace('.','').str.replace(',','.').astype(float)*-1
    df_taxas.loc[df_taxas.valor == 0,'valor'] = df_taxas['valor']*-1
    df_taxas['data'] = pd.to_datetime(df_taxas['data'], dayfirst=True)
    df_taxas.loc[df_taxas.corretora.str.contains('CLEAR CORRETORA'),'corretora'] = 'Clear Investimentos' 
    df_taxas.loc[df_taxas.corretora.str.contains('CM CAPITAL'),'corretora'] = 'CM Capital'

    # dataframe com os dados de irrf para day trade
    df_irrf_daytrade = pd.DataFrame(columns=['data','corretora','taxa','base','valor'])
    df_irrf_daytrade.loc[:,'data'] = [text[i][2].split(' ')[-1] for i in range(0,len(text))]

    proj_list = []
    base_list = []
    for i in range(0,len(text)):
        try:
            proj_list.append(get_value(l=text[i],c=cond(l=text[i],s='IRRF Day')).split('Projeção')[1].split(' ')[2])
            base_list.append(get_value(l=text[i],c=cond(l=text[i],s='IRRF Day')).split('Base')[1].split(' ')[2])
        except:
            proj_list.append('0')
            base_list.append('0')

    df_irrf_daytrade['corretora'] = [get_value(l=text[i],c=cond(l=text[i],s='CM CAPITAL')|cond(l=text[i],s='CLEAR CORRETORA')) for i in range(0,len(text))]
    df_irrf_daytrade['valor'] = proj_list
    df_irrf_daytrade['base'] = base_list
    df_irrf_daytrade['valor'] = df_irrf_daytrade['valor'].str.replace('.','').str.replace(',','.').astype(float)*-1
    df_irrf_daytrade['base'] = df_irrf_daytrade['base'].str.replace('.','').str.replace(',','.').astype(float)
    df_irrf_daytrade['data'] = pd.to_datetime(df_irrf_daytrade['data'], dayfirst=True)
    df_irrf_daytrade.loc[df_irrf_daytrade.corretora.str.contains('CLEAR CORRETORA'),'corretora'] = 'Clear Investimentos' 
    df_irrf_daytrade.loc[df_irrf_daytrade.corretora.str.contains('CM CAPITAL'),'corretora'] = 'CM Capital'
    df_irrf_daytrade.loc[df_irrf_daytrade.valor == 0,'valor'] = df_irrf_daytrade['valor']*-1
    df_irrf_daytrade['taxa'] = 'IRRF Day Trade'


    # dataframe com os dados de irrf para swing trade
    df_irrf_swingtrade = pd.DataFrame(columns=['data','corretora','taxa','base','valor'])
    df_irrf_swingtrade['corretora'] = [get_value(l=text[i],c=cond(l=text[i],s='CM CAPITAL')|cond(l=text[i],s='CLEAR CORRETORA')) for i in range(0,len(text))]
    df_irrf_swingtrade['data'] = [text[i][2].split(' ')[-1] for i in range(0,len(text))]
    df_irrf_swingtrade['base'] = [get_value(l=text[i],c=cond(l=text[i],s='I.R.R.F')).split('base')[1].replace(' D','').replace(' C','').strip().split(' ')[0] for i in range(0,len(text))]
    df_irrf_swingtrade['valor'] = [get_value(l=text[i],c=cond(l=text[i],s='I.R.R.F')).split('base')[1].replace(' D','').replace(' C','').strip().split(' ')[-1] for i in range(0,len(text))]
    df_irrf_swingtrade['valor'] = df_irrf_swingtrade['valor'].str.replace('.','').str.replace(',','.').astype(float)*-1
    df_irrf_swingtrade['base'] = df_irrf_swingtrade['base'].replace('[~R\$)]','', regex=True).str.replace('.','').str.replace(',','.').astype(float)
    df_irrf_swingtrade['data'] = pd.to_datetime(df_irrf_swingtrade['data'], dayfirst=True)
    df_irrf_swingtrade.loc[df_irrf_swingtrade.corretora.str.contains('CLEAR CORRETORA'),'corretora'] = 'Clear Investimentos' 
    df_irrf_swingtrade.loc[df_irrf_swingtrade.corretora.str.contains('CM CAPITAL'),'corretora'] = 'CM Capital'
    df_irrf_swingtrade.loc[df_irrf_swingtrade.valor == 0,'valor'] = df_irrf_swingtrade['valor']*-1
    df_irrf_swingtrade['taxa'] = 'IRRF Swing Trade'

    # Juntar irrf daytrade e swingtrade
    df_irrf = pd.concat([df_irrf_swingtrade,df_irrf_daytrade])
    df_irrf = df_irrf.loc[df_irrf['base']!=0]

    # Juntar df taxas
    df_taxas = pd.concat([df_taxas,df_irrf])
    df_taxas = df_taxas.sort_values(by='data').reset_index(drop=True)
    return df_taxas,time.time() - start_time