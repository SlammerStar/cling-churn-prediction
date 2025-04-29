document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('actionForm');
    const tableBody = document.querySelector('#actionTable tbody');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const customer = document.getElementById('customer').value;
        const action = document.getElementById('action').value;

        const res = await fetch('/track_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ customer, action })
        });

        const result = await res.json();
        if (res.ok) {
            form.reset();
            loadActions(); // Refresh table
        } else {
            alert(result.error || 'Error submitting action');
        }
    });

    async function loadActions() {
        const res = await fetch('/get_actions');
        const actions = await res.json();
        tableBody.innerHTML = actions.map(row => `
            <tr>
                <td>${row.user}</td>
                <td>${row.customer}</td>
                <td>${row.action}</td>
                <td>${new Date(row.timestamp).toLocaleString()}</td>
            </tr>
        `).join('');
    }

    loadActions(); // Initial load
});
