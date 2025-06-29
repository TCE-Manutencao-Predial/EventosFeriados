// app/static/js/main.js

// Configuração global do jQuery AJAX
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        // Adicionar o prefixo da rota se não estiver presente
        if (!settings.url.startsWith('http') && !settings.url.startsWith('/EventosFeriados')) {
            settings.url = '/EventosFeriados' + settings.url;
        }
    }
});

// Sistema de Toast (padrão RFID)
function showNotification(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Criar container se não existir
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast_' + Date.now();
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const toastHtml = `
        <div class="toast ${type}" id="${toastId}">
            <i class="fas ${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="closeToast('${toastId}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHtml);
    
    // Auto fechar após 5 segundos
    setTimeout(() => {
        closeToast(toastId);
    }, 5000);
}

function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Função para formatar data
function formatarData(dia, mes, ano) {
    return `${dia.toString().padStart(2, '0')}/${mes.toString().padStart(2, '0')}/${ano}`;
}

// Função para validar formulários
function validarFormulario(formId) {
    const form = document.getElementById(formId);
    if (!form.checkValidity()) {
        form.reportValidity();
        return false;
    }
    return true;
}

// Função para limpar formulário
function limparFormulario(formId) {
    document.getElementById(formId).reset();
}

// Função para fazer requisições AJAX com loading
function ajaxComLoading(options) {
    // Mostrar loading
    const loadingHtml = `
        <div class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        </div>
    `;
    
    if (options.loadingTarget) {
        $(options.loadingTarget).html(loadingHtml);
    }
    
    // Fazer requisição
    return $.ajax({
        ...options,
        complete: function(xhr, status) {
            // Callback original
            if (options.complete) {
                options.complete(xhr, status);
            }
        }
    });
}

// Função para debounce (evitar múltiplas chamadas)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Função para exportar tabela para CSV
function exportarTabelaCSV(tabelaId, nomeArquivo) {
    const tabela = document.getElementById(tabelaId);
    let csv = [];
    
    // Cabeçalhos
    const headers = [];
    tabela.querySelectorAll('thead th').forEach(th => {
        headers.push('"' + th.textContent.trim() + '"');
    });
    csv.push(headers.join(','));
    
    // Dados
    tabela.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push('"' + td.textContent.trim() + '"');
        });
        if (row.length > 0) {
            csv.push(row.join(','));
        }
    });
    
    // Download
    const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', nomeArquivo);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Função para verificar conflitos de horário
function verificarConflitoHorario(horaInicio1, horaFim1, horaInicio2, horaFim2) {
    const inicio1 = moment(horaInicio1, 'HH:mm');
    const fim1 = moment(horaFim1, 'HH:mm');
    const inicio2 = moment(horaInicio2, 'HH:mm');
    const fim2 = moment(horaFim2, 'HH:mm');
    
    return !(fim1.isSameOrBefore(inicio2) || inicio1.isSameOrAfter(fim2));
}

// Função para verificar se um feriado deve ser exibido (não muito antigo e não do próximo ano)
function feriadoDeveSerExibido(dia, mes, ano) {
    const dataFeriado = new Date(ano, mes - 1, dia);
    const agora = new Date();
    const anoAtual = agora.getFullYear();
    const umaSemanaaAtras = new Date();
    umaSemanaaAtras.setDate(agora.getDate() - 7);
    
    // Não exibir feriados muito antigos (anterior a 1 semana) ou do próximo ano
    return dataFeriado >= umaSemanaaAtras && ano <= anoAtual;
}

// Função para verificar se um evento deve ser exibido (não muito antigo)
function eventoDeveSerExibido(dia, mes, ano) {
    const dataEvento = new Date(ano, mes - 1, dia);
    const agora = new Date();
    const umaSemanaaAtras = new Date();
    umaSemanaaAtras.setDate(agora.getDate() - 7);
    
    return dataEvento >= umaSemanaaAtras;
}

// Inicialização global
$(document).ready(function() {
    // Ativar tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Ativar popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Adicionar animação suave ao scroll
    $('a[href^="#"]').on('click', function(event) {
        const target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 70
            }, 1000);
        }
    });
});

// Função para atualizar contador de caracteres em textareas
function setupCharacterCounter(textareaId, maxLength) {
    const textarea = document.getElementById(textareaId);
    const counter = document.createElement('small');
    counter.className = 'text-muted float-end';
    textarea.parentElement.appendChild(counter);
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${remaining} caracteres restantes`;
        
        if (remaining < 20) {
            counter.classList.add('text-danger');
            counter.classList.remove('text-muted');
        } else {
            counter.classList.remove('text-danger');
            counter.classList.add('text-muted');
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}