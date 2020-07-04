{ pkgs }:
import ./common.nix {
  inherit pkgs;
  jgnssrc = ./.;
}
