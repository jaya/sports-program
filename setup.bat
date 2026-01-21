@echo off
echo Installing dependencies...
call poetry install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    exit /b %ERRORLEVEL%
)

echo Installing pre-commit hooks...
call poetry run pre-commit install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install pre-commit hooks.
    exit /b %ERRORLEVEL%
)

echo Setup complete!
