# 0) set up environment if not already done
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 1) activate environment
source .venv/bin/activate

# 2) clean previous builds
rm -rf dist build *.egg-info

# 3) install tools
pip install -U build twine

# 4) build
python -m build

# 5) validate metadata/README
twine check dist/*