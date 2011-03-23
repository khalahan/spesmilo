qm = $(patsubst %.ts,%.qm,$(wildcard i18n/*.ts))

%.qm: %.ts
	lrelease $<

lang: $(qm)

clean:
	rm -vf $(qm)
