# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 20:07:55 2020

@author: femdi
"""

import pandas as pd
import camelot
import datetime
import numpy as np
from os import chdir, listdir

#List taken from https://www.infomoney.com.br/minhas-financas/confira-o-cnpj-das-acoes-negociadas-em-bolsa-e-saiba-como-declarar-no-imposto-de-renda/
# and http://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/etf/renda-variavel/etfs-listados/
Lista_empresas = pd.read_excel(r'C:\Users\femdi\OneDrive\Documentos\Python\PyCharm\Leitor_de_nota_de_corretagem_clear\Empresas_Listadas.xlsx')

def pdf_to_pandas_clear(path):
    '''
    Parameters
    ----------
    path : complete path of the folder when your pdfs are stored
            exemple: "C:\\Users\\exemple\\Downloads"
    Returns
    -------
    notas : pandas dataframe with columns 'Negociação', 
    'Compra/Venda', 'Tipo de Mercado', 'Epecificação do título', 'Quantidade', 'Preço', 'Valor',
    'Débito/Crédito', 'Data' and 'Código' well formated
    '''
           
    arquivos_path = listdir(path)

    notas_path = []
    for i in range(len(arquivos_path)):
                   if 'NotaNegociacao' in arquivos_path[i]:
                       notas_path.append(arquivos_path[i])
    
    
    
    notas = pd.DataFrame()
    for i in notas_path:
        path_pdf = r'{}\{}'.format(path, i)
        
        
    
        #Using the lib camelot to select tables in a pdf 
        tables = camelot.read_pdf(path_pdf, flavor='stream', table_areas = ['0,600,600,400'],
                                  columns=['91,105,167,180,305,345,402,445,543'])
        
          
        ######## IF ERROR "EOF marker not found":
            #That's a strange error that usually happens with Clear pdf's
            #It's caused because the pdf had an error in the making of it.
            #####SOLVING ######
            #I normally open the pdf file and make a little edit:
            #For example, I open the pdf using Microsoft Edge, because there it is possible
            #To write with your mouse. So I make a little dot in the top of the pdf.
            #That way, the pdf is saved properly, with a good format (with EOF marker)
        
        
        #Selecting the second table
        notas_de_corretagem = tables[0].df
        
        #Making the first row the header
        notas_de_corretagem.columns = notas_de_corretagem.loc[0]
        
        #Excluding the first row (now it is the header) and reseting the index
        notas_de_corretagem2 = notas_de_corretagem.drop([0], axis=0).reset_index(drop =True)
        
        #Fixing the columns
        notas_de_corretagem2.columns = ['Negociação', 'Compra/Venda', 'Tipo de Mercado', 'Prazo',
                                        'Especificação do título','Obs', 'Quantidade', 'Preço','Valor', 'Débito/Crédito']
        
        notas_de_corretagem3 = notas_de_corretagem2.drop(['Prazo','Obs'], axis=1).reset_index(drop =True)
        
        
        # Fixing date 
        tables1 = camelot.read_pdf(path_pdf, flavor='stream')
        df_date = tables1[0].df
        date_wrong = df_date.iloc[2,2]
        year = int(date_wrong[-4:])
        month = int(date_wrong[-7:-5])
        day = int(date_wrong[-10:-8])
        date = datetime.datetime(year, month, day).date()
        
        #Adding date to the main table
        notas_de_corretagem4 = notas_de_corretagem3.assign(Data = [date]*len(notas_de_corretagem2))
        
        #transforming 'V' to 'Venda' and 'C' to 'Compra'
        x = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Compra/Venda']
            if y == 'C':
                w = 'Compra'
            elif y == 'V':
                w = 'Venda'
            else:
                w = 'Error'
            x = np.append(x, w)
        notas_de_corretagem4['Compra/Venda'] = x
        
        #transforming 'D' to 'Débito' and 'C' to 'Crédito'
        x = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Débito/Crédito']
            if y == 'D':
                w = 'Débito'
            elif y == 'C':
                w = 'Crédito'
            else:
                w = 'Error'
            x = np.append(x, w)
        notas_de_corretagem4['Débito/Crédito'] = x
        
        #Converting 'Preço / Ajuste' into a numerical value (float)
        x = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Preço']
            # Here we substitute the decimal ',' with '.' and the milliard '.' with ''
            local = y.rfind(',')
            z = y[:local] + '.' +  y[local+1:]
            if len(z) > 6:
                local2 = z.find('.')
                t = float(z[:local2] + '' +  z[local2+1:])
            else:
                t = float(z)
            x = np.append(x, t)
        notas_de_corretagem4['Preço'] = x
              
        
        #Converting 'Quantidade' into a numerical value (int)
        x = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = int(notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Quantidade'])
            x = np.append(x, y)
        notas_de_corretagem4['Quantidade'] = x    
        
        #Calculating 'Valor / Ajuste' as numerical value (float)    
        x = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = np.round(notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Preço'] * notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Quantidade'],2)
            x = np.append(x, y)
        notas_de_corretagem4['Valor'] = x    
        
        #Coverting the enterprise name ('Especificação do título') to the stock code ('Código')
        
        #Selecting only the main name of the good (ticker)        
        
        on_pn = 0
        nome = 0
        codigo = []
        tipo = []
        for i in np.arange(len(notas_de_corretagem4)):
            y = notas_de_corretagem4.loc[notas_de_corretagem4.index[i], 'Especificação do título']
            w = y.split('          ')
            if len(w) == 3:
                w = w[:-1]

            nome = w[0]
            on_pn = w[1]
            
            cod = ''
            tipo_papel = ''
            for j in np.arange(len(Lista_empresas)):
                if nome == Lista_empresas['Nome de Pregão'][j]:
                    cod = str(Lista_empresas['Código'][j])[:4]
                    if "ON" in on_pn:
                        cod = f'{cod}{3}'
                        tipo_papel = 'Ação'
                    elif "PNA" in on_pn:
                        cod = f'{cod}{5}'
                        tipo_papel = 'Ação'
                    elif "PNB" in on_pn:
                        cod = f'{cod}{6}'
                        tipo_papel = 'Ação'
                    elif "PNC" in on_pn:
                        cod = f'{cod}{7}'
                        tipo_papel = 'Ação'
                    elif "PND" in on_pn:
                        cod = f'{cod}{8}'
                        tipo_papel = 'Ação'
                    elif "UNT " in on_pn:
                        cod = f'{cod}{11}'
                        tipo_papel = 'Ação'
                    elif "PN" in on_pn:
                        cod = f'{cod}{4}'
                        tipo_papel = 'Ação'
                    elif "CI" in on_pn:
                        cod = f'{cod}{11}'
                        tipo_papel = 'ETF'
                        
            if cod == '':
                cod = on_pn
                tipo_papel = 'FII'
            codigo.append(cod)
            tipo.append(tipo_papel)
        
        notas_de_corretagem4['Código'] = codigo
        notas_de_corretagem4['Tipo Papel'] = tipo

        notas = pd.concat([notas,notas_de_corretagem4]).reset_index(drop=True)
        
    return notas




##########TESTE



path = r'C:\Users\femdi\OneDrive\Documentos\Python\PyCharm\Leitor_de_nota_de_corretagem_clear\Felipe'
notas = pdf_to_pandas_clear(path)


notas.to_excel(r'C:\Users\femdi\OneDrive\Documentos\Python\PyCharm\Leitor_de_nota_de_corretagem_clear\Felipe\Notas_Corretagem_Felipe.xlsx')


