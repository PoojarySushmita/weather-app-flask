document.addEventListener("DOMContentLoaded", function () {

    // ===== WEATHER API CHARTS =====
    if (window.trendsData && window.trendsData.dates && window.trendsData.dates.length > 0) {

        const dates = window.trendsData.dates;

        // Temperature Chart
        if (document.getElementById("tempChart")) {
            new Chart(document.getElementById("tempChart"), {
                type: "line",
                data: {
                    labels: dates,
                    datasets: [{
                        label: "Temperature (°C)",
                        data: window.trendsData.temps,
                        borderColor: "red",
                        backgroundColor: "rgba(255,0,0,0.2)",
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    animation: {
                        duration: 2000
                    }
                }
            });
        }

        // Wind Chart
        if (document.getElementById("windChart")) {
            new Chart(document.getElementById("windChart"), {
                type: "line",
                data: {
                    labels: dates,
                    datasets: [{
                        label: "Wind Speed",
                        data: window.trendsData.winds,
                        borderColor: "blue",
                        backgroundColor: "rgba(0,0,255,0.2)",
                        tension: 0.4
                    }]
                }
            });
        }

        // Rain Chart
        if (document.getElementById("rainChart")) {
            new Chart(document.getElementById("rainChart"), {
                type: "bar",
                data: {
                    labels: dates,
                    datasets: [{
                        label: "Rain %",
                        data: window.trendsData.precip,
                        backgroundColor: "rgba(0,200,150,0.6)"
                    }]
                }
            });
        }

    } else {
        console.log("No API trend data available yet");
    }

    // ===== DATABASE CHARTS =====

    // Temperature History
    if (window.historyData && window.historyData.dates && window.historyData.dates.length > 0) {
        new Chart(document.getElementById("historyChart"), {
            type: "line",
            data: {
                labels: window.historyData.dates,
                datasets: [{
                    label: "Temperature History",
                    data: window.historyData.temps,
                    borderColor: "orange",
                    backgroundColor: "rgba(255,165,0,0.2)",
                    tension: 0.4
                }]
            }
        });
    }

    // Most Searched Cities
    if (window.cityData && window.cityData.cities && window.cityData.cities.length > 0) {
        new Chart(document.getElementById("cityChart"), {
            type: "bar",
            data: {
                labels: window.cityData.cities,
                datasets: [{
                    label: "Search Count",
                    data: window.cityData.counts,
                    backgroundColor: "rgba(100,200,255,0.7)"
                }]
            }
        });
    }

});