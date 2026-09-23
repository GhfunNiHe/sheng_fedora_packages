# Copr builds this repository with the "make srpm" SCM method, which delegates
# SRPM generation to this target (see .copr/README.md):
#
#   make -f <cloned repo>/.copr/Makefile srpm outdir=<dir> spec=<spec>
#
# The actual work lives in make-srpm.sh.  Its path is resolved from this file's
# location, not from the working directory, so the target works wherever Copr
# decides to run it from.
COPR_MAKE_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: srpm
.DEFAULT_GOAL := srpm

srpm:
	@bash "$(COPR_MAKE_DIR)/make-srpm.sh" "$(spec)" "$(outdir)"
