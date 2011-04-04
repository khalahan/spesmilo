APP := spesmilo
PREFIX := /usr/local/
BINDIR := $(PREFIX)/bin
LIBEXECDIR := $(PREFIX)/libexec/$(APP)
DESTDIR := 

INSTALL := install -v
PYTHON := python
PYTHON_O := $(PYTHON) -OO -m py_compile

qm = $(patsubst %.ts,%.qm,$(wildcard i18n/*.ts))
pyo = $(patsubst %.py,%.pyo,$(wildcard *.py jsonrpc/*.py))

all: lang pyo

%.qm: %.ts
	lrelease $<

lang: $(qm)

%.pyo: %.py
	$(PYTHON_O) $<

pyo: $(pyo)

exescript:
	{ \
		echo '#!'"`which sh`"; \
		echo "exec `which python` -O $(LIBEXECDIR)/main.pyo"; \
	} \
	>"$(APP).exescript"

clean:
	rm -vf $(qm) $(pyo)

install: lang pyo exescript
	$(INSTALL) -d "$(DESTDIR)/$(LIBEXECDIR)"
	for pyo in $(pyo); do \
		$(INSTALL) -D "$$pyo" "$(DESTDIR)/$(LIBEXECDIR)/$$pyo"; \
	done
	$(INSTALL) -d "$(DESTDIR)/$(BINDIR)"
	$(INSTALL) --mode=0755 "$(APP).exescript" "$(DESTDIR)/$(BINDIR)/$(APP)"

.PHONY: lang clean install pyo
