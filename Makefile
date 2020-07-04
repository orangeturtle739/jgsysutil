all:
	@cached-nix-shell --pure --command ./lint

.PHONY: format
format:
	@cached-nix-shell --pure --command ./format
