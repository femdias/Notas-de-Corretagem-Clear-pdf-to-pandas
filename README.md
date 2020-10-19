# Notas-de-Corretagem-Clear-pdf-to-pandas
This program (function) reads 'Notas de Corretagem' and transforms it into a pandas DataFrame. The function receives the path (folder) where the 'Notas de Corretagem' are stored and returns a DataFrame with all your negociations.

For the function to work, you should import the following  libraries:

import pandas as pd
import camelot
import datetime
import numpy as np
from os import chdir, listdir

You should also have an excel file with the Names and Codes from the stock. The information is taken from the website: https://www.infomoney.com.br/minhas-financas/confira-o-cnpj-das-acoes-negociadas-em-bolsa-e-saiba-como-declarar-no-imposto-de-renda/
