APP := spesmilo
PREFIX := /usr/local/
BINDIR := $(PREFIX)/bin
LIBEXECDIR := $(PREFIX)/libexec/$(APP)
DATADIR := $(PREFIX)/share
ICONDIR := $(DATADIR)/icons/hicolor
XDGDATADIR := $(DATADIR)
XDGAPPDIR := $(XDGDATADIR)/applications
KDESERVICEDIR := 
DISABLE_FALLBACK_ICONS := 
LINGUAS := $(patsubst i18n/%.ts,%,$(wildcard i18n/*.ts))

DESTDIR := 

INSTALL := install -v
PYTHON := python
PYTHON_O := $(PYTHON) -OO -m py_compile
IMGCONVERT := convert -background none

qm = $(patsubst %,i18n/%.qm,$(LINGUAS))
pyo = $(patsubst %.py,%.pyo,$(wildcard *.py lib/*/*.py))
exescript = $(APP).exescript
icon = icons/bitcoin32.png
ifeq ($(DISABLE_FALLBACK_ICONS),)
	fallback_icons = $(patsubst %.svg,%.png,$(wildcard icons/*.svg))
endif

GIT_POC = if [ -e $(2) ]; then ( cd $(2) && git pull; ); else git clone $(1) $(2); $(3); fi

all: $(APP) $(qm) $(pyo) $(icon) $(fallback_icons)

%.qm: %.ts
	lrelease $<

lang: $(qm)

%.pyo: %.py
	$(PYTHON_O) $<

pyo: $(pyo)

%.xpm: %.svg
	$(IMGCONVERT) $< $@

%.png: %.xpm
	$(IMGCONVERT) $< $@

%.ico: %.xpm
	$(IMGCONVERT) $< $@

$(APP):
	make exescript exescript="$@" LIBEXECDIR=.
	chmod +x $@

exescript:
	{ \
		echo '#!'"`which sh`"; \
		echo "PYTHONPATH=\"\$${PYTHONPATH}:$(LIBEXECDIR)/lib\" \\"; \
		echo "exec \"`which python`\" -O \"$(LIBEXECDIR)/main.pyo\" \"\$$@\""; \
	} \
	>"$(exescript)"

local:
	mkdir -p lib
	$(call GIT_POC, \
		git://github.com/jgarzik/python-bitcoinrpc.git, lib/bitcoinrpc, \
		true)
	@if [ -e "lib/jsonrpc" ]; then \
		if ! [ -L "lib/jsonrpc" ]; then \
			echo '*** You may wish to delete lib/jsonrpc and re-run "make local".'; \
		fi \
	else \
		ln -s bitcoinrpc/jsonrpc lib/jsonrpc; \
	fi
	$(call GIT_POC, \
		git://gitorious.org/anynumber/python.git, lib/anynumber, \
		ln -s anynumber.py lib/anynumber/__init__.py)

winprep: all icons/bitcoin32.ico icons/go-next.ico

winexe:
	makensis -NOCD windows/spesmilo.nsis

clean:
	rm -vf $(qm) $(pyo) $(APP) $(exescript) $(icon) $(fallback_icons)

install: $(qm) $(pyo) exescript $(icon) $(fallback_icons)
	$(INSTALL) -d "$(DESTDIR)/$(LIBEXECDIR)"
	for pyo in $(pyo); do \
		$(INSTALL) -D "$$pyo" "$(DESTDIR)/$(LIBEXECDIR)/$$pyo"; \
	done
	$(INSTALL) -d "$(DESTDIR)/$(ICONDIR)/32x32/apps"
	$(INSTALL) "$(icon)" "$(DESTDIR)/$(ICONDIR)/32x32/apps/bitcoin.png"
	for xicon in $(fallback_icons); do \
		$(INSTALL) -D "$$xicon" "$(DESTDIR)/$(LIBEXECDIR)/$$xicon"; \
	done
	for xqm in $(qm); do \
		$(INSTALL) -D "$$xqm" "$(DESTDIR)/$(LIBEXECDIR)/$$xqm"; \
	done
	$(INSTALL) -d "$(DESTDIR)/$(BINDIR)"
	$(INSTALL) --mode=0755 "$(exescript)" "$(DESTDIR)/$(BINDIR)/$(APP)"
	$(INSTALL) -d "$(DESTDIR)/$(XDGAPPDIR)"
	$(INSTALL) "$(APP).desktop" "$(DESTDIR)/$(XDGAPPDIR)/"
	if [ -n "$(KDESERVICEDIR)" ]; then \
		$(INSTALL) -d "$(DESTDIR)/$(KDESERVICEDIR)"; \
		$(INSTALL) "$(APP).protocol" "$(DESTDIR)/$(KDESERVICEDIR)/"; \
	fi

.PHONY: lang clean install pyo local
