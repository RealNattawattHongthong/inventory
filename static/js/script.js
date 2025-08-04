document.addEventListener('DOMContentLoaded', function() {
    // Single QR Code Generation
    document.getElementById('generate-single').addEventListener('click', async function() {
        const itemId = document.getElementById('single-item-id').value;
        const customCode = document.getElementById('custom-code').value;
        const resultDiv = document.getElementById('single-result');
        
        resultDiv.innerHTML = '<div class="loading"></div>';
        
        try {
            const response = await fetch('/generate_qr', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    item_id: parseInt(itemId),
                    custom_code: customCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                resultDiv.innerHTML = `
                    <div class="qr-item">
                        <img src="${data.qr_image}" alt="QR Code">
                        <div class="item-info">Item ID: ${data.item_id}</div>
                        <div class="item-code">${data.item_code}</div>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = '<div class="error">Failed to generate QR code</div>';
            }
        } catch (error) {
            resultDiv.innerHTML = '<div class="error">Error: ' + error.message + '</div>';
        }
    });
});