import os
from PyPDF2 import PdfFileReader, PdfFileMerger
import pdf_to_text as pdftt

def juntar_pdf(diretorio):
    """Função que junta todos os arquivos pdf de um diretório"""
    arquivos_pdf = [nome_arquivo for nome_arquivo in os.listdir(diretorio) if nome_arquivo.endswith("pdf")]
    agregador = PdfFileMerger()

    for nome_arquivo in arquivos_pdf:
        agregador.append(PdfFileReader(os.path.join(diretorio, nome_arquivo), "rb"))

    agregador.write(os.path.join(diretorio, "pdf_agregado.pdf"))
    
def juntar_texto(diretorio):
    """Função que transforma todos os arquivos pdf de um diretório em texto e os junta"""
    arquivos_pdf = [nome_arquivo for nome_arquivo in os.listdir(diretorio) if nome_arquivo.endswith("pdf")]
    agregador = []

    for nome_arquivo in arquivos_pdf:
        arquivo = pdftt.get_pdf_text(os.path.join(diretorio, nome_arquivo))[0]
        for pagina in arquivo:
            agregador.append(pagina)
        
    return agregador