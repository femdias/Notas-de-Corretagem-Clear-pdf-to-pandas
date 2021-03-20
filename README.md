# Notas-de-Corretagem-Clear-pdf-to-pandas
This program (function) reads pdf files called 'Notas de Corretagem' and transforms it into a pandas DataFrame. There's one function per trade financial agency. The main argument is the path where the pdfs files are located. The output is a dataframe with all your negociations.

## Commum Error
If you got: AttributeError: module 'camelot' has no attribute 'read_pdf'

Try to unstall and install again 
pip uninstall camelot
pip install camelot-py[cv]