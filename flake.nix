{
  description = "Various usefull tools for managing linux systems";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-20.03";
  inputs.dirstamp.url = "github:orangeturtle739/dirstamp";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.unicmake.url = "github:orangeturtle739/unicmake";
  # inputs.unicmake.url = "/home/jacob/Documents/MyStuff/projects/unicmake";

  outputs = { self, nixpkgs, dirstamp, flake-utils, unicmake }:
    flake-utils.lib.eachSystem ([ "aarch64-linux" "i686-linux" "x86_64-linux" ])
    (system:
      let
        pkgs = import nixpkgs { inherit system; };
        xdg = pkgs.python3Packages.buildPythonPackage rec {
          pname = "xdg";
          version = "4.0.1";
          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            sha256 = "0mzcbnilpy1ss31fpnfqmrg4qzpasvpmbvm3cpvvlk1rxyfwjff9";
          };
        };
        pydeps = with pkgs.python3Packages; [
          setuptools
          click
          toml
          xdg
          pytest
        ];
        pybuilddeps = with pkgs.python3Packages; [
          black
          flake8
          isort
          mypy
          wrapPython
        ];
        mypy_hook = pkgs.makeSetupHook { } (pkgs.writeScript "mypy_hook" ''
          export MYPYPATH=$(toPythonPath "${
            builtins.concatStringsSep " " pydeps
          }")
        '');
        jgsysutil = pkgs.stdenv.mkDerivation rec {
          pname = "jgsysutil";
          version =
            "0.1.0"; # pkgs.lib.removeSuffix "\n" (builtins.readFile ./VERSION);
          src = self;
          nativeBuildInputs = pybuilddeps ++ [
            pkgs.cmake
            pkgs.ensureNewerSourcesForZipFilesHook
            dirstamp.defaultPackage.${system}
          ];
          buildInputs = with pkgs; [
            mypy_hook
            unicmake.defaultPackage.${system}
            coreutils
            cryptsetup
            dosfstools
            e2fsprogs
            gptfdisk
            lvm2
            openssl
            procps-ng
            rsync
            utillinux
          ];
          propagatedBuildInputs = pydeps;
          postInstall = ''
            wrapProgram $out/lib/jgsysutil_test/integration/test \
                --set PYTHONPATH "${
                  pkgs.python3Packages.makePythonPath pydeps
                }":$(toPythonPath $out) \
                --set PATH ${
                  pkgs.lib.makeBinPath [
                    pkgs.python3Packages.pytest
                    pkgs.coreutils
                  ]
                }:$out/bin
          '';
          postFixup = ''
            wrapPythonPrograms
              '';
          doCheck = true;
          checkPhase = ''
            ${pkgs.runtimeShell} pyrun pytest ../test
          '';
        };
        integration = pkgs.nixosTest {
          machine = { config, pkgs, ... }: {
            environment.systemPackages = [ jgsysutil ];
            # https://github.com/NixOS/nixpkgs/blob/master/nixos/modules/virtualisation/qemu-vm.nix#L280
            virtualisation.memorySize = 1024;
            virtualisation.diskSize = 8192;
          };
          testScript = ''
            machine.wait_for_unit("default.target")
            print(
                machine.succeed(
                    "${jgsysutil}/lib/jgsysutil_test/integration/test"
                )
            )
          '';
        };
      in {
        devShell = jgsysutil;
        defaultPackage = jgsysutil;
        checks.integration = integration;
      });
}
