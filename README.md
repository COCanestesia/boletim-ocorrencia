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

## Instalação rápida

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
