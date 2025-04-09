#!/bin/bash

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Installing Streamlit..."
    pip install streamlit
fi

# Set environment variables
export PYTHONASYNCIODEBUG=1
export STREAMLIT_SERVER_PORT=8505
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=500
export STREAMLIT_SERVER_ENABLE_CORS=true
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
export PYTHONPATH=$PYTHONPATH:$(pwd)
export TORCH_DISABLE_CUSTOM_CLASS_PICKLING=1
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Function to check if port is in use
check_port() {
    lsof -i :$STREAMLIT_SERVER_PORT > /dev/null 2>&1
    return $?
}

# Kill any existing process on the port
if check_port; then
    echo "Port $STREAMLIT_SERVER_PORT is in use. Attempting to free it..."
    lsof -ti :$STREAMLIT_SERVER_PORT | xargs kill -9 2>/dev/null || true
fi

# Deploy to Streamlit Cloud
echo "Deploying to Streamlit Cloud..."
streamlit run streamlit_app.py --server.port=$STREAMLIT_SERVER_PORT --server.address=$STREAMLIT_SERVER_ADDRESS --server.headless=true --server.fileWatcherType=none --server.enableCORS=true --server.enableXsrfProtection=true --server.maxUploadSize=500 --browser.gatherUsageStats=false

# If deployment fails, provide troubleshooting steps
if [ $? -ne 0 ]; then
    echo "If deployment failed, try these steps:"
    echo "1. Go to https://github.com/settings/applications"
    echo "2. Find Streamlit in 'Authorized OAuth Apps'"
    echo "3. Click 'Revoke access'"
    echo "4. Run: streamlit logout"
    echo "5. Run: streamlit login"
    echo "6. Try deploying again with: streamlit run streamlit_app.py"
    echo ""
    echo "To deploy your app to Streamlit Cloud:"
    echo "1. Go to https://streamlit.io/cloud"
    echo "2. Click 'New app'"
    echo "3. Select your repository: bharti26/cognisgraph"
    echo "4. Set the following configuration:"
    echo "   - Main file path: streamlit_app.py"
    echo "   - Python version: 3.8 or higher"
    echo "   - Requirements file: requirements_streamlit.txt"
    echo "   - Environment variables:"
    echo "     PYTHONASYNCIODEBUG=1"
    echo "     STREAMLIT_SERVER_PORT=8505"
    echo "     STREAMLIT_SERVER_ADDRESS=0.0.0.0"
    echo "     STREAMLIT_SERVER_MAX_UPLOAD_SIZE=500"
    echo "     STREAMLIT_SERVER_ENABLE_CORS=true"
    echo "     STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true"
    echo "     PYTHONPATH=\$PYTHONPATH:\$(pwd)"
    echo "     TORCH_DISABLE_CUSTOM_CLASS_PICKLING=1"
    echo "     STREAMLIT_SERVER_FILE_WATCHER_TYPE=none"
    echo "     STREAMLIT_SERVER_HEADLESS=true"
    echo "     STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
    echo ""
    echo "If you get an access error:"
    echo "1. Sign out of Streamlit Cloud"
    echo "2. Clear your browser cache"
    echo "3. Go to https://github.com/settings/applications"
    echo "4. Find Streamlit in 'Authorized OAuth Apps'"
    echo "5. Click 'Revoke access'"
    echo "6. Go back to https://streamlit.io/cloud"
    echo "7. Click 'Sign in with GitHub'"
    echo "8. Authorize Streamlit"
    echo "9. Try deploying again"
fi 