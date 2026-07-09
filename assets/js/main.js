document.addEventListener('DOMContentLoaded', () => {

    // --- Reports Grid (Reports Page) ---
    const reportsGrid = document.getElementById('reports-grid');
    if (reportsGrid) {
        fetch('reports/manifest.json')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(reports => {
                reportsGrid.innerHTML = '';
                reports.sort((a, b) => new Date(b.date) - new Date(a.date));
                reports.forEach(report => {
                    const card = document.createElement('div');
                    card.className = 'report-card';
                    const topicsHtml = report.topics
                        ? report.topics.map(t => `<span style="font-size:0.7rem;color:var(--muted);margin-right:0.5rem;">${t}</span>`).join('')
                        : '';
                    card.innerHTML = `
                        <span class="report-label">Analytical Brief</span>
                        <h4>${report.title}</h4>
                        <div class="caption">${report.date.toUpperCase()}</div>
                        <p>${report.summary}</p>
                        <div style="margin-top:auto;padding-top:1rem;">
                            ${topicsHtml}
                        </div>
                        <a href="reports/${report.filename}" style="margin-top:1rem;" class="btn btn-primary btn-sm">Read Full Report</a>
                    `;
                    reportsGrid.appendChild(card);
                });
            })
            .catch(err => {
                console.error('Error loading reports:', err);
                if (reportsGrid) {
                    reportsGrid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--muted);"><p>Unable to load reports at this time.</p></div>';
                }
            });
    }

    
    // --- Mobile Menu Toggle ---
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuBtn.classList.toggle('open');
        });
    }

    // --- Load Posts (Home Page & Insights Page) ---
    const postsGrid = document.getElementById('posts-grid');
    if (postsGrid) {
        let fetchUrl = 'posts/manifest.json';
        
        fetch(fetchUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(posts => {
                postsGrid.innerHTML = ''; // Clear loading placeholder if any
                
                // Sort posts by date descending (newest first)
                posts.sort((a, b) => new Date(b.date) - new Date(a.date));
                
                // Apply limit if data-limit attribute exists
                const limit = postsGrid.getAttribute('data-limit');
                const postsToDisplay = limit ? posts.slice(0, parseInt(limit, 10)) : posts;

                postsToDisplay.forEach((post, index) => {
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
                        console.log('Loading article:', filename);
                        loadArticle(filename);
                    });
                });
            })
            .catch(err => {
                console.error('Error loading posts:', err);
                postsGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; color: var(--muted);">
                        <p>Unable to load insights at this time.</p>
                        <small>${err.message}</small>
                    </div>
                `;
            });
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
        
        // Close on background click
        articleViewer.addEventListener('click', (e) => {
            if (e.target === articleViewer) {
                articleViewer.classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        });
    }

    function loadArticle(filename) {
        console.log('Fetching:', `posts/${filename}`);
        
        fetch(`posts/${filename}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.text();
            })
            .then(markdown => {
                console.log('Markdown loaded, length:', markdown.length);
                
                // Strip frontmatter (--- ... ---)
                const frontmatterRegex = /^---[\s\S]*?---/;
                const content = markdown.replace(frontmatterRegex, '').trim();
                
                if (!content) {
                    console.error('Content is empty after stripping frontmatter');
                    alert('Error: Article content is empty.');
                    return;
                }

                // Check if marked is loaded
                if (typeof marked === 'undefined') {
                    console.error('Marked.js library not found');
                    alert('Error: Markdown parser not loaded.');
                    return;
                }
                
                // Convert MD to HTML
                // Note: marked 4.x uses marked.parse, older might use marked()
                const htmlContent = typeof marked.parse === 'function' ? marked.parse(content) : marked(content);
                
                const articleBody = document.getElementById('article-body');
                if (articleBody) {
                    // Update content first
                    articleBody.innerHTML = htmlContent;
                    
                    // Convert any mermaid code blocks (rendered by marked as <pre><code class="language-mermaid">)
                    // into actual mermaid divs so mermaid.init() can find them.
                    const mermaidBlocks = articleBody.querySelectorAll('code.language-mermaid');
                    mermaidBlocks.forEach((block, index) => {
                        const pre = block.parentElement;
                        const div = document.createElement('div');
                        div.className = 'mermaid';
                        // Need to ensure raw text content without HTML entities from marked
                        div.textContent = block.textContent;
                        pre.parentNode.replaceChild(div, pre);
                    });

                    // Render mermaid diagrams if library is loaded
                    if (typeof mermaid !== 'undefined') {
                        try {
                            mermaid.initialize({ startOnLoad: false, theme: 'default' });
                            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                        } catch (e) {
                            console.error('Mermaid render error:', e);
                        }
                    }
                    
                    articleViewer.classList.remove('hidden');
                    document.body.style.overflow = 'hidden'; // Disable background scroll
                    
                    // Reset scroll position of the article content to the top
                    const articleContent = document.querySelector('.article-content');
                    if (articleContent) {
                        articleContent.scrollTop = 0;
                    }
                } else {
                    console.error('Element #article-body not found');
                }
            })
            .catch(err => {
                console.error('Error loading article:', err);
                alert('Failed to load article. See console for details.');
            });
    }

});
