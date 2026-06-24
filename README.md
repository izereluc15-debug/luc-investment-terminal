# Luc Investment Terminal - Final Streamlit Version

## Files included
- app.py
- requirements.txt
- runtime.txt
- README.md

## Important deployment fix
This version includes `runtime.txt` with:

python-3.11

This prevents Streamlit Cloud from using Python 3.14, which caused the Pillow/zlib build error.

## Deploy on Streamlit Cloud
Upload all files in this folder to your GitHub repository, then redeploy your Streamlit app.

Your repository must contain:
- app.py
- requirements.txt
- runtime.txt
- README.md
