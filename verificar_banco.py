import psycopg2
import json

def verificar_dados_poc():
    try:
        # Conexão com o banco (mesmas credenciais do seu docker-compose)
        conn = psycopg2.connect(
            dbname="rag_database",
            user="admin",
            password="adminpassword",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        print("\n" + "="*60)
        print("🔍 RELATÓRIO DA POC: VERIFICAÇÃO DO BANCO VETORIAL")
        print("="*60 + "\n")

        # 1. Conta o total de chunks salvos
        cursor.execute("SELECT COUNT(*) FROM documentos_especificacoes;")
        total_chunks = cursor.fetchone()[0]
        print(f"📊 TOTAL DE CHUNKS NO BANCO: {total_chunks} blocos de texto.\n")

        if total_chunks == 0:
            print("⚠️ O banco está vazio. Rode o script de indexação primeiro.")
            return

        # 2. Busca uma amostra para mostrar a separação e os vetores
        query = """
            SELECT id, nome_documento, pagina, conteudo, embedding::text
            FROM documentos_especificacoes
            LIMIT 3;
        """
        cursor.execute(query)
        amostras = cursor.fetchall()

        print("📂 AMOSTRA DE DADOS (3 primeiros blocos):")
        for linha in amostras:
            id_chunk, nome_doc, pagina, conteudo, vetor_str = linha
            
            # Pega os primeiros 100 caracteres do conteúdo para não poluir a tela
            trecho_texto = conteudo[:100].replace('\n', ' ') + "..."
            
            # O pgvector retorna uma string '[0.012, -0.231, ...]'. 
            # Convertendo para lista podemos contar o tamanho real do vetor.
            vetor_lista = json.loads(vetor_str)
            dimensao_vetor = len(vetor_lista)
            
            # Pega só os 3 primeiros números do vetor para demonstrar visualmente
            vetor_amostra = str(vetor_lista[:3]).replace(']', ', ...]')

            print("-" * 60)
            print(f"🆔 ID do Chunk : {id_chunk}")
            print(f"📄 Documento   : {nome_doc} (Página {pagina})")
            print(f"📝 Texto       : {trecho_texto}")
            print(f"🔢 Embedding   : {dimensao_vetor} dimensões matemáticas geradas {vetor_amostra}")

        print("-" * 60)
        print("\n✅ Verificação concluída! Banco validado e pronto para a Busca Semântica.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Erro ao conectar ou consultar o banco: {e}")

if __name__ == "__main__":
    verificar_dados_poc()