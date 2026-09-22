# COC · Boletim de Ocorrência

Aplicativo local em Streamlit para registrar, guardar e compartilhar boletins de ocorrência.

## Características

- roda no Windows;
- não exige usuário ou senha do aplicativo;
- identifica automaticamente o usuário do Windows;
- salva dados em SQLite no próprio computador;
- salva anexos localmente;
- permite editar rascunhos antes da finalização;
- gera PDF;
- gera ZIP com PDF + JSON + anexos;
- importa boletins recebidos em modo somente leitura;
- não depende de Supabase ou internet depois da instalação.

## Instalação nas máquinas da enfermagem

Para uso diário, use o instalador disponível em **Releases** no GitHub. A enfermeira não precisa instalar Python, GitHub ou dependências manualmente.

1. Baixe o arquivo `Instalar_Boletim_COC_<versão>.exe` da versão mais recente.
2. Dê dois cliques no instalador e avance até concluir.
3. O instalador cria o atalho **Boletim de Ocorrência COC** na área de trabalho e no menu Iniciar.
4. Depois disso, para o uso diário, basta abrir o atalho.

O programa é instalado somente para o usuário atual do Windows, em `%LOCALAPPDATA%\Programs\COC\BoletimOcorrencia`, evitando a necessidade de senha de administrador na instalação normal.

Os boletins, anexos e o banco continuam fora da pasta do programa, em `%LOCALAPPDATA%\COC\BoletimOcorrencia`. Por isso, instalar uma versão nova por cima da anterior não apaga os registros.

> **Aviso do Windows:** enquanto o instalador não tiver uma assinatura digital de código, o Windows pode mostrar um aviso de editor desconhecido/SmartScreen na primeira instalação. Isso não afeta o uso diário depois de instalado. Para remover esse aviso por completo, é necessário adquirir e configurar um certificado de assinatura digital.

## Instalação manual para desenvolvimento

1. Instale Python 3.12 ou superior em https://www.python.org/downloads/windows/ e habilite o Python Launcher (`py`).
2. Baixe ou clone este repositório.
3. Execute `run_coc.bat`.
4. Na primeira execução, as dependências serão instaladas; por isso é necessária conexão com a internet apenas nessa etapa.
5. O aplicativo abrirá no navegador local.

## Onde os dados ficam

Por padrão:

`%LOCALAPPDATA%\COC\BoletimOcorrencia`

A pasta contém o banco `boletins.db`, os anexos, os recebidos e as exportações. O repositório não contém dados reais da COC.

## Identificação de cada pessoa

O aplicativo usa automaticamente o usuário logado no Windows. **Meus Registros** mostra somente os boletins criados por esse usuário do Windows.

Se duas pessoas utilizarem a mesma conta do Windows, o aplicativo não consegue distingui-las.

## Compartilhamento

Finalize um boletim e use:

- **Baixar PDF** para impressão, WhatsApp ou e-mail;
- **Baixar ZIP completo** para enviar a outro usuário deste aplicativo.

O destinatário abre **Recebidos**, importa o ZIP e recebe uma cópia somente leitura. O mesmo pacote não pode ser importado duas vezes.

## Privacidade

Nenhum boletim é enviado automaticamente para a internet. A publicação deste código no GitHub não publica bancos, anexos nem registros locais.

## Desenvolvimento

Instale as dependências e rode os testes:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Inicie o app manualmente com:

```bash
python -m streamlit run app.py
```
