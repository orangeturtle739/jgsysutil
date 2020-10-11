all: build/Makefile
	make --no-print-directory --directory=build -j$(shell nproc) develop

format: build/Makefile
	make --no-print-directory --directory=build -j$(shell nproc) format

build/Makefile:
	mkdir -p build
	cd build && cmake ..

.PHONY: clean
clean:
	test build/Makefile && make --no-print-directory --directory=build clean
	rm -rf build
