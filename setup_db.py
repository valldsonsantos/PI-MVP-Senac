# setup_db.py

import sqlite3
import os

# --- 1. CONFIGURAÇÃO E CONEXÃO ---

# Define o nome do arquivo do banco de dados.
# O SQLite criará este arquivo se ele não existir.
DB_NAME = 'lixo_eletronico.db'


def conectar_bd():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    try:
        # sqlite3.connect(DB_NAME) cria a conexão.

        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        # Termina o script se houver erro crítico na conexão
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
            tipo TEXT NOT NULL -- 'cidadao' ou 'empresa'
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
            horario_func TEXT -- Ex: "Seg-Sex, 9h-18h"
        );
    """)

    # Tabela 3: AGENDAMENTOS

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_retirada DATE NOT NULL,
            tipo_lixo TEXT NOT NULL, -- Ex: "Monitores", "Pequenos Eletrodomésticos"
            status TEXT NOT NULL, -- Ex: "pendente", "confirmado", "concluido"
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    print("✅ Tabelas criadas ou já existentes.")


# --- 3. POPULAÇÃO DOS DADOS (Seed) ---

def popular_bd(conn):
    """Insere dados de exemplo nas tabelas para testes."""
    cursor = conn.cursor()

    # 3.1. Dados Fictícios para Usuários
    usuarios = [
        ('Aline Dev', 'aline@exemplo.com', 'senha123', 'cidadao'),
        ('Empresa Recicla Tudo', 'empresa@recicla.com', 'senha456', 'empresa'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", usuarios)

    # 3.2. Dados Fictícios para Pontos de Coleta

    pontos = [
        ('Ponto Recicla Fácil', 'Rua das Flores, 100, Centro', -23.6698, -46.5492, 'Seg-Sex, 8h-17h'),
        ('Ecoponto Central', 'Av. Queiroz, 500, Vila Assunção', -23.6601, -46.5350, 'Sab, 9h-13h'),
    ]
    # O 'INSERT OR IGNORE' evita erros se você rodar o script mais de uma vez.
    cursor.executemany("""
        INSERT OR IGNORE INTO pontos_coleta (nome, endereco, latitude, longitude, horario_func) 
        VALUES (?, ?, ?, ?, ?)
    """, pontos)

    # 3.3. Dados Fictícios para Agendamentos
    # Assumindo que o ID do usuário 'aline@exemplo.com' é 1
    agendamentos = [
        (1, '2025-11-15', 'Monitor e CPU', 'pendente'),
        (1, '2025-11-20', 'Celulares e Baterias', 'pendente'),
    ]
    cursor.executemany("""
        INSERT INTO agendamentos (usuario_id, data_retirada, tipo_lixo, status) 
        VALUES (?, ?, ?, ?)
    """, agendamentos)

    conn.commit()
    print("✅ Banco de dados populado com dados de teste.")


# --- 4. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    # Verifica se o banco já existe para avisar o usuário
    if os.path.exists(DB_NAME):
        print(f"⚠️ Atenção: O arquivo '{DB_NAME}' já existe. O script tentará adicionar dados.")

    conn = conectar_bd()
    if conn:
        criar_tabelas(conn)
        popular_bd(conn)
        conn.close()
        print(f"\n✨ Setup do banco de dados '{DB_NAME}' concluído com sucesso!")
        print("Você pode agora iniciar o desenvolvimento do seu back-end em Python.")