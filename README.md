# Notas-de-Corretagem-Clear-pdf-to-pandas
This program (function) reads 'Notas de Corretagem' and transforms it into a pandas DataFrame. The function receives the path (folder) where the 'Notas de Corretagem' are stored and returns a DataFrame with all your negociations.

For the function to work, you should import the following  libraries:

import pandas as pd
import camelot
import datetime
import numpy as np
from os import chdir, listdir

You should also have an excel file with the Names and Codes from the stock. The information is taken from the website: https://www.infomoney.com.br/minhas-financas/confira-o-cnpj-das-acoes-negociadas-em-bolsa-e-saiba-como-declarar-no-imposto-de-renda/

This Excel is in this repository with the name "Empresas_Listadas.xlsx"

## Commum Error

A commun error with Clear PDF's is "EOF marker not found". It's caused because the pdf had an error in the making of it. 

That's how I solve it:
I open the pdf file and make a little edit. For example, I open the pdf using Microsoft Edge, because there it is possible to write with your mouse. So I make a little dot in the top of the pdf and save it. That way, the pdf is saved properly, with a good format (with EOF marker), fixing the error

If you got: AttributeError: module 'camelot' has no attribute 'read_pdf'

That's how I solve it:
Try to unstall and install again 
pip uninstall camelot
pip install camelot-py[cv]