import ollama
import psycopg2

DB_CONFIG = {
    "dbname": "rag_database",
    "user": "admin",
    "password": "adminpassword",
    "host": "localhost",
    "port": "5433",
}

EMBEDDING_MODEL = "nomic-embed-text"
NUM_RESULTADOS = 5


def buscar_trechos(pergunta, cursor, limite=NUM_RESULTADOS):
    resposta = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=pergunta,
    )
    vetor_pergunta = resposta["embedding"]
    vetor_pgvector = "[" + ",".join(str(valor) for valor in vetor_pergunta) + "]"

    cursor.execute(
        """
        SELECT id, nome_documento, pagina, conteudo,
               embedding <=> %s::vector AS distancia
        FROM documentos_especificacoes
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (vetor_pgvector, vetor_pgvector, limite),
    )
    return cursor.fetchall()


def main():
    print("Busca de documentos iniciada. Digite 'sair' para encerrar.\n")

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                while True:
                    pergunta = input("Pergunta: ").strip()
                    if pergunta.lower() in {"sair", "exit", "quit"}:
                        break
                    if not pergunta:
                        continue

                    resultados = buscar_trechos(pergunta, cursor)
                    if not resultados:
                        print("\nNenhum documento foi encontrado. Rode a indexação primeiro.\n")
                        continue

                    print("\nDocumentos e páginas mais prováveis:")
                    for indice, (_, nome_documento, pagina, _, distancia) in enumerate(resultados, 1):
                        print(
                            f"  [{indice}] {nome_documento} - página {pagina} "
                            f"(distância: {distancia:.4f})"
                        )
                    print()
    except KeyboardInterrupt:
        print("\nChat encerrado.")
    except Exception as erro:
        print(f"\nErro ao executar o chat: {erro}")


if __name__ == "__main__":
    main()
