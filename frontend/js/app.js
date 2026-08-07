/**
 * Speech & Document Extractor — Frontend Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // ─── DOM Element References ───
    const loadingOverlay = document.getElementById('loading-overlay');
    const toastContainer = document.getElementById('toast-container');
    const providerText = document.getElementById('provider-text');

    // Navigation Tabs
    const tabSpeech = document.getElementById('tab-speech');
    const tabDocument = document.getElementById('tab-document');
    const sectionSpeech = document.getElementById('section-speech');
    const sectionDocument = document.getElementById('section-document');

    // Speech Module Elements
    const modeUpload = document.getElementById('mode-upload');
    const modeMic = document.getElementById('mode-mic');
    const speechUploadArea = document.getElementById('speech-upload-area');
    const speechMicArea = document.getElementById('speech-mic-area');
    
    const speechDropzone = document.getElementById('speech-dropzone');
    const speechFileInput = document.getElementById('speech-file-input');
    const speechFileInfo = document.getElementById('speech-file-info');
    const speechFileName = document.getElementById('speech-file-name');
    const speechFileSize = document.getElementById('speech-file-size');
    const speechFileRemove = document.getElementById('speech-file-remove');
    const speechLanguage = document.getElementById('speech-language');
    const speechSubmitBtn = document.getElementById('speech-submit-btn');

    // Speech Mic Elements
    const micBtn = document.getElementById('mic-btn');
    const micIconOn = document.getElementById('mic-icon-on');
    const micIconOff = document.getElementById('mic-icon-off');
    const micStatus = document.getElementById('mic-status');
    const micTimer = document.getElementById('mic-timer');
    const micLanguage = document.getElementById('mic-language');

    // Speech Result Elements
    const speechResultPlaceholder = document.getElementById('speech-result-placeholder');
    const speechResultContent = document.getElementById('speech-result-content');
    const speechLangBadge = document.getElementById('speech-lang-badge');
    const speechLangName = document.getElementById('speech-lang-name');
    const speechTranscript = document.getElementById('speech-transcript');
    const speechDuration = document.getElementById('speech-duration');
    const speechConfidence = document.getElementById('speech-confidence');
    const speechProvider = document.getElementById('speech-provider');
    const speechSegments = document.getElementById('speech-segments');

    // Document Module Elements
    const docDropzone = document.getElementById('doc-dropzone');
    const docFileInput = document.getElementById('doc-file-input');
    const docFileInfo = document.getElementById('doc-file-info');
    const docFileName = document.getElementById('doc-file-name');
    const docFileSize = document.getElementById('doc-file-size');
    const docFileRemove = document.getElementById('doc-file-remove');
    const docSubmitBtn = document.getElementById('doc-submit-btn');

    // Document Result Elements
    const docResultPlaceholder = document.getElementById('doc-result-placeholder');
    const docResultContent = document.getElementById('doc-result-content');
    const docTypeBadge = document.getElementById('doc-type-badge');
    const docTypeValue = document.getElementById('doc-type-value');
    const docInvalidWarning = document.getElementById('doc-invalid-warning');
    const docMetadataSection = document.getElementById('doc-metadata-section');
    const docResultsSection = document.getElementById('doc-results-section');
    const docResultsTbody = document.getElementById('doc-results-tbody');
    const docNoResults = document.getElementById('doc-no-results');
    const docResultsTable = document.getElementById('doc-results-table');
    
    // Patient Metadata Fields
    const patientName = document.getElementById('patient-name');
    const patientAge = document.getElementById('patient-age');
    const patientSex = document.getElementById('patient-sex');
    const patientId = document.getElementById('patient-id');
    const labName = document.getElementById('lab-name');
    const labDate = document.getElementById('lab-date');
    const labRef = document.getElementById('lab-ref');
    const labDoctor = document.getElementById('lab-doctor');
    const docPages = document.getElementById('doc-pages');
    const docLanguage = document.getElementById('doc-language');
    const docProvider = document.getElementById('doc-provider');
    const docRawOcr = document.getElementById('doc-raw-ocr');

    // State Variables
    let selectedSpeechFile = null;
    let selectedDocFile = null;
    let isRecording = false;
    let mediaRecorder = null;
    let websocket = null;
    let timerInterval = null;
    let recordingSeconds = 0;

    // ─── Fetch System Health on Startup ───
    fetchHealth();

    async function fetchHealth() {
        try {
            const res = await fetch('/api/v1/health');
            if (res.ok) {
                const data = await res.json();
                providerText.textContent = `Speech: ${data.speech_provider} | OCR: ${data.ocr_provider}`;
            } else {
                providerText.textContent = 'Service Ready';
            }
        } catch (e) {
            providerText.textContent = 'Service Ready';
        }
    }

    // ─── Utility Functions ───
    function showLoading(text = 'Processing...') {
        loadingOverlay.querySelector('.loading-text').textContent = text;
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = `toast ${isError ? 'toast-error' : ''}`;
        toast.innerHTML = `
            <span>${isError ? '⚠️' : '✓'}</span>
            <span>${message}</span>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // ─── Navigation Tabs Logic ───
    tabSpeech.addEventListener('click', () => switchTab('speech'));
    tabDocument.addEventListener('click', () => switchTab('document'));

    function switchTab(tab) {
        if (tab === 'speech') {
            tabSpeech.classList.add('active');
            tabDocument.classList.remove('active');
            sectionSpeech.classList.add('active');
            sectionDocument.classList.remove('active');
        } else {
            tabDocument.classList.add('active');
            tabSpeech.classList.remove('active');
            sectionDocument.classList.add('active');
            sectionSpeech.classList.remove('active');
        }
    }

    // ─── Speech Input Mode Toggle ───
    modeUpload.addEventListener('click', () => switchSpeechMode('upload'));
    modeMic.addEventListener('click', () => switchSpeechMode('mic'));

    function switchSpeechMode(mode) {
        if (mode === 'upload') {
            modeUpload.classList.add('active');
            modeMic.classList.remove('active');
            speechUploadArea.classList.remove('hidden');
            speechMicArea.classList.add('hidden');
            if (isRecording) stopRecording();
        } else {
            modeMic.classList.add('active');
            modeUpload.classList.remove('active');
            speechMicArea.classList.remove('hidden');
            speechUploadArea.classList.add('hidden');
        }
    }

    // ─── Speech File Handling ───
    setupDragAndDrop(speechDropzone, speechFileInput, handleSpeechFileSelected);

    speechFileRemove.addEventListener('click', () => {
        selectedSpeechFile = null;
        speechFileInput.value = '';
        speechDropzone.classList.remove('hidden');
        speechFileInfo.classList.add('hidden');
        speechSubmitBtn.disabled = true;
    });

    function handleSpeechFileSelected(file) {
        if (!file) return;
        const validExtensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.wma', '.aac', '.webm'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(ext)) {
            showToast(`Unsupported audio format '${ext}'`, true);
            return;
        }
        if (file.size > 25 * 1024 * 1024) {
            showToast('File exceeds 25 MB limit', true);
            return;
        }
        selectedSpeechFile = file;
        speechFileName.textContent = file.name;
        speechFileSize.textContent = formatBytes(file.size);
        speechDropzone.classList.add('hidden');
        speechFileInfo.classList.remove('hidden');
        speechSubmitBtn.disabled = false;
    }

    // ─── Speech Form Submission ───
    speechSubmitBtn.addEventListener('click', async () => {
        if (!selectedSpeechFile) return;

        showLoading('Transcribing Audio...');
        const formData = new FormData();
        formData.append('file', selectedSpeechFile);
        if (speechLanguage.value) {
            formData.append('language', speechLanguage.value);
        }

        try {
            const res = await fetch('/api/v1/speech/transcribe', {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();
            hideLoading();

            if (res.ok && data.success) {
                renderSpeechResult(data);
                showToast('Transcription completed!');
            } else {
                const errMsg = data.detail?.message || data.message || 'Transcription failed';
                showToast(errMsg, true);
            }
        } catch (e) {
            hideLoading();
            showToast('Network error during transcription', true);
        }
    });

    function renderSpeechResult(data) {
        speechResultPlaceholder.classList.add('hidden');
        speechResultContent.classList.remove('hidden');

        // Detected Language
        const langName = data.detected_language || data.language || 'Detected';
        speechLangName.textContent = langName;

        // Transcript
        speechTranscript.textContent = data.transcript || '(No speech detected)';

        // Metadata
        speechDuration.textContent = data.duration_seconds ? `${data.duration_seconds}s` : '—';
        speechConfidence.textContent = data.language_confidence ? `${Math.round(data.language_confidence * 100)}%` : '—';
        speechProvider.textContent = data.provider || '—';

        // Segments
        speechSegments.innerHTML = '';
        if (data.segments && data.segments.length > 0) {
            data.segments.forEach(seg => {
                const item = document.createElement('div');
                item.style.marginBottom = '0.5rem';
                item.style.fontSize = '0.85rem';
                item.innerHTML = `
                    <span style="color: var(--text-muted); font-family: monospace;">[${seg.start.toFixed(1)}s - ${seg.end.toFixed(1)}s]</span>
                    <span style="margin-left: 0.5rem; color: var(--text-primary);">${seg.text}</span>
                `;
                speechSegments.appendChild(item);
            });
        } else {
            speechSegments.textContent = 'No detailed segment timing available.';
        }
    }

    // ─── Speech Live Microphone WebSocket Streaming ───
    micBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Connect WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/v1/speech/stream`;
            
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                // Send config
                const configMsg = {
                    type: 'config',
                    sample_rate: 16000,
                    language: micLanguage.value || null
                };
                websocket.send(JSON.stringify(configMsg));

                // Clear previous result and show workspace
                speechResultPlaceholder.classList.add('hidden');
                speechResultContent.classList.remove('hidden');
                speechTranscript.textContent = 'Listening to live audio...';
                speechLangName.textContent = micLanguage.value ? micLanguage.value.toUpperCase() : 'Detecting...';
                speechDuration.textContent = 'Live';
                speechConfidence.textContent = '—';
                speechProvider.textContent = 'WebSocket Stream';
                speechSegments.innerHTML = '';

                // Start recording media stream
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
                        event.data.arrayBuffer().then(buffer => {
                            websocket.send(buffer);
                        });
                    }
                };

                mediaRecorder.start(1000); // 1-second chunks
                isRecording = true;
                updateMicUI(true);
                startTimer();
            };

            websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'final' || data.text) {
                        if (speechTranscript.textContent === 'Listening to live audio...') {
                            speechTranscript.textContent = '';
                        }
                        speechTranscript.textContent += (speechTranscript.textContent ? ' ' : '') + data.text;
                        if (data.language) {
                            speechLangName.textContent = data.language;
                        }
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };

            websocket.onerror = (e) => {
                console.error('WebSocket error:', e);
                showToast('WebSocket connection error', true);
                stopRecording();
            };

            websocket.onclose = () => {
                if (isRecording) {
                    stopRecording();
                }
            };

        } catch (e) {
            showToast('Microphone access denied or unsupported', true);
            console.error('Mic access error:', e);
        }
    }

    function stopRecording() {
        isRecording = false;
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ type: 'stop' }));
            websocket.close();
        }
        updateMicUI(false);
        stopTimer();
        showToast('Microphone recording stopped');
    }

    function updateMicUI(recording) {
        if (recording) {
            micBtn.classList.add('recording');
            micIconOn.classList.add('hidden');
            micIconOff.classList.remove('hidden');
            micStatus.textContent = 'Recording live speech...';
            micTimer.classList.remove('hidden');
        } else {
            micBtn.classList.remove('recording');
            micIconOn.classList.remove('hidden');
            micIconOff.classList.add('hidden');
            micStatus.textContent = 'Click to start recording';
            micTimer.classList.add('hidden');
        }
    }

    function startTimer() {
        recordingSeconds = 0;
        micTimer.textContent = '00:00';
        timerInterval = setInterval(() => {
            recordingSeconds++;
            const mins = Math.floor(recordingSeconds / 60).toString().padStart(2, '0');
            const secs = (recordingSeconds % 60).toString().padStart(2, '0');
            micTimer.textContent = `${mins}:${secs}`;
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) clearInterval(timerInterval);
    }

    // ─── Document File Handling ───
    setupDragAndDrop(docDropzone, docFileInput, handleDocFileSelected);

    docFileRemove.addEventListener('click', () => {
        selectedDocFile = null;
        docFileInput.value = '';
        docDropzone.classList.remove('hidden');
        docFileInfo.classList.add('hidden');
        docSubmitBtn.disabled = true;
    });

    function handleDocFileSelected(file) {
        if (!file) return;
        const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.pdf'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(ext)) {
            showToast(`Unsupported document format '${ext}'`, true);
            return;
        }
        if (file.size > 25 * 1024 * 1024) {
            showToast('File exceeds 25 MB limit', true);
            return;
        }
        selectedDocFile = file;
        docFileName.textContent = file.name;
        docFileSize.textContent = formatBytes(file.size);
        docDropzone.classList.add('hidden');
        docFileInfo.classList.remove('hidden');
        docSubmitBtn.disabled = false;
    }

    // ─── Document Form Submission ───
    docSubmitBtn.addEventListener('click', async () => {
        if (!selectedDocFile) return;

        showLoading('Extracting Medical Lab Report...');
        const formData = new FormData();
        formData.append('file', selectedDocFile);

        try {
            const res = await fetch('/api/v1/document/extract', {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();
            hideLoading();

            if (res.ok && data.success) {
                renderDocumentResult(data);
                showToast('Report extraction complete!');
            } else {
                const errMsg = data.detail?.message || data.message || 'Report extraction failed';
                showToast(errMsg, true);
            }
        } catch (e) {
            hideLoading();
            showToast('Network error during report extraction', true);
        }
    });

    function renderDocumentResult(data) {
        docResultPlaceholder.classList.add('hidden');
        docResultContent.classList.remove('hidden');

        const isValidLab = data.is_valid_lab_report;

        // Document Type Badge
        docTypeValue.textContent = data.document_type || (isValidLab ? 'Medical Laboratory Report' : 'Non-Laboratory Document');

        if (!isValidLab) {
            // Case 3: Invalid Laboratory Report
            docInvalidWarning.classList.remove('hidden');
            docMetadataSection.classList.add('hidden');
            docResultsSection.classList.add('hidden');
        } else {
            docInvalidWarning.classList.add('hidden');
            docMetadataSection.classList.remove('hidden');
            docResultsSection.classList.remove('hidden');

            // Patient Info Card
            const p = data.patient_info || {};
            patientName.textContent = p.name || '—';
            patientAge.textContent = p.age || '—';
            patientSex.textContent = p.sex || '—';
            patientId.textContent = p.patient_id || '—';

            // Lab Details Card
            const l = data.lab_metadata || {};
            labName.textContent = l.lab_name || '—';
            labDate.textContent = l.report_date || '—';
            labRef.textContent = l.reference_number || '—';
            labDoctor.textContent = l.referring_doctor || '—';

            // Test Results Table
            docResultsTbody.innerHTML = '';
            if (data.test_results && data.test_results.length > 0) {
                // Case 1: Valid report with test results
                docResultsTable.classList.remove('hidden');
                docNoResults.classList.add('hidden');

                data.test_results.forEach(res => {
                    const tr = document.createElement('tr');
                    
                    let flagHtml = '—';
                    if (res.flag) {
                        const flagClass = `flag-${res.flag.toLowerCase()}`;
                        flagHtml = `<span class="flag-badge ${flagClass}">${res.flag}</span>`;
                    }

                    tr.innerHTML = `
                        <td style="font-weight: 600;">${res.test_name}</td>
                        <td>${res.value || '—'}</td>
                        <td style="color: var(--text-muted);">${res.unit || '—'}</td>
                        <td style="color: var(--text-muted);">${res.reference_range || '—'}</td>
                        <td>${flagHtml}</td>
                    `;
                    docResultsTbody.appendChild(tr);
                });
            } else {
                // Case 2: Valid report with no test results detected
                docResultsTable.classList.add('hidden');
                docNoResults.classList.remove('hidden');
            }
        }

        // Provider Info
        docPages.textContent = data.page_count || 1;
        docLanguage.textContent = data.language || 'English';
        docProvider.textContent = data.provider || '—';

        // Raw OCR Output
        docRawOcr.textContent = (data.raw_ocr_lines && data.raw_ocr_lines.length > 0) 
            ? data.raw_ocr_lines.join('\n') 
            : 'No raw OCR lines recorded.';
    }

    // ─── Drag and Drop Helper ───
    function setupDragAndDrop(dropzone, fileInput, onFileSelected) {
        dropzone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                onFileSelected(e.target.files[0]);
            }
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                onFileSelected(files[0]);
            }
        });
    }
});
