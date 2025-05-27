#!/bin/bash
# Upload script for mercury-api-client

echo "Mercury API Client - PyPI Upload Helper"
echo "======================================"
echo

# Check if PYPI_API_TOKEN is set
if [ -z "$PYPI_API_TOKEN" ]; then
    echo "ERROR: PYPI_API_TOKEN environment variable is not set!"
    echo
    echo "Please set it with:"
    echo "  export PYPI_API_TOKEN='your-token-here'"
    exit 1
fi

# Check token format
if [[ ! "$PYPI_API_TOKEN" =~ ^(pypi-|testpypi-) ]]; then
    echo "WARNING: Token doesn't start with 'pypi-' or 'testpypi-'"
    echo "Make sure you're using a valid PyPI API token"
    echo
fi

# Check if distributions exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo "ERROR: No distribution files found in dist/"
    echo "Build first with: python -m build"
    exit 1
fi

echo "Found distributions:"
ls -la dist/
echo

# Ask which repository
echo "Which repository would you like to upload to?"
echo "1) PyPI (production)"
echo "2) TestPyPI (testing)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "Uploading to PyPI..."
        python -m twine upload dist/* \
            --username __token__ \
            --password "$PYPI_API_TOKEN"
        ;;
    2)
        echo "Uploading to TestPyPI..."
        python -m twine upload dist/* \
            --repository testpypi \
            --username __token__ \
            --password "$PYPI_API_TOKEN"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo
    echo "✅ Upload successful!"
    if [ "$choice" = "2" ]; then
        echo "View your package at: https://test.pypi.org/project/mercury-api-client/"
        echo "Install with: pip install -i https://test.pypi.org/simple/ mercury-api-client"
    else
        echo "View your package at: https://pypi.org/project/mercury-api-client/"
        echo "Install with: pip install mercury-api-client"
    fi
else
    echo
    echo "❌ Upload failed!"
    echo
    echo "Common issues:"
    echo "- Token is for wrong repository (PyPI vs TestPyPI)"
    echo "- Token has insufficient permissions"
    echo "- Token has expired"
    echo
    echo "Get a new token from:"
    echo "- PyPI: https://pypi.org/manage/account/token/"
    echo "- TestPyPI: https://test.pypi.org/manage/account/token/"
fi 