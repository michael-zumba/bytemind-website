// Tab Switching
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

document.addEventListener('DOMContentLoaded', () => {
    
    // --- TEFI Data ---
    Papa.parse("data/tefi_raw.csv", {
        download: true,
        header: true,
        complete: function(results) {
            const data = results.data.filter(row => row.Country); // Filter empty rows
            
            // Sort by TEFI Score
            data.sort((a, b) => parseFloat(a["TEFI Score (0-100)"]) - parseFloat(b["TEFI Score (0-100)"]));
            
            // Render Chart
            const countries = data.map(row => row.Country);
            const scores = data.map(row => parseFloat(row["TEFI Score (0-100)"]));
            
            const trace = {
                x: countries,
                y: scores,
                type: 'bar',
                text: scores,
                textposition: 'auto',
                marker: {
                    color: scores,
                    colorscale: [
                        [0, '#E8EDF6'],
                        [0.33, '#B7C6E5'],
                        [0.66, '#6E8ECC'],
                        [1, '#0B3D91']
                    ],
                    showscale: false
                }
            };
            
            const layout = {
                title: 'TEFI 2026: Tax & Compliance Friction by Country',
                font: { family: "Inter, sans-serif", size: 12, color: "#1F2937" },
                xaxis: { showgrid: false },
                yaxis: { showgrid: true, gridcolor: "#E8EDF6", title: "Friction Score (Lower is Better)" },
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                autosize: true
            };
            
            Plotly.newPlot('tefi-chart', [trace], layout, {displayModeBar: false, responsive: true});
            
            // Render Table
            renderTable('tefi-table', data, ["Country", "Corporate Tax Rate", "Compliance Hours", "TEFI Score (0-100)"]);
        }
    });

    // --- SME Resilience Data ---
    
    // Score
    fetch('data/nz_sme_score.txt')
        .then(response => response.text())
        .then(score => {
            const scoreEl = document.getElementById('sme-score');
            if (scoreEl) scoreEl.textContent = `${score.trim()} / 100`;
        })
        .catch(err => console.error("SME Score missing", err));

    // Chart & Table
    Papa.parse("data/nz_sme_resilience.csv", {
        download: true,
        header: true,
        complete: function(results) {
            const data = results.data.filter(row => row.Metric);
            
            // Render Chart (Horizontal Bar)
            const metrics = data.map(row => row.Metric);
            const values = data.map(row => parseFloat(row["Value (%)"]));
            
            const trace = {
                x: values,
                y: metrics,
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: values,
                    colorscale: [
                        [0, '#E8EDF6'],
                        [1, '#0B3D91']
                    ],
                    showscale: false
                }
            };
            
            const layout = {
                xaxis: { title: 'Change (%)', showgrid: true, gridcolor: "#E8EDF6" },
                yaxis: { automargin: true },
                font: { family: "Inter, sans-serif", size: 12, color: "#1F2937" },
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                autosize: true,
                margin: { l: 150 }
            };
            
            Plotly.newPlot('sme-chart', [trace], layout, {displayModeBar: false, responsive: true});
            
            // Render Table
            renderTable('sme-table', data, ["Metric", "Value (%)", "Source", "Impact on Resilience"]);
        }
    });

    function renderTable(containerId, data, columns) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let html = '<table><thead><tr>';
        columns.forEach(col => html += `<th>${col}</th>`);
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => html += `<td>${row[col] || ''}</td>`);
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    }

});
