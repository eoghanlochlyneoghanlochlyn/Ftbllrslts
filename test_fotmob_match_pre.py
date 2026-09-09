name: Test FotMob Match Pre

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install requests
        run: python -m pip install requests

      - name: Debug
        run: |
          echo "=== DEBUG START ==="
          pwd
          echo "=== FILES ==="
          ls -la
          echo "=== PYTHON ==="
          python --version
          echo "=== TARGET FILE ==="
          ls -l test_fotmob_match_pre.py
          echo "=== FILE CONTENT ==="
          cat test_fotmob_match_pre.py
          echo "=== DEBUG END ==="
