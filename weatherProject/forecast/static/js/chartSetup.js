// Initialize Chart.js with sample forecast data
document.addEventListener("DOMContentLoaded", () => {
    const chartElement = document.getElementById("chart");
    if (!chartElement) {
        console.error("Chart element not found");
        return;
    }

    const ctx = chartElement.getContext("2d");

    // Create gradient for the line fill
    const gradient = ctx.createLinearGradient(0, 0, 0, chartElement.height);
    gradient.addColorStop(0, "rgba(74, 144, 226, 0.3)");
    gradient.addColorStop(1, "rgba(74, 144, 226, 0)");

    // Select forecast items
    // Prefer data provided by the server via data attributes on the canvas
    let times = [];
    let temps = [];
    let actualTemps = [];
    let predTemps = [];

    try {
        const ds = chartElement.dataset;
        if (ds.times && ds.temps) {
            times = JSON.parse(ds.times);
            temps = JSON.parse(ds.temps);
            if (ds.actualTemps) actualTemps = JSON.parse(ds.actualTemps);
            if (ds.predTemps) predTemps = JSON.parse(ds.predTemps);
        }
    } catch (e) {
        console.warn('Failed to parse dataset on canvas, falling back to DOM parse', e);
    }

    // Fallback: parse from DOM nodes if dataset not present or empty
    if (!times.length || !temps.length) {
        const forecastItems = document.querySelectorAll("ul.forecast-week li");
        forecastItems.forEach(item => {
            const time = item.querySelector(".forecast-day")?.textContent?.trim();
            let tempText = item.querySelector(".forecast-temp")?.textContent || "";
            tempText = tempText.replace(/[^0-9\-\.]/g, '');
            const temp = parseFloat(tempText);
            let humText = item.querySelector(".forecast-hum")?.textContent || "";
            humText = (humText.match(/([0-9]+(\.[0-9]+)?)/) || [null,null])[1];
            const hum = humText ? parseFloat(humText) : null;

            if (time && !isNaN(temp)) {
                times.push(time);
                temps.push(temp);
                if (hum !== null && !isNaN(hum)) hums.push(hum);
            }
        });
    }

    if (temps.length === 0 || times.length === 0) {
        console.error("No forecast data found");
        return;
    }

    // If a previous chart instance exists, destroy it to avoid duplicates
    if (window._forecastChart instanceof Chart) {
        try { window._forecastChart.destroy(); } catch (e) { /* ignore */ }
        window._forecastChart = null;
    }

    // Build datasets; temperature uses left axis, humidity uses right axis (if available)
    const datasets = [];

    // Actual temps (solid blue)
    if (actualTemps && actualTemps.length) {
        datasets.push({
            label: "Actual Temp (°C)",
            data: actualTemps,
            borderColor: "#4A90E2",
            backgroundColor: 'rgba(74,144,226,0.12)',
            borderWidth: 2,
            tension: 0.35,
            pointRadius: 3,
            fill: false,
            spanGaps: true,
            yAxisID: 'y'
        });
    }

    // Predicted temps (dashed amber)
    if (predTemps && predTemps.length) {
        datasets.push({
            label: "Predicted Temp (°C)",
            data: predTemps,
            borderColor: "#F5C542",
            backgroundColor: 'rgba(245,197,66,0.10)',
            borderWidth: 2,
            borderDash: [6, 6],
            tension: 0.35,
            pointRadius: 3,
            fill: false,
            spanGaps: true,
            yAxisID: 'y'
        });
    }

    // Fallback: legacy temps if provided (keep backwards compatibility)
    if ((!actualTemps || !actualTemps.length) && (!predTemps || !predTemps.length) && temps && temps.length) {
        datasets.push({
            label: "Temperature (°C)",
            data: temps,
            borderColor: "#4A90E2",
            backgroundColor: gradient,
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 3,
            fill: true,
            yAxisID: 'y'
        });
    }

    // Humidity removed from the chart per request

    // Create Chart.js line chart
    window._forecastChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: times,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: { 
                    labels: {
                        color: "#ffffff",
                        font: { weight: "bold" }
                    },
                    position: "top"
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    type: "linear",
                    position: "left",
                    title: {
                        display: true,
                        text: "Temperature (°C)",
                        color: "#ffffff"
                    },
                    ticks: {
                        color: "#ffffff",
                        font: { weight: "bold" }
                    },
                    grid: { color: "rgba(255,255,255,0.2)" }
                },
                // No secondary y-axis (humidity removed)
                x: {
                    ticks: { color: "#ffffff", font: { weight: "bold" } },
                    grid: { color: "rgba(255,255,255,0.1)" }
                }
            },
            animation: { duration: 1000 },
            interaction: { mode: 'index', intersect: false }
        }
    });
});
