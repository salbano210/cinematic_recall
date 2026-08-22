# Cinematic Recall Deployment Guide

## Backend Deployment (Render.com)

1. Create a new **Web Service** on Render
2. Connect to your GitHub repository
3. Configure settings:
   - Name: `cinematic-recall-backend`
   - Region: Select closest region
   - Branch: `main`
   - Runtime: Docker
   - Dockerfile Path: `backend/Dockerfile`
   - Port: `10000`
4. Set environment variables:
   - `TMDB_API_KEY` - Your TMDb API key
5. Deploy

## Frontend Deployment (Render.com)

1. Create a new **Static Site** on Render
2. Connect to your GitHub repository
3. Configure settings:
   - Name: `cinematic-recall-frontend`
   - Branch: `main`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
4. Set environment variables:
   - `VITE_BACKEND_URL` - URL of your backend service (e.g. `https://cinematic-recall-backend.onrender.com`)
5. Deploy

## Daily Game Setup

The game will automatically select a new actor each day based on the day of the year.

## GitHub Security Recommendations

1. Add `.env` to `.gitignore`
2. Enable branch protection for `main` branch
3. Use GitHub Actions for CI/CD
4. Enable Dependabot for dependency security