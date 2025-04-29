document.addEventListener('DOMContentLoaded', () => {
    const comment = document.getElementById('comment');
    const charCounter = document.getElementById('charCounter');
    const accordion = document.getElementById('feedbackAccordion');

    comment.addEventListener('input', () => {
        const length = comment.value.length;
        charCounter.textContent = `${length}/200 characters`;
    });

    // Dummy feedback
    const feedback = [
        { id: 1, customerId: 1, comment: 'Customer was unhappy with service.', timestamp: '2025-04-24', tag: 'dissatisfied' },
        { id: 2, customerId: 2, comment: 'Support response was delayed.', timestamp: '2025-04-23', tag: 'support_delay' }
    ];

    accordion.innerHTML = feedback.map((f, i) => `
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button ${i === 0 ? '' : 'collapsed'}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${f.id}" aria-expanded="${i === 0}">
                    Customer ${f.customerId} - ${f.timestamp}
                </button>
            </h2>
            <div id="collapse${f.id}" class="accordion-collapse collapse ${i === 0 ? 'show' : ''}">
                <div class="accordion-body">
                    <p><strong>Comment:</strong> ${f.comment}</p>
                    <p><strong>Tag:</strong> ${f.tag || 'None'}</p>
                </div>
            </div>
        </div>
    `).join('');
});