// frontend/upload.js

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const csvFile = document.getElementById('csvFile');
    const errorMsg = document.getElementById('errorMsg');
    const progressBar = document.getElementById('progressBar');
    const previewTable = document.getElementById('previewTable');
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');

    dropZone.addEventListener('click', () => csvFile.click());
    dropZone.addEventListener('dragover', (e) => e.preventDefault());
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        csvFile.files = e.dataTransfer.files;
        handleFile();
    });
    csvFile.addEventListener('change', handleFile);

    async function handleFile() {
        const file = csvFile.files[0];
        if (!file || !file.name.endsWith('.csv')) {
            errorMsg.textContent = 'Please upload a valid CSV file.';
            errorMsg.classList.remove('d-none');
            return;
        }
        errorMsg.classList.add('d-none');
        progressBar.classList.remove('d-none');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://127.0.0.1:5000/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                console.log('✅ Upload successful!');
                const jsonResponse = await response.json();
                console.log('Server Response:', jsonResponse.message);

                // Optionally preview uploaded CSV
                previewCSV(file);

                setTimeout(() => { progressBar.classList.add('d-none'); }, 1000);
            } else {
                console.error('❌ Upload failed.');
                errorMsg.textContent = 'Upload failed. Please try again.';
                errorMsg.classList.remove('d-none');
                progressBar.classList.add('d-none');
            }
        } catch (error) {
            console.error('❌ Error uploading file:', error);
            errorMsg.textContent = 'Server error. Please try later.';
            errorMsg.classList.remove('d-none');
            progressBar.classList.add('d-none');
        }
    }

    function previewCSV(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            const rows = text.split('\n').map(row => row.split(','));
            const headers = rows[0];
            const body = rows.slice(1);

            tableHeader.innerHTML = headers.map(header => `<th>${header.trim()}</th>`).join('');
            tableBody.innerHTML = body.map(row => `<tr>${row.map(cell => `<td>${cell.trim()}</td>`).join('')}</tr>`).join('');

            previewTable.classList.remove('d-none');
        };
        reader.readAsText(file);
    }
});
