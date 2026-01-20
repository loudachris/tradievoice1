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

const BACKEND_URL = "https://tradie-voice-loudachris-2gra2.ondigitalocean.app";

// --- Interaction Handlers ---

// Toggle Mode
toggleSwitch.addEventListener('change', (e) => {
    state.mode = e.target.checked ? 'walkthrough' : 'command';
    statusText.textContent = state.mode === 'command' ? 'Ready (Command)' : 'Ready (Walkthrough)';
    console.log(`Switched to ${state.mode} mode`);

    if (state.mode === 'walkthrough') {
        pulseBtn.style.backgroundColor = 'var(--secondary-color)';
    } else {
        pulseBtn.style.backgroundColor = 'var(--primary-color)';
    }
});

// Pulse Button (Recording Logic)
let mediaRecorder;
let audioChunks = [];

pulseBtn.addEventListener('mousedown', startRecording);
pulseBtn.addEventListener('mouseup', stopRecording);
pulseBtn.addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
pulseBtn.addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });

async function startRecording() {
    if (state.isRecording) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Chrome/Android default
            await sendAudioToBackend(audioBlob);
        };

        mediaRecorder.start();
        state.isRecording = true;
        pulseBtn.style.transform = 'scale(0.9)';
        statusText.textContent = 'Listening...';

    } catch (err) {
        console.error("Error accessing microphone:", err);
        statusText.textContent = "Mic Error";
        alert("Could not access microphone. Please ensure permission is granted.");
    }
}

function stopRecording() {
    if (!state.isRecording || !mediaRecorder) return;

    mediaRecorder.stop();
    // Stop all tracks to release mic
    mediaRecorder.stream.getTracks().forEach(track => track.stop());

    state.isRecording = false;
    pulseBtn.style.transform = 'scale(1)';
    statusText.textContent = 'Processing...';
}

async function sendAudioToBackend(audioBlob) {
    const formData = new FormData();
    // Using .webm extension; backend Whisper should handle it.
    formData.append("file", audioBlob, "recording.webm");

    try {
        const response = await fetch(`${BACKEND_URL}/api/transcribe`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Backend Response:", data);

        // Handle result
        // The backend returns a QuoteData object
        // For this MVP, we'll append the items to our list

        if (data.items && data.items.length > 0) {
            data.items.forEach(item => {
                addQuoteItem(item);
            });
            statusText.textContent = "Success!";
            setTimeout(() => {
                statusText.textContent = state.mode === 'command' ? 'Ready (Command)' : 'Ready (Walkthrough)';
            }, 2000);
        } else {
            statusText.textContent = "No items found";
            setTimeout(() => statusText.textContent = 'Ready', 2000);
        }

    } catch (error) {
        console.error("Upload failed:", error);
        statusText.textContent = "Error";
        alert("Failed to process audio. See console for details.");
    }
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
