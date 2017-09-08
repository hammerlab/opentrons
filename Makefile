# opentrons platform makefile
# https://github.com/OpenTrons/opentrons

SHELL := /bin/bash

API_DIR := api
APP_DIR := app

.PHONY: install test coverage

# install project dependencies for both api and app
install:
	$(MAKE) -C $(API_DIR) install
	$(MAKE) -C $(APP_DIR) install

# run api and app tests
test:
	$(MAKE) -C $(API_DIR) test
	$(MAKE) -C $(APP_DIR) test

# upload coverage reports
# uses codecov's bash upload script
# TODO(mc, 2018-08-28): add test as a task dependency once travis is setup to
# use this Makefile for tests
coverage:
	$(SHELL) <(curl -s https://codecov.io/bash) -X coveragepy
