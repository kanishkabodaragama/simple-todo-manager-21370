import uvicorn

if __name__ == "__main__":
    # This enables `python -m src.api` to run the app for local development.
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)
