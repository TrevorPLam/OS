SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

REPO_ROOT := $(abspath ..)

.PHONY: validate build lint-md spell-check check-completeness docs-check

# Legacy validate target (for backward compatibility)
validate:
	$(Q)python $(REPO_ROOT)/scripts/validate_docs_structure.py
	$(Q)python $(REPO_ROOT)/scripts/check_markdown_links.py $(REPO_ROOT)/README.md $(REPO_ROOT)/docs

# Markdown linting (requires markdownlint-cli: npm install -g markdownlint-cli)
lint-md:
	$(Q)if command -v markdownlint >/dev/null 2>&1; then \
		echo "Running markdown linter..."; \
		markdownlint --config $(REPO_ROOT)/.markdownlint.jsonc --ignore-path $(REPO_ROOT)/.markdownlintignore "$(REPO_ROOT)/**/*.md"; \
	else \
		echo "⚠️  markdownlint not found. Install with: npm install -g markdownlint-cli"; \
		echo "⚠️  Skipping markdown linting."; \
	fi

# Spell checking (requires cspell: npm install -g cspell)
spell-check:
	$(Q)if command -v cspell >/dev/null 2>&1; then \
		echo "Running spell checker..."; \
		cspell --config $(REPO_ROOT)/cspell.json "$(REPO_ROOT)/**/*.md"; \
	else \
		echo "⚠️  cspell not found. Install with: npm install -g cspell"; \
		echo "⚠️  Skipping spell checking."; \
	fi

# Documentation completeness check
check-completeness:
	$(Q)echo "Checking documentation completeness..."
	$(Q)python $(REPO_ROOT)/scripts/check_docs_completeness.py

# Comprehensive docs quality check
docs-check: validate check-completeness lint-md spell-check
	$(Q)echo "=== DOCS QUALITY CHECK COMPLETE ==="

build:
	$(Q)if [ ! -f $(REPO_ROOT)/mkdocs.yml ]; then \
		echo "mkdocs.yml not found. Configure a docs site before enabling docs build/publish."; \
		exit 1; \
	fi
	$(Q)if ! command -v mkdocs >/dev/null 2>&1; then \
		echo "mkdocs is not installed. Install it (pip install mkdocs) before running docs build."; \
		exit 1; \
	fi
	$(Q)mkdocs build --config-file $(REPO_ROOT)/mkdocs.yml
