#!/bin/bash

# Setup script for Genomics ETL Pipeline Advanced Edition

echo "🧬 Setting up Genomics ETL Pipeline v2.0..."
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Install base dependencies
echo ""
echo "📦 Installing base dependencies..."
pip install -e ".[dev]" -q

# Install new dependencies
echo "📦 Installing advanced dependencies..."
pip install plotly -q
pip install schedule -q

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 To run the application:"
echo "   streamlit run app_advanced.py"
echo ""
echo "📊 Or use make command:"
echo "   make gui-advanced"
echo ""
