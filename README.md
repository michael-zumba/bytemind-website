# ByteMind Website

This folder contains the source code for the ByteMind Ltd website, built with **Streamlit**.
Streamlit allows us to combine a professional marketing site with interactive data apps (our Indices) in one codebase.

## 1. How to Run Locally

1.  Open your terminal in this folder.
2.  Install the requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    streamlit run Home.py
    ```
4.  The website will open in your browser at `http://localhost:8501`.

## 2. How to Deploy to GitHub & Streamlit Cloud

To make this live on your custom domain (e.g., `www.bytemind.co.nz`):

1.  **GitHub:** Upload this entire folder to a new GitHub repository (e.g., `bytemind-website`).
2.  **Streamlit Cloud:**
    *   Go to [share.streamlit.io](https://share.streamlit.io/).
    *   Click "New App".
    *   Select your GitHub repository (`bytemind-website`).
    *   Set "Main file path" to `Home.py`.
    *   Click "Deploy".
3.  **Custom Domain:**
    *   In Streamlit Cloud settings, go to "Custom Domain".
    *   Enter your domain name.
    *   Follow the instructions to update your DNS records (CNAME).

## 3. Structure

*   `Home.py`: The main landing page.
*   `pages/`: Contains the sub-pages (Services, Indices, About, Contact).
*   `assets/style.css`: Custom CSS to make the site look professional (fonts, colors).
