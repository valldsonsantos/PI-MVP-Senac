# app.py

import sqlite3
import json
# Adicionado request aqui, no topo, junto com as outras importações do Flask.
from flask import Flask, jsonify, abort, request

# --- 1. CONFIGURAÇÃO DA APLICAÇÃO ---

app = Flask(__name__)
# DATABASE é o nome do arquivo com o script setup_db.py
DATABASE = 'lixo_eletronico.db'


# --- 2. FUNÇÃO DE CONEXÃO E AUXILIAR ---

def get_db_connection():
    """Cria e retorna a conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE)
        # sqlite3.Row permite que o resultado da consulta seja acessado por nome da coluna (como um dicionário)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        # Se houver erro de conexão, a API retorna um erro 500
        print(f"Erro ao conectar ao banco de dados: {e}")
        abort(500, description="Falha na conexão com o banco de dados.")


# --- 3. ROTA DA API: GET /pontos (LEITURA) ---

@app.route('/pontos', methods=['GET'])
def listar_pontos_coleta():
    """
    Lista todos os pontos de coleta, essencial para a funcionalidade de geolocalização.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Executa a consulta SQL para buscar os dados
    cursor.execute('SELECT id, nome, endereco, latitude, longitude, horario_func FROM pontos_coleta')

    # 2. Pega todos os resultados (que já estão em formato de Row/dicionário)
    pontos_raw = cursor.fetchall()

    # 3. Converte a lista de resultados em uma lista de dicionários padrão Python (JSON serializável)
    pontos_json = [dict(ponto) for ponto in pontos_raw]

    conn.close()  # Sempre feche a conexão

    # 4. Retorna a lista em formato JSON com o código HTTP 200 (OK)
    return jsonify({
        "status": "sucesso",
        "dados": pontos_json
    }), 200


# --- 4. ROTA DA API: POST /agendamentos (ESCRITA) ---

# Este bloco foi movido para cá para que o Flask o encontre antes de rodar.
@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    """
    Rota para criar um novo agendamento de coleta de lixo eletrônico.
    Recebe os dados via POST em formato JSON.
    """
    # 1. Tenta obter os dados JSON enviados pelo Front-end (ou Postman/Insomnia)
    dados = request.get_json()

    # 2. Validação básica dos campos obrigatórios
    campos_obrigatorios = ['usuario_id', 'data_retirada', 'tipo_lixo']

    if not dados:
        # Erro 400 Bad Request se não houver JSON
        return jsonify({"status": "erro", "mensagem": "Nenhum dado JSON fornecido."}), 400

    for campo in campos_obrigatorios:
        if campo not in dados:
            # Erro 400 se faltar algum campo essencial
            return jsonify({"status": "erro", "mensagem": f"Campo obrigatório '{campo}' não fornecido."}), 400

    # 3. Extrai os dados
    usuario_id = dados['usuario_id']
    data_retirada = dados['data_retirada']
    tipo_lixo = dados['tipo_lixo']

    # Define o status inicial como 'pendente'
    status_inicial = 'pendente'

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 4. Executa o comando INSERT para salvar no banco
        cursor.execute(
            """
            INSERT INTO agendamentos (usuario_id, data_retirada, tipo_lixo, status) 
            VALUES (?, ?, ?, ?)
            """,
            (usuario_id, data_retirada, tipo_lixo, status_inicial)
        )
        conn.commit()

        # Pega o ID do último registro inserido para a resposta
        novo_id = cursor.lastrowid
        conn.close()

        # 5. Retorna a confirmação e o ID do novo agendamento
        return jsonify({
            "status": "sucesso",
            "mensagem": "Agendamento criado com sucesso!",
            "id_agendamento": novo_id
        }), 201  # Código 201 Created (Criado)

    except sqlite3.IntegrityError as e:
        # Erro de integridade, como um usuario_id que não existe (FK)
        conn.close()
        return jsonify({"status": "erro", "mensagem": f"Erro de integridade ao criar agendamento: {e}"}), 409

    except sqlite3.Error as e:
        # Outros erros de banco de dados
        conn.close()
        return jsonify({"status": "erro", "mensagem": f"Erro de banco de dados: {e}"}), 500


# Continuação do app.py

# --- 5. ROTA DA API: GET /agendamentos (LEITURA DA LISTA) ---

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    """
    Lista todos os agendamentos existentes no banco de dados.
    (Em um sistema real, esta rota seria filtrada por usuário logado ou admin).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Executa a consulta SQL para buscar os dados na tabela 'agendamentos'.
    # Usamos JOIN para trazer o nome do usuário junto, tornando o dado mais útil.
    cursor.execute("""
        SELECT 
            a.id, 
            a.data_retirada, 
            a.tipo_lixo, 
            a.status, 
            u.nome AS nome_usuario, 
            u.email AS email_usuario
        FROM agendamentos a
        JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.data_retirada DESC
    """)

    # 2. Pega todos os resultados
    agendamentos_raw = cursor.fetchall()

    # 3. Converte para uma lista de dicionários
    agendamentos_json = [dict(agendamento) for agendamento in agendamentos_raw]

    conn.close()  # Sempre feche a conexão

    # 4. Retorna a lista em formato JSON com o código HTTP 200 (OK)
    return jsonify({
        "status": "sucesso",
        "total": len(agendamentos_json),
        "dados": agendamentos_json
    }), 200


# Continuação do app.py

# --- 6. ROTA DA API: PUT /agendamentos/<id> (ATUALIZAÇÃO) ---

# O <id> na rota captura o número do agendamento que será atualizado
@app.route('/agendamentos/<int:id>', methods=['PUT'])
def atualizar_agendamento(id):
    """
    Atualiza o status de um agendamento específico.
    Ideal para o admin mudar de 'pendente' para 'confirmado' ou 'concluido'.
    """
    dados = request.get_json()

    # 1. Validação: Checar se o campo 'status' foi fornecido
    if not dados or 'status' not in dados:
        return jsonify({"status": "erro", "mensagem": "O campo 'status' é obrigatório para atualização."}), 400

    novo_status = dados['status']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 2. Executa o comando UPDATE no banco
        cursor.execute(
            """
            UPDATE agendamentos 
            SET status = ? 
            WHERE id = ?
            """,
            (novo_status, id)
        )
        conn.commit()

        # 3. Verifica se alguma linha foi realmente atualizada
        if cursor.rowcount == 0:
            conn.close()
            # Retorna 404 Not Found se o ID não existir
            return jsonify({"status": "erro", "mensagem": f"Agendamento com ID {id} não encontrado."}), 404

        conn.close()

        # 4. Retorna a confirmação de sucesso
        return jsonify({
            "status": "sucesso",
            "mensagem": f"Status do Agendamento {id} atualizado para '{novo_status}'."
        }), 200  # Código 200 OK

    except sqlite3.Error as e:
        conn.close()
        return jsonify({"status": "erro", "mensagem": f"Erro de banco de dados na atualização: {e}"}), 500





# --- 5. EXECUÇÃO DA APLICAÇÃO ---

if __name__ == '__main__':
    # Roda o servidor Flask na porta 5000.
    # host='0.0.0.0' permite acesso de outros IPs (como o front-end).
    app.run(debug=True, host='0.0.0.0', port=5000)
    # A API estará acessível em: http://127.0.0.1:5000/pontos