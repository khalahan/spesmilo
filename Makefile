APP := spesmilo
PREFIX := /usr/local/
BINDIR := $(PREFIX)/bin
LIBEXECDIR := $(PREFIX)/libexec/$(APP)
DATADIR := $(PREFIX)/share
ICONDIR := $(DATADIR)/icons/hicolor
DESTDIR := 

INSTALL := install -v
PYTHON := python
PYTHON_O := $(PYTHON) -OO -m py_compile

qm = $(patsubst %.ts,%.qm,$(wildcard i18n/*.ts))
pyo = $(patsubst %.py,%.pyo,$(wildcard *.py jsonrpc/*.py))
exescript = $(APP).exescript

all: $(APP)

%.qm: %.ts
	lrelease $<

lang: $(qm)

%.pyo: %.py
	$(PYTHON_O) $<

pyo: $(pyo)

$(APP): $(pyo) $(qm)
	make exescript exescript="$@" LIBEXECDIR=.
	chmod +x $@

exescript:
	{ \
		echo '#!'"`which sh`"; \
		echo "exec \"`which python`\" -O \"$(LIBEXECDIR)/main.pyo\" \"\$$@\""; \
	} \
	>"$(exescript)"

clean:
	rm -vf $(qm) $(pyo) $(APP) $(exescript)

install: $(qm) $(pyo) exescript
	$(INSTALL) -d "$(DESTDIR)/$(LIBEXECDIR)"
	for pyo in $(pyo); do \
		$(INSTALL) -D "$$pyo" "$(DESTDIR)/$(LIBEXECDIR)/$$pyo"; \
	done
	$(INSTALL) -d "$(DESTDIR)$(ICONDIR)/32x32/apps"
	$(INSTALL) "icons/bitcoin32.xpm" "$(DESTDIR)$(ICONDIR)/32x32/apps/bitcoin.xpm"
	$(INSTALL) -d "$(DESTDIR)/$(BINDIR)"
	$(INSTALL) --mode=0755 "$(exescript)" "$(DESTDIR)/$(BINDIR)/$(APP)"

.PHONY: lang clean install pyo
