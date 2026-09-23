import ollama
import psycopg2

DB_CONFIG = {
    "dbname": "rag_database",
    "user": "admin",
    "password": "adminpassword",
    "host": "localhost",
    "port": "5433",
}

EMBEDDING_MODEL = "nomic-embed-text-v2-moe"
NUM_RESULTADOS = 5

def buscar_trechos(pergunta, cursor, limite=NUM_RESULTADOS):
    # 1. ADICIONADO: Inserimos o prefixo obrigatório para perguntas
    pergunta_formatada = f"search_query: {pergunta}"

    # 2. ALTERADO: Usamos a pergunta_formatada em vez da pergunta original
    resposta = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=pergunta_formatada, 
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
    perguntas_teste = [
        # --- TESTE CROSS-LINGUAL (Perguntas em PT-BR para base em EN) ---
        "Qual é a altitude padrão para entrada no circuito de tráfego VFR para aeronaves pesadas?",
        "É permitido usar epóxi ou massa automotiva para consertar amassados nas pás das hélices de metal?",
        "O que significa a seta para cima (Up Arrow) em uma solicitação de trabalho no sistema de manutenção?",
        "Quem tem a responsabilidade de atribuir os números aos documentos de controle no nível do Programa?",
        
        # --- TESTE LINHA DE BASE (Perguntas em EN para base em EN) ---
        "What is the standard altitude for entering the VFR traffic pattern for heavy aircraft?",
        "Is it permitted to use epoxy or auto filler to repair dents on metal propeller blades?",
        "What does the up arrow mean on a work request in the maintenance system?",
        "Who is responsible for assigning control document numbers at the Program level?"
    ]

    print(f"Iniciando calibração de limites de distância com {EMBEDDING_MODEL}...\n")

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                for pergunta in perguntas_teste:
                    print("-" * 80)
                    print(f"PERGUNTA: '{pergunta}'")
                    
                    resultados = buscar_trechos(pergunta, cursor)
                    
                    if not resultados:
                        print("  Nenhum documento foi encontrado. Rode a indexação primeiro.\n")
                        continue

                    print("  TOP RESULTADOS:")
                    for indice, (_, nome_documento, pagina, conteudo, distancia) in enumerate(resultados, 1):
                        # Preview do texto para validar se é o trecho exato ou alucinação
                        conteudo_preview = conteudo.replace('\n', ' ').strip()[:100]
                        
                        print(
                            f"  [{indice}] Distância: {distancia:.4f} | Arquivo: {nome_documento} (Pág {pagina})\n"
                            f"      Texto: {conteudo_preview}...\n"
                        )
                    print()
                    
    except KeyboardInterrupt:
        print("\nTeste encerrado.")
    except Exception as erro:
        print(f"\nErro ao executar o teste: {erro}")

if __name__ == "__main__":
    main()