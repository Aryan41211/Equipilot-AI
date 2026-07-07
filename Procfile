# Railway start command (Procfile is used only if Railway chooses it over Dockerfile).
# IMPORTANT: Do not rely on shell expansion of $PORT. Railway may pass the literal string "$PORT"
# to uvicorn if it does not execute Procfile commands through a shell.
#
# This command reads PORT from the environment inside Python and passes it as an integer.
web: python -c "import os,uvicorn; port=int(os.environ.get('PORT','8000')); uvicorn.run('backend.app:app', host='0.0.0.0', port=port)"
