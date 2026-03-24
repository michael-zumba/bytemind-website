# ByteMind Website

This repository contains the source code for the ByteMind Ltd website (www.bytemind.co.nz).
The website is a static site (HTML/CSS/JS) hosted on GitHub Pages, designed for performance, security, and ease of maintenance without backend dependencies.

## Structure

*   `index.html`: Home page.
*   `services.html`: Services page.
*   `indices.html`: Economic Indices (Charts powered by Plotly.js).
*   `about.html`: About page.
*   `contact.html`: Contact page.
*   `assets/`: CSS (modern design system), JS (interactive logic), Images, Logos.
*   `data/`: Data files (CSV/TXT) for Economic Indices.
*   `posts/`: Markdown files for "Latest Insights".
*   `legacy_streamlit/`: Archived Python files from the previous version.

## How to Update Content

### 1. Adding a New Insight (Blog Post)
1.  **Create File**: Add your markdown file (e.g., `YYYY-MM-DD-title.md`) to the `posts/` folder.
    *   *Tip: You can include a YAML frontmatter block at the top, though the current viewer strips it.*
2.  **Update Manifest**: Open `posts/manifest.json` and add an entry for the new post:
    ```json
    {
        "filename": "YYYY-MM-DD-title.md",
        "title": "Your Title Here",
        "date": "Month DD, YYYY",
        "summary": "A brief summary of the post..."
    }
    ```
    *   *Note: Ensure the JSON syntax is valid (commas between objects).*

### 2. Updating Indices Data
*   **TEFI (Tax Friction):** Update `data/tefi_raw.csv`. The chart on the Indices page will automatically reflect changes.
*   **SME Resilience:** Update `data/nz_sme_resilience.csv` and `data/nz_sme_score.txt`.

### 3. Modifying Design
*   Edit `assets/style.css`. The site uses a variable-based design system (`:root`) for colors, spacing, and shadows.
*   Common variables: `--primary`, `--accent`, `--bg-body`.

## Local Development
Since this is a static site, you can view it locally. However, due to browser security policies (CORS), fetching local JSON/CSV files might be blocked if you just open the file directly.

**Recommended:** Run a simple local server.
```bash
python3 -m http.server 8000
```
Then visit `http://localhost:8000`.

## Deployment

The site is hosted via **GitHub Pages**.

### Updating the Live Site

The site uses continuous deployment through GitHub Pages. This means that as soon as you push code changes to the `main` branch, GitHub automatically rebuilds and publishes the website online.

Here is the step-by-step process to push your changes:

1.  **Open the Terminal**: Open a terminal window in your IDE (like VS Code or Trae) and make sure you are in the `ByteMind_Website` directory.
    ```bash
    cd "/Users/zhangy6j/Python Projects/Personal/ByteMind Project/ByteMind_Website"
    ```

2.  **Stage your changes**: Tell Git which files you want to include in the update. The `.` means "include everything that changed".
    ```bash
    git add .
    ```

3.  **Commit your changes**: Package the changes with a descriptive message of what you did.
    ```bash
    git commit -m "Describe your changes here (e.g., Added new tax article)"
    ```

4.  **Push to the live website**: Send the packaged changes to the GitHub repository. This triggers the website update.
    ```bash
    git push origin main
    ```

*(Alternatively, you can combine these steps into one quick command:)*
```bash
git add . && git commit -m "Update website content" && git push origin main
```

**What happens next?**
After running `git push`, wait about **1-2 minutes**. GitHub Pages will automatically process the files and deploy the site. Refresh `www.bytemind.co.nz` in your browser to see your updates live!

### First-Time Setup (If not already configured)
1.  Go to the repository on GitHub.
2.  Navigate to **Settings** > **Pages**.
3.  Under **Build and deployment**:
    *   **Source**: Select `Deploy from a branch`.
    *   **Branch**: Select `main` and folder `/ (root)`.
4.  Click **Save**.
5.  (Optional) Under **Custom domain**, enter `www.bytemind.co.nz` and save. Ensure your DNS provider has a CNAME record pointing to `<username>.github.io`.
