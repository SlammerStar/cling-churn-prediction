const app = {
    userId: null,
    state: {
        stats: null,
        history: [],
        charts: {}
    },

    init() {
        this.bindEvents();
        this.checkApiHealth();
        this.loadStats();
    },

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-links li').forEach(li => {
            li.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-links li').forEach(n => n.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.navigateTo(e.currentTarget.dataset.page);
            });
        });

        // Single Predict Form
        const predictForm = document.getElementById('predict-form');
        if(predictForm) {
            predictForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handlePredict();
            });
        }

        // Batch Upload
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-upload');
        const btnUpload = document.getElementById('btn-upload');
        let selectedFile = null;

        if(uploadZone) {
            uploadZone.addEventListener('click', () => fileInput.click());
            uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.style.borderColor = 'var(--accent)'; });
            uploadZone.addEventListener('dragleave', () => { uploadZone.style.borderColor = 'var(--border-glass)'; });
            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = 'var(--border-glass)';
                if(e.dataTransfer.files.length) {
                    selectedFile = e.dataTransfer.files[0];
                    uploadZone.querySelector('h4').textContent = selectedFile.name;
                    btnUpload.disabled = false;
                }
            });

            fileInput.addEventListener('change', (e) => {
                if(e.target.files.length) {
                    selectedFile = e.target.files[0];
                    uploadZone.querySelector('h4').textContent = selectedFile.name;
                    btnUpload.disabled = false;
                }
            });

            btnUpload.addEventListener('click', () => {
                if(selectedFile) this.handleBatchUpload(selectedFile);
            });
        }
    },

    navigateTo(pageId) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`page-${pageId}`).classList.add('active');
        
        const titles = {
            'landing': 'Welcome to Cling',
            'dashboard': 'Analytics Dashboard',
            'predict': 'Single Customer Prediction',
            'batch': 'Batch Prediction Analyzer',
            'insights': 'Model Insights & Evaluation',
            'about': 'About Architecture'
        };
        const subtitles = {
            'landing': 'AI-Powered Customer Retention',
            'dashboard': 'Overview of churn metrics and history',
            'predict': 'Get instant churn risk for a specific customer',
            'batch': 'Process thousands of customers at once',
            'insights': 'Deep dive into model performance',
            'about': 'How it works under the hood'
        };

        document.getElementById('page-title').textContent = titles[pageId] || 'Cling';
        document.getElementById('page-subtitle').textContent = subtitles[pageId] || '';
    },

    showLoader(show = true) {
        document.getElementById('loader').classList.toggle('hidden', !show);
    },

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => toast.classList.remove('show'), 3000);
    },

    async checkApiHealth() {
        const statusText = document.getElementById('api-status-text');
        const statusDot = document.querySelector('.status-dot');
        try {
            const res = await fetch('/api/health');
            if (res.ok) {
                statusText.textContent = 'API Online';
                statusText.style.color = 'var(--success)';
                statusDot.style.background = 'var(--success)';
            } else {
                throw new Error('Not OK');
            }
        } catch (e) {
            statusText.textContent = 'API Offline';
            statusText.style.color = 'var(--danger)';
            statusDot.style.background = 'var(--danger)';
        }
    },

    async loadStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();
            this.state.stats = data;
            
            // Dashboard values
            document.getElementById('dash-best-model').textContent = data.best_model;
            document.getElementById('dash-auc').textContent = data.roc_auc.toFixed(4);
            document.getElementById('dash-samples').textContent = data.n_samples;

            // Render Charts
            this.renderGlobalImportanceChart(data.feature_importances);
            this.renderModelCompareTable(data.all_models);
            this.renderConfusionMatrix(data.all_models.find(m => m.model === data.best_model).confusion_matrix);
            // Render pseudo-ROC using generic curve for visual purposes
            this.renderRocChart();

        } catch (e) {
            console.error('Failed to load stats', e);
        }
    },

    async handlePredict() {
        // Collect form data
        const data = {
            tenure: parseFloat(document.getElementById('p-tenure').value),
            MonthlyCharges: parseFloat(document.getElementById('p-monthly').value),
            TotalCharges: parseFloat(document.getElementById('p-total').value),
            Contract: document.getElementById('p-contract').value,
            InternetService: document.getElementById('p-internet').value,
            SeniorCitizen: parseInt(document.getElementById('p-senior').value),
            // Default other fields for the demo
            gender: "Male", Partner: "No", Dependents: "No", PhoneService: "Yes",
            MultipleLines: "No", OnlineSecurity: "No", OnlineBackup: "No",
            DeviceProtection: "No", TechSupport: "No", StreamingTV: "No",
            StreamingMovies: "No", PaymentMethod: "Electronic check", PaperlessBilling: "Yes"
        };

        this.showLoader(true);
        try {
            const headers = { 'Content-Type': 'application/json' };
            if (this.userId) headers['X-User-Id'] = this.userId;

            const res = await fetch('/api/predict', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });
            const result = await res.json();
            
            if (!res.ok) throw new Error(result.error || 'Prediction failed');

            this.updatePredictUI(result);
            this.addToHistory(data, result);
            this.showToast('Prediction generated successfully!');
        } catch (e) {
            this.showToast(e.message, 'error');
        } finally {
            this.showLoader(false);
        }
    },

    updatePredictUI(result) {
        document.getElementById('predict-result-empty').classList.add('hidden');
        document.getElementById('predict-result-content').classList.remove('hidden');

        document.getElementById('res-prob').textContent = `${result.probability}%`;
        const riskBadge = document.getElementById('res-risk');
        riskBadge.textContent = `${result.risk_level} Risk`;
        
        let color = 'var(--success)';
        if(result.risk_level === 'Medium') color = 'var(--warning)';
        if(result.risk_level === 'High') color = 'var(--danger)';
        
        riskBadge.style.backgroundColor = `${color}22`;
        riskBadge.style.color = color;

        // Animate Gauge
        const gaugeVal = document.getElementById('gauge-val');
        gaugeVal.style.stroke = color;
        const offset = 125.6 - (125.6 * (result.probability / 100));
        setTimeout(() => {
            gaugeVal.style.strokeDashoffset = offset;
        }, 100);

        // SHAP Waterfall Simulation
        const shapContainer = document.getElementById('shap-waterfall');
        shapContainer.innerHTML = '';
        
        const topFeats = result.top_features;
        // Normalize importances for visual bar width
        const maxImp = Math.max(...topFeats.map(f => f.importance));
        
        topFeats.forEach((feat, idx) => {
            const pct = (feat.importance / maxImp) * 100;
            const isPos = idx % 2 === 0; // Simulate positive/negative impact
            const barColor = isPos ? 'var(--danger)' : 'var(--success)';
            
            const div = document.createElement('div');
            div.className = 'shap-bar';
            div.innerHTML = `
                <div class="shap-label" title="${feat.feature}">${feat.feature}</div>
                <div class="shap-track">
                    <div class="shap-fill" style="width: ${pct}%; background: ${barColor}; ${isPos ? 'left:0;' : 'right:0;'}"></div>
                </div>
            `;
            shapContainer.appendChild(div);
        });
    },

    addToHistory(data, result) {
        this.state.history.unshift({ data, result, time: new Date() });
        if(this.state.history.length > 5) this.state.history.pop();
        
        const tbody = document.querySelector('#history-table tbody');
        tbody.innerHTML = '';
        
        document.getElementById('dash-total-preds').textContent = this.state.history.length;

        this.state.history.forEach(item => {
            let color = 'var(--success)';
            if(item.result.risk_level === 'Medium') color = 'var(--warning)';
            if(item.result.risk_level === 'High') color = 'var(--danger)';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="color:var(--text-secondary)">${item.time.toLocaleTimeString()}</td>
                <td>${item.data.tenure}m</td>
                <td>$${item.data.MonthlyCharges}</td>
                <td><span style="color:${color}; font-weight:600">${item.result.risk_level}</span></td>
                <td>${item.result.probability}%</td>
            `;
            tbody.appendChild(tr);
        });
    },

    async handleBatchUpload(file) {
        this.showLoader(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const headers = {};
            if (this.userId) headers['X-User-Id'] = this.userId;

            const res = await fetch('/api/predict/batch', {
                method: 'POST',
                headers: headers,
                body: formData
            });
            const result = await res.json();
            
            if(!res.ok) throw new Error(result.error || 'Batch processing failed');

            document.getElementById('batch-results').classList.remove('hidden');
            document.getElementById('batch-total').textContent = result.total;
            document.getElementById('batch-high').textContent = result.risk_distribution.High || 0;
            document.getElementById('batch-avg').textContent = `${result.avg_churn_probability}%`;
            
            this.showToast(`Processed ${result.total} records successfully!`);
        } catch (e) {
            this.showToast(e.message, 'error');
        } finally {
            this.showLoader(false);
        }
    },

    renderGlobalImportanceChart(importances) {
        const ctx = document.getElementById('chart-global-importance').getContext('2d');
        const labels = importances.map(f => f.feature);
        const data = importances.map(f => f.importance);

        if(this.state.charts.globalImp) this.state.charts.globalImp.destroy();

        this.state.charts.globalImp = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Feature Importance',
                    data,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
    },

    renderModelCompareTable(models) {
        const tbody = document.querySelector('#model-compare-table tbody');
        tbody.innerHTML = '';
        models.forEach(m => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${m.model}</strong></td>
                <td>${m.roc_auc.toFixed(4)}</td>
                <td>${m.cv_auc_mean.toFixed(4)}</td>
                <td>${m.f1.toFixed(4)}</td>
                <td>${m.accuracy.toFixed(4)}</td>
            `;
            tbody.appendChild(tr);
        });
    },

    renderConfusionMatrix(matrix) {
        const cm = document.getElementById('confusion-matrix');
        if(!cm || !matrix) return;
        
        cm.innerHTML = `
            <div></div>
            <div class="cm-header">Pred: Stay (0)</div>
            <div class="cm-header">Pred: Churn (1)</div>
            
            <div class="cm-header" style="text-align:right; padding-right:10px;">Actual: Stay (0)</div>
            <div class="cm-cell" style="background: rgba(16, 185, 129, 0.2); color: var(--success)">TN: ${matrix[0][0]}</div>
            <div class="cm-cell" style="background: rgba(239, 68, 68, 0.2); color: var(--danger)">FP: ${matrix[0][1]}</div>
            
            <div class="cm-header" style="text-align:right; padding-right:10px;">Actual: Churn (1)</div>
            <div class="cm-cell" style="background: rgba(239, 68, 68, 0.2); color: var(--danger)">FN: ${matrix[1][0]}</div>
            <div class="cm-cell" style="background: rgba(16, 185, 129, 0.2); color: var(--success)">TP: ${matrix[1][1]}</div>
        `;
    },

    renderRocChart() {
        const ctx = document.getElementById('chart-roc').getContext('2d');
        if(this.state.charts.roc) this.state.charts.roc.destroy();

        // Synthetic ROC curve for visual placeholder
        const fpr = [0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1];
        const tpr = [0, 0.4, 0.6, 0.8, 0.9, 0.95, 0.98, 1];

        this.state.charts.roc = new Chart(ctx, {
            type: 'line',
            data: {
                labels: fpr,
                datasets: [
                    {
                        label: 'ROC Curve',
                        data: tpr,
                        borderColor: 'var(--accent)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Random Model',
                        data: fpr,
                        borderColor: 'var(--text-secondary)',
                        borderDash: [5, 5],
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'False Positive Rate', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { title: { display: true, text: 'True Positive Rate', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    },

    async loadHistory() {
        if (!this.userId) return;
        try {
            const res = await fetch('/api/history?limit=10', {
                headers: { 'X-User-Id': this.userId }
            });
            if (!res.ok) return;
            const result = await res.json();
            
            const tbody = document.querySelector('#history-table tbody');
            tbody.innerHTML = '';
            
            if (result.history && result.history.length > 0) {
                document.getElementById('dash-total-preds').textContent = result.history.length;
                
                result.history.forEach(item => {
                    const time = new Date(item.timestamp).toLocaleDateString();
                    let color = 'var(--success)';
                    if(item.risk_level === 'Medium') color = 'var(--warning)';
                    if(item.risk_level === 'High') color = 'var(--danger)';

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="color:var(--text-secondary)">${time}</td>
                        <td>${item.tenure}m</td>
                        <td>$${item.monthly_charges}</td>
                        <td><span style="color:${color}; font-weight:600">${item.risk_level}</span></td>
                        <td>${item.probability}%</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        } catch (e) {
            console.error('Failed to load history', e);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
