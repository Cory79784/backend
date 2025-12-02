# Data Directory

This directory contains static data files served by the FastAPI backend:

## Structure

- `snapshots/` - Chart images and visualizations
  - `saudi/` - Saudi Arabia specific charts
- `citations/` - Metadata and citation information (JSON files)
  - `saudi/` - Saudi Arabia specific citations

## Usage

Files in this directory are served at `/static-data/` endpoint by the FastAPI app.

Example:
- File: `backend/data/snapshots/saudi/chart.png`  
- URL: `http://localhost:8000/static-data/snapshots/saudi/chart.png`

## File Formats

- Images: PNG, JPG, SVG
- Citations: JSON files with metadata
- Other: Any static file format

## Notes

- Images are referenced in JSONL files with `backend/data/` prefix
- The backend automatically maps these to `/static-data/` URLs
- Frontend renders images inline using these mapped URLs




