import shutil
import glob
import sys
import os

try:
    ext = sys.argv[1]
except:
    ext = 'txt'

files_of = glob.glob(f'./OFs/*{ext}') + glob.glob(f'./OFs/*png')
files_cf = glob.glob(f'./CFs/*{ext}') + glob.glob(f'./CFs/*png')
files_ot = glob.glob(f'./OTs/*{ext}') + glob.glob(f'./OTs/*png')

tudo = files_of + files_cf + files_ot

print(f'Arquivos:\n\t', *tudo, sep='  ')
y = input('Deseja remover todos os arquivos? (s)/n\n')

if 's' in y.lower():
    for file in files_of + files_cf + files_ot:
        print(f'Removendo {file}')
        os.remove(file)