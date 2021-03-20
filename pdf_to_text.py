import pdfplumber
import time

# criando função que pega o texto do pdf
def pdf_to_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text_list = [pdf.pages[page_numb].extract_text().splitlines() for page_numb in range(0,len(pdf.pages))]
    return text_list

# criando função que transforma a primeira linha de um dataframe em sua coluna
def first_header(df):
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header
    return df

# transformando o pdf em texto
def get_pdf_text(diretorio):
    start_time = time.time()
    text = pdf_to_text(diretorio)
    return text,time.time() - start_time