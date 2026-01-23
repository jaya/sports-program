#!/bin/bash
set -e

echo "Installing dependencies..."
poetry lock
poetry install

echo "Installing pre-commit hooks..."
poetry run pre-commit install

echo "Setup complete!"
