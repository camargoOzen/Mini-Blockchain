// Wallet storage
let wallets = JSON.parse(localStorage.getItem('wallets')) || [];

// DOM Elements
const createWalletBtn = document.getElementById('createWalletBtn');
const walletsList = document.getElementById('walletsList');
const senderSelect = document.getElementById('senderSelect');
const minerSelect = document.getElementById('minerSelect');
const transactionForm = document.getElementById('transactionForm');
const mineBtn = document.getElementById('mineBtn');
const pendingCount = document.getElementById('pendingCount');
const blockCount = document.getElementById('blockCount');
const pendingTransactions = document.getElementById('pendingTransactions');
const blockchain = document.getElementById('blockchain');
const miningStatus = document.getElementById('miningStatus');
const toast = document.getElementById('toast');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    renderWallets();
    updateBlockchain();
    updatePendingTransactions();

    // Auto-refresh every 5 seconds
    setInterval(() => {
        updateBlockchain();
        updatePendingTransactions();
    }, 5000);
});

// Event Listeners
createWalletBtn.addEventListener('click', createWallet);
transactionForm.addEventListener('submit', sendTransaction);
mineBtn.addEventListener('click', mineBlock);

document.getElementById('resetBtn').addEventListener('click', () => {
    if (confirm('Are you sure you want to reset all local data? This will clear your stored wallets from the browser.')) {
        localStorage.clear();
        window.location.reload();
    }
});

// Create Wallet
async function createWallet() {
    try {
        const response = await fetch('/api/wallet/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            const wallet = {
                address: data.address,
                public_key: data.public_key
            };

            wallets.push(wallet);
            localStorage.setItem('wallets', JSON.stringify(wallets));

            renderWallets();
            showToast('Wallet created successfully! 🎉');
        } else {
            showToast('Error creating wallet: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Delete Wallet
async function deleteWallet(address) {
    if (!confirm('Are you sure you want to delete this wallet? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/wallet/${address}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.success) {
            // Remove from local storage
            wallets = wallets.filter(w => w.address !== address);
            localStorage.setItem('wallets', JSON.stringify(wallets));

            renderWallets();
            showToast('Wallet deleted successfully');
        } else {
            showToast('Error deleting wallet: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Request Faucet
async function requestFaucet(address) {
    try {
        const response = await fetch('/api/faucet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: address })
        });

        const data = await response.json();

        if (data.success) {
            showToast(`💰 ${data.amount} coins requested! Mine a block to confirm.`);
            updatePendingTransactions();
        } else {
            showToast('Faucet request failed: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Render Wallets
function renderWallets() {
    if (wallets.length === 0) {
        walletsList.innerHTML = '<p class="empty-state">No wallets created yet. Click the button above to create one!</p>';
        senderSelect.innerHTML = '<option value="">Select a wallet...</option>';
        minerSelect.innerHTML = '<option value="">No miner reward</option>';
        return;
    }

    // Render wallets list with faucet button
    walletsList.innerHTML = wallets.map((wallet, index) => `
        <div class="wallet-item">
            <div class="wallet-address">Wallet #${index + 1}</div>
            <div class="wallet-pubkey">Address: ${wallet.address}</div>
            <div class="wallet-pubkey">Public Key: ${wallet.public_key.substring(0, 40)}...</div>
            <div class="wallet-balance" id="balance-${wallet.address}">Balance: Loading...</div>

            <div class="wallet-actions">
                <button class="btn btn-faucet" onclick="requestFaucet('${wallet.address}')">💰 Faucet</button>
                <button class="btn btn-danger" onclick="deleteWallet('${wallet.address}')" style="background: #ff4757; margin-left: 10px;">🗑️ Delete</button>
            </div>
        </div>
    `).join('');

    // Update sender select
    senderSelect.innerHTML = '<option value="">Select a wallet...</option>' +
        wallets.map((wallet, index) => `
            <option value="${index}">Wallet #${index + 1} (${wallet.address})</option>
        `).join('');

    // Update miner select
    minerSelect.innerHTML = '<option value="">No miner reward</option>' +
        wallets.map((wallet, index) => `
            <option value="${wallet.address}">Wallet #${index + 1} - ${wallet.address}</option>
        `).join('');

    // Load balances
    wallets.forEach(wallet => {
        updateBalance(wallet.address);
    });
}

// Update Balance
async function updateBalance(address) {
    try {
        const response = await fetch(`/api/wallet/balance/${address}`);
        const data = await response.json();

        if (data.success) {
            const balanceEl = document.getElementById(`balance-${address}`);
            if (balanceEl) {
                balanceEl.textContent = `Balance: ${data.balance} coins`;
            }
        }
    } catch (error) {
        console.error('Error fetching balance:', error);
    }
}

// Send Transaction
async function sendTransaction(e) {
    e.preventDefault();

    const senderIndex = parseInt(senderSelect.value);
    const receiverAddress = document.getElementById('receiverAddress').value;
    const amount = parseFloat(document.getElementById('amount').value);

    if (isNaN(senderIndex)) {
        showToast('Please select a sender wallet', 'error');
        return;
    }

    const sender = wallets[senderIndex];

    try {
        const response = await fetch('/api/transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender_address: sender.address,
                sender_pubkey: sender.public_key,
                receiver_address: receiverAddress,
                amount: amount
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Transaction submitted successfully! ✅');
            transactionForm.reset();
            updatePendingTransactions();
        } else {
            showToast('Transaction failed: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Mine Block
async function mineBlock() {
    mineBtn.disabled = true;
    miningStatus.textContent = 'Mining in progress...';
    miningStatus.className = 'status-message status-success';

    const minerAddress = minerSelect.value || null;

    try {
        const response = await fetch('/api/mine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ miner_address: minerAddress })
        });

        const data = await response.json();

        if (data.success) {
            miningStatus.textContent = data.message;
            miningStatus.className = 'status-message status-success';
            showToast('Block mined successfully! ⛏️');

            updateBlockchain();
            updatePendingTransactions();

            // Update balances
            wallets.forEach(wallet => updateBalance(wallet.address));
        } else {
            miningStatus.textContent = data.error;
            miningStatus.className = 'status-message status-error';
        }
    } catch (error) {
        miningStatus.textContent = 'Mining failed: ' + error.message;
        miningStatus.className = 'status-message status-error';
    } finally {
        mineBtn.disabled = false;
        setTimeout(() => {
            miningStatus.textContent = '';
            miningStatus.className = 'status-message';
        }, 5000);
    }
}

// Update Blockchain
async function updateBlockchain() {
    try {
        const response = await fetch('/api/blockchain');
        const data = await response.json();

        if (data.success) {
            blockCount.textContent = data.length;

            if (data.chain.length === 0) {
                blockchain.innerHTML = '<p class="empty-state">No blocks in chain</p>';
                return;
            }

            blockchain.innerHTML = data.chain.reverse().map(block => {
                const date = new Date(block.timestamp * 1000);
                const txCount = Array.isArray(block.transactions) ? block.transactions.length : 0;

                return `
                    <div class="block">
                        <div class="block-header">
                            <span class="block-index">Block #${block.index}</span>
                            <span class="block-time">${date.toLocaleString()}</span>
                        </div>
                        <div class="block-info">Hash: <span class="block-hash">${block.hash || 'Pending...'}</span></div>
                        <div class="block-info">Previous Hash: ${block.previous_hash}</div>
                        <div class="block-info">Nonce: ${block.nonce}</div>
                        <div class="block-info">Transactions: ${txCount}</div>
                        ${txCount > 0 ? `
                            <div style="margin-top: 1rem;">
                                ${block.transactions.map(tx => {
                    const isCoinbase = tx.sender_address === 'COINBASE' || tx.sender_address === 'FAUCET';
                    const txClass = isCoinbase ? 'transaction-coinbase' : 'transaction-item';
                    const senderLabel = isCoinbase ? `${tx.sender_address} ⭐` : `${tx.sender_address.substring(0, 10)}...`;

                    return `
                                        <div class="${txClass}">
                                            ${senderLabel} → ${tx.receiver_address.substring(0, 10)}... 
                                            <strong>${tx.amount} coins</strong>
                                        </div>
                                    `;
                }).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Error fetching blockchain:', error);
    }
}

// Update Pending Transactions
async function updatePendingTransactions() {
    try {
        const response = await fetch('/api/transactions/pending');
        const data = await response.json();

        if (data.success) {
            pendingCount.textContent = data.count;

            if (data.count === 0) {
                pendingTransactions.innerHTML = '<p class="empty-state">No pending transactions</p>';
                mineBtn.disabled = true;
            } else {
                mineBtn.disabled = false;
                pendingTransactions.innerHTML = data.transactions.map(tx => {
                    const isCoinbase = tx.sender_address === 'COINBASE' || tx.sender_address === 'FAUCET';
                    const txClass = isCoinbase ? 'transaction-coinbase transaction-pending' : 'transaction-pending';
                    const senderLabel = isCoinbase ? `${tx.sender_address} ⭐` : `${tx.sender_address.substring(0, 10)}...`;

                    return `
                        <div class="transaction-item ${txClass}">
                            ${senderLabel} → ${tx.receiver_address.substring(0, 10)}... 
                            <strong>${tx.amount} coins</strong>
                        </div>
                    `;
                }).join('');
            }
        }
    } catch (error) {
        console.error('Error fetching pending transactions:', error);
    }
}

// Show Toast Notification
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.style.background = type === 'error'
        ? 'linear-gradient(135deg, #f44336 0%, #e91e63 100%)'
        : 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)';
    toast.style.color = 'white';
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
