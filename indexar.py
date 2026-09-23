import ollama
import psycopg2
import glob
import os
import re
import pymupdf4llm
from psycopg2.extras import execute_batch
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter


EMBEDDING_MODEL = "nomic-embed-text-v2-moe"


def remover_marca_everyspec(texto):
    marca = r"(?im)^\s*.*Downloaded\s+from.*everyspec\.com.*(?:\r?\n|$)"
    texto = re.sub(marca, "", texto)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", texto)

# 1. Conexão com o PostgreSQL (pgvector)
conn = psycopg2.connect(
    dbname="rag_database",
    user="admin",
    password="adminpassword",
    host="localhost",
    port="5433" # Confirme se está usando 5433
)
cursor = conn.cursor()

cursor.execute("TRUNCATE TABLE documentos_especificacoes RESTART IDENTITY;")
conn.commit()

# 2. Carregar os PDFs do EverySpec
pasta_documentos = "documentos_teste"
arquivos_pdf = glob.glob(os.path.join(pasta_documentos, "*.pdf"))

if not arquivos_pdf:
    print(f"Nenhum PDF encontrado na pasta '{pasta_documentos}'.")
else:
    total_documentos_salvos = 0

    for pdf_path in arquivos_pdf:
        print(f"\n--- Processando (Markdown): {pdf_path} ---")
        
        # Extrai o PDF já em formato Markdown, mantendo tabelas, separado por páginas
        md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
        
        # Converte o resultado para o formato Document do LangChain
        documents = []
        for p in md_pages:
            texto_limpo = remover_marca_everyspec(p['text'])
            documents.append(Document(
                page_content=texto_limpo,
                metadata={'page_number': p['metadata'].get('page_number', 1)}
            ))

        # 3. Aplicar o chunking específico para Markdown
        # Ele prioriza não cortar no meio de tabelas ou entre um título (#) e seu parágrafo
        text_splitter = MarkdownTextSplitter(
            chunk_size=700,
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Total de {len(chunks)} chunks Markdown para processar.")

        # 4. Vetorizar e preparar os dados para inserção
        dados_para_inserir = []
        nome_arquivo_curto = os.path.basename(pdf_path)

        for idx, chunk in enumerate(chunks):
            texto = chunk.page_content.strip()
            texto = texto.replace('\x00', '')
            
            if not texto:
                continue

            pagina = chunk.metadata.get("page_number", 1)
            
# INJEÇÃO DE METADADOS: Garante que o LLM ache o arquivo pelo nome
            texto_enriquecido = f"Documento: {nome_arquivo_curto}.\n{texto}"
            
            # 1. ADICIONADO: Criamos uma string específica para o embedding com o prefixo
            texto_para_vetorizar = f"search_document: {texto_enriquecido}"
            
            # 2. ALTERADO: Geramos o vetor usando a string COM o prefixo
            resposta = ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt=texto_para_vetorizar
            )
            vetor = resposta["embedding"]

            # 3. MANTIDO: Salvamos no banco o 'texto_enriquecido' original, SEM o prefixo, para não sujar a leitura
            dados_para_inserir.append((
                nome_arquivo_curto,
                pagina,
                texto_enriquecido, 
                vetor
            ))

            if (idx + 1) % 50 == 0 or (idx + 1) == len(chunks):
                print(f"  Vetorizados {idx + 1}/{len(chunks)} blocos...")

        # 5. Salvar em lote no PostgreSQL
        if dados_para_inserir:
            query_sql = """
                INSERT INTO documentos_especificacoes (nome_documento, pagina, conteudo, embedding)
                VALUES (%s, %s, %s, %s::vector);
            """
            print(f"  Salvando {len(dados_para_inserir)} blocos no banco...")
            execute_batch(cursor, query_sql, dados_para_inserir)
            conn.commit()
            total_documentos_salvos += 1
            print(f"  [{pdf_path}] concluído.")
        
    cursor.close()
    conn.close()
    print(f"\n✅ Processamento finalizado! {total_documentos_salvos} PDF(s) indexado(s) em Markdown com sucesso.")