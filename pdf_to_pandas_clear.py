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

path  = "/home/fm/Documents/GitHub/em_desenvolvimento/Notas-de-Corretagem-Clear-pdf-to-pandas"

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
        notas_de_corretagem[['Especificação do título', 'Códigos Papel']] = notas_de_corretagem['Especificação do título'].str.split('          ', expand = True)
        
        return notas_de_corretagem
    
def etl(path):
    
    df = []
    
    arquivos_path = listdir(path)
    
    #filter files that contain the string "NotaCorretagem" in filename
    notas_path = [os.path.join(path, file) for file in arquivos_path if 'NotaNegociacao' in file]
    
    for path_pdf in notas_path:
        #Extract data from pdf
        notas_de_corretagem, tables1 = extract(path_pdf)
        
        #Format extracted data        
        notas_de_corretagem = treat(notas_de_corretagem, tables1)
       
        #store results
        df.append(notas_de_corretagem)
        
    return pd.concat(df)

df = etl(path)
