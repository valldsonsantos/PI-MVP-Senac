# ♻️ Back-end do MVP: E-Waste Collector API (Python/Flask)

Este repositório contém o Back-end (API REST) do nosso Módulo de Agendamentos e Pontos de Coleta. O Back-end foi implementado em Python com o framework Flask e usa SQLite como banco de dados.

## 🚀 Como Rodar e Testar o Servidor

Para que o Front-end e os testes funcionem, o Back-end precisa estar rodando.

1.  **Pré-requisitos:** Python 3.9+ e ter o Git/GitHub configurado.
2.  **Configurar Ambiente Virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    .venv\Scripts\activate      # Windows
    ```
3.  **Instalar Flask:** O único módulo necessário.
    ```bash
    pip install Flask
    ```
4.  **Criar o Banco de Dados (Setup):**
    * Este passo cria o arquivo `lixo_eletronico.db` e popula as tabelas `usuarios`, `pontos_coleta` e `agendamentos` com dados de teste.
    ```bash
    python setup_db.py
    ```
    *(Confirmação de sucesso: "Setup do banco de dados... concluído com sucesso!")*

5.  **Iniciar a API (Servidor):**
    ```bash
    python app.py
    ```
    *A API estará ativa em `http://127.0.0.1:5000`. Mantenha este terminal rodando.*

---

## 📋 Endpoints da API (Para o Front-end)

Estes são os **endpoints** testados e prontos para uso pela Alline:

| Funcionalidade | Método | Endpoint | Status de Sucesso | Evidência de Teste |
| :--- | :--- | :--- | :--- | :--- |
| **Listar Pontos de Coleta** | `GET` | `/pontos` | `200 OK` | Dados de geolocalização disponíveis. |
| **Listar Agendamentos** | `GET` | `/agendamentos` | `200 OK` | Retorna lista de agendamentos com dados do usuário. |
| **Criar Novo Agendamento** | `POST` | `/agendamentos` | `201 CREATED` | Cria novo registro no BD. |
| **Atualizar Status** | `PUT` | `/agendamentos/<id>` | `200 OK` | Permite mudar status (ex: "pendente" para "confirmado"). |

### Exemplo de Requisição POST (Criação)

```json
POST [http://127.0.0.1:5000/agendamentos](http://127.0.0.1:5000/agendamentos)
{
  "usuario_id": 1, 
  "data_retirada": "2025-12-10", 
  "tipo_lixo": "Geladeira Antiga"
}