CREATE EXTENSION IF NOT EXISTS vector;

-- Cria a tabela onde os chunks dos PDFs serão salvos
CREATE TABLE documentos_especificacoes (
    id SERIAL PRIMARY KEY,
    nome_documento VARCHAR(255),
    pagina INTEGER,
    conteudo TEXT,
    embedding VECTOR(768) 
);
