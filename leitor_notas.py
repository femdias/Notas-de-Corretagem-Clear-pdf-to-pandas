import pandas as pd
import numpy as np
import re

from utils import pdf_to_text, df_taxas, df_negociation
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)

# Pegando o texto do pdf
text,time_text = ptt.get_pdf_text(r'D:\Projetos\Leitor nota de corretagem\notas\merged_full.pdf')

# Criando df_negociation
df_negociation,time_negociation = dfn.build_dfneg(text)

# Criando df_taxas
df_taxas,time_taxas = dftx.build_dftx(text)

# mostrando resultados
dict_mes = {1:'Janeiro',
            2:'Fevereiro',
            3:'Março',
            4:'Abril',
            5:'Maio',
            6:'Junho',
            7:'Julho',
            8:'Agosto',
            9:'Setembro',
            10:'Outubro',
            11:'Novembro',
            12:'Dezembro'}

df_negociation['mes'] = [str(df_negociation['data'].dt.year[i])+'/'+str(df_negociation['data'].dt.month[i]).zfill(2) for i in range(0,len(df_negociation))]

colunas = ['mes_name'
           'mes_num',
           'ano',
           'resultado',
           'pagar_IR']
df_resultado = pd.DataFrame(columns = colunas)
cond = (df_negociation['data'].dt.month == 5)&(df_negociation['data'].dt.year == 2020)&(df_negociation['operação'] == 'Day Trade')
df_negociation[df_negociation['operação'] == 'Day Trade'].groupby(['mes','ativo'], as_index=False).sum()

# função que descobre a posição do ativo
def get_position(linha):
    quantidade = linha.quantidade
    if quantidade > 0:
        posição = 'comprado'
        df_ativos = df_negociation.loc[(df_negociation.ativo==linha.ativo) & (df_negociation.valor>=0) & (df_negociation.fechado == 2)]
    else:
        posição = 'vendido'
        df_ativos = df_negociation.loc[(df_negociation.ativo==linha.ativo) & (df_negociation.valor<0) & (df_negociation.fechado == 2)]
    return posição, df_ativos

# coluna responsável por gravar as operações já analisadas pelo código
df_negociation['fechado'] = 2

# laço que irá percorrer por cada linha desde que ela já não tenha feito parte de outra operação
for indicex, linhax in df_negociation[df_negociation.fechado != 1].iterrows():
    df_negociation.loc[indicex,'fechado'] = 1 # a primeira linha já foi estudada
    # descobre se a linha se trata de uma posição comprada ou vendida e faz um filtro na tabela
    # que deve aparecer apenas as operações complementares a ela
    posiçãox, df_ativos = get_position(linhax)

    # qtd ativos em custódia 
    qtd_oper = linhax.quantidade
    
    # irá formar uma lista com o indice do dataframe das operações que fazem parte
    # da operação do indicex
    indice_list = []
    
    # laço que percorre as linhas que podem ter relação com a operação do indicex
    for indicey, linhay in df_ativos.iterrows():
        qtd_oper = qtd_oper + linhay.quantidade # atualiza qtd ativos em custódia
        linhay.fechado = 1 # recebe 1 para mostrar que já foi uma linha usada
        indice_list.append(indicey) # é adicionada na lista de indices já usados em relação ao indicex
        
        # descobre a duração da operação
        oper_duration = linhay.data - linhax.data
        
        # guarda inicialmente qual é o tipo de operação do indicex
        oper_indicex = linhax.operação
        
        # preço do ativo no inicio
        preco_at = linhax.valor/linhax.quantidade
        
        # designa se é day trade ou swing trade
        if oper_duration == 0:
            df_negociation.loc[indicey,'operação'] = 'Day Trade'
        elif (oper_duration > 0) & (oper_duration <= 30):
            df_negociation.loc[indicey,'operação'] = 'Swing Trade'
        elif (oper_duration > 30):
            df_negociation.loc[indicey,'operação'] = 'Position Trade'
                  
        if qtd_oper == 0:
            linhas_y = df_negociation.iloc[indice_list]
            tipos_negoc = linhas_y.operação.unique()
            
            for tipo in tipos_negoc:
                qtd_tipo = linhas_y.loc[linhas_y.operação == tipo,'quantidade'].sum()
                tipo_result = qtd_tipo + linhax.quantidade
                
                if tipo_result == 0:
                    break
                else:
                    linha_new = linhax
                    linha_new['quantidade'] = qtd_tipo*-1
                    linha_new['valor'] = preco_at * abs(linha_new['quantidade'])
                    linha_new['fechado'] = 1
                    linha_new['operação'] = tipo
                    df_negociation.append(linha_new)
                    
                    df_negociation.loc[indicex,'quantidade'] = linhax.quantidade + qtd_tipo
                    df_negociation.loc[indicex,'valor'] = preco_at * abs(df_negociation.loc[indicex,'quantidade'])
            break
            
        else:
            if linhay.quantidade < 0:
                linha_new = linhay
                linha_new['quantidade'] = qtd_oper
                linha_new['valor'] = (linhay.valor/linhay.quantidade) * abs(linha_new['quantidade'])
                linha_new['fechado'] = 1
                df_negociation.append(linha_new)
                
                df_negociation.loc[indicey,'quantidade'] = linhay.quantidade + abs(qtd_oper)
                df_negociation.loc[indicey,'valor'] = preco_at * abs(df_negociation.loc[indicey,'quantidade'])
            
            
            