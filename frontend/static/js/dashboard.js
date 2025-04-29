document.addEventListener('DOMContentLoaded', () => {
    const churnChart = document.getElementById('churnChart');
    const churnRate = document.getElementById('churnRate');
    const contractFilter = document.getElementById('contractFilter');
    const tenureSlider = document.getElementById('tenureSlider');
    const tenureValue = document.getElementById('tenureValue');
    const resetFilters = document.getElementById('resetFilters');

    // Animate KPI
    let rate = 0;
    const targetRate = 42;
    const interval = setInterval(() => {
        if (rate >= targetRate) clearInterval(interval);
        churnRate.textContent = `${rate++}%`;
    }, 50);

    // Dummy data
    let data = [
        { contract: 'Month-to-month', churn: 60, noChurn: 40, tenure: 12, region: 'North' },
        { contract: 'One year', churn: 20, noChurn: 80, tenure: 24, region: 'South' },
        { contract: 'Two year', churn: 10, noChurn: 90, tenure: 36, region: 'North' },
    ];

    function renderChart(filteredData) {
        churnChart.classList.add('skeleton');
        setTimeout(() => {
            churnChart.classList.remove('skeleton');
            Plotly.newPlot(churnChart, [{
                x: filteredData.map(d => d.contract),
                y: filteredData.map(d => d.churn),
                type: 'bar',
                name: 'Churn',
                marker: { color: '#0476D9' }
            }, {
                x: filteredData.map(d => d.contract),
                y: filteredData.map(d => d.noChurn),
                type: 'bar',
                name: 'No Churn',
                marker: { color: '#0487D9' }
            }], {
                barmode: 'stack',
                title: 'Churn by Contract Type',
                xaxis: { title: 'Contract Type' },
                yaxis: { title: 'Count' }
            });
        }, 1000);
    }

    function applyFilters() {
        const contract = contractFilter.value;
        const tenure = parseInt(tenureSlider.value);
        const regions = Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);

        const filtered = data.filter(d => (
            (contract === 'all' || d.contract === contract) &&
            (tenure === 0 || d.tenure <= tenure) &&
            (regions.length === 0 || regions.includes(d.region))
        ));
        renderChart(filtered);
    }

    contractFilter.addEventListener('change', applyFilters);
    tenureSlider.addEventListener('input', () => {
        tenureValue.textContent = tenureSlider.value;
        applyFilters();
    });
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.addEventListener('change', applyFilters));
    resetFilters.addEventListener('click', () => {
        contractFilter.value = 'all';
        tenureSlider.value = 0;
        tenureValue.textContent = '0';
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        applyFilters();
    });

    renderChart(data);
});