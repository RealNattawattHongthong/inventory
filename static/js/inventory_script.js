// Auto-capitalize item code input
document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.getElementById('code');
    if (codeInput) {
        codeInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }
});