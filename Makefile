APP := spesmilo
PREFIX := /usr/local/
BINDIR := $(PREFIX)/bin
LIBEXECDIR := $(PREFIX)/libexec/$(APP)
DATADIR := $(PREFIX)/share
ICONDIR := $(DATADIR)/icons/hicolor
XDGDATADIR := $(DATADIR)
XDGAPPDIR := $(XDGDATADIR)/applications
KDESERVICEDIR := 

DESTDIR := 

INSTALL := install -v
PYTHON := python
PYTHON_O := $(PYTHON) -OO -m py_compile
IMGCONVERT := convert

qm = $(patsubst %.ts,%.qm,$(wildcard i18n/*.ts))
pyo = $(patsubst %.py,%.pyo,$(wildcard *.py jsonrpc/*.py))
exescript = $(APP).exescript
icon = icons/bitcoin32.png

all: $(APP) $(qm) $(pyo) $(icon)

%.qm: %.ts
	lrelease $<

lang: $(qm)

%.pyo: %.py
	$(PYTHON_O) $<

pyo: $(pyo)

%.png: %.xpm
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
	svn co http://svn.json-rpc.org/trunk/python-jsonrpc/jsonrpc lib/jsonrpc

clean:
	rm -vf $(qm) $(pyo) $(APP) $(exescript)

install: $(qm) $(pyo) exescript $(icon)
	$(INSTALL) -d "$(DESTDIR)/$(LIBEXECDIR)"
	for pyo in $(pyo); do \
		$(INSTALL) -D "$$pyo" "$(DESTDIR)/$(LIBEXECDIR)/$$pyo"; \
	done
	$(INSTALL) -d "$(DESTDIR)/$(ICONDIR)/32x32/apps"
	$(INSTALL) "$(icon)" "$(DESTDIR)/$(ICONDIR)/32x32/apps/bitcoin.png"
	$(INSTALL) -d "$(DESTDIR)/$(BINDIR)"
	$(INSTALL) --mode=0755 "$(exescript)" "$(DESTDIR)/$(BINDIR)/$(APP)"
	$(INSTALL) -d "$(DESTDIR)/$(XDGAPPDIR)"
	$(INSTALL) "$(APP).desktop" "$(DESTDIR)/$(XDGAPPDIR)/"
	if [ -n "$(KDESERVICEDIR)" ]; then \
		$(INSTALL) -d "$(DESTDIR)/$(KDESERVICEDIR)"; \
		$(INSTALL) "$(APP).protocol" "$(DESTDIR)/$(KDESERVICEDIR)/"; \
	fi

.PHONY: lang clean install pyo local
