# Detect Python paths
PYTHON_VERSION := $(shell python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_INCLUDE := $(shell python3-config --includes)
PYTHON_LIBDIR := $(shell python3-config --exec-prefix)/lib
PYTHON_LIBRARY := -lpython$(PYTHON_VERSION)

# macOS ARM64 specific flags
CC = clang
CFLAGS = -fPIC -shared -undefined dynamic_lookup $(PYTHON_INCLUDE)
LDFLAGS = -L$(PYTHON_LIBDIR) $(PYTHON_LIBRARY)

clib.so: clib.c
	$(CC) $(CFLAGS) -o clib.so clib.c $(LDFLAGS)

clean:
	rm -f clib.so *.o

.PHONY: clean