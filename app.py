from flask_cors import CORS
import sqlite3
from flask import Flask, jsonify, abort, request, g

# --- 1. CONFIGURAÇÃO DA APLICAÇÃO ---

app = Flask(__name__)
# Permite que o Front-end acesse a API (essencial para evitar erro CORS)
CORS(app)
DATABASE = 'lixo_eletronico.db'


# --- 2. FUNÇÃO DE CONEXÃO E AUXILIAR ---

def get_db_connection():
    """Cria e retorna a conexão com o banco de dados."""
    # O uso de g.db garante que uma única conexão é usada por requisição
    db = getattr(g, '_database', None)
    if db is None:
        try:
            db = g._database = sqlite3.connect(DATABASE)
            # Permite que o resultado da consulta seja acessado por nome da coluna (como um dicionário)
            db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            abort(500, description="Falha na conexão com o banco de dados.")
    return db

# Fecha a conexão após a requisição
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# --- 3. ROTA DA API: GET /pontos (LEITURA) ---

@app.route('/pontos', methods=['GET'])
def listar_pontos_coleta():
    """
    Lista todos os pontos de coleta (para popular o <select> no Front-end).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, endereco, horario_func FROM pontos_coleta')
    pontos_raw = cursor.fetchall()
    pontos_json = [dict(ponto) for ponto in pontos_raw]

    return jsonify({
        "status": "sucesso",
        "dados": pontos_json
    }), 200


# --- 4. ROTA DA API: POST /agendamentos (ESCRITA) - AJUSTADA ---

@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    """
    Rota para criar um novo agendamento.
    AGORA RECEBE 'ponto_coleta_id' como campo obrigatório.
    """
    dados = request.get_json()

    # 1. Validação básica dos campos obrigatórios (ponto_coleta_id é NOVO OBRIGATÓRIO)
    campos_obrigatorios = ['usuario_id', 'data_retirada', 'tipo_lixo', 'endereco_coleta', 'ponto_coleta_id']

    if not dados:
        return jsonify({"status": "erro", "mensagem": "Nenhum dado JSON fornecido."}), 400

    for campo in campos_obrigatorios:
        if campo not in dados:
            return jsonify({"status": "erro", "mensagem": f"Campo obrigatório '{campo}' não fornecido."}), 400

    # 2. Extrai e trata os dados
    usuario_id = dados['usuario_id']
    ponto_coleta_id = dados['ponto_coleta_id'] # NOVO CAMPO
    data_retirada = dados['data_retirada']
    tipo_lixo = dados['tipo_lixo']
    endereco_coleta = dados['endereco_coleta']
    ponto_referencia = dados.get('ponto_referencia', None)
    status_inicial = 'Pendente'

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 3. Executa o comando INSERT (COM NOVO CAMPO)
        cursor.execute(
            """
            INSERT INTO agendamentos (usuario_id, ponto_coleta_id, data_retirada, tipo_lixo, endereco_coleta, ponto_referencia, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (usuario_id, ponto_coleta_id, data_retirada, tipo_lixo, endereco_coleta, ponto_referencia, status_inicial)
        )
        conn.commit()

        # 4. Pega o ID do último registro inserido
        novo_id = cursor.lastrowid

        # 5. Retorna o objeto do agendamento para o Front-end
        return jsonify({
            "status": "sucesso",
            "mensagem": "Agendamento criado com sucesso!",
            "id_agendamento": novo_id,
            "novo_agendamento": {
                "id": novo_id,
                "usuario_id": usuario_id,
                "ponto_coleta_id": ponto_coleta_id, # NOVO CAMPO
                "data_retirada": data_retirada,
                "tipo_lixo": tipo_lixo,
                "endereco_coleta": endereco_coleta,
                "ponto_referencia": ponto_referencia,
                "status": status_inicial
            }
        }), 201

    except sqlite3.IntegrityError as e:
        # Erro de FK: ID de usuário ou ID de ponto de coleta não existe
        return jsonify({"status": "erro", "mensagem": f"Erro de integridade (ID de usuário ou Ponto de Coleta não existe): {e}"}), 409

    except sqlite3.Error as e:
        return jsonify({"status": "erro", "mensagem": f"Erro de banco de dados: {e}"}), 500


# --- 5. ROTA DA API: GET /agendamentos (LEITURA DA LISTA) - AJUSTADA ---

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    """
    Lista todos os agendamentos.
    AGORA FAZ JOIN COM 'pontos_coleta' para retornar o nome da empresa.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id, 
            a.data_retirada, 
            a.tipo_lixo,
            a.endereco_coleta,       
            a.ponto_referencia,      
            a.status, 
            u.nome AS nome_usuario, 
            u.email AS email_usuario,
            pc.nome AS nome_ponto_coleta  -- NOVO CAMPO
        FROM agendamentos a
        JOIN usuarios u ON a.usuario_id = u.id
        LEFT JOIN pontos_coleta pc ON a.ponto_coleta_id = pc.id -- NOVO JOIN
        ORDER BY a.data_retirada DESC
    """)

    agendamentos_raw = cursor.fetchall()
    agendamentos_json = [dict(agendamento) for agendamento in agendamentos_raw]

    return jsonify({
        "status": "sucesso",
        "total": len(agendamentos_json),
        "dados": agendamentos_json
    }), 200


# --- 6. ROTA DA API: PUT /agendamentos/<id> (ATUALIZAÇÃO) ---
# A rota PUT (Check) foi mantida e está CORRETA.

@app.route('/agendamentos/<int:id>', methods=['PUT'])
def atualizar_agendamento(id):
    """
    Atualiza o status de um agendamento específico (usado para o botão 'Check').
    """
    dados = request.get_json()

    if not dados or 'status' not in dados:
        return jsonify({"status": "erro", "mensagem": "O campo 'status' é obrigatório para atualização."}), 400

    novo_status = dados['status']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE agendamentos 
            SET status = ? 
            WHERE id = ?
            """,
            (novo_status, id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "erro", "mensagem": f"Agendamento com ID {id} não encontrado."}), 404

        return jsonify({
            "status": "sucesso",
            "mensagem": f"Status do Agendamento {id} atualizado para '{novo_status}'."
        }), 200

    except sqlite3.Error as e:
        return jsonify({"status": "erro", "mensagem": f"Erro de banco de dados na atualização: {e}"}), 500


# --- 7. EXECUÇÃO DA APLICAÇÃO ---

if __name__ == '__main__':
    # Roda o servidor Flask na porta 5000.
    app.run(debug=True, host='0.0.0.0', port=5000)