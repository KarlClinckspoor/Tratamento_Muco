#!python3

import pandas as pd
import glob
import numpy as np
import os
import sys

import logging
logging.basicConfig(filename='extração.log',level=logging.DEBUG)


# todo: pensar se eu posso extrair as curvas de fluxo do oscilatório.
def extraction(df, nome=''):
    df = df.replace(to_replace=r'\s+', value=np.nan, regex=True)

    # Determinar quais columas existem
    necessary_CF_columns = ['GP', 'Eta']
    optional_CF_columns = ['T', 'Tau', 'serie']

    necessary_OF_columns1 = ["G'", "G''", 'omega']
    necessary_OF_columns2 = ["G'", "G''", 'f']
    optional_OF_columns = ['T', 'G*', 'Eta*', 'serie']

    necessary_OT_columns = ['Tau', "G'", "G''"]
    optional_OT_columns = ['T', 'serie']

    extract_CF = False
    extract_OF = False
    extract_OT = False
    CF_columns = []
    OF_columns = []
    OT_columns = []

    df_CF = None
    df_OT = None
    df_OF = None

    ## Curva de fluxo
    if set(necessary_CF_columns).issubset(set(df.columns)):
        extract_CF = True
        for column in necessary_CF_columns + optional_CF_columns:
            if column in df.columns:
                CF_columns.append(column)

    ## Oscilatório Frequência
    if set(necessary_OF_columns1).issubset(set(df.columns)) or set(necessary_OF_columns2).issubset(set(df.columns)):
        extract_OF = True
        for column in necessary_OF_columns1 + necessary_OF_columns2 + optional_OF_columns:
            if column in df.columns:
                OF_columns.append(column)

    ## Oscilatório Tensão
    if set(necessary_OT_columns).issubset(set(df.columns)):
        extract_OT = True
        for column in necessary_OT_columns + optional_OT_columns:
            if column in df.columns:
                OT_columns.append(column)

    # Extraindo seções
    if extract_CF:
        df_CF = df[CF_columns].dropna()
        if df_CF.size == 0:
            df_CF = None

    if extract_OF or extract_OT:
        df_osc = df[list({*OF_columns, *OT_columns})].dropna() # Como CF não tem omega/f, o dropna remove isso

    # Determinar a divisão entre o oscilatório de frequência e de tensão:
    if (extract_OF or extract_OT) and df_osc.size != 0:
        df_osc['experimentos'] = df_osc['serie'].str.split('|').apply(lambda x: x[0])
        experimentos_unicos = df_osc['experimentos'].unique() # Vê se tem 1, 2, 3, e quais são os números

        partes = [df_osc[df_osc['experimentos'] == experimento] for experimento in experimentos_unicos]
        # Idealmente divide em 2 partes só
        #partes = []

        use_freq = False
        use_tau = False

        if ('f' in df_osc.columns) or ('omega' in df_osc.columns): use_freq, use_tau = True, False
        if 'Tau' in df_osc.columns: use_freq, use_tau = False, True

        if not use_freq and not use_tau:
            raise ValueError('Um erro ocorreu na hora de tentar separar os experimentos oscilatórios')

        threshold_count = 1

        if use_freq:
            if 'f' in df_osc.columns: freq = 'f'
            if 'omega' in df_osc.columns: freq = 'omega'
            for parte in partes:
                if parte[freq].value_counts().max() > threshold_count:
                    df_OT = parte.copy() # todo: precisa de copy?
                elif not parte[freq].value_counts().max() > threshold_count:
                    df_OF = parte.copy()
                else:
                    df_OT = None
                    df_OF = None

        if use_tau:
            for parte in partes:
                if parte['Tau'].value_counts().max() > threshold_count:
                    df_OF = parte.copy()
                elif not parte['Tau'].value_counts().max() > threshold_count:
                    df_OT = parte.copy()
                else:
                    df_OF = None
                    df_OT = None

    # if df_osc.size != 0:  # Checa se tem dado de oscilatório
    #     ## Oscilatório Tensão
    #     contagem_w_OT = df_osc['omega'].value_counts()  # Conta quantas vezes um valor de freq se repetiu
    #     if contagem_w_OT.size == 0:  # Matriz vazia
    #         w_mais_freq_OT = pd.Series([])
    #         df_OT = None  # Sem qualquer dado oscilatório
    #     elif contagem_w_OT.max() == 1:  # Não repete nenhum valor
    #         df_OT = None  # Sem dado de Osc Tens
    #         w_mais_freq_OT = 0  # Coloca um valor para comparar
    #     else:
    #         w_mais_freq_OT = contagem_w_OT.idxmax()  # Valor de freq que mais repete (1 Hz): indica Osc Tens
    #         indice_w_mais_freq = contagem_w_OT.max()
    #
    #         df_OT_m = df_osc['omega'] == w_mais_freq_OT  # Criar máscara para o Osc Tens
    #         df_OT = df_osc[df_OT_m]  # Aplicar a máscara.  #### Problema aqui!
    #         df_OT = df_OT[['Tau', "G'", "G''", 'T']]  # Separa só os valores de interesse
    #
    #         if df_OT.index[-1] - 1 != df_OT.index[
    #             -2]:  # É possível que haja uma coincidencia e repita um valor de Freq.
    #             # df_OT = df_OT.drop(index = df_OT.index[-1]) # Remove último ponto se ele não for contínuo com o anterior
    #             df_OT = df_OT.drop(df_OT.index[-1])
    #
    #         #df_OT = df_OT.add_prefix(nome)  # Coloca o nome para exportação
    #
    #     ## Frequencia
    #
    #     if contagem_w_OT.size != 0:  # Revisar aqui
    #         df_OF_m = df_osc['omega'] != w_mais_freq_OT  # complementar ao Osc Tens
    #     else:
    #         df_OF_m = []  # Matriz vazia
    #
    #     for i, item in enumerate(df_OF_m):
    #         try:
    #             if df_OF_m[i - 1] == True and df_OF_m[i + 1] == True and df_OF_m[i] == False:
    #                 df_OF_m[i] = True
    #         except KeyError:
    #             pass
    #         except IndexError:
    #             pass
    #
    #     df_OF = df_osc[df_OF_m]
    #     df_OF = df_OF[['omega', "G'", "G''", 'T']]
    #     #df_OF = df_OF.add_prefix(nome)
    #
    #     if df_OF.size == 0:
    #         df_OF = None
    #     elif (df_OF.index[0] + 1) != df_OF.index[1]:  # É possível que haja uma coincidencia e repita um valor de Freq.
    #         # df_OF = df_OF.drop(index = df_OF.index[-1]) # Remove primeiro ponto se ele não for contínuo com o próximo
    #         df_OF = df_OF.drop(df_OF.index[-1])
    # else:
    #     df_OT = None
    #     df_OF = None

    if df_CF is not None:
        df_CF.drop(labels='serie', axis=1, inplace=True)
    if df_OF is not None:
        df_OF = df_OF.drop(labels=['serie', 'experimentos'], axis=1)
    if df_OT is not None:
        df_OT = df_OT.drop(labels=['serie', 'experimentos'], axis=1)
        if 'Tau' not in df_OT.columns:
            df_OT = None

    return df_CF, df_OT, df_OF


def detect_header(lines):
    header_line = None
    for i, line in enumerate(lines):
        if len(line) < 3:
            header_line = i
            continue
        if header_line != None and header_line != 0:
            header_names = line
            break
    else:
        raise Exception('Não foi possível encontrar o cabeçalho! Existe uma linha em branco antes do mesmo?')

    return header_line, header_names


def detect_columns(header_names):
    columns = header_names.split(';')
    sequence = []
    # Assume que sempre tem um espaço depois dos nomes! Isso permite diferenciar G' de G''.
    # Senão, será necessário utilizar regexes, ou alguma lógica muito mais complexa.
    # Se uma coluna não for reconhecida, coloque-a aqui.
    valid_columns = ['GP ', 'Eta ', "G' ", "G'' ", 'omega ', 'Tau ', 'T ', 'f ', 'w ', 't ', 't_seg ', 'G* ', '|G*| ',
                     'Eta*']

    for i, column in enumerate(columns):
        if i == 0 and len(column) <= 1:
            sequence.append('serie')
        if i != 0 and len(column) <= 1:
            sequence.append('lixo')
        for test in valid_columns:
            if test in column:
                sequence.append(test.strip())
        # todo: detectar se há uma coluna não reconhecida
        #else:
        #    logging.debug(f'Coluna não reconhecida: {column}')
        #    print(f'Coluna não reconhecida: {column}')

    return sequence


def check_create_dirs():
    if not os.path.isdir('./CFs'):
        os.mkdir('./CFs')
    if not os.path.isdir('./OFs'):
        os.mkdir('./OFs')
    if not os.path.isdir('./OTs'):
        os.mkdir('./OTs')

def main(ext):

    if not ext:
        ext = 'txt'

    arquivos = glob.glob(f'*{ext}')
    print(f'Foram encontrados {len(arquivos)} arquivos')
    logging.info(f'{len(arquivos)} arquivos encontrados: {arquivos}')

    for arquivo in arquivos:
        print(f'\tSeparando {arquivo}')
        logging.info(f'Início da separação das linhas do arquivo {arquivo}')

        file = open(arquivo, 'r').read().split('\n')
        header_line, header_names = detect_header(file)
        names = detect_columns(header_names)

        try:
            pd_temp = pd.read_csv(arquivo,
                                  delimiter=';',
                                  header=header_line,  # Testar este número
                                  names=names,
                                  encoding='latin1',
                                  decimal=',')
        except Exception as e:
            print(f'Erro ao abrir o arquivo {arquivo}. \n Erro: {e}')

        temp_CF, temp_OT, temp_OF = extraction(pd_temp)

        check_create_dirs()

        # Isso é para garantir que não exista sobreposição de arquivos
        if type(temp_CF) != type(None):
            filename = fr'.\CFs\{arquivo}'
            counter = 0
            while os.path.isfile(filename):
                filename = filename[:-4] + str(counter) + filename[-4:]

            temp_CF.to_csv(filename, sep=';', encoding='utf8', index=False, decimal=',')

        if type(temp_OT) != type(None):
            filename = fr'.\OTs\{arquivo}'
            counter = 0
            while os.path.isfile(filename):
                filename = filename[:-4] + str(counter) + filename[-4:]

            temp_OT.to_csv(filename, sep=';', encoding='utf8', index=False, decimal=',')

        if type(temp_OF) != type(None):
            filename = rf'.\OFs\{arquivo}'
            counter = 0
            while os.path.isfile(filename):
                filename = filename[:-4] + str(counter) + filename[-4:]

            temp_OF.to_csv(filename, sep=';', encoding='utf8', index=False, decimal=',')


if __name__ == '__main__':
    main(sys.argv[1:])