# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 20:07:55 2020

@author: femdi
@coautor: 
"""

import pandas as pd
import camelot
from datetime import datetime
import os
from os import listdir
import pikepdf
import numpy as np

path  = os.path.join(os.getcwd(), './notas')

def refactor_pdf(path_pdf):
        modified_pdf_name = os.path.basename(path_pdf).split('.')
        modified_pdf_name = modified_pdf_name[0]+'_resaved.pdf'
        dir_name = os.path.dirname(path_pdf)
        path_pdf_resaved = os.path.join(dir_name,modified_pdf_name)
        pdf_resaved = pikepdf.Pdf.open(path_pdf)            
        pdf_resaved.save(path_pdf_resaved)
        return path_pdf_resaved

def parse_num(num_str):
     x = num_str.replace('.','').replace(',','.')
     return float(x)

def extract(path_pdf):
    try:
        #Using the lib camelot to select tables in a pdf 
        tables = camelot.read_pdf(path_pdf , flavor='stream', table_areas = ['0,600,600,400'],
                              columns=['91,105,167,180,305,345,402,445,543'])
    except:
        #Open and save pdf solve some possible errors
        path_pdf = refactor_pdf(path_pdf)
        
        tables = camelot.read_pdf(path_pdf , flavor='stream', table_areas = ['0,600,600,400'], columns=['91,105,167,180,305,345,402,445,543'])
    
    notas_de_corretagem = tables[0].df
    tables1 = camelot.read_pdf(path_pdf, flavor='stream')
    return notas_de_corretagem, tables1     

def id_patterns(notas_de_corretagem):
    #All patterns have the same treatment, but for debugs sake they are classified
    pattern1 = ['Q Negociação',
                 '',
                 'C/V Tipo mercado',
                 'Prazo',
                 'Especificação do título',
                 'Obs. (*)\nQuantidade',
                 '',
                 'Preço / Ajuste',
                 'Valor Operação / Ajuste',
                 'D/C']
    
    pattern2 = ['Q Negociação',
                 'C/V Tipo mercado',
                 '',
                 'Prazo',
                 'Especificação do título',
                 'Obs. (*)',
                 'Quantidade',
                 'Preço / Ajuste',
                 'Valor Operação / Ajuste',
                 'D/C']
    
    pattern3 = ['Q Negociação',
                 '',
                 'C/V Tipo mercado',
                 'Prazo',
                 'Especificação do título',
                 'Obs. (*)',
                 'Quantidade',
                 'Preço / Ajuste',
                 'Valor Operação / Ajuste',
                 'D/C']
    
    pattern = notas_de_corretagem.loc[0].to_list()
    
    
    #Excluding the first row (now it is the header) and reseting the index
    notas_de_corretagem = notas_de_corretagem.iloc[1:,:].copy()
    
    if pattern == pattern1 or pattern == pattern2 or pattern == pattern3:
        
        notas_de_corretagem.columns = ['Q Negociação',
                 'Compra/Venda',
                 'Tipo mercado',
                 'Prazo',
                 'Especificação do título',
                 'Obs. (*)',
                 'Quantidade',
                 'Preço / Ajuste',
                 'Valor Operação / Ajuste',
                 'D/C']
        
        return notas_de_corretagem
        
    
def treat(notas_de_corretagem, tables1):
        #Treat the pdf data
        
        #Find pattern
        notas_de_corretagem = id_patterns(notas_de_corretagem)

        #Excluding useless columns
        notas_de_corretagem.drop(columns = ['Prazo','Obs. (*)'], inplace = True)


        #format values and data types
        df_date = tables1[0].df
        dt_string = df_date.iloc[2,2]
        date_datetime  = datetime.strptime(dt_string, "%d/%m/%Y")
        notas_de_corretagem['Data Pregao'] = date_datetime
        notas_de_corretagem['D/C'] = notas_de_corretagem['D/C'].replace({'D':'Debito', 'C':'Credito'}).copy()                
        notas_de_corretagem['Preço / Ajuste'] = notas_de_corretagem['Preço / Ajuste'].map(parse_num)
        notas_de_corretagem['Valor Operação / Ajuste'] = notas_de_corretagem['Valor Operação / Ajuste'].map(parse_num)
        notas_de_corretagem['Quantidade'] = notas_de_corretagem['Quantidade'].astype(int)

        # Esse padrão não funciona mais, agora na descrição vem uma string onde esse espaço aparece duas vezes e isso estava
        # Gerando um erro, é necessário tratar manualmente
        # notas_de_corretagem[['Especificação do título', 'Códigos Papel']] = notas_de_corretagem['Especificação do título'].str.split('          ', expand = True)
        a = notas_de_corretagem['Especificação do título'].str.split('          ', expand = True)
        notas_de_corretagem['Especificação do título'] = a[0]
        notas_de_corretagem['Códigos Papel'] = a[1]
        
        
        return notas_de_corretagem
    
def ets(path):
    
    df = []
    
    arquivos_path = listdir(path)
    
    #as some files probably are corrupted and corrected by the refactor_pdf function, we need to manage duplicates
    notas_resaved = [ _file for _file in arquivos_path if 'resaved' in _file]
    notas_corrupted = [_file.replace('_resaved','') for _file in notas_resaved]
    
    #filtering corrupted, other files and join to the full path from each nota
    notas_path = [os.path.join(path,_file) for _file in arquivos_path if (_file not in notas_corrupted) and ('NotaNegociacao' in _file)]
    
    for path_pdf in notas_path:
        path_pdf
        #Extract data from pdf
        notas_de_corretagem, tables1 = extract(path_pdf)

        print(notas_de_corretagem)
        print(tables1)
        
        #Format extracted data        
        notas_de_corretagem = treat(notas_de_corretagem, tables1)
        
        #register basefile
        notas_de_corretagem['file'] = path_pdf
        
        #store results
        df.append(notas_de_corretagem)
        
    return pd.concat(df)

#Agrouped pdfs in pandas df

df = ets(path)

def calculate_results(df):    
    df_ = df.set_index(['Especificação do título', 'Data Pregao']).sort_index()
    df_['Signal'] = df_['Compra/Venda'].map({'C':-1,'V':1})
    df_['Value'] = df_['Signal'] * df_['Valor Operação / Ajuste']
    df_.reset_index(inplace = True)
    df_['Value_acum'] = np.nan
    
    
    for i,r in df_.groupby('Especificação do título'):
        
        df_.loc[r.index,'Value_acum'] = r['Value'].cumsum()
    
    cols = ['Especificação do título', 'Data Pregao',
           'Compra/Venda', 'D/C','Códigos Papel',
           'Value_acum']
    
    df_2 = df_[cols].groupby('Especificação do título').max()
    
    df_2.Value_acum.sum()
    return df_2

df_results = calculate_results(df)
df_results.Value_acum.sum()

df_results.to_excel('df_results.xlsx',encoding='utf-8',index=True)

print(df_results)