document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('predictionTable');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const exportBtn = document.getElementById('exportBtn');
    let data = [];

    function renderTable(data) {
        tableBody.innerHTML = data.map(row => {
            const percent = (row.probability * 100).toFixed(2);
            const barClass = row.probability > 0.7
                ? 'bg-danger'
                : row.probability > 0.4
                    ? 'bg-warning'
                    : 'bg-success';

            return `
                <tr>
                    <td>${row.id}</td>
                    <td>${row.name}</td>
                    <td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar ${barClass}" role="progressbar"
                                 style="width: ${percent}%;" aria-valuenow="${percent}"
                                 aria-valuemin="0" aria-valuemax="100">${percent}%</div>
                        </div>
                    </td>
                    <td>
                        <span class="badge ${row.label === 'Churn' ? 'bg-danger' : 'bg-success'}">
                            ${row.label}
                        </span>
                    </td>
                    <td>${row.probability > 0.7 ? 'Offer Discount, Free Support' : 'Monitor'}</td>
                </tr>
            `;
        }).join('');
    }

    // ✅ Fetch live data from backend
    loadingOverlay.classList.remove('d-none');
    fetch('/predict')
        .then(res => res.json())
        .then(json => {
            data = json;
            renderTable(data);
            loadingOverlay.classList.add('d-none');
        })
        .catch(err => {
            console.error('Error fetching prediction data:', err);
            loadingOverlay.classList.add('d-none');
        });

    // ✅ Enable column sorting
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const key = th.dataset.sort;
            const sorted = [...data].sort((a, b) => {
                if (typeof a[key] === 'string') {
                    return a[key].localeCompare(b[key]);
                } else {
                    return a[key] - b[key];
                }
            });
            renderTable(sorted);
        });
    });

    // ✅ Export as CSV
    exportBtn.addEventListener('click', () => {
        const csv = 'ID,Name,Probability,Label\n' + data.map(row =>
            `${row.id},${row.name},${row.probability},${row.label}`
        ).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'predictions.csv';
        a.click();
        URL.revokeObjectURL(url);
        validateForm('none'); // Optional toast
    });
});
