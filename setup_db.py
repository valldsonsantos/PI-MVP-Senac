import sqlite3
import os

# --- 1. CONFIGURAÇÃO E CONEXÃO ---

DB_NAME = 'lixo_eletronico.db'


def conectar_bd():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    try:
        # check_same_thread=False é necessário para o Flask, mas aqui não fará mal
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        exit()


# --- 2. CRIAÇÃO DAS TABELAS (Schema) ---

def criar_tabelas(conn):
    """Cria as tabelas 'usuarios', 'pontos_coleta' e 'agendamentos'."""
    cursor = conn.cursor()

    # Tabela 1: USUÁRIOS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL 
        );
    """)

    # Tabela 2: PONTOS DE COLETA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pontos_coleta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            horario_func TEXT
        );
    """)

    # Tabela 3: AGENDAMENTOS (COLUNA ponto_coleta_id ADICIONADA AQUI)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            ponto_coleta_id INTEGER,               -- NOVO: ID do Ponto de Coleta escolhido
            data_retirada DATE NOT NULL,
            tipo_lixo TEXT NOT NULL,
            endereco_coleta TEXT NOT NULL,         
            ponto_referencia TEXT,                 
            status TEXT NOT NULL DEFAULT 'pendente',
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (ponto_coleta_id) REFERENCES pontos_coleta(id)
        );
    """)

    conn.commit()
    print("✅ Tabelas criadas ou já existentes.")


# --- 3. POPULAÇÃO DOS DADOS (Seed) ---

def popular_bd(conn):
    """Insere dados de exemplo nas tabelas para testes."""
    cursor = conn.cursor()

    # 3.1. Dados Fictícios para Usuários (AGORA COM 10 USUÁRIOS)
    usuarios = [
        ('Bruno Ruiz', 'bruno.ruiz@exemplo.com.br', 'senha123', 'cidadao'),
        ('Aline Dev', 'aline.dev@exemplo.com.br', 'senha456', 'cidadao'),
        ('Empresa Recicla Tudo', 'empresa@recicla.com', 'senha789', 'empresa'),
        ('Carlos Souza', 'carlos@exemplo.com', 'senha101', 'cidadao'),
        ('Diana Santos', 'diana@exemplo.com', 'senha102', 'cidadao'),
        ('Eduardo Lima', 'eduardo@exemplo.com', 'senha103', 'cidadao'),
        ('Fernanda Melo', 'fernanda@exemplo.com', 'senha104', 'cidadao'),
        ('Gustavo Pires', 'gustavo@exemplo.com', 'senha105', 'cidadao'),
        ('Helena Alves', 'helena@exemplo.com', 'senha106', 'cidadao'),
        ('Igor Costa', 'igor@exemplo.com', 'senha107', 'cidadao'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", usuarios)

    # 3.2. Dados Fictícios para Pontos de Coleta (Empresas)
    pontos = [
        ('Ponto Recicla Fácil', 'Rua das Flores, 100, Centro', -23.6698, -46.5492, 'Seg-Sex, 8h-17h'),
        ('Ecoponto Central', 'Av. Queiroz, 500, Vila Assunção', -23.6601, -46.5350, 'Sab, 9h-13h'),
        ('Reciclagem Delta', 'Rua Delta, 10', -23.6550, -46.5400, 'Seg-Sab, 8h-18h'),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO pontos_coleta (nome, endereco, latitude, longitude, horario_func) 
        VALUES (?, ?, ?, ?, ?)
    """, pontos)

    # 3.3. Dados Fictícios para Agendamentos (AGORA COM ponto_coleta_id)
    agendamentos = [
        # (usuario_id, ponto_coleta_id, data_retirada, tipo_lixo, endereco_coleta, ponto_referencia, status)
        (1, 1, '2025-11-15', 'Monitor e CPU', 'Rua das Gaivotas, 45', 'Próximo ao mercado', 'pendente'),
        (2, 2, '2025-11-20', 'Celulares e Baterias', 'Avenida Principal, 123', None, 'pendente'),
        (3, 1, '2025-12-01', 'Geladeira Antiga', 'Rua B, 500', 'Deixar com porteiro', 'confirmado'),
        (4, 3, '2025-12-05', 'TV de Tubo', 'Praça da Liberdade, 10', 'Em frente à farmácia', 'pendente'),
    ]
    # Limpa agendamentos para não ter erro de FK se as tabelas foram alteradas
    cursor.execute("DELETE FROM agendamentos")

    cursor.executemany("""
        INSERT INTO agendamentos (usuario_id, ponto_coleta_id, data_retirada, tipo_lixo, endereco_coleta, ponto_referencia, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, agendamentos)

    conn.commit()
    print("✅ Banco de dados populado com dados de teste.")


# --- 4. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        print(
            f"⚠️ Atenção: O arquivo '{DB_NAME}' já existe. **Você deve DELETAR o arquivo** para garantir que a nova coluna 'ponto_coleta_id' seja criada na tabela 'agendamentos'.")
        # É VITAL DELETAR o arquivo para a nova coluna ser criada.
        # Caso contrário, o CREATE TABLE IF NOT EXISTS irá ignorar a alteração.

    conn = conectar_bd()
    if conn:
        criar_tabelas(conn)
        popular_bd(conn)
        conn.close()
        print(f"\n✨ Setup do banco de dados '{DB_NAME}' concluído com sucesso!")
        print(
            "\nPRÓXIMOS PASSOS: Você precisa ajustar o app.py, index.html e script.js para lidar com a nova coluna 'ponto_coleta_id'.")