# Detect platform and Python paths
UNAME_S := $(shell uname -s)
PYTHON_VERSION := $(shell python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_INCLUDE := $(shell python3-config --includes)
PYTHON_LIBDIR := $(shell python3-config --exec-prefix)/lib
PYTHON_LIBRARY := -lpython$(PYTHON_VERSION)

# Platform-specific compiler and flags
ifeq ($(UNAME_S),Darwin)
    # macOS specific flags
    CC = clang
    CFLAGS = -fPIC -shared -undefined dynamic_lookup $(PYTHON_INCLUDE)
    LDFLAGS = -L$(PYTHON_LIBDIR) $(PYTHON_LIBRARY)
else
    # Linux/Raspberry Pi specific flags
    CC = gcc
    CFLAGS = -fPIC -shared $(PYTHON_INCLUDE)
    LDFLAGS = -L$(PYTHON_LIBDIR) $(PYTHON_LIBRARY)
endif

clib.so: clib.c
	$(CC) $(CFLAGS) -o clib.so clib.c $(LDFLAGS)

clean:
	rm -f clib.so *.o

.PHONY: clean