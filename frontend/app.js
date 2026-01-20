// State Management
const state = {
    mode: 'command', // 'command' or 'walkthrough'
    quoteItems: [],
    get quoteTotal() {
        return this.quoteItems.reduce((sum, item) => sum + item.total, 0);
    },
    isRecording: false
};

// DOM Elements
const pulseBtn = document.getElementById('pulse-btn');
const toggleSwitch = document.getElementById('mode-toggle');
const statusText = document.getElementById('status-text');
const totalDisplay = document.getElementById('total-value');
const upsellNotification = document.getElementById('upsell-notification');
const quoteItemsContainer = document.getElementById('quote-items');
const debugBtn = document.getElementById('sim-high-value');

// --- Hidden Logic: $10k Trigger Listener ---
// Using a Proxy or a simple update function pattern. 
// I'll call updateUI() on every state change which checks the logic.

function checkUpsellTrigger() {
    if (state.quoteTotal > 10000) {
        if (!upsellNotification.classList.contains('active')) {
            upsellNotification.classList.add('active');
            // Play a subtle sound or haptic feedback in a real app
            console.log("Upsell Trigger Activated: Total > $10k");
        }
    } else {
        upsellNotification.classList.remove('active');
    }
}

function updateUI() {
    // Update Total
    totalDisplay.textContent = state.quoteTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // Update List
    if (state.quoteItems.length === 0) {
        quoteItemsContainer.innerHTML = '<div class="empty-state">No items yet. Speak to add.</div>';
    } else {
        quoteItemsContainer.innerHTML = state.quoteItems.map(item => `
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #eee; padding-bottom:8px;">
                <span>${item.description}</span>
                <span style="font-weight:600;">$${item.total.toFixed(2)}</span>
            </div>
        `).join('');
    }

    // Check Trigger
    checkUpsellTrigger();
}

// --- Interaction Handlers ---

// Toggle Mode
toggleSwitch.addEventListener('change', (e) => {
    state.mode = e.target.checked ? 'walkthrough' : 'command';
    statusText.textContent = state.mode === 'command' ? 'Ready (Command)' : 'Ready (Walkthrough)';
    console.log(`Switched to ${state.mode} mode`);

    // Visual feedback for mode switch
    if (state.mode === 'walkthrough') {
        pulseBtn.style.backgroundColor = 'var(--secondary-color)'; // Change color slightly for mode? Or keep consistent?
        // Let's keep consistent Brand Pulse Button as per verify, but maybe change icon or shadow.
        // For now sticking to Brand Primary as requested.
    } else {
        pulseBtn.style.backgroundColor = 'var(--primary-color)';
    }
});

// Pulse Button (Recording Logic Stub)
pulseBtn.addEventListener('mousedown', startRecording);
pulseBtn.addEventListener('mouseup', stopRecording);
pulseBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); }); // Mobile support
pulseBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });

function startRecording() {
    if (state.isRecording) return;
    state.isRecording = true;
    pulseBtn.style.transform = 'scale(0.9)';
    statusText.textContent = 'Listening...';
    // Logic: Connect to WebSocket or MediaRecorder based on state.mode
}

function stopRecording() {
    if (!state.isRecording) return;
    state.isRecording = false;
    pulseBtn.style.transform = 'scale(1)';
    statusText.textContent = 'Processing...';

    // START SIMULATION FOR DEMO
    setTimeout(() => {
        statusText.textContent = state.mode === 'command' ? 'Ready (Command)' : 'Ready (Walkthrough)';

        // Simulate adding an item
        const newItem = {
            description: "Simulated Item " + (state.quoteItems.length + 1),
            total: Math.floor(Math.random() * 500) + 100
        };
        addQuoteItem(newItem);

    }, 1000);
}

function addQuoteItem(item) {
    state.quoteItems.push(item);
    updateUI();
}

// Debug Button for $10k Trigger
debugBtn.addEventListener('click', () => {
    addQuoteItem({
        description: "High Value Job (Upsell Test)",
        total: 10500.00
    });
});

// Initialize
updateUI();
