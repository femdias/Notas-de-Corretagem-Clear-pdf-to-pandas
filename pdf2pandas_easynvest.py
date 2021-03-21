# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 20:07:55 2020

@author: femdi
@coautor: LeonardoDonatoNunes
"""

# Instructions

# To identify the PDF coordinates where the data is located use the function bellow at the terminal
# camelot stream -plot text pdf_path.pdf

import pandas as pd
import camelot
from datetime import datetime
import os
from os import listdir
import pikepdf
import numpy as np


# Path where the pdf files are located
path  = "C:/Users/leona/Documents/Arquivos/Projetos/NotasCorretagem/Easynvest"

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
        tables = camelot.read_pdf(path_pdf , flavor='stream', table_areas = ['0,685,685,0'],
            columns=['65,102,168,274,360,445,505,560'])
    except:
        #Open and save pdf solve some possible errors
        path_pdf = refactor_pdf(path_pdf)
        
        tables = camelot.read_pdf(path_pdf , flavor='stream', table_areas = ['0,685,685,400'], 
        columns=['65,102,168,274,360,445,505,560'])
    
    notas_de_corretagem = tables[0].df
    tables1 = camelot.read_pdf(path_pdf, flavor='stream')
    return notas_de_corretagem, tables1     

def id_patterns(notas_de_corretagem):
    #All patterns have the same treatment, but for debugs sake they are classified
    
    pattern1 = ['Mercado',
                 'C/VC',
                 'Tipo de Mercado',
                 'Especificação do Título',
                 'Observação',
                 'Quantidade',
                 'Preço/Ajuste',
                 'Valor/Ajuste',
                 'D/CD/C']   
    
    pattern2 = ['Mercado\nMercado',
                 'C/VC/V',
                 'Tipo de Mercado\nTipo de Mercado',
                 'Especificação do Título\nEspecificação do Título',
                 'Observação\nObservação',
                 'Quantidade\nQuantidade',
                 'Preço/Ajuste\nPreço/Ajuste',
                 'Valor/Ajuste',
                 'Valor/Ajuste D/CD/C']   
                 
    pattern2 = ['Mercado\nMercado',
                 'C/VC/V',
                 'Tipo de Mercado\nTipo de Mercado',
                 'Especificação do Título\nEspecificação do Título',
                 'Observação\nObservação',
                 'Quantidade\nQuantidade',
                 'Preço/Ajuste\nPreço/Ajuste',
                 'Valor/Ajuste',
                 'Valor/Ajuste D/CD/C']     
                 
    pattern = notas_de_corretagem.loc[0].to_list()
    
    
    #Excluding the first row (now it is the header) and reseting the index
    notas_de_corretagem = notas_de_corretagem.iloc[1:,:].copy()
    
    
    
    
    if pattern == pattern1 or pattern == pattern2 or pattern == pattern3:
        notas_de_corretagem.columns = ['Q Negociação',
                 'Compra/Venda',
                 'Tipo mercado',
                 'Especificação do título',
                 'Obs. (*)',
                 'Quantidade',
                 'Preço / Ajuste',
                 'Valor Operação / Ajuste',
                 'D/C']
        notas_de_corretagem = notas_de_corretagem[notas_de_corretagem['Q Negociação'] == 'BOVESPA']
        return notas_de_corretagem
        
    
    
def treat(notas_de_corretagem, tables1):
        #Treat the pdf data
        
        #Find pattern
        notas_de_corretagem = id_patterns(notas_de_corretagem)

        #Excluding useless columns
        notas_de_corretagem.drop(columns = ['Obs. (*)'], inplace = True)


        #format values and data types
        df_date = tables1[0].df
        dt_string = df_date.iloc[3,2]
        date_datetime  = datetime.strptime(dt_string, "%d/%m/%Y")
        notas_de_corretagem['Data Pregao'] = date_datetime
        notas_de_corretagem['D/C'] = notas_de_corretagem['D/C'].replace({'D':'Debito', 'C':'Credito', 'DC': "Debido/Credito"}).copy()                
        notas_de_corretagem['Preço / Ajuste'] = notas_de_corretagem['Preço / Ajuste'].map(parse_num)
        notas_de_corretagem['Valor Operação / Ajuste'] = notas_de_corretagem['Valor Operação / Ajuste'].map(parse_num)
        notas_de_corretagem['Quantidade'] = notas_de_corretagem['Quantidade'].astype(int)

        return notas_de_corretagem
    
def ets(path):
    
    df = []
    
    arquivos_path = listdir(path)
    
    #filter files that contain the string "NotaCorretagem" in filename
    notas_path = [os.path.join(path, file) for file in arquivos_path if 'Invoice' in file and False==file.endswith('_resaved.pdf')]
    
    for path_pdf in notas_path:
        #Extract data from pdf
        notas_de_corretagem, tables1 = extract(path_pdf)
        
        #Format extracted data        
        notas_de_corretagem = treat(notas_de_corretagem, tables1)
        
        #register basefile
        notas_de_corretagem['file'] = path_pdf
        
        #store results
        df.append(notas_de_corretagem)
        
    return pd.concat(df)

#Agrouped pdfs in pandas df
df = ets(path)

df2 = df

def calculate_results(df):    
    df_ = df.set_index(['Especificação do título', 'Data Pregao']).sort_index()
    df_['Signal'] = df_['Compra/Venda'].map({'C':-1,'V':1})
    df_['Value'] = df_['Signal'] * df_['Valor Operação / Ajuste']
    df_.reset_index(inplace = True)
    df_['Value_acum'] = np.nan
    
    
    for i,r in df_.groupby('Especificação do título'):
        
        df_.loc[r.index,'Value_acum'] = r['Value'].cumsum()
    
    cols = ['Especificação do título', 'Data Pregao',
           'Compra/Venda', 'D/C',
           'Value_acum']
    
    df_2 = df_[cols].groupby('Especificação do título').max()
    
    df_2.Value_acum.sum()
    return df_2

df_results = calculate_results(df)

