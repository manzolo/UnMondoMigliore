# Makefile di Un Mondo Migliore
# Genera un sito HTML statico in locale a partire dal manifesto.

PY        := python3
SITE_DIR  := docs
ASSET_SRC := assets
SRCS      := MANIFESTO.md ROADMAP.md diario/README.md
OUT       := $(SITE_DIR)/index.html
PORT      := 8000

.DEFAULT_GOAL := build

.PHONY: help build open serve clean

help: ## Mostra questo aiuto
	@echo "Un Mondo Migliore — comandi disponibili:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-8s %s\n", $$1, $$2}'
	@echo ""

build: $(OUT) ## Genera il sito in dist/

$(OUT): $(SRCS) build.py $(ASSET_SRC)/hero.png
	@mkdir -p $(SITE_DIR)
	@cp -r $(ASSET_SRC) $(SITE_DIR)/
	@$(PY) build.py $(SITE_DIR)
	@touch $(SITE_DIR)/.nojekyll
	@echo "✓ Sito generato in $(SITE_DIR)/ (manifesto · roadmap · diario)"

open: build ## Genera e apre il sito nel browser
	@(xdg-open $(OUT) >/dev/null 2>&1 || open $(OUT) >/dev/null 2>&1 || \
		echo "Apri manualmente: $(OUT)") &

serve: build ## Genera e avvia un server locale su http://localhost:$(PORT)
	@echo "→ http://localhost:$(PORT)  (Ctrl+C per fermare)"
	@$(PY) -m http.server $(PORT) --directory $(SITE_DIR)

clean: ## Rimuove il sito generato
	@rm -rf $(SITE_DIR)
	@echo "✓ Pulito ($(SITE_DIR) rimosso)"
