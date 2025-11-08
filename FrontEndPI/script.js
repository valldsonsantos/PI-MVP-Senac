// script.js - Versão Final Completa (Com Ponto de Coleta, Abas, Correção de Usuário e Botão de Check)

const API_AGENDAMENTOS_URL = 'http://127.0.0.1:5000/agendamentos';
const API_PONTOS_URL = 'http://127.0.0.1:5000/pontos'; // NOVA API
const form = document.getElementById('agendamentoForm');
const mensagemDiv = document.getElementById('mensagem');
const pontoColetaSelect = document.getElementById('ponto_coleta_id'); // NOVO SELECT

// VARIÁVEIS para as duas listas e contadores
const agendamentosPendentesList = document.getElementById('agendamentos-pendentes-list');
const agendamentosConfirmadosList = document.getElementById('agendamentos-confirmados-list');
const countPendentes = document.getElementById('count-pendentes');
const countConfirmados = document.getElementById('count-confirmados');


// --- 1. FUNÇÕES DE EXIBIÇÃO ---

function mostrarMensagem(texto, tipo) {
    mensagemDiv.textContent = texto;
    mensagemDiv.className = '';
    mensagemDiv.classList.add(tipo);
    mensagemDiv.style.display = 'block';
    setTimeout(() => {
        mensagemDiv.style.display = 'none';
    }, 5000);
}

function formatarData(dataStr) {
    const partes = dataStr.split('-');
    if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    return dataStr;
}

function criarItemAgendamento(agendamento) {
    const li = document.createElement('li');
    let statusLower = agendamento.status.toLowerCase();
    let statusClass = statusLower.includes('pendente') ? 'pendente' : 'confirmado';

    let conteudo = `
        <span class="status-${statusClass}">${agendamento.status.toUpperCase()}</span>
        <br>
        <strong>ID ${agendamento.id}</strong> | Data: ${formatarData(agendamento.data_retirada)}
        <br>
        Lixo: ${agendamento.tipo_lixo}
        <br>
        Endereço: ${agendamento.endereco_coleta || 'Não informado'}
    `;

    if (agendamento.ponto_referencia) {
        conteudo += `
            <br>
            Referência: ${agendamento.ponto_referencia}
        `;
    }

    // NOVIDADE: Exibe a Empresa/Ponto de Coleta
    if (agendamento.nome_ponto_coleta) {
        conteudo += `
            <br>
            Empresa: <strong>${agendamento.nome_ponto_coleta}</strong>
        `;
    } else if (agendamento.ponto_coleta_id) {
         // Fallback caso a API não tenha o nome (como em um novo agendamento)
        conteudo += `
            <br>
            Ponto de Coleta ID: ${agendamento.ponto_coleta_id}
        `;
    }

    // CORREÇÃO DO UNDEFINED: Exibe Nome/Email OU ID do usuário
    if (agendamento.nome_usuario && agendamento.nome_usuario !== null) {
        conteudo += `
            <br>
            Usuário: ${agendamento.nome_usuario} (${agendamento.email_usuario})
        `;
    } else if (agendamento.usuario_id) {
        conteudo += `
            <br>
            Usuário ID: ${agendamento.usuario_id}
        `;
    }

    // NOVIDADE: Adiciona o botão de Check/Confirmação se for PENDENTE
    if (statusLower.includes('pendente')) {
        conteudo += `
            <div class="actions">
                <button onclick="mudarStatusAgendamento(${agendamento.id}, 'Confirmado')" class="check-button">
                    ✅ Confirmar Retirada
                </button>
            </div>
        `;
    }

    li.innerHTML = conteudo;
    return li;
}

// Função para enviar o PUT (mudar o status)
async function mudarStatusAgendamento(id, novoStatus) {
    if (!confirm(`Tem certeza que deseja mudar o status do Agendamento #${id} para '${novoStatus}'?`)) {
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/agendamentos/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: novoStatus })
        });

        const data = await response.json();

        if (response.ok && data.status === 'sucesso') {
            mostrarMensagem(`Agendamento #${id} atualizado para '${novoStatus}' com sucesso!`, 'success');
            // Recarrega as listas para mover o item da aba Pendentes para Confirmados
            listarAgendamentos();
        } else {
            mostrarMensagem(`Erro ao atualizar agendamento: ${data.mensagem}`, 'error');
        }

    } catch (error) {
        console.error('Erro de rede ao atualizar status:', error);
        mostrarMensagem('Erro de conexão com o servidor.', 'error');
    }
}


// --- 2. FUNÇÕES DE INTERAÇÃO COM A API ---

// NOVIDADE: Carrega a lista de Pontos de Coleta e preenche o <select>
async function carregarPontosColeta() {
    pontoColetaSelect.innerHTML = '<option value="">Carregando empresas...</option>';
    try {
        const response = await fetch(API_PONTOS_URL);
        const data = await response.json();

        if (response.ok && data.status === 'sucesso' && data.dados) {
            pontoColetaSelect.innerHTML = '<option value="">Selecione uma Empresa</option>';
            data.dados.forEach(ponto => {
                const option = document.createElement('option');
                option.value = ponto.id;
                option.textContent = `${ponto.nome} (${ponto.endereco.substring(0, 30)}...)`;
                pontoColetaSelect.appendChild(option);
            });
        } else {
            pontoColetaSelect.innerHTML = '<option value="">Erro ao carregar empresas.</option>';
        }
    } catch (error) {
        console.error('Erro ao carregar pontos de coleta:', error);
        pontoColetaSelect.innerHTML = '<option value="">Erro de conexão com a API de Pontos.</option>';
    }
}


async function listarAgendamentos() {
    // Limpa as listas e zera os contadores
    agendamentosPendentesList.innerHTML = '';
    agendamentosConfirmadosList.innerHTML = '';
    countPendentes.textContent = '0';
    countConfirmados.textContent = '0';

    // Mostra um estado de carregamento
    agendamentosPendentesList.innerHTML = '<li>Carregando...</li>';
    agendamentosConfirmadosList.innerHTML = '<li>Carregando...</li>';

    try {
        const response = await fetch(API_AGENDAMENTOS_URL);
        const data = await response.json();

        // Limpa novamente para os resultados
        agendamentosPendentesList.innerHTML = '';
        agendamentosConfirmadosList.innerHTML = '';

        if (response.ok && data.status === 'sucesso' && data.dados) {

            let pendentesCount = 0;
            let confirmadosCount = 0;

            data.dados.forEach(agendamento => {
                const li = criarItemAgendamento(agendamento);

                // Filtra e adiciona na lista correta
                let statusLower = agendamento.status.toLowerCase();
                if (statusLower.includes('pendente')) {
                    agendamentosPendentesList.appendChild(li);
                    pendentesCount++;
                } else {
                    agendamentosConfirmadosList.appendChild(li);
                    confirmadosCount++;
                }
            });

            // Atualiza os contadores
            countPendentes.textContent = pendentesCount.toString();
            countConfirmados.textContent = confirmadosCount.toString();


            // Se não houver itens, adiciona a mensagem de "vazio"
            if (pendentesCount === 0) {
                 agendamentosPendentesList.innerHTML = '<li>🎉 Nenhum agendamento pendente no momento!</li>';
            }
            if (confirmadosCount === 0) {
                 agendamentosConfirmadosList.innerHTML = '<li>Nenhum agendamento concluído ou confirmado.</li>';
            }

        } else {
            agendamentosPendentesList.innerHTML = `<li>Erro da API: ${data.mensagem}</li>`;
        }
    } catch (error) {
        console.error('Erro ao listar agendamentos:', error);
        agendamentosPendentesList.innerHTML = '<li>Não foi possível conectar à API para listar agendamentos.</li>';
        agendamentosConfirmadosList.innerHTML = '<li>Não foi possível conectar à API para listar agendamentos.</li>';
    }

    // Ajusta a altura do primeiro acordeão para mostrar o conteúdo carregado
    const activeHeader = document.querySelector('.accordion-header.active');
    if (activeHeader) {
        activeHeader.nextElementSibling.style.maxHeight = activeHeader.nextElementSibling.scrollHeight + "px";
    }
}


async function handleAgendamento(event) {
    event.preventDefault();

    const usuario_id = document.getElementById('usuario_id').value;
    const ponto_coleta_id = pontoColetaSelect.value; // NOVIDADE: Captura o ID do Ponto de Coleta
    const tipo_lixo = document.getElementById('tipo_lixo').value;
    const data_retirada = document.getElementById('data_retirada').value;
    const endereco_coleta = document.getElementById('endereco_coleta').value;
    const ponto_referencia = document.getElementById('ponto_referencia').value;

    const usuarioID_int = parseInt(usuario_id);
    const pontoColetaID_int = parseInt(ponto_coleta_id); // Converte para inteiro

    // NOVIDADE: Validação do Ponto de Coleta
    if (isNaN(usuarioID_int) || usuarioID_int <= 0 || !data_retirada || !tipo_lixo || !endereco_coleta || isNaN(pontoColetaID_int)) {
        mostrarMensagem('Preencha todos os campos obrigatórios, incluindo o ID de Usuário e a Empresa de Coleta.', 'error');
        return;
    }

    const dadosParaAPI = {
        usuario_id: usuarioID_int,
        ponto_coleta_id: pontoColetaID_int, // NOVIDADE: Envia o ID para a API
        data_retirada: data_retirada,
        tipo_lixo: tipo_lixo,
        endereco_coleta: endereco_coleta
    };

    if (ponto_referencia) {
        dadosParaAPI.ponto_referencia = ponto_referencia;
    }

    try {
        const response = await fetch(API_AGENDAMENTOS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dadosParaAPI)
        });

        const data = await response.json();

        if (response.status === 201 && data.status === 'sucesso') {
            mostrarMensagem(`Agendamento #${data.id_agendamento} criado com sucesso!`, 'success');
            form.reset();
            // Recarrega a lista de pontos de coleta para resetar a seleção do <select>
            carregarPontosColeta();

            // NOVIDADE: Adiciona o novo agendamento (Pendente) na lista correta
            if (data.novo_agendamento) {
                const novoAgendamento = data.novo_agendamento;

                // Garante que os IDs estão presentes para a exibição (usados nos fallbacks)
                novoAgendamento.usuario_id = usuarioID_int;
                novoAgendamento.ponto_coleta_id = pontoColetaID_int;
                novoAgendamento.nome_usuario = null;
                novoAgendamento.nome_ponto_coleta = null; // O nome da empresa virá com o refresh da lista

                const li = criarItemAgendamento(novoAgendamento);
                agendamentosPendentesList.prepend(li);

                // Atualiza o contador de pendentes
                let currentCount = parseInt(countPendentes.textContent);
                countPendentes.textContent = (currentCount + 1).toString();

                // Abre o painel de pendentes se estiver fechado
                const pendenteHeader = agendamentosPendentesList.closest('.accordion-content').previousElementSibling;
                if (!pendenteHeader.classList.contains('active')) {
                     // Verifica se a função toggleAccordion foi definida no index.html
                     if (typeof toggleAccordion === 'function') {
                        toggleAccordion(pendenteHeader);
                     }
                }

            } else {
                // Se a API não retornou o objeto, recarrega a lista
                listarAgendamentos();
            }

        } else {
            mostrarMensagem(`Falha no agendamento: ${data.mensagem}`, 'error');
        }

    } catch (error) {
        console.error('Erro de rede ao agendar:', error);
        mostrarMensagem('Erro de conexão com o servidor. Verifique se a API está rodando.', 'error');
    }
}

// --- 3. INICIALIZAÇÃO DA PÁGINA ---

form.addEventListener('submit', handleAgendamento);

// Carrega a lista de Pontos de Coleta e, em seguida, a lista de Agendamentos
carregarPontosColeta();
listarAgendamentos();