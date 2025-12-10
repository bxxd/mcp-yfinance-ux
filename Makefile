.PHONY: help test lint lint-fix mypy ruff stdio run server logs clean all

# Load configuration from .env (create from .env.example if missing)
-include .env
export

# Default configuration (fallback if .env not present)
# Dev port: 5011, Prod port: 5001
PORT ?= 5011

# Default target - show help
help:
	@echo "yfinance-ux-mcp development commands:"
	@echo ""
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run type checking (mypy) and linting (ruff)"
	@echo "  make lint-fix   - Auto-fix linting issues where possible"
	@echo "  make mypy       - Run mypy type checking only"
	@echo "  make ruff       - Run ruff linting only"
	@echo "  make stdio      - Run MCP server (stdio mode for Claude Code)"
	@echo "  make run        - Run MCP HTTP server (alias for make server)"
	@echo "  make server     - Run MCP HTTP server (graceful restart, port $(PORT))"
	@echo "  make logs       - Tail server logs (logs/server.log)"
	@echo "  make clean      - Remove Python cache files"
	@echo "  make all        - Run lint + test (use before committing)"
	@echo ""
	@echo "Before committing, ALWAYS run: make all"

# Run all tests
test:
	@echo "Running tests..."
	@poetry run python tests/test_core.py

# Run type checking only
mypy:
	@echo "Running mypy type checker..."
	@poetry run mypy mcp_yfinance_ux/

# Run linting only
ruff:
	@echo "Running ruff linter..."
	@poetry run ruff check mcp_yfinance_ux/

# Run both type checking and linting
lint: mypy ruff
	@echo "✓ All checks passed!"

# Auto-fix linting issues and run checks
lint-fix:
	@echo "Auto-fixing linting issues..."
	@poetry run ruff check --fix mcp_yfinance_ux/
	@echo ""
	@$(MAKE) lint

# Run MCP server via stdio (for Claude Code)
stdio:
	@echo "Starting MCP server (stdio mode)..." >&2
	@echo "Press Ctrl+C to stop" >&2
	@poetry run python -m mcp_yfinance_ux.server

# Run MCP HTTP server (alias for server)
run: server

# Run MCP HTTP server (for web integration)
# Uses PID file to track and kill previous server instances
server:
	@mkdir -p logs
	@# Kill process from PID file if exists
	@if [ -f logs/server.pid ]; then \
		OLD_PID=$$(cat logs/server.pid); \
		if ps -p $$OLD_PID > /dev/null 2>&1; then \
			echo "Killing previous server (PID $$OLD_PID)..." >&2; \
			kill $$OLD_PID 2>/dev/null || true; \
			sleep 1; \
			if ps -p $$OLD_PID > /dev/null 2>&1; then \
				echo "Force killing..." >&2; \
				kill -9 $$OLD_PID 2>/dev/null || true; \
				sleep 1; \
			fi; \
		fi; \
	fi
	@# Also kill any process listening on the port (catch orphans)
	@if lsof -ti:$(PORT) -sTCP:LISTEN > /dev/null 2>&1; then \
		PORT_PID=$$(lsof -ti:$(PORT) -sTCP:LISTEN); \
		echo "Killing process on port $(PORT) (PID $$PORT_PID)..." >&2; \
		kill -9 $$PORT_PID 2>/dev/null || true; \
		sleep 1; \
	fi
	@echo "Starting MCP HTTP server on http://127.0.0.1:$(PORT) (logs/server.log)..." >&2
	@nohup poetry run uvicorn mcp_yfinance_ux.server_http:app --host 127.0.0.1 --port $(PORT) > logs/server.log 2>&1 & echo $$! > logs/server.pid
	@# Wait for server to be ready (up to 10 seconds)
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -s -f http://127.0.0.1:$(PORT)/ping > /dev/null 2>&1; then \
			echo "Server ready on port $(PORT) (PID $$(cat logs/server.pid))"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Warning: Server may not be ready yet (PID $$(cat logs/server.pid))"

# Tail server logs
logs:
	@tail -f logs/server.log

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# Run everything (use before committing)
all: lint test
	@echo ""
	@echo "✓ All checks passed - ready to commit!"
