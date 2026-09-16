# 📄 POC: Sistema RAG Local para Documentação Técnica

## 🧠 Visão Geral
Esta Prova de Conceito (POC) implementa uma arquitetura de Retrieval-Augmented Generation (RAG) 100% local e open-source para realizar buscas precisas em manuais técnicos dispersos. 

O pipeline consiste em:
1. **Extração Inteligente:** Conversão de PDFs complexos para Markdown (preservando tabelas e hierarquias) via `pymupdf4llm`.
2. **Chunking e Injeção de Metadados:** Divisão do texto respeitando a estrutura do Markdown e injeção do nome do arquivo no bloco de texto para permitir buscas exatas.
3. **Vetorização:** Geração de *embeddings* matemáticos salvos em um banco PostgreSQL com a extensão `pgvector`.
4. **Recuperação e Geração:** Busca semântica que alimenta um LLM local para responder perguntas citando as fontes exatas.

---

## 🗄️ Alterações e Adições no Banco de Dados
Para suportar o motor de IA sem quebrar a estrutura existente do sistema, a arquitetura do banco foi expandida:

* **O que foi mantido:** Os modelos originais `Documento` e `Etiqueta` mantêm sua estrutura original e a relação de Muitos-para-Muitos (N:N) através da tabela intermediária `EtiquetaDocumento`.
* **O que foi adicionado (Nova Tabela):** Foi criada uma nova entidade chamada `DocumentoChunk` (ou `documentos_especificacoes` no banco cru). 
* **Relacionamento:** Esta nova tabela armazena os blocos de texto divididos e possui uma Chave Estrangeira (*Foreign Key*) apontando para o `id_documento` da tabela de documentos.
* **Campos da Nova Tabela:**
  * `id_documento` (FK para vincular o texto ao PDF original).
  * `pagina` (Inteiro, para citar a origem da resposta).
  * `conteudo` (Texto longo em formato Markdown).
  * `embedding` (Campo do tipo `VECTOR(768)` que armazena a representação matemática do texto gerada pela IA).

*(Nota: O ID da Etiqueta propositalmente não vai na tabela de chunks para evitar duplicação de dados. A filtragem por setor/etiqueta ocorrerá dinamicamente via JOINs durante a pesquisa).*

---

## 🤖 Modelos de Inteligência Artificial (Ollama)
Todo o processamento de linguagem natural ocorre localmente através do **Ollama**. É necessário baixar dois modelos distintos para o pipeline funcionar:

1. **Modelo de Embedding (`nomic-embed-text`):** Responsável por ler os blocos de texto e transformá-los em vetores matemáticos de 768 dimensões.
2. **Modelo de Geração (`qwen2.5:7b`):** Responsável por ler a pergunta do usuário, analisar os blocos recuperados do banco e redigir a resposta final formatada.

**Comandos para baixar os modelos no terminal:**
`ollama pull nomic-embed-text`
`ollama pull qwen2.5:7b`

*(Certifique-se de que o aplicativo do Ollama esteja rodando em background no seu computador antes de executar os comandos).*

---

## 🚀 Como Rodar o Projeto

**1. Subir o Banco de Dados (Docker)**
Inicie o contêiner do PostgreSQL com a extensão `pgvector` configurada (o arquivo `init.sql` criará as tabelas automaticamente na primeira execução):
`docker-compose up -d`

**2. Instalar Dependências Python**
Crie um ambiente virtual (recomendado) e instale as bibliotecas necessárias:
`pip install psycopg2-binary langchain-core langchain-text-splitters pymupdf4llm ollama`

**3. Alimentar o Banco de Dados (Indexação)**
Coloque seus PDFs na pasta `documentos_teste` e execute o script de ingestão. Este processo fará a extração em Markdown, o chunking e a vetorização:
`python indexar.py`

**4. Auditar a Extração (Opcional)**
Para comprovar visualmente que o texto foi corretamente fatiado e convertido em vetores de 768 dimensões no banco de dados:
`python verificar_banco.py`

**5. Fazer Perguntas (Chat RAG)**
Execute o script de interação para simular o assistente técnico. Altere a variável `pergunta_teste` no final do arquivo Python para fazer novas buscas:
`python chat_rag.py`
