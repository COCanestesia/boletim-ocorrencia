# Design — Boletim de Ocorrência COC

Data: 2026-09-22

## 1. Objetivo

Criar um aplicativo Streamlit separado do sistema principal da COC, executado localmente em computadores Windows, sem tela de login e sem senha. O aplicativo deve identificar automaticamente o usuário do Windows, salvar dados e anexos no próprio computador e permitir compartilhar boletins por PDF ou por pacote ZIP completo.

O aplicativo terá três áreas principais: **Novo Registro**, **Meus Registros** e **Recebidos**.

## 2. Princípios

- Sem dependência de Supabase para boletins.
- Sem necessidade de usuário/senha dentro do aplicativo.
- Identificação automática por usuário do Windows.
- Dados pessoais permanecem locais no computador.
- Boletins recebidos são somente leitura.
- Boletins exportados podem ser compartilhados com outros computadores.
- Pacotes importados devem ser validados e não podem ser duplicados.

## 3. Armazenamento local

Diretório base recomendado no Windows:

`%LOCALAPPDATA%\COC\BoletimOcorrencia`

Estrutura:

```text
COC/BoletimOcorrencia/
├── boletins.db
├── anexos/
│   ├── <uuid-boletim>/
│   └── ...
├── recebidos/
│   ├── <uuid-boletim>/
│   └── ...
├── exportados/
└── logs/
```

O SQLite será a fonte oficial local dos registros.

## 4. Identificação do usuário

O aplicativo obtém o usuário logado no Windows com `getpass.getuser()` e registra esse valor automaticamente em cada novo boletim.

Em **Meus Registros**, a consulta sempre filtra por `windows_user`.

Se duas pessoas usarem a mesma conta do Windows, o aplicativo não conseguirá distingui-las.

## 5. Modelo de dados

Tabela `boletins`:

- `id` — UUID interno
- `codigo` — código humano, ex.: `COC-2026-000001`
- `origem` — `local` ou `recebido`
- `windows_user` — usuário do Windows que criou/importou
- `autor_original` — autor informado no pacote recebido
- `data_ocorrencia`
- `hora_ocorrencia`
- `local`
- `setor`
- `tipo_ocorrencia`
- `titulo`
- `descricao`
- `consequencias`
- `pessoas_envolvidas`
- `acoes_imediatas`
- `acoes_preventivas`
- `status` — `rascunho` ou `finalizado`
- `criado_em`
- `atualizado_em`
- `finalizado_em`
- `hash_conteudo` — usado para integridade e deduplicação

Tabela `anexos`:

- `id`
- `boletim_id`
- `nome_original`
- `nome_armazenado`
- `caminho_relativo`
- `mime_type`
- `tamanho_bytes`
- `sha256`
- `criado_em`

Tabela `importacoes`:

- `id`
- `boletim_id`
- `arquivo_origem`
- `importado_em`
- `hash_pacote`

## 6. Fluxo — Novo Registro

Campos:

- Data da ocorrência
- Hora da ocorrência
- Local
- Setor
- Tipo da ocorrência
- Título curto
- Descrição detalhada
- Consequências / impacto
- Pessoas envolvidas
- Ações imediatas tomadas
- Ações preventivas / recomendações
- Anexos

Preenchimento automático:

- UUID
- Código do boletim
- Usuário do Windows
- Data/hora de criação

Ações:

- Salvar como rascunho
- Finalizar boletim
- Limpar formulário

## 7. Fluxo — Meus Registros

Exibe somente registros com:

`origem = local` e `windows_user = usuário atual do Windows`.

Recursos:

- Busca textual
- Filtro por período
- Filtro por tipo
- Filtro por status
- Abrir boletim
- Editar rascunho
- Finalizar
- Gerar PDF
- Gerar ZIP completo

Após finalizado, o boletim deixa de ser editável.

## 8. Fluxo — Recebidos

A área Recebidos permite importar um arquivo `.zip` gerado pelo próprio aplicativo.

O sistema deve:

1. validar a estrutura do pacote;
2. ler `boletim.json`;
3. conferir UUID e hash;
4. impedir duplicação;
5. copiar anexos para a pasta local;
6. cadastrar como `origem = recebido`;
7. abrir o registro somente em modo leitura.

Boletins recebidos não podem ser alterados.

## 9. Exportação PDF

O PDF deve trazer:

- identidade visual COC;
- código do boletim;
- data e hora da ocorrência;
- local e setor;
- tipo;
- título;
- descrição;
- consequências;
- pessoas envolvidas;
- ações imediatas;
- ações preventivas;
- autor original;
- data de criação;
- indicação de status;
- lista de anexos.

O PDF será apropriado para impressão e envio por WhatsApp ou e-mail.

## 10. Exportação ZIP

Estrutura:

```text
COC-2026-000001.zip
├── boletim.pdf
├── boletim.json
└── anexos/
    ├── foto.jpg
    ├── documento.pdf
    └── ...
```

`boletim.json` contém os dados estruturados necessários para reimportação.

O pacote também inclui hashes SHA-256 para validar integridade.

## 11. Interface

Layout Streamlit com menu lateral simples:

- 📝 Novo Registro
- 📚 Meus Registros
- 📥 Recebidos

Visual inspirado no mockup aprovado: fundo claro, cartões brancos, azul institucional, campos grandes e leitura fácil.

## 12. Segurança e integridade

- Sem execução de arquivos anexados.
- Nome de arquivo sanitizado antes de salvar.
- Limite configurável de tamanho por anexo.
- Extensões aceitas inicialmente: PDF, JPG, JPEG, PNG, DOCX, XLSX.
- Importação só aceita ZIP compatível com o formato do sistema.
- Hash SHA-256 em anexos e pacote.
- Boletins recebidos são imutáveis.
- Boletins finalizados são imutáveis.

## 13. Projeto público

O código poderá ser publicado em repositório separado, por exemplo:

`COCanestesia/boletim-ocorrencia-coc`

O repositório público não conterá nenhum banco real, anexos, dados pessoais ou ocorrências.

`.gitignore` deve excluir:

- `*.db`
- `*.sqlite*`
- diretórios de dados locais
- anexos
- exportações
- logs locais

## 14. Distribuição Windows

Primeira versão: execução local por script de inicialização (`.bat`) que abre o Streamlit no navegador.

Estrutura futura opcional: empacotar como instalador do Windows.

## 15. Testes mínimos

- criar boletim;
- editar rascunho;
- finalizar boletim;
- impedir edição após finalização;
- listar somente registros do usuário atual;
- anexar arquivo;
- gerar PDF;
- gerar ZIP;
- importar ZIP válido;
- impedir importação duplicada;
- rejeitar ZIP inválido;
- garantir leitura somente para recebidos;
- recriar banco automaticamente na primeira execução.

## 16. Critérios de aceite

O módulo estará pronto quando:

1. rodar localmente em Windows sem login do aplicativo;
2. identificar automaticamente o usuário do Windows;
3. salvar SQLite e anexos localmente;
4. permitir criar, editar rascunhos e finalizar boletins;
5. mostrar somente os próprios registros em Meus Registros;
6. gerar PDF;
7. gerar ZIP com PDF + JSON + anexos;
8. importar ZIP de outro computador;
9. mostrar importados em Recebidos, somente leitura;
10. funcionar sem Supabase e sem conexão com internet.
