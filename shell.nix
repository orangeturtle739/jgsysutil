import ./common.nix {
  pkgs = import <nixpkgs> { };
  jgnssrc = ./setup.py;
}
