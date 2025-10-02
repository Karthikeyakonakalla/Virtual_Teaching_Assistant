// VTA JEE - Main JavaScript

// Global variables
let currentQueryId = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;

// API Base URL
const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeTextInput();
    initializeVoiceInput();
    initializeImageInput();
    initializeFeedback();
    initializeAudioPlayer();
});

// Tab switching functionality
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
}

// Text input functionality
function initializeTextInput() {
    const submitBtn = document.getElementById('submitTextBtn');
    const textInput = document.getElementById('textInput');
    
    submitBtn.addEventListener('click', () => {
        const query = textInput.value.trim();
        if (query) {
            submitTextQuery(query);
        } else {
            showNotification('Please enter a question', 'error');
        }
    });
    
    // Submit on Ctrl+Enter
    textInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            submitBtn.click();
        }
    });
}

// Submit text query
async function submitTextQuery(query) {
    try {
        showLoading(true);
        hideSolution();
        
        const subject = document.getElementById('subjectSelect').value;
        
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                query: query,
                subject: subject || null,
                include_audio: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentQueryId = data.query_id;
            displaySolution(data);
        } else {
            showNotification(data.error || 'Failed to process query', 'error');
        }
    } catch (error) {
        console.error('Error submitting query:', error);
        showNotification('Failed to connect to server', 'error');
    } finally {
        showLoading(false);
    }
}

// Voice input functionality
function initializeVoiceInput() {
    const recordBtn = document.getElementById('recordBtn');
    
    recordBtn.addEventListener('click', toggleRecording);
}

// Toggle recording
async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await submitAudioQuery(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        const recordBtn = document.getElementById('recordBtn');
        recordBtn.classList.add('recording');
        recordBtn.querySelector('span').textContent = 'Stop Recording';
        
        // Show recording time
        document.getElementById('recordingTime').style.display = 'block';
        startRecordingTimer();
        
        // Animate voice visualizer
        document.getElementById('voiceVisualizer').classList.add('active');
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        showNotification('Microphone access denied', 'error');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        // Update UI
        const recordBtn = document.getElementById('recordBtn');
        recordBtn.classList.remove('recording');
        recordBtn.querySelector('span').textContent = 'Start Recording';
        
        // Stop timer
        stopRecordingTimer();
        document.getElementById('recordingTime').style.display = 'none';
        
        // Stop visualizer animation
        document.getElementById('voiceVisualizer').classList.remove('active');
    }
}

// Recording timer
function startRecordingTimer() {
    recordingSeconds = 0;
    updateRecordingTime();
    
    recordingTimer = setInterval(() => {
        recordingSeconds++;
        updateRecordingTime();
        
        // Auto-stop after 60 seconds
        if (recordingSeconds >= 60) {
            stopRecording();
            showNotification('Maximum recording time reached', 'info');
        }
    }, 1000);
}

function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
}

function updateRecordingTime() {
    const minutes = Math.floor(recordingSeconds / 60);
    const seconds = recordingSeconds % 60;
    const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('recordingTime').textContent = timeStr;
}

// Submit audio query
async function submitAudioQuery(audioBlob) {
    try {
        showLoading(true);
        hideSolution();
        
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentQueryId = data.query_id;
            
            // Show transcription
            if (data.query) {
                const transcriptionDiv = document.getElementById('transcription');
                transcriptionDiv.textContent = `Transcribed: "${data.query}"`;
                transcriptionDiv.style.display = 'block';
            }
            
            displaySolution(data);
        } else {
            showNotification(data.error || 'Failed to process audio', 'error');
        }
    } catch (error) {
        console.error('Error submitting audio:', error);
        showNotification('Failed to process audio', 'error');
    } finally {
        showLoading(false);
    }
}

// Image input functionality
function initializeImageInput() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const submitBtn = document.getElementById('submitImageBtn');
    const removeBtn = document.getElementById('removeImageBtn');
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleImageFile(files[0]);
        }
    });
    
    // File input change
    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageFile(e.target.files[0]);
        }
    });
    
    // Submit image
    submitBtn.addEventListener('click', () => {
        const file = imageInput.files[0];
        if (file) {
            submitImageQuery(file);
        }
    });
    
    // Remove image
    removeBtn.addEventListener('click', () => {
        clearImagePreview();
    });
}

// Handle image file
function handleImageFile(file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please upload a valid image file', 'error');
        return;
    }
    
    // Validate file size (16MB)
    if (file.size > 16 * 1024 * 1024) {
        showNotification('File size must be less than 16MB', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        showImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);
}

// Show image preview
function showImagePreview(src) {
    document.getElementById('uploadArea').style.display = 'none';
    document.getElementById('imagePreview').style.display = 'block';
    document.getElementById('previewImg').src = src;
    document.getElementById('imageContext').style.display = 'block';
    document.getElementById('submitImageBtn').style.display = 'block';
}

// Clear image preview
function clearImagePreview() {
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('imageContext').style.display = 'none';
    document.getElementById('submitImageBtn').style.display = 'none';
    document.getElementById('imageInput').value = '';
    document.getElementById('imageContext').value = '';
}

// Submit image query
async function submitImageQuery(file) {
    try {
        showLoading(true);
        hideSolution();
        
        const formData = new FormData();
        formData.append('image', file);
        
        const context = document.getElementById('imageContext').value.trim();
        if (context) {
            formData.append('context', context);
        }
        
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentQueryId = data.query_id;
            displaySolution(data);
        } else {
            showNotification(data.error || 'Failed to process image', 'error');
        }
    } catch (error) {
        console.error('Error submitting image:', error);
        showNotification('Failed to process image', 'error');
    } finally {
        showLoading(false);
    }
}

// Display solution
function displaySolution(data) {
    const solutionSection = document.getElementById('solutionSection');
    solutionSection.style.display = 'block';
    
    const solution = data.solution;
    
    // Problem understanding
    if (solution.problem_understanding) {
        const problemDiv = document.getElementById('problemUnderstanding');
        problemDiv.innerHTML = `
            <h3><i class="fas fa-brain"></i> Understanding the Problem</h3>
            <p>${solution.problem_understanding}</p>
        `;
        problemDiv.style.display = 'block';
    }
    
    // Formulas used
    if (solution.formulas_used && solution.formulas_used.length > 0) {
        const formulasDiv = document.getElementById('formulasUsed');
        const formulasContent = formulasDiv.querySelector('.formulas-content');
        
        formulasContent.innerHTML = solution.formulas_used.map(formula => {
            if (formula.latex) {
                return `<div class="formula-item">$$${formula.latex}$$</div>`;
            } else if (formula.description) {
                return `<div class="formula-item">${formula.description}</div>`;
            }
            return '';
        }).join('');
        
        formulasDiv.style.display = 'block';
    }
    
    // Steps
    if (solution.steps && solution.steps.length > 0) {
        const stepsDiv = document.getElementById('stepsSolution');
        const stepsContent = stepsDiv.querySelector('.steps-content');
        
        stepsContent.innerHTML = solution.steps.map((step, index) => {
            const isCollapsible = step.collapsible ? 'collapsible' : '';
            return `
                <div class="step-item" data-step="${step.number || index + 1}">
                    <div class="step-title">${step.title}</div>
                    <div class="step-content ${isCollapsible}">${step.content}</div>
                    ${isCollapsible ? '<span class="expand-btn" onclick="toggleExpand(this)">Show more...</span>' : ''}
                </div>
            `;
        }).join('');
        
        stepsDiv.style.display = 'block';
    }
    
    // Final answer
    if (solution.final_answer) {
        const answerDiv = document.getElementById('finalAnswer');
        answerDiv.innerHTML = `
            <i class="fas fa-check-circle"></i> Final Answer: ${solution.final_answer}
        `;
        answerDiv.style.display = 'block';
    }
    
    // Verification
    if (solution.verification) {
        const verificationDiv = document.getElementById('verification');
        const verificationContent = verificationDiv.querySelector('.verification-content');
        verificationContent.innerHTML = solution.verification;
        verificationDiv.style.display = 'block';
    }
    
    // References
    if (data.context_used && data.context_used.length > 0) {
        const referencesDiv = document.getElementById('references');
        const referencesContent = referencesDiv.querySelector('.references-content');
        
        referencesContent.innerHTML = data.context_used.map(ref => `
            <div class="reference-item">
                <strong>${ref.source}</strong> - ${ref.subject || 'General'}
                <span class="reference-score">Relevance: ${(ref.score * 100).toFixed(0)}%</span>
            </div>
        `).join('');
        
        referencesDiv.style.display = 'block';
    }
    
    // Confidence score
    if (solution.confidence_score) {
        const confidence = Math.round(solution.confidence_score * 100);
        document.querySelector('.confidence-fill').style.width = `${confidence}%`;
        document.querySelector('.confidence-value').textContent = `${confidence}%`;
    }
    
    // Trigger MathJax rendering
    if (window.MathJax) {
        MathJax.typesetPromise();
    }
    
    // Scroll to solution
    solutionSection.scrollIntoView({ behavior: 'smooth' });
}

// Toggle expand/collapse
function toggleExpand(btn) {
    const content = btn.previousElementSibling;
    content.classList.toggle('expanded');
    btn.textContent = content.classList.contains('expanded') ? 'Show less...' : 'Show more...';
}

// Hide solution
function hideSolution() {
    document.getElementById('solutionSection').style.display = 'none';
}

// Audio functionality
function initializeAudioPlayer() {
    const audioBtn = document.getElementById('audioBtn');
    
    audioBtn.addEventListener('click', async () => {
        if (!currentQueryId) return;
        
        try {
            audioBtn.disabled = true;
            audioBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Get solution text
            const solutionText = extractSolutionText();
            
            const response = await fetch(`${API_BASE}/query/${currentQueryId}/audio?text=${encodeURIComponent(solutionText)}`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            const data = await response.json();
            
            if (data.success && data.audio) {
                playAudio(data.audio, data.format);
            } else {
                showNotification('Failed to generate audio', 'error');
            }
        } catch (error) {
            console.error('Error generating audio:', error);
            showNotification('Failed to generate audio', 'error');
        } finally {
            audioBtn.disabled = false;
            audioBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
        }
    });
}

// Extract solution text for audio
function extractSolutionText() {
    const sections = [
        document.querySelector('#problemUnderstanding p'),
        document.querySelector('#stepsSolution .steps-content'),
        document.querySelector('#finalAnswer')
    ];
    
    return sections
        .filter(s => s)
        .map(s => s.textContent)
        .join('\n\n');
}

// Play audio
function playAudio(audioBase64, format) {
    const audio = document.getElementById('audioPlayer');
    audio.src = `data:audio/${format};base64,${audioBase64}`;
    audio.play();
}

// Feedback functionality
function initializeFeedback() {
    const feedbackBtn = document.getElementById('feedbackBtn');
    const modal = document.getElementById('feedbackModal');
    const closeBtn = modal.querySelector('.modal-close');
    const submitBtn = document.getElementById('submitFeedbackBtn');
    
    // Open modal
    feedbackBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
    });
    
    // Close modal
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Rating stars
    const stars = modal.querySelectorAll('.rating-stars i');
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.dataset.rating);
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.classList.remove('far');
                    s.classList.add('fas');
                } else {
                    s.classList.remove('fas');
                    s.classList.add('far');
                }
            });
        });
    });
    
    // Submit feedback
    submitBtn.addEventListener('click', async () => {
        const rating = modal.querySelectorAll('.rating-stars .fas').length;
        const comment = document.getElementById('feedbackComment').value;
        const issueType = document.querySelector('input[name="issue"]:checked')?.value;
        
        if (rating === 0) {
            showNotification('Please select a rating', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    query_id: currentQueryId,
                    rating: rating,
                    comment: comment,
                    issue_type: issueType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Thank you for your feedback!', 'success');
                modal.style.display = 'none';
                resetFeedbackForm();
            } else {
                showNotification(data.error || 'Failed to submit feedback', 'error');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            showNotification('Failed to submit feedback', 'error');
        }
    });
}

// Reset feedback form
function resetFeedbackForm() {
    document.querySelectorAll('.rating-stars i').forEach(star => {
        star.classList.remove('fas');
        star.classList.add('far');
    });
    document.getElementById('feedbackComment').value = '';
    document.querySelectorAll('input[name="issue"]').forEach(radio => {
        radio.checked = false;
    });
}

// Copy solution
document.getElementById('copyBtn')?.addEventListener('click', () => {
    const solutionText = extractSolutionText();
    navigator.clipboard.writeText(solutionText).then(() => {
        showNotification('Solution copied to clipboard', 'success');
    }).catch(() => {
        showNotification('Failed to copy solution', 'error');
    });
});

// Show/hide loading
function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#50C878' : type === 'error' ? '#FF6B6B' : '#4A90E2'};
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 3000;
        animation: slideIn 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    `;
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Get auth token (placeholder - implement actual auth)
function getAuthToken() {
    return localStorage.getItem('authToken') || '';
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
