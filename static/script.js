document.addEventListener("DOMContentLoaded", function () {
    const locationForm = document.getElementById("locationForm");

    // ================= SINGLE CITY GRAPH =================
    if (window.weatherChartData) {
        const ctx = document.getElementById("weatherChart").getContext("2d");

        new Chart(ctx, {
            data: {
                labels: window.weatherChartData.hours,
                datasets: [
                    {
                        type: 'line',
                        label: "Temperature (°C)",
                        data: window.weatherChartData.temps,
                        borderColor: "rgba(255, 99, 132, 1)",
                        backgroundColor: "rgba(255, 99, 132, 0.2)",
                        yAxisID: 'yTemp',
                        tension: 0.4,
                        borderWidth: 2
                    },
                    {
                        type: 'line',
                        label: "Wind (m/s)",
                        data: window.weatherChartData.winds,
                        borderColor: "rgba(54, 162, 235, 1)",
                        backgroundColor: "rgba(54, 162, 235, 0.2)",
                        yAxisID: 'yWind',
                        tension: 0.4,
                        borderWidth: 2
                    },
                    {
                        type: 'bar',
                        label: "Precipitation (%)",
                        data: window.weatherChartData.precip,
                        backgroundColor: "rgba(75, 192, 192, 0.5)",
                        yAxisID: 'yPrecip'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                stacked: false,
                scales: {
                    yTemp: {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Temperature (°C)' }
                    },
                    yWind: {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Wind (m/s)' },
                        grid: { drawOnChartArea: false }
                    },
                    yPrecip: {
                        type: 'linear',
                        position: 'right',
                        offset: true,
                        title: { display: true, text: 'Precipitation (%)' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    // ================= AUTO LOAD LOCATION =================
    if (locationForm && !locationLoaded && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                document.getElementById("lat").value = position.coords.latitude;
                document.getElementById("lon").value = position.coords.longitude;
                locationForm.submit(); // submit only once
            },
            function (error) {
                console.log("Geolocation unavailable or denied. Showing default city.");
            }
        );
    }

    // ================= LOCATION BUTTON =================
    window.getLocation = function () {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    document.getElementById("lat").value = position.coords.latitude;
                    document.getElementById("lon").value = position.coords.longitude;
                    locationForm.submit();
                },
                function (error) {
                    alert("Could not get your location. Please allow location access.");
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }
    };

    // ================= COMPARE CITY GRAPH =================
    if (window.weatherCompareData) {
        const ctx2 = document.getElementById("weatherCompareChart");
        if (ctx2) {
            new Chart(ctx2, {
                type: "line",
                data: {
                    labels: window.weatherCompareData.hours,
                    datasets: [
                        {
                            label: window.weatherCompareData.city1 + " Temp",
                            data: window.weatherCompareData.temps1,
                            borderWidth: 2,
                            tension: 0.4
                        },
                        {
                            label: window.weatherCompareData.city2 + " Temp",
                            data: window.weatherCompareData.temps2,
                            borderWidth: 2,
                            tension: 0.4
                        },
                        {
                            label: window.weatherCompareData.city1 + " Wind",
                            data: window.weatherCompareData.winds1,
                            borderWidth: 2,
                            tension: 0.4
                        },
                        {
                            label: window.weatherCompareData.city2 + " Wind",
                            data: window.weatherCompareData.winds2,
                            borderWidth: 2,
                            tension: 0.4
                        },
                        {
                            label: window.weatherCompareData.city1 + " Rain %",
                            data: window.weatherCompareData.precip1,
                            borderWidth: 2,
                            tension: 0.4
                        },
                        {
                            label: window.weatherCompareData.city2 + " Rain %",
                            data: window.weatherCompareData.precip2,
                            borderWidth: 2,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true
                }
            });
        }
    }

    // ================= BACKGROUND CAROUSEL =================
    let slides = document.querySelectorAll('.slide');
    if (slides.length > 0) {
        let currentIndex = 0;
        function changeSlide() {
            slides[currentIndex].classList.remove('active');
            currentIndex = (currentIndex + 1) % slides.length;
            slides[currentIndex].classList.add('active');
        }
        setInterval(changeSlide, 4000);
    }

    // ================= ENTER KEY SUBMIT =================
    const forms = document.querySelectorAll("form");
    forms.forEach(function (form) {
        const textInputs = form.querySelectorAll("input[type='text']");
        textInputs.forEach(function (input) {
            input.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    form.submit();
                }
            });
        });
    });

    // ================= SORT HISTORY TABLE =================
    const table = document.querySelector("table");
    if (table) {
        const headers = table.querySelectorAll("th");
        const tbody = table.querySelector("tbody");
        headers.forEach(function (header, index) {
            header.addEventListener("click", function () {
                const rows = Array.from(tbody.querySelectorAll("tr"));
                const isAsc = header.classList.contains("asc");
                rows.sort(function (a, b) {
                    const aText = a.children[index].textContent;
                    const bText = b.children[index].textContent;
                    if (!isNaN(parseFloat(aText))) {
                        return isAsc
                            ? parseFloat(aText) - parseFloat(bText)
                            : parseFloat(bText) - parseFloat(aText);
                    }
                    return isAsc
                        ? aText.localeCompare(bText)
                        : bText.localeCompare(aText);
                });
                tbody.innerHTML = "";
                rows.forEach(row => tbody.appendChild(row));
                headers.forEach(h => h.classList.remove("asc", "desc"));
                header.classList.add(isAsc ? "desc" : "asc");
            });
        });
    }
});
