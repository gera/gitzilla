
NAME=gitzilla
PY2DSC=$(shell which py2dsc)
BUILDCMD=$(shell which dpkg-buildpackage)
DEPENDENCIES=python-setuptools
BUILDOPTS= -rfakeroot -uc -us
VERSION:=$(shell perl -ne 'print $$1 if /version=.(\S+).,/' setup.py)
ETC_DIR=/etc

define CONFIG_REPLACEMENT_STUB
binary: build \
\n\tdh install --until dh_install\
\n\tmkdir -p debian/python-${NAME}${ETC_DIR}\
\n\tcp etc/* debian/python-${NAME}${ETC_DIR}\
\n\tdh install --after dh_install\
\n\tdh binary
endef

DEPS_REPLACEMENT:="s/$$/, ${DEPENDENCIES}/ if /^Depends: /"
CONF_REPLACEMENT:="s(binary: build.*$$)(${CONFIG_REPLACEMENT_STUB})"

.PHONY: check-prerequisites deb debianize-source edit-source build clean bumpversion

deb: check-prerequisites build
	$(info collecting packages ...)
	@mkdir -p debian
	@mv ${TARGETDIR}/deb_dist/python-${NAME}*.deb debian/
	@mv ${TARGETDIR}/deb_dist/*.orig.tar.gz debian/
	@mv ${TARGETDIR}/deb_dist/*.diff.gz debian/
	@mv ${TARGETDIR}/deb_dist/*.dsc debian/
	@rm -rf ${TARGETDIR}

dist/${NAME}-${VERSION}.tar.gz: setup.py
	$(info preparing source distribution ...)
	@python  setup.py sdist
	@rm -rf ${NAME}.egg-info

debianize-source: dist/${NAME}-${VERSION}.tar.gz
	$(info debianizing ${NAME} via py2dsc ...)
	@cd ${TARGETDIR} ; \
	cp ${CURDIR}/dist/${NAME}-${VERSION}.tar.gz . ; \
	${PY2DSC} *.tar.gz ;

edit-source: debianize-source
	$(info changing build dependencies for ${NAME} ...)
	@cd ${TARGETDIR}/deb_dist/${NAME}-${VERSION} ; \
	perl -pi -e 's/python-all-dev/python-dev/' debian/control ; \
	perl -pi -e ${DEPS_REPLACEMENT} debian/control ; \
	BUILD_STR=`grep 'binary: build' debian/rules 2>/dev/null` ; \
	if [ x"$$BUILD_STR" == x ]; then \
		echo -e "${CONFIG_REPLACEMENT_STUB}" >> debian/rules ; \
	else \
		perl -pi -e ${CONF_REPLACEMENT} debian/rules ; \
	fi

build: edit-source
	$(info building ${NAME} version ${VERSION} ...)
	@cd ${TARGETDIR}/deb_dist/${NAME}-${VERSION} ; \
	${BUILDCMD} ${BUILDOPTS}

check-prerequisites:
ifeq ($(PY2DSC), )
	$(error no py2dsc found)
else ifeq ($(BUILDCMD), )
	$(error no dpkg-buildpackage found)
else ifeq ($(VERSION), )
	$(error could not determine version from setup.py)
else
TARGETDIR:=$(shell mktemp -d)
endif


clean:
	@rm -rf ${NAME}.egg-info
	@rm -rf dist
	@rm -rf ${TARGETDIR}
	@rm -rf debian

bumpversion:
	@${EDITOR} setup.py
	@${EDITOR} __init__.py


