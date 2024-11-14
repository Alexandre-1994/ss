// script.js
function reiniciarVerificacao() {
    fetch('/reiniciar', {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            // Redireciona para a página inicial ou limpa a interface conforme necessário
            window.location.reload();
        } else {
            alert("Erro ao reiniciar o sistema.");
        }
    });
}
