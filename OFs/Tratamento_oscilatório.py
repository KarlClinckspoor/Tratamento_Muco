# Esse script é uma adaptação do script utilizado para o tratamento de dados oscilatorios, feito na primeira vez com as
# amostras de muco

FREQ = 1  # Pegar dado em 1 Hz


import matplotlib.pyplot as plt
import pandas as pd
import glob
import gc
import numpy as np
import os
import sys
from collections import namedtuple
from lmfit import minimize, Parameters, report_fit
import shutil
import logging
logging.basicConfig(filename='oscilatorio.log',level=logging.DEBUG)


def achar_linha_cabeçalho(arquivos):
    """Essa função está aqui mais por compatibilidade. A versão nova assume que a primeira linha já contém as colunas.
     Encontra a linha onde os dados começam, e retorna um dicionário com o nome do arquivo e a linha."""

    linhas = {}
    for arquivo in arquivos:
        fhand = open(arquivo, encoding='latin1')
        for i, line in enumerate(fhand):
            if line.startswith(';'):
                linhas[arquivo] = i
            else:
                continue

    return linhas


def testar_abrir_arquivos(arquivos, use_headers=False, linhas=None):
    """Busca em todos os arquivos e checa se tem as colunas necessárias para fazer o tratamento, isso é, G', G'' e
    alguma frequência, seja angular ou linear. Retorna uma lista de arquivos falhos"""

    falhas = []

    for arquivo in arquivos:
        try:
            if use_headers:
                df = pd.read_csv(arquivo,
                                 header=linhas[arquivo] - 1,
                                 sep=';',
                                 encoding='latin1',
                                 decimal=',',
                                 na_values=' ')
            else:
                df = pd.read_csv(arquivo,
                                 sep=';',
                                 decimal=',',
                                 na_values=' ')
        except Exception as e:
            print('Falha ao abrir arquivo:', arquivo, '. Exceção {}'.format(e))
            print(df.head())
            continue

        has_necessary_columns = {'Freq': False, "G'": False, "G''": False}
        for col in df.columns:
            if ('omega' in col) or ('f' in col):
                has_necessary_columns['Freq'] = True
            if ("G''" in col):
                has_necessary_columns["G''"] = True
            if ("G'" in col) and ("G''" not in col):
                has_necessary_columns["G'"] = True

        if not all(has_necessary_columns.values()):
            print(f'O arquivo "{arquivo}" não possui as colunas necessárias para o tratamento.')
            print(f'\tColunas: {df.columns}')
            falhas.append(arquivo)
        else:
            print(f'O arquivo "{arquivo}" possui as colunas necessárias para o tratamento.')

    return falhas


def mover_falhas(falhas):
    if not os.path.isdir('./falhas'):
        os.mkdir('./falhas')
    for falha in falhas:
        shutil.move(falha, os.path.join('./falhas', falha))


###### Funções para os ajustes

def linear(x, a, b):
    return a * x + b

def residual(params, x, dataset):
    return dataset - linear(x, params['a'], params['b'])

def exp(x, a, b, c):
    return a * np.e ** (x / b) + c

def residual_exp(params, x, dataset):
    return dataset - exp(x, params['a'], params['b'], params['c'])


# todo: refactor para manter os nomes consistentes
# todo:
def tratamento_exponencial(files):
    res_aj = namedtuple('Ajuste', ['nome', 'R2', 'ponto',
                                   'a', 'aerr',
                                   'b', 'berr',
                                   'c', 'cerr',
                                   'numfits'])

    if not os.path.isdir('./ajustes_exp'):
        os.mkdir('./ajustes_exp')

    log = open('erros.dat', 'w')
    resultados1 = open('paramsg1.dat', 'w')
    resultados2 = open('paramsg2.dat', 'w')
    resultados_tot = open('resultados_ajustes.dat', 'w')

    resultados1.write(f'nome;sobrenome;hora_coleta;hora_medida;data;num1;'
                      f'a_exp1;aerr_exp1;b_exp1;berr_exp1;c_exp1;cerr_exp1;R2_exp1;media1;std1;G{FREQ}Hz\n')
    resultados2.write(f'nome;sobrenome;hora_coleta;hora_medida;data;num2;'
                      f'a_exp2;aerr_exp2;b_exp2;berr_exp2;c_exp2;cerr_exp2;R2_exp2;media2;std2;G{FREQ}Hz\n')
    resultados_tot.write(f'nome;sobrenome;hora_coleta;hora_medida;data;num1;num2;'
                         f'a_exp1;aerr_exp1;b_exp1;berr_exp1;c_exp1;cerr_exp1;R2_exp1;media1;std1;'
                         f'a_exp2;aerr_exp2;b_exp2;berr_exp2;c_exp2;cerr_exp2;R2_exp2;media2;std2;G1_{FREQ}Hz;G2_{FREQ}Hz\n')

    for j, file in enumerate(files[:]):
        print(f'\tTratando "{file}"')
        g1fitsmade = 0
        g2fitsmade = 0

        try:
            df = pd.read_csv(file,
                             sep=';',
                             decimal=',',
                             na_values=' ')
        except Exception as e:
            print('Failed to open file', file, 'Exception {}'.format(e))
            continue

        usar_f = False
        usar_omega = False

        if 'f' in df.columns:
            usar_f = True
            fr = 'f'

        if 'omega' in df.columns:
            usar_w = True
            fr = 'omega'

        # todo: deixar isso passível de aceitar omega. No momento só aceita f, e passa pro próximo
        if not usar_f:
            print(f'O arquivo "{file}" não contém frequência em Hz. Pulando.')
            continue

        if usar_f and len(df['f']) == 0:
            continue

        if usar_w and len(df['omega']) == 0:
            continue


        df = df.dropna()  #
        df = df.reset_index(drop=True)

        #if all(df['Unnamed: 0'].str.startswith('1')):
        #    df = df
        #else:
        #    df = df[df['Unnamed: 0'].str.startswith('2')]

        if (any(df["G'"] < 0) or any(df["G''"] < 0)):
            print(f"O arquivo '{file}' tem valores negativos de G' e G''. Cuidado\n")

        x = np.log10(df["f"]).reset_index(drop=True)
        y1 = np.log10(df["G'"]).reset_index(drop=True)
        y2 = np.log10(df["G''"]).reset_index(drop=True)

        ajustes_g1_exp = []
        ajustes_g2_exp = []
        ajustes_g1_lin = []
        ajustes_g2_lin = []

        if (len(y1) != len(y2)):
            print(f'Comprimentos diferentes: {file}')

        for i, val in enumerate(y1):
            if i < 4:
                continue

            ############ Exponencial ##################

            params_e = Parameters()
            params_e.add('a', 10., vary=True)
            params_e.add('b', 1., vary=True)
            params_e.add('c', 0., vary=True)

            try:
                fit1e = minimize(residual_exp, params_e, args=(x[:i], y1[:i]))
                g1fitsmade += 1
            except Exception as e:
                print(file, 'error on fit G1: {}'.format(e))
                # print(y1.hasnans, i, '\n\n', y1[:i])
                continue
            try:
                fit2e = minimize(residual_exp, params_e, args=(x[:i], y2[:i]))
                g2fitsmade += 1
            except Exception as e:
                print(file, 'error on fit G2: {}'.format(e))
                # print(y2.hasnans, i, '\n\n', y2[:i])
                continue

            ############### Linear #########################

            params_l = Parameters()
            params_l.add('a', 10., vary=True)
            params_l.add('b', 1., vary=True)

            try:
                fit1l = minimize(residual, params_l, args=(x[:i], y1[:i]))
            except Exception as e:
                print(file, 'error on linear fit G1: {}'.format(e))
                # print(y1.hasnans, i, '\n\n', y1[:i])
                continue
            try:
                fit2l = minimize(residual, params_l, args=(x[:i], y2[:i]))
            except Exception as e:
                print(file, 'error on linear fit G2: {}'.format(e))
                # print(y2.hasnans, i, '\n\n', y2[:i])
                continue

            ################################################
            a1e = fit1e.params['a'].value
            aerr1e = fit1e.params['a'].stderr
            b1e = fit1e.params['b'].value
            berr1e = fit1e.params['b'].stderr
            c1e = fit1e.params['c'].value
            cerr1e = fit1e.params['c'].stderr

            a2e = fit2e.params['a'].value
            aerr2e = fit2e.params['a'].stderr
            b2e = fit2e.params['b'].value
            berr2e = fit2e.params['b'].stderr
            c2e = fit2e.params['c'].value
            cerr2e = fit2e.params['c'].stderr

            SSres1e = fit1e.chisqr
            SSres2e = fit2e.chisqr
            SStot1e = sum((y1[:i] - np.mean(y1[:i])) ** 2)
            SStot2e = sum((y2[:i] - np.mean(y2[:i])) ** 2)
            R21e = 1 - SSres1e / SStot1e
            R22e = 1 - SSres2e / SStot2e

            r1e = res_aj(file, R21e, i, a1e, aerr1e, b1e, berr1e, c1e, cerr1e, g1fitsmade)
            r2e = res_aj(file, R22e, i, a2e, aerr2e, b2e, berr2e, c2e, cerr2e, g2fitsmade)

            ajustes_g1_exp.append(r1e)
            ajustes_g2_exp.append(r2e)
            ###########################################################

            a1l = fit1l.params['a'].value
            aerr1l = fit1l.params['a'].stderr
            b1l = fit1l.params['b'].value
            berr1l = fit1l.params['b'].stderr

            a2l = fit2l.params['a'].value
            aerr2l = fit2l.params['a'].stderr
            b2l = fit2l.params['b'].value
            berr2l = fit2l.params['b'].stderr

            SSres1l = fit1l.chisqr
            SSres2l = fit2l.chisqr
            SStot1l = sum((y1[:i] - np.mean(y1[:i])) ** 2)
            SStot2l = sum((y2[:i] - np.mean(y2[:i])) ** 2)
            R21l = 1 - SSres1l / SStot1l
            R22l = 1 - SSres2l / SStot2l

            r1l = res_aj(file, R21l, i, a1l, aerr1l, b1l, berr1l, 0, 0, 0)
            r2l = res_aj(file, R22l, i, a2l, aerr2l, b2l, berr2l, 0, 0, 0)

            ajustes_g1_lin.append(r1l)
            ajustes_g2_lin.append(r2l)

            ###########################################################

        filtro1e = [i for i in ajustes_g1_exp if i.R2 > 0.90]
        filtro2e = [i for i in ajustes_g2_exp if i.R2 > 0.90]

        filtro1l = [i for i in ajustes_g1_lin if i.R2 > 0.90]
        filtro2l = [i for i in ajustes_g2_lin if i.R2 > 0.90]

        ###############################
        ## Exp ##
        if len(filtro1e) == 0:
            filtro1e = [i for i in ajustes_g1_exp if i.R2 > 0.85]
            filtro1e.sort(key=lambda x: x.R2, reverse=True)
            if len(filtro1e) == 0:
                filtro1e = ajustes_g1_exp[:]
                filtro1e.sort(key=lambda x: x.R2, reverse=True)
        else:
            filtro1e.sort(key=lambda x: x.ponto, reverse=True)

        if len(filtro2e) == 0:
            filtro2e = [i for i in ajustes_g2_exp if i.R2 > 0.85]
            filtro2e.sort(key=lambda x: x.R2, reverse=True)
            if len(filtro2e) == 0:
                filtro2e = ajustes_g2_exp[:]
                filtro2e.sort(key=lambda x: x.R2, reverse=True)
        else:
            filtro2e.sort(key=lambda x: x.ponto, reverse=True)
        #################################
        ## Linear ##
        if len(filtro1l) == 0:
            filtro1l = [i for i in ajustes_g1_lin if i.R2 > 0.85]
            filtro1l.sort(key=lambda x: x.R2, reverse=True)
            if len(filtro1l) == 0:
                filtro1l = ajustes_g1_lin[:]
                filtro1l.sort(key=lambda x: x.R2, reverse=True)
        else:
            filtro1l.sort(key=lambda x: x.ponto, reverse=True)

        if len(filtro2l) == 0:
            filtro2l = [i for i in ajustes_g2_lin if i.R2 > 0.85]
            filtro2l.sort(key=lambda x: x.R2, reverse=True)
            if len(filtro2l) == 0:
                filtro2l = ajustes_g2_lin[:]
                filtro2l.sort(key=lambda x: x.R2, reverse=True)
        else:
            filtro2l.sort(key=lambda x: x.ponto, reverse=True)

        #################################

        bom1 = filtro1e[0]
        bom2 = filtro2e[0]

        bom1l = filtro1l[0]
        bom2l = filtro2l[0]

        media1 = np.average(df["G'"][:bom1.ponto])
        media2 = np.average(df["G''"][:bom2.ponto])
        stdmedia1 = np.std(df["G'"][:bom1.ponto])
        stdmedia2 = np.std(df["G''"][:bom2.ponto])

        media1l = np.average(df["G'"][:bom1l.ponto])
        media2l = np.average(df["G''"][:bom2l.ponto])
        stdmedia1l = np.std(df["G'"][:bom1l.ponto])
        stdmedia2l = np.std(df["G''"][:bom2l.ponto])

        try:
            g1_1hz = df[df['f'] == FREQ]["G'"].iloc[0]
            g2_1hz = df[df['f'] == FREQ]["G''"].iloc[0]
        except:
            print(f'O arquivo "{file}" não tem dados na frequência {FREQ}')

        resultados1.write(f'{bom1.nome[:-4].replace(" ", ";")};{bom1.ponto};'
                          f'{bom1.a};{bom1.aerr};'
                          f'{bom1.b};{bom1.berr};'
                          f'{bom1.c};{bom1.cerr};'
                          f'{bom1.R2};{media1l};{stdmedia1l};{g1_1hz}\n')

        resultados2.write(f'{bom2.nome[:-4].replace(" ", ";")};{bom2.ponto};'
                          f'{bom2.a};{bom2.aerr};'
                          f'{bom2.b};{bom2.berr};'
                          f'{bom2.c};{bom2.cerr};'
                          f'{bom2.R2};{media2l};{stdmedia2l};{g2_1hz}\n')

        resultados_tot.write(f'{bom1.nome[:-4].replace(" ", ";")};{bom1.ponto};{bom2.ponto};'
                             f'{bom1.a};{bom1.aerr};'
                             f'{bom1.b};{bom1.berr};'
                             f'{bom1.c};{bom1.cerr};'
                             f'{bom1.R2};{media1l};{stdmedia1l};'
                             f'{bom2.a};{bom2.aerr};'
                             f'{bom2.b};{bom2.berr};'
                             f'{bom2.c};{bom2.cerr};'
                             f'{bom2.R2};{media2l};{stdmedia2l};{g1_1hz};{g2_1hz}\n')

        # print("G'", bom1.nome, bom1.R2, bom1.a, bom1.ponto)
        # print("G''", bom2.nome, bom2.R2, bom2.a, bom2.ponto)

        plt.figure()
        plt.plot(x, y1, 'ro', label="G'")
        plt.plot(x[:bom1.ponto], exp(x[:bom1.ponto], bom1.a, bom1.b, bom1.c), 'r-', label="G' exp")
        plt.plot(x[:bom1l.ponto], linear(x[:bom1l.ponto], bom1l.a, bom1l.b), 'm--', label="G' lin")

        plt.plot(x, y2, 'bo', label="G''")
        plt.plot(x[:bom2.ponto], exp(x[:bom2.ponto], bom2.a, bom2.b, bom2.c), 'b-', label="G'' exp")
        plt.plot(x[:bom2l.ponto], linear(x[:bom2l.ponto], bom2l.a, bom2l.b), 'm--', label="G'' lin")

        plt.xlabel('log(f/Hz)')
        plt.ylabel("log(G', G''/Pa)")

        try:
            plt.axvline(x[bom1.ponto - 1], linestyle='--', color='r')  # , ymax=y1[bom1.ponto]
            plt.axvline(x[bom2.ponto - 1], linestyle='--', color='b')
        except:
            print(x)
            break
        plt.legend(ncol=2)
        plt.title(file[:-4])


        plt.savefig(f'./ajustes_exp/{file[:-4]}.png')

        plt.gcf().clf()
        plt.close()
        del df
        gc.collect()

        print(f'Tratado arquivo {j+1} de {len(files)}\r', end='')

    resultados1.close()
    resultados2.close()
    resultados_tot.close()
    log.close()


if __name__ == '__main__':
    tratar = glob.glob('*txt')
    tratamento_exponencial(tratar)
