SHELL=/bin/bash

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# List required executables
EXECUTABLES=asciinema agg
K := $(foreach exec,$(EXECUTABLES),\
        $(if $(shell which $(exec) 2>/dev/null),some string,$(error "No $(exec) in PATH")))

RECORDING_SOURCES := $(wildcard *.cast)
RECORDING_GIFS=$(RECORDING_SOURCES:%.cast=%)

all: $(RECORDING_GIFS)

show-sources:
	@echo $(RECORDING_SOURCES)

show-gifs:
	@echo $(RECORDING_GIFS)

# Convert .cast files into .gif files
%: %.cast
	@echo "ROOT_DIR=$(ROOT_DIR)"
	@echo "Converting $@.cast into $@.gif"
	agg --theme nord --idle-time-limit 2 --font-size 20 --rows 15 --cols 148 $@.cast $@.gif

.PHONY: record
record:
	@echo "ROOT_DIR=$(ROOT_DIR)"
	$(eval recording:=$(shell mktemp --tmpdir=$(ROOT_DIR) recording.XXXXXX.cast))
	asciinema rec --title "Recording" --idle-time-limit 1 $(recording)
