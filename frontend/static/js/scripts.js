console.log('scripts.js loaded');

// Dark Mode Toggle
document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('darkModeToggle');
    const sunIcon = toggleButton.querySelector('.sun-icon');
    const moonIcon = toggleButton.querySelector('.moon-icon');

    if (!toggleButton) {
        console.error('Dark mode toggle not found');
        return;
    }

    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        sunIcon.classList.add('d-none');
        moonIcon.classList.remove('d-none');
    }

    toggleButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        sunIcon.classList.toggle('d-none');
        moonIcon.classList.toggle('d-none');
        console.log('Theme:', isDark ? 'dark' : 'light');
    });
});

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error('Form not found:', formId);
        return false;
    }

    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });

    if (isValid) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-success border-0 position-fixed bottom-0 end-0 m-3';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">Action completed successfully!</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.append(toast);
        new bootstrap.Toast(toast).show();
    }

    return isValid;
}