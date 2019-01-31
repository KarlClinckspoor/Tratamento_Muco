---
title: 'Instruções para o uso do conjunto de script de tratamento'
author: 
- Karl Jan Clinckspoor
email:
- karl970@gmail.com
- karlclinckspoor@protonmail.com
---

# Instruções para o tratamento de dados de muco

Nesse guia serão fornecidas algumas instruções para o tratamento de um conjunto de dados de reologia de muco. O projeto anterior não seguiu essa sequência, nem esses métodos, rigorosamente, mas agora, sabendo bem do processo, é possível estabelecer uma metodologia. 

## Pré-requisitos

1. Python
2. Dados reológicos que foram exportados com as seguintes colunas, na seguinte ordem, que devem estar com esses nomes:
    * `Série` (1|2: primeiro experimento, segundo ponto)
    * `GP` (taxa de cisalhamento)
    * `Eta` (viscosidade)
    * `omega` (frequência em rad/s)
    * `f` (frequência em Hz)
    * `G1` (G')
    * `G2` (G'')
    * `T` (temperatura)
    * `Tau` (Tensão de cisalhamento)
    
    Caso os dados sejam exportados com columas em outra ordem, será necessário ou reexportá-los, ou alterar o script e colocar as colunas presentes.
    
3. Os nomes dos arquivos devem seguir a seguinte sequência, tudo em letras minúsculas, e sem caracteres com acentos e cedilhas:
    
        nome sobrenome hora_coleta(separado por h) hora_medida(separado por ponto) data_medida(separado por traço) extensão
        
    Por exemplo:
    
        caio lins 11h50 08.29.41 2018-01-24.txt
        caio lins 09h50 08.29.41 2018-01-24.txt
        
    É importante que as horas sejam precedidas de zero, caso seja menor que 10.
    
    Quando o arquivo for criado no reômetro, deve-se informar o nome, sobrenome e data de coleta. O resto deve vir automaticamente. Essa nomenclatura facilita bastante a análise posterior dos dados, tornando possível agrupar os pacientes por nome e sobrenome facilmente.
    
## Instalação do Python e dos pacotes necessários

Existem duas maneiras de se instalar o Python e de utilizar os pacotes. A primeira, mais simples, é baixando o Anaconda, instalador que contém o Python e uma enorme quantidade de outros pacotes. O site deles é https://www.anaconda.com/distribution/. Clique na versão mais recente do Python. Durante a instalação, é importante pedir para colocar o Python na variável PATH de ambiente. Se você não fizer isso, poderá ter alguns problemas posteriormente.

A outra maneira é instalando diretamente o Python, e em seguida instalando os pacotes necessários para rodar esta coletânea de scripts. Para isso, vá no site https://www.python.org/downloads/, baixe a versão mais recente, instale e, novamente, não se esqueça de colocar o python na variável PATH de ambiente. Para se certificar disso, faça o seguinte:

1. Abra um terminal. Isso pode ser feito apertando a tecla do windows + R, e digitando `powershell`, e depois apertando Enter. Isso irá abrir o powershell, um console no Windows onde alguns comandos de texto são rodados. Uma alternativa é o prompt de comando, que é iniciado digitando `cmd`.
2. Escreva `python` e digite enter. Caso apareça um erro como:

        python : O termo 'python' não é reconhecido como nome de cmdlet, função, arquivo de script ou programa operável. Verifique a grafia do nome ou, se um caminho tiver sido incluído, veja se o caminho está correto e tente novamente.
        No linha:1 caractere:1
        + python
        + ~~~
            + CategoryInfo          : ObjectNotFound: (asd:String) [], CommandNotFoundException
            + FullyQualifiedErrorId : CommandNotFoundException
            
    ou
    
        'python' não é reconhecido como um comando interno
        ou externo, um programa operável ou um arquivo em lotes.
        
    significa que, apesar do Python ter sido instalado, o Windows não consegue encontrá-lo. Para configurar isso no Windows, siga as instruções neste site: https://www.computerhope.com/issues/ch000549.htm
    
    Caso apareça algo como 
    
        Python 3.6.1 |Anaconda custom (64-bit)| (default, May 11 2017, 13:25:24) [MSC v.1900 64 bit (AMD64)] on win32
        Type "help", "copyright", "credits" or "license" for more information.
        
    significa que o Python foi instalado corretamente. Se seu número de versão for maior do que o que está aqui (3.6.1), não há problemas. Digite `quit()`, aperte enter para sair do Python.
       
3. Agora, precisamos instalar as dependências dos scripts utilizados. Para isso, abra um terminal na pasta onde estão os scripts e, mais importante, o arquivo `requirements.txt`. Esse arquivo contém os pacotes utilizados e suas versões. Isso é feito da seguinte forma:
    * Apertando com o botão direito numa seção vazia do windows explorer enquanto aperta o botão Shift do teclado. Depois, clicar em `Abrir janela do Powershell aqui`, ou `Abrir prompt de comando aqui`.
    * Clicando na barra de endereço do windows explorer e digitando `powershell` ou `cmd`.

Feito isso, digite: `pip install -r requirements.txt`. Isso instalará todas as dependências de uma vez só. Se ele reclamar que o pip está desatualizado, rode o comando `python -m pip install --upgrade pip`. Se outro erro ocorrer, entre em contato comigo.

Pronto, agora os scripts poderão ser utilizados facilmente. Para fazer isso, digite `python <nome do script.py>`. A tecla Tab geralmente autocompleta o nome de arquivos, então vc pode digitar somente as primeiras letras do nome e apertar tab, então `python Separ<TAB>` irá completar para `python Separação_dados.py`. Se vc der duplo-clique num arquivo .py, ou clicar com o botão direito e depois em `Abrir com`, é possível escolher o executável do Python para rodar os arquivos `.py` sem ter que abrir um terminal.

## Separação dos experimentos
    
Cada arquivo de cada experimento geralmente consiste das seguintes informações:

    Caminho do arquivo após ser exportado
    Informações da companhia
    Informações do Software
    Nome da substância    
    <linha em branco>    
    Cabeçalho
    Início dos dados
    ...
    
Exemplo:

    C:\Users\Karl\Desktop\_Medidas\2018 04 11\Felipe Martins 9h10  09.43.03 2018-04-11.rwd
    Company / Operator: UNICAMP / IQ
    Date / Time / Version: 11.04.2018 / 09:33:02 / HAAKE RheoWin 4.30.0021
    Substance / Sample no: Felipe Martins 9h10 / 
    
    ;t / s;t_seg / s;f / Hz;omega / rad/s;G' / Pa;G'' / Pa;|G*| / Pa;|Eta*| / Pas;
    1|1;65,42;4,375;1,000;6,283;4,424;1,141;4,568;0,7271;
    1|2;70,81;9,767;1,000;6,283;4,310;1,115;4,452;0,7086;
    1|3;76,20;15,15;1,000;6,283;4,233;1,114;4,377;0,6966;
    1|4;81,62;20,58;1,000;6,283;4,135;1,125;4,285;0,6821;
    1|5;87,08;26,03;1,000;6,283;4,018;1,128;4,174;0,6643;
    1|6;92,48;31,44;1,000;6,283;3,890;1,151;4,056;0,6456;
    1|7;97,96;36,92;1,000;6,283;3,733;1,160;3,909;0,6222;
    1|8;103,4;42,34;1,000;6,283;3,563;1,185;3,755;0,5976;
    1|9;108,8;47,76;1,000;6,283;3,389;1,193;3,592;0,5717;
    1|10;114,3;53,23;1,000;6,283;3,188;1,182;3,400;0,5411;
    2|1;156,1;40,31;0,1000;0,6283;2,358;0,8780;2,516;4,005;
    2|2;188,8;73,06;0,1468;0,9222;2,595;0,8514;2,731;2,962;
    2|3;211,3;95,55;0,2154;1,354;2,768;0,8586;2,899;2,141;
    2|4;226,7;111,0;0,3162;1,987;2,966;0,8809;3,094;1,557;
    2|5;237,5;121,7;0,4642;2,916;3,164;0,8991;3,289;1,128;
    2|6;244,6;128,8;0,6813;4,281;3,397;0,9574;3,529;0,8245;
    2|7;249,7;134,0;1,000;6,283;3,578;1,070;3,735;0,5944;
    2|8;253,8;138,0;1,468;9,222;4,231;1,315;4,430;0,4804;
    2|9;256,7;141,0;2,154;13,54;5,947;0,6313;5,980;0,4418;
    2|10;258,9;143,1;3,162;19,87;1,965;1,188;2,296;0,1156;
    2|11;260,6;144,8;4,642;29,16;13,01;0,5796;13,02;0,4464;
    3|1;294,7;33,16; ; ; ; ; ; ;
    3|2;327,8;66,32; ; ; ; ; ; ;
    3|3;361,0;99,46; ; ; ; ; ; ;
    3|4;394,1;132,6; ; ; ; ; ; ;
    3|5;427,3;165,7; ; ; ; ; ; ;
    3|6;460,4;198,9; ; ; ; ; ; ;
    3|7;493,6;232,1; ; ; ; ; ; ;
    3|8;526,8;265,2; ; ; ; ; ; ;
    3|9;559,9;298,4; ; ; ; ; ; ;
    3|10;593,1;331,5; ; ; ; ; ; ;
    
Nesse exemplo, vemos problemas, que tiveram que ser resolvidos antes do tratamento. Primeiro, o nome do arquivo não seque o estabelecido, com tudo em letras minúsculas. Segundo, a hora deveria estar escrita `09h10`. Esse tipo de problema foi consertado, antes do tratamento, por scripts para renomeá-los, mas isso é sempre mais trabalhoso do que renomear antes. Terceiro, as colunas não contém todas as informações. Como estes dados foram utilizados somente para fazer o tratamento dos resultados oscilatórios, não foi problemático.

Além disso, vemos outra característica desse dado. Há três séries de valores, `1|`, `2|`, `3|`. Para saber qual parte corresponde a qual experimento, sem saber a sequência utilizada, pode-se observar o seguinte.

1. A frequência de perturbação da série 1 é, sempre, igual a 1 Hz. Isso indica que esse é o experimento de reologia variando-se a tensão a frequência constante.
2. A frequência da segunda série é crescente, indicando que é o experimento de varredura de frequência. Caso a coluna de Tau estivesse no dado, seria possível ver esse valor praticamente constante.
3. O terceiro experimento é um ensaio sem dados oscilatórios, logo, deve ser uma curva de fluxo.

O script de separação de dados se baseia nessas condições para realizar a separação.

Para fazer a separação, coloque todos os arquivos que serão extraídos em uma pasta junto com os scripts. Depois, rode o script `Separação_dados.txt`. Os dados separados serão colocados em três pastas, `CFs` para as **C**urvas de **F**luxo, `OTs` para os **O**scilatórios de **T**ensão e `OFs` para os **O**scilatórios de **F**requência. Caso um arquivo não tenha os dados necessários para construir um gráfico, um arquivo não será gerado. Portanto, no exemplo acima, apesar de haver informações sobre 3 experimentos, não há informações da tensão de cisalhamento (Tau), então não há dados do experimento oscilatório.

É possível fazer plots dos dados extraídos para ver se há algum problema na exportação, ou para ver a qualidade dos dados, rapidamente. Para isso, utilize os scripts de `plot_rapido`.

O script também faz um log das informações, que é mais útil para mim, então você pode deletar o arquivo `extração.log` tranquilamente.

## Tratamento oscilatório

Na pasta OFs há um arquivo chamado `Tratamento_oscilatório.py`. Esse script é essencialmente idêntico ao utilizado para o tratamento dos experimentos de reologia oscilatória do trabalho original do muco. Ele exige que os arquivos estejam nomeados da maneira mostrada anteriormente. Separando nos espaços, deve haver, exatamente, 5 items! (nome, sobrenome, hora da coleta, hora da medida, data da medida.extensão)

Ao rodar o script, ele irá mostrar quais são os arquivos que estão sendo tratados, irá gerar os gráficos de cada arquivo com o tratamento, na pasta `ajustes_exp` e irá gerar vários arquivos de texto:

* `erros.dat`: Caso ocorram erros, eles serão marcados aqui.
* `oscilatorio.log`: Mostra o log de atividades durante as análises
* `paramsg1.dat`: Contém os parâmetros de ajuste para G' de tudo. É fácil de abrir no Excel.
* `paramsg2.dat`: Contém os parâmetros de ajuste para G'' de tudo. É fácil de abrir no Excel.
* `resultados_ajustes.dat`: Uma junção dos dois arquivos anteriores. Fácil de abrir no Excel.

Esse script extrai as informações a 1 Hz. Caso você deseje mudar esse valor, terá que abrir o arquivo do script num editor de texto, e logo no começo, alterar `FREQ` para a frequência que você deseja editar. O valor deve ser EXATO!

## Tratamento de curva de fluxo

Na pasta CFs tem o arquivo chamado `RheoFCClass.py`, que contém o script principal para tratamento. Os arquivos `Settings.py` e `settings.dat` contém funções auxiliares para rodar esse script. Do jeito que os arquivos estão configurados agora, os ajustes devem prosseguir sem muitos problemas. Esse script é um pouco frágil, porém, então entre em contato comigo se ocorrer algum problema durante o tratamento.

Como nos outros casos, rodar esse script irá gerar um arquivo com os resultados do ajuste linear `results.csv` e um com o ajuste de Carreau, `Carreau.csv`. Além disso, irá gerar imagens com os ajustes e os valores dos parâmetros, para checar se tudo ocorreu bem.

Caso você deseje alterar as configurações do ajuste, sinta-se a vontade de fazer isso tanto pelo Script principal como editando diretamente o arquivo `settings.dat`

## Conclusão

Feito isso, os dados de reologia de muco foram tratados. Espero que você tenha bastante sucesso posteriormente no tratamento estatístico desses dados.

Karl