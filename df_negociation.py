import pandas as pd
import numpy as np
import re
import pickle
import time
import comp_carteira_bovespa as ccb

# função que move todas as linhas para a direita até não ter nenhum valor número nas últimas colunas
def rshift_col(df):
    mask = df[df.iloc[:,-1].isna()].all(axis=1).index
    for index, row in df.iloc[mask,:].iterrows():
        max_col_notnull = np.max(np.array(row[row.notnull()].index))
        periods_to_shift = (len(row)-1) - max_col_notnull
        numb_cols = len(df.columns)
        
        # movendo os dados para a direita
        operação = row[row.notnull()].iloc[-6] # provavel coluna da operação
        df.iloc[index,-4-periods_to_shift:numb_cols] = df.iloc[index,-4-periods_to_shift:numb_cols].shift(periods_to_shift, axis=0)
    return df

# função que cria o dataframe de negociação com a coluna de data
def get_negociation(df):
    start_time = time.time()
    df = pd.DataFrame(df)
    
    # pegando linhas que mostram as negociações junto com a data
    cond_neg = (df[0].str.contains('1-BOVESPA'))|(df.index==2)|(df[0].str.contains('CLEAR CORRETORA'))|(df[0].str.contains('CM CAPITAL'))
    
    df = df.loc[cond_neg].reset_index(drop=True)
    
    df['data'] = df.iloc[0][0][-10:len(df.iloc[0][0])].strip() +'###'+ (df.iloc[1][0]).replace(' ','')
    df = df.iloc[2:].reset_index(drop=True)
    df2 = pd.DataFrame(df[0].str.split(' ').tolist())
    df2.iloc[:,0] = df['data']
    return df2

# Função que cria a df_negociation
def build_dfneg(pdf_texto):
    start_time = time.time()
    
    # limpando o texto para não ter mais de 1 espaço
    text = []
    for pagina in pdf_texto:
        text.append(list(map(lambda x: ' '.join(x.split()),pagina)))
    
    # pegando os dados de todas as paginas do pdf sobre negociação
    negociation = pd.concat([get_negociation(text[i]) for i in range(0,len(text))]).reset_index(drop=True)

    # movendo para a direita as linhas com a ultima coluna nula
    negociation = rshift_col(negociation)

    # movendo uma coluna pra esquerda as notas da CM Capital
    cond_cmc = negociation.iloc[:,-1].str.replace('D','').str.replace('C','') != ''
    negociation.loc[cond_cmc,list(negociation.columns)[-5:len(negociation.columns)]] = negociation.loc[cond_cmc,list(negociation.columns)[-5:len(negociation.columns)]].shift(-1,axis=1)
    
    # Preenchendo a ultima coluna da penultima coluna das notas da CM Capital
    cond_pcolC = (negociation.iloc[:,-2].str.contains('C')==True)
    cond_pcolD = (negociation.iloc[:,-2].str.contains('D')==True)
    negociation.loc[cond_pcolC,list(negociation.columns)[-1]] = ['C' for i in negociation.loc[cond_pcolC].iloc[:,-1]]
    negociation.loc[cond_pcolD,list(negociation.columns)[-1]] = ['D' for i in negociation.loc[cond_pcolD].iloc[:,-1]]
    negociation.loc[cond_pcolC,list(negociation.columns)[-2]] = negociation.loc[cond_pcolC,list(negociation.columns)[-2]].replace('C','',regex=True)
    negociation.loc[cond_pcolD,list(negociation.columns)[-2]] = negociation.loc[cond_pcolD,list(negociation.columns)[-2]].replace('D','',regex=True)
    
    # Verificando se a coluna -5 é nula enquanto a coluna -6 não, caso sim a coluna -5 deve ser substituida pela -6
    cond_5nan = (negociation.iloc[:,-5].isnull())&(negociation.iloc[:,-6].notnull())
    negociation.loc[cond_5nan,list(negociation.columns)[-5]] = negociation.loc[cond_5nan,list(negociation.columns)[-6]]
    negociation.loc[cond_5nan,list(negociation.columns)[-6]] = np.nan
    
    # definindo quais colunas correspondem ao tipo de ativo
    negociation.loc[(negociation[2]=='VISTA')|(negociation[2]=='FRACIONARIO'),'tipo_ativo'] = negociation[2]
    negociation.loc[(negociation[2]=='OPCAO')|(negociation[2]=='EXERC'),'tipo_ativo'] = negociation[2] + ' ' + negociation[3] + ' ' + negociation[4]
    
    # Corrigindo operação que não está na posição correta
    for indice,linha in negociation.loc[negociation.iloc[:,-6].isnull()].iterrows():
        indice_valor = max(linha.iloc[:-5].dropna().index)
        try:
            if (linha[indice_valor] == 'D') | ('D#' in linha[indice_valor]):
                negociation.iloc[indice,-6] = linha[indice_valor]
                negociation.iloc[indice, indice_valor] = np.nan
        except:
            pass

    # substituindo valores nulo por strings vazias
    negociation = negociation.fillna('')
    negociation = negociation.replace(np.nan,'')

    # definindo quais colunas correspondem ao ativo
    cols_acoes = list(negociation.iloc[:,3:-6].columns)
    cols_opcoes = list(negociation.iloc[:,6:-4].columns)
    cond_acoes = (negociation[2]=='VISTA')|(negociation[2]=='FRACIONARIO')
    cond_opcoes = (negociation[2]=='OPCAO')|(negociation[2]=='EXERC')

    try:
        negociation.loc[cond_acoes,'ativo'] = negociation[cols_acoes].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
    except:
        pass

    try:
        negociation.loc[cond_opcoes,'ativo'] = negociation.loc[:,6]
    except:
        pass

    # criando o dataframe de negociação
    colunas = ['data',
               'corretora',
               'operação',
               'C/V',
               'tipo_ativo',
               'ativo',
               'quantidade',
               'valor']
    df_negociation = pd.DataFrame(columns = colunas)

    df_negociation['data'] = [pd.to_datetime(row[0],dayfirst=True) for row in negociation[0].str.split('###')]
    df_negociation['corretora'] = [row[1] for row in negociation[0].str.split('###')]
    df_negociation['operação'] = (negociation.iloc[:,-7]).str.strip()
    df_negociation['C/V'] = negociation[1]
    df_negociation['quantidade'] = negociation.iloc[:,-6]
    df_negociation['valor'] = negociation.iloc[:,-4]
    df_negociation['tipo_ativo'] = negociation['tipo_ativo']
    df_negociation['ativo'] = negociation['ativo']

    # corrigindo tipo de operação
    df_negociation['operação'] = (df_negociation['operação'].replace('/','',regex=True)
                                                            .replace('FM','',regex=True)
                                                            .replace('EDR','',regex=True)
                                                            .replace('J','',regex=True)
                                                            .replace('E','',regex=True)
                                                            .replace('CIR','',regex=True))
    day_trade_cond = (df_negociation['operação'].str.strip()=='D')|(df_negociation['operação'].str.strip().str.contains('D#'))
    df_negociation.loc[day_trade_cond,'operação'] = 'Day Trade'
    df_negociation.loc[df_negociation['operação']!='Day Trade','operação'] = 'Swing Trade'
    df_negociation.loc[df_negociation['tipo_ativo'].str.contains('EXERC'),'operação'] = 'Exercício de opções'

    # renomeando os tipos de ativo
    df_negociation.loc[df_negociation['tipo_ativo'].str.contains('OPCAO'),'tipo_ativo2'] = 'Opção'
    df_negociation.loc[df_negociation['tipo_ativo'].str.contains('EXERC'),'tipo_ativo2'] = 'Ação'
    df_negociation.loc[df_negociation['ativo'].str.contains('FII'),'tipo_ativo2'] = 'Fundo imobiliário'
    df_negociation.loc[df_negociation['tipo_ativo2'].isnull(),'tipo_ativo2'] = 'Ação'
    df_negociation['tipo_ativo'] = df_negociation['tipo_ativo2']
    df_negociation.drop(['tipo_ativo2'],inplace=True,axis=1)

    # corrigindo as colunas numéricas
    df_negociation['quantidade'] = df_negociation['quantidade'].str.replace('.','').astype(int)
    df_negociation['valor'] = df_negociation['valor'].str.replace('.','').str.replace(',','.').astype(float)

    # inserindo informação de compra e venda nas colunas numéricas
    df_negociation.loc[df_negociation['C/V']=='C','valor'] = df_negociation['valor']*-1
    df_negociation.loc[df_negociation['C/V']=='V','quantidade'] = df_negociation['quantidade']*-1
    df_negociation.drop(['C/V'], axis=1, inplace=True)

    # corrigindo nome das corretoras
    df_negociation.loc[df_negociation.corretora.str.contains('CLEARCORRETORA'),'corretora'] = 'Clear Investimentos'
    df_negociation.loc[df_negociation.corretora.str.contains('CMCAPITAL'),'corretora'] = 'CM Capital'
    df_negociation = df_negociation.sort_values(by='data').reset_index(drop=True)
    
    # corrigindo nome de ativos
    df_negociation.loc[:,'ativo'] = df_negociation.loc[:,'ativo'].replace(' ','',regex=True).replace('#','',regex=True)
    
    df_negociation.loc[df_negociation.ativo.str.contains('ENGIEBRASILO'),'ativo'] = 'EGIE3'
    df_negociation.loc[df_negociation.ativo.str.contains('AESTIETEEUNT'),'ativo'] = 'TIET11'
    df_negociation.loc[df_negociation.ativo.str.contains('BBSEGURIDADEON'),'ativo'] = 'BBSE3'
    df_negociation.loc[df_negociation.ativo.str.contains('CCRSAON'),'ativo'] = 'CCRO3'
    df_negociation.loc[df_negociation.ativo.str.contains('TELEFBRASILPN'),'ativo'] = 'VIVT4'
    
    ativos_dict = ccb.cart_bovesp()[1]

    try:
        ativos = df_negociation.loc[(df_negociation.tipo_ativo!='Opção')&(df_negociation.operação!='Exercício de opções'),'ativo']
        for n in list(ativos_dict.keys()):
            ativos.loc[ativos.str.contains(n)] = ativos_dict[n]
        df_negociation.loc[(df_negociation.tipo_ativo!='Opção')&(df_negociation.operação!='Exercício de opções'),'ativo'] = ativos
    except:
        pass
    
    df_negociation.loc[:,'ativo'] = df_negociation.loc[:,'ativo'].replace('NM','',regex=True).replace('N1','',regex=True).replace('N2','',regex=True).replace('EJS','',regex=True)
    
    return df_negociation, negociation, time.time() - start_time