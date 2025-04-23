import re
import sqlite3
import pandas as pd 

def banco_de_dados(script):
    match = re.search(r'##([a-zA-Z0-9_-]+\.db)##', script)

    if match:
        nome_arquivo = match.group(1)
        script = re.sub(r'##([a-zA-Z0-9_-]+\.db)##', '', script)
        
        conn = sqlite3.connect(f'dbs/{nome_arquivo}')
        cursor = conn.cursor()
    
        script = re.sub(r"\s+", " ", script)
        list_comandos = re.findall(r"[^;]+;", script.replace("\n", "").strip())
        
        modificacao_tabela = set(["CREATE", "ALTER", "DROP"])
        modificacao_dados = set(["INSERT", "UPDATE", "DELETE"])
        selecao_dados = ["SELECT"]
        transacao = ["COMMIT", "ROLLBACK"]
        
        for sql in list_comandos:
            for modificacao in modificacao_tabela:
                indice_inicio = sql.upper().find(modificacao)
                if indice_inicio != -1:
                    #print(sql)
                    cursor.execute(sql)

            for modificacao in modificacao_dados:
                indice_inicio = sql.upper().find(modificacao)
                if indice_inicio != -1:
                    #print(sql)
                    cursor.execute(sql)
            
            if transacao[0] == "COMMIT" and sql.upper().find(transacao[0]) != -1:
                conn.commit()
            elif transacao[0] == "ROLLBACK" and sql.upper().find(transacao[1]) != -1:
                conn.rollback()
                    
            for selecao in selecao_dados:
                indice_inicio = sql.upper().find(selecao)
                if indice_inicio != -1:
                    cursor.execute(sql)
                    dados = cursor.fetchall()  # Busca todos os resultados
                    colunas = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(dados, columns=colunas)
                    print(df)
    
    else:
        print("Não encontrou o nome do banco de dados entre ##   .db##")
    
    conn.close()
    
    
