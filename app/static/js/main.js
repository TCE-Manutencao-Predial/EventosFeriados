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

// Função para mostrar notificações
function showNotification(message, type = 'info') {
    const toast = $('#notificationToast');
    const toastBody = toast.find('.toast-body');
    const toastHeader = toast.find('.toast-header');
    
    // Remover classes anteriores
    toastHeader.removeClass('bg-success bg-danger bg-warning bg-info text-white');
    
    // Adicionar classe baseada no tipo
    switch(type) {
        case 'success':
            toastHeader.addClass('bg-success text-white');
            toastHeader.find('i').attr('class', 'bi bi-check-circle-fill me-2');
            break;
        case 'error':
            toastHeader.addClass('bg-danger text-white');
            toastHeader.find('i').attr('class', 'bi bi-exclamation-circle-fill me-2');
            break;
        case 'warning':
            toastHeader.addClass('bg-warning');
            toastHeader.find('i').attr('class', 'bi bi-exclamation-triangle-fill me-2');
            break;
        default:
            toastHeader.addClass('bg-info text-white');
            toastHeader.find('i').attr('class', 'bi bi-info-circle-fill me-2');
    }
    
    toastBody.text(message);
    
    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();
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
    
    // Auto-hide alerts após 5 segundos
    setTimeout(function() {
        $('.alert-dismissible').fadeOut('slow');
    }, 5000);
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

// Função para dark mode (futuro)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Verificar preferência de dark mode
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}