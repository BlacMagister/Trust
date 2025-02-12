async function fetchBlocks() {
    try {
        // Mengambil data dari endpoint /blocks
        const response = await fetch('http://206.189.44.12:5001/blocks');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const blocks = data.chain || [];
        const blocksDiv = document.getElementById('blocks');
        blocksDiv.innerHTML = ''; // Mengosongkan konten sebelumnya

        // Iterasi setiap blok dan tampilkan dalam layout grid Bootstrap
        blocks.forEach(block => {
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6';

            const card = document.createElement('div');
            card.className = 'card block-card shadow-sm';
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">Block #${block.index}</h5>
                    <p class="card-text"><strong>Timestamp:</strong> ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                    <p class="card-text"><strong>Hash:</strong> ${block.hash}</p>
                    <p class="card-text"><strong>Previous Hash:</strong> ${block.previous_hash}</p>
                    <p class="card-text"><strong>Transactions:</strong> ${JSON.stringify(block.transactions)}</p>
                </div>
            `;
            colDiv.appendChild(card);
            blocksDiv.appendChild(colDiv);
        });
    } catch (error) {
        console.error('Error fetching blocks:', error);
        const blocksDiv = document.getElementById('blocks');
        blocksDiv.innerHTML = `
          <div class="alert alert-danger" role="alert">
            Error fetching blocks: ${error.message}
          </div>
        `;
    }
}

// Pastikan DOM telah dimuat
document.addEventListener("DOMContentLoaded", function() {
    fetchBlocks();
    // Refresh data setiap 10 detik
    setInterval(fetchBlocks, 10000);
});
