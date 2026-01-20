#!/bin/bash
# Quick test without full pip install

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"

echo "✓ Testing ETL imports..."
python3 -c "from src.etl.ingest import ingest_all; print('✓ ingest OK')"
python3 -c "from src.etl.validate import validate_all; print('✓ validate OK')"
python3 -c "from src.etl.transform import transform_all; print('✓ transform OK')"
python3 -c "from src.etl.load import load_to_processed; print('✓ load OK')"

echo ""
echo "✓ Testing CLI..."
python3 -c "from src.cli import app; print('✓ CLI OK')"

echo ""
echo "✓ All imports successful!"
echo ""
echo "To install properly, use:"
echo "  python -m pip install setuptools wheel"
echo "  pip install -e ."
