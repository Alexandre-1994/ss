// Arquivo JavaScript principal
document.addEventListener('DOMContentLoaded', function() {
    // Seu código JavaScript aqui
    console.log('Sistema de Diagnóstico Médico iniciado');
});

// Funções para gerenciar pacientes
function viewPatient(id) {
    // Implementar visualização de paciente
    fetch(`/paciente/${id}`)
        .then(response => response.json())
        .then(data => {
            // Mostrar dados do paciente
            console.log(data);
        });
}

function editPatient(id) {
    // Implementar edição de paciente
    fetch(`/paciente/${id}`)
        .then(response => response.json())
        .then(data => {
            // Preencher formulário com dados do paciente
            console.log(data);
        });
}

function deletePatient(id) {
    if (confirm('Tem certeza que deseja excluir este paciente?')) {
        fetch(`/paciente/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                // Atualizar lista de pacientes
                location.reload();
            });
    }
}

function savePatient() {
    const form = document.getElementById('addPatientForm');
    const formData = new FormData(form);

    fetch('/paciente', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Fechar modal e atualizar lista
        const modal = bootstrap.Modal.getInstance(document.getElementById('addPatientModal'));
        modal.hide();
        location.reload();
    });
}

// Implementar busca de pacientes
document.getElementById('searchPatient').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});