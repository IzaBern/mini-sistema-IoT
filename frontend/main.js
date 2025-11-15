// =======================================================================
// VARIÁVEIS GLOBAIS
// =======================================================================

// URL base do backend 
const API_URL = "http://127.0.0.1:5000";

// XML de exemplo (completo) 
const XML_EXEMPLO_T2 = `<?xml version="1.0" encoding="UTF-8"?>
<estufa id="EST01">
  <sensores>
    <sensor id="S01" tipo="temperatura">
      <unidade>°C</unidade>
    </sensor>
    <sensor id="S02" tipo="umidadear">
      <unidade>%</unidade>
    </sensor>
    <sensor id="S03" tipo="umidadesolo">
      <unidade>%</unidade>
    </sensor>
    <sensor id="S04" tipo="ph">
      <unidade>pH</unidade>
    </sensor>
    <sensor id="S05" tipo="ce">
      <unidade>mS/cm</unidade>
    </sensor>
    <sensor id="S06" tipo="luminosidade">
      <unidade>lux</unidade>
    </sensor>
    <sensor id="S07" tipo="co2">
      <unidade>ppm</unidade>
    </sensor>
  </sensores>
  <leituras>
    <leitura id="L01">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S01"/>
      <valor>22.5</valor>
    </leitura>
    <leitura id="L02">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S02"/>
      <valor>70.0</valor> </leitura>
    <leitura id="L03">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S03"/>
      <valor>65.0</valor>
    </leitura>
    <leitura id="L04">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S04"/>
      <valor>6.0</valor> </leitura>
    <leitura id="L05">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S05"/>
      <valor>1.5</valor>
    </leitura>
    <leitura id="L06">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S06"/>
      <valor>30000</valor>
    </leitura>
    <leitura id="L07">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S07"/>
      <valor>800</valor>
    </leitura>
  </leituras>
</estufa>
`;

// XML de exemplo (simples) 
const XML_EXEMPLO_SIMPLES = `<?xml version="1.0" encoding="UTF-8"?>
<estufa id="EST01">
  <sensores>
    <sensor id="S01" tipo="temperatura">
      <unidade>°C</unidade>
    </sensor>
  </sensores>
  <leituras>
    <leitura id="L01">
      <dataHora>2025-10-20T14:30:00</dataHora>
      <sensorRef ref="S01"/>
      <valor>22.5</valor>
    </leitura>
  </leituras>
</estufa>
`;

//Cache global para as regras de configuração
let regrasDeValidacaoCache = {};

// =======================================================================
// O "ROUTER" PRINCIPAL (LÓGICA DE INICIALIZAÇÃO)
// =======================================================================

document.addEventListener('DOMContentLoaded', () => {
    inicializarNavegacaoSPA();

    // Carrega o Dashboard
    const dashboardContainer = document.getElementById('dashboard-data-container');
    if (dashboardContainer) {
        carregarDashboard(dashboardContainer);
    }

    // Carrega os Alertas
    const alertasContainer = document.getElementById('alertas-data-container');
    if (alertasContainer) {
        carregarAlertas(alertasContainer);
    }

    // Inicializa a Configuração
    const configForm = document.getElementById('config-form');
    if (configForm) {
        inicializarConfiguracao(configForm, document.getElementById('config-feedback'));
    }

    // Inicializa o Editor
    const editorTextarea = document.getElementById('xml-editor');
    if (editorTextarea) {
        inicializarEditor(editorTextarea, document.getElementById('editor-feedback'));
    }

    // Botão Limpar Dashboard
    const btnLimpar = document.getElementById('btn-limpar-dashboard');
    if (btnLimpar) {
        inicializarBotaoLimpar(btnLimpar);
    }
});
async function iniciarAplicacao() {
    // inicializa a navegação
    inicializarNavegacaoSPA();

    // pega os elementos (DOM) de todas as vistas
    const dashboardContainer = document.getElementById('dashboard-data-container');
    const alertasContainer = document.getElementById('alertas-data-container');
    const configForm = document.getElementById('config-form');
    const configFeedback = document.getElementById('config-feedback');
    const editorTextarea = document.getElementById('xml-editor');
    const editorFeedback = document.getElementById('editor-feedback');
    const btnLimpar = document.getElementById('btn-limpar-dashboard');

    // carrega dados que NÃO dependem das regras (podem correr em paralelo)
    if (dashboardContainer) carregarDashboard(dashboardContainer);
    if (alertasContainer) carregarAlertas(alertasContainer);
    if (btnLimpar) inicializarBotaoLimpar(btnLimpar);

    // espera as regras serem carregadas
    try {
        if (configForm) {
            await carregarConfiguracao(configForm, configFeedback);
        }
    } catch (e) {
        console.error("ERRO CRÍTICO: Falha ao carregar regras na inicialização.", e);
    }

    if (configForm) {
        inicializarBotoesConfiguracao(configForm, configFeedback);
    }
    if (editorTextarea) {
        inicializarEditor(editorTextarea, editorFeedback);
    }
}
// =======================================================================
// LÓGICA DE NAVEGAÇÃO SPA
// =======================================================================

function inicializarNavegacaoSPA() {
    const navButtons = document.querySelectorAll('.nav-button');
    const views = document.querySelectorAll('.view-content');

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const viewId = button.getAttribute('data-view');
            views.forEach(view => view.classList.remove('active'));
            const activeView = document.getElementById(`view-${viewId}`);
            if (activeView) {
                activeView.classList.add('active');
            }
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        });
    });
}

// =======================================================================
// DASHBOARD
// =======================================================================

async function carregarDashboard(container) {
    const NomesParaDisplay = {
        "temperatura": "Temperatura",
        "umidadear": "Umidade do Ar",
        "umidadesolo": "Umidade do Solo",
        "ph": "pH",
        "ce": "Condutividade Elétrica (CE)",
        "luminosidade": "Luminosidade",
        "co2": "CO₂"
    };
    const UnidadesParaDisplay = {
        "temperatura": "°C",
        "umidadear": "%",
        "umidadesolo": "%",
        "ph": "pH",
        "ce": "mS/cm",
        "luminosidade": "lux",
        "co2": "ppm"
    };
    try {
        container.innerHTML = '<p>Carregando dados da API...</p>';
        const response = await fetch(`${API_URL}/api/leituras`);

        if (!response.ok) {
            throw new Error(`Erro da API: ${response.status} ${response.statusText}`);
        }
        const dadosEstufas = await response.json();

        if (dadosEstufas.length === 0) {
            container.innerHTML = '<p>Nenhum dado de leitura encontrado no backend.</p>';
            return;
        }

        container.innerHTML = '';
        dadosEstufas.forEach(estufa => {
            const cardEstufa = document.createElement('div');
            cardEstufa.className = 'card-estufa';
            
            let leiturasHtml = '';
            estufa.leituras.forEach(leitura => {
                const tipoSensorKey = leitura.tipo;
                const tipoSensorNome = NomesParaDisplay[tipoSensorKey] || tipoSensorKey || "Sensor";
                const unidade = UnidadesParaDisplay[tipoSensorKey] || "";

                leiturasHtml += `
                    <li>
                        <strong>${tipoSensorNome}</strong> (Ref: ${leitura.sensorRef}) | 
                        Valor: <strong>${leitura.valor} ${unidade}</strong> | 
                        Data: ${leitura.dataHora}
                    </li>
                `;
            });

            cardEstufa.innerHTML = `<h3>Estufa ID: ${estufa.estufa_id}</h3><ul class="lista-leituras">${leiturasHtml}</ul>`;
            container.appendChild(cardEstufa);
        });

    } catch (error) {
        console.error("Falha ao carregar dados do dashboard:", error);
        container.innerHTML = `<div class="error-box"><strong>Erro ao conectar ao Backend.</strong><p>O servidor Flask está rodando?</p><p>${error.message}</p></div>`;
    }
}

// =======================================================================
// ALERTAS
// =======================================================================

async function carregarAlertas(container) {
    try {
        container.innerHTML = '<p>Carregando alertas da API...</p>';
        const response = await fetch(`${API_URL}/api/alertas`);

        if (!response.ok) {
            throw new Error(`Erro da API: ${response.status} ${response.statusText}`);
        }
        const alertas = await response.json();

        if (alertas.length === 0) {
            container.innerHTML = '<p>Nenhum alerta ativo encontrado.</p>';
            return;
        }

        container.innerHTML = '';
        alertas.forEach(alerta => {
            const cardAlerta = document.createElement('div');
            cardAlerta.className = 'card-alerta'; 
            cardAlerta.innerHTML = `
                <h3>Alerta de ${alerta.tipo.toUpperCase()} (Estufa ${alerta.estufa_id})</h3>
                <ul class="lista-leituras">
                    <li><strong>Valor Lido: ${alerta.valor_lido}</strong></li>
                    <li>Faixa Ideal: ${alerta.faixa_ideal}</li>
                    <li>Sensor ID: ${alerta.sensor_id}</li>
                    <li>Data: ${alerta.dataHora}</li>
                </ul>
            `;
            container.appendChild(cardAlerta);
        });

    } catch (error) {
        console.error("Falha ao carregar alertas:", error);
        container.innerHTML = `<div class="error-box"><strong>Erro ao conectar ao Backend.</strong><p>O servidor Flask está rodando?</p><p>${error.message}</p></div>`;
    }
}

// =======================================================================
// CONFIGURAÇÃO
// =======================================================================

function inicializarConfiguracao(form, feedback) {
    carregarConfiguracao(form, feedback);

    document.getElementById('btn-save-config').addEventListener('click', async () => {
        await salvarConfiguracao(form, feedback);
    });

    document.getElementById('btn-reset-config').addEventListener('click', async () => {
        if (confirm("Deseja restaurar as regras padrão? Isso apagará as modificações feitas nas configurações.")) {
            await resetarConfiguracao(form, feedback);
        }
    });
}
/**
 * (GET /api/configuracoes) Carrega as regras, constrói o form e atualiza o cache
 */
async function carregarConfiguracao(form, feedback) {
    const NomesParaDisplay = {
        "temperatura": "Temperatura",
        "umidadear": "Umidade do Ar",
        "umidadesolo": "Umidade do Solo",
        "ph": "pH",
        "ce": "Condutividade Elétrica (CE)",
        "luminosidade": "Luminosidade",
        "co2": "CO₂"
    };

    try {
        form.innerHTML = '<p>Carregando regras...</p>';
        const response = await fetch(`${API_URL}/api/configuracoes`);
        if (!response.ok) throw new Error("Falha ao carregar regras.");
        
        const regras = await response.json();
        regrasDeValidacaoCache = regras; // Atualiza o cache global
        
        form.innerHTML = ''; 
        
        Object.keys(regras).forEach(tipoSensor => { 
            const regra = regras[tipoSensor];
            const fieldset = document.createElement('fieldset');
            fieldset.dataset.tipo = tipoSensor;
            const nomeSensor = NomesParaDisplay[tipoSensor] || tipoSensor.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
            fieldset.dataset.tipo = tipoSensor; 
            
            fieldset.innerHTML = `
                <legend>${nomeSensor}</legend>
                <label for="config-${tipoSensor}-min">Min:</label>
                <input type="number" step="0.1" id="config-${tipoSensor}-min" value="${regra.min}">
                
                <label for="config-${tipoSensor}-max">Max:</label>
                <input type="number" step="0.1" id="config-${tipoSensor}-max" value="${regra.max}">
            `;
            form.appendChild(fieldset);
        });

    } catch (error) {
        showFeedback(feedback, `Erro: ${error.message}`, 'error');
    }
}
/**
 * (PUT /api/configuracoes) Salva as regras e atualiza o cache
 */
async function salvarConfiguracao(form, feedback) {
    try {
        const novasRegras = {};
        const fieldsets = form.getElementsByTagName('fieldset');
        
        for (const fs of fieldsets) {
            const tipo = fs.dataset.tipo; 
            
            if (tipo) {
                const minInput = document.getElementById(`config-${tipo}-min`);
                const maxInput = document.getElementById(`config-${tipo}-max`);
                if (minInput && maxInput) {
                    novasRegras[tipo] = { 
                        min: parseFloat(minInput.value), 
                        max: parseFloat(maxInput.value) 
                    };
                } else {
                    console.error(`Erro: Não encontrei inputs para o tipo ${tipo}`);
                }
            }
        }

        const response = await fetch(`${API_URL}/api/configuracoes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(novasRegras)
        });

        if (!response.ok) throw new Error(`API retornou ${response.status}`);
        
        // Atualiza o cache global com as novas regras
        regrasDeValidacaoCache = novasRegras;
        showFeedback(feedback, "Regras salvas com sucesso!", 'success');

    } catch (error) {
        showFeedback(feedback, `Erro ao salvar: ${error.message}`, 'error');
    }
}
/**
 * (POST /api/configuracoes/reset) Reseta as regras e ATUALIZA O CACHE.
 */
async function resetarConfiguracao(form, feedback) {
    try {
        const response = await fetch(`${API_URL}/api/configuracoes/reset`, { method: 'POST' });
        if (!response.ok) throw new Error("Falha ao restaurar.");

        showFeedback(feedback, "Regras restauradas para o padrão.", 'success');
        
        // Recarrega o formulário, que (pelo carregarConfiguracao)
        // também atualiza o cache global.
        await carregarConfiguracao(form, feedback);

    } catch (error) {
        showFeedback(feedback, `Erro ao restaurar: ${error.message}`, 'error');
    }
}

// =======================================================================
// EDITOR XML
// =======================================================================

function inicializarEditor(textarea, feedback) {
    // Botão "Importar XML de Exemplo (Completo)"
    document.getElementById('btn-import-xml').addEventListener('click', () => {
        textarea.value = XML_EXEMPLO_T2; 
        showFeedback(feedback, "XML de exemplo completo importado.", 'success');
    });

    // Botão "Importar XML de Exemplo (Simples)"
    document.getElementById('btn-import-xml-simple').addEventListener('click', () => {
        textarea.value = XML_EXEMPLO_SIMPLES; 
        showFeedback(feedback, "XML de exemplo simples importado.", 'success');
    });

    // Botão "Enviar para API"
    document.getElementById('btn-send-api').addEventListener('click', async () => {
        await enviarXmlApi(textarea.value, feedback);
    });
}

/**
 * Envia o XML do editor para o backend T3 (POST /api/leituras).
 */
async function enviarXmlApi(xmlString, feedback) {
    try {
        // a validação serve como aviso, não bloqueia o envio
        showFeedback(feedback, "Enviando XML para a API...", 'info');

        const response = await fetch(`${API_URL}/api/leituras`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/xml' },
            body: xmlString
        });

        const responseData = await response.json();

        if (response.ok) { // Status 201 (Created)
            showFeedback(feedback, `Sucesso! API retornou 201: ${responseData.message}`, 'success');
            
            carregarDashboard(document.getElementById('dashboard-data-container'));
            carregarAlertas(document.getElementById('alertas-data-container'));
            
        } else { // Status 400, 409, 500
            throw new Error(`API retornou ${response.status}: ${responseData.error.description}`);
        }

    } catch (error) {
        showFeedback(feedback, error.message, 'error');
    }
}
// =======================================================================
//  BOTÃO "LIMPAR"
// =======================================================================
function inicializarBotaoLimpar(btnLimpar) {
    btnLimpar.addEventListener('click', async () => {
        // confirmação
        if (!confirm("Tem a certeza? Esta ação irá apagar todos os dados de leitura do backend.")) {
            return; // Se o usuário clicar "Cancelar"
        }

        try {
            // chama o endpoint DELETE
            const response = await fetch(`${API_URL}/api/leituras`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error("Falha ao contactar a API para exclusão.");
            }
            
            const resultado = await response.json();
            
            // Mostra o feedback (ex: "5 ficheiros excluídos")
            showFeedback(document.getElementById('editor-feedback'), resultado.message, 'success');

            // Recarrega o dashboard
            // (O dashboard agora vai mostrar "Nenhum dado...")
            carregarDashboard(document.getElementById('dashboard-data-container'));

        } catch (error) {
            console.error("Erro ao limpar o dashboard:", error);
            showFeedback(document.getElementById('editor-feedback'), error.message, 'error');
        }
    });
}
// =======================================================================
// FUNÇÕES AUXILIARES
// =======================================================================

/**
 * Mostra uma mensagem de feedback numa div específica.
 */
function showFeedback(feedbackContainer, message, type) {
    if (feedbackContainer) {
        // Usa <pre> para formatar os alertas de validação corretamente
        feedbackContainer.innerHTML = `<pre class"feedback ${type}">${message}</pre>`;
    }
}