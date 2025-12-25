SHELL := /bin/bash
.ONESHELL:

Q := @
ifneq ($(V),1)
Q := @
else
Q :=
endif

REPO_ROOT := $(abspath ..)

.PHONY: validate build

validate:
	$(Q)python $(REPO_ROOT)/scripts/validate_docs_structure.py
	$(Q)python $(REPO_ROOT)/scripts/check_markdown_links.py $(REPO_ROOT)/README.md $(REPO_ROOT)/docs

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
