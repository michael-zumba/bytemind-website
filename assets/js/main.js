document.addEventListener('DOMContentLoaded', () => {
    
    // --- Mobile Menu Toggle ---
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuBtn.classList.toggle('open');
        });
    }

    // --- TEFI Chart Preview (Home Page) ---
    const tefiChartDiv = document.getElementById('tefi-chart-preview');
    if (tefiChartDiv) {
        Papa.parse("data/tefi_raw.csv", {
            download: true,
            header: true,
            complete: function(results) {
                const data = results.data;
                // Sort by TEFI Score
                data.sort((a, b) => parseFloat(a["TEFI Score (0-100)"]) - parseFloat(b["TEFI Score (0-100)"]));
                
                const countries = data.map(row => row.Country);
                const scores = data.map(row => parseFloat(row["TEFI Score (0-100)"]));
                
                const trace = {
                    x: countries,
                    y: scores,
                    type: 'bar',
                    marker: {
                        color: scores,
                        colorscale: [
                            [0, '#CBD5E1'],
                            [0.33, '#94A3B8'],
                            [0.66, '#64748B'],
                            [1, '#1E3A8A']
                        ],
                        showscale: false
                    }
                };
                
                const layout = {
                    margin: { l: 40, r: 40, t: 40, b: 40 },
                    font: { family: "Inter, sans-serif", size: 12, color: "#1F2937" },
                    xaxis: { showgrid: false },
                    yaxis: { showgrid: true, gridcolor: "#F3F4F6", title: "Friction Score (Lower is Better)" },
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                    autosize: true
                };
                
                Plotly.newPlot('tefi-chart-preview', [trace], layout, {displayModeBar: false, responsive: true});
            }
        });
    }

    // --- Load Posts (Home Page) ---
    const postsGrid = document.getElementById('posts-grid');
    if (postsGrid) {
        fetch('posts/manifest.json')
            .then(response => response.json())
            .then(posts => {
                postsGrid.innerHTML = ''; // Clear loading placeholder if any
                posts.forEach((post, index) => {
                    const card = document.createElement('div');
                    card.className = 'media-card';
                    card.innerHTML = `
                        <h4>${post.title}</h4>
                        <div class="caption">PUBLISHED: ${post.date.toUpperCase()}</div>
                        <p>${post.summary}</p>
                        <button class="btn btn-primary btn-sm read-article-btn" data-filename="${post.filename}">Read Article</button>
                    `;
                    postsGrid.appendChild(card);
                });

                // Attach event listeners to new buttons
                document.querySelectorAll('.read-article-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const filename = e.target.getAttribute('data-filename');
                        loadArticle(filename);
                    });
                });
            })
            .catch(err => console.error('Error loading posts:', err));
    }

    // --- Article Viewer ---
    const articleViewer = document.getElementById('article-viewer');
    const closeBtns = [document.getElementById('close-article'), document.getElementById('close-article-bottom')];
    
    if (articleViewer) {
        closeBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    articleViewer.classList.add('hidden');
                    document.body.style.overflow = 'auto'; // Enable scroll
                });
            }
        });
    }

    function loadArticle(filename) {
        fetch(`posts/${filename}`)
            .then(response => response.text())
            .then(markdown => {
                // Strip frontmatter (--- ... ---)
                const frontmatterRegex = /^---[\s\S]*?---/;
                const content = markdown.replace(frontmatterRegex, '');
                
                // Convert MD to HTML
                const htmlContent = marked.parse(content);
                
                const articleBody = document.getElementById('article-body');
                if (articleBody) {
                    articleBody.innerHTML = htmlContent;
                    articleViewer.classList.remove('hidden');
                    document.body.style.overflow = 'hidden'; // Disable background scroll
                }
            })
            .catch(err => console.error('Error loading article:', err));
    }

});
