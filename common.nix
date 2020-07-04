{ pkgs, jgnssrc }:
with pkgs.python3Packages;

let
  gen-package = { name, text }:
    let
      pysrc = pkgs.runCommand "${name}-gen-package" {
        inherit text;
        passAsFile = [ "text" ];
        preferLocalBuild = true;
        allowSubstitutes = false;
      } ''
        mkdir $out
        pushd $out
        cat << EOF > setup.py
        from setuptools import setup, find_packages
        packages = find_packages()
        setup(
            name="${name}",
            packages=packages,
            package_data={pkg: ["py.typed"] for pkg in packages},
        )
        EOF
        mkdir ${name}
        cp -a "$textPath" "${name}/__init__.py"
        touch "${name}/py.typed"
        popd
      '';
    in buildPythonPackage rec {
      inherit name;
      src = "${pysrc}";
    };

  jgns-deps = gen-package {
    name = "jgns_deps";
    text = ''
      coreutils = "${pkgs.coreutils}"
      cryptsetup = "${pkgs.cryptsetup}"
      dosfstools = "${pkgs.dosfstools}"
      e2fsprogs = "${pkgs.e2fsprogs}"
      gptfdisk = "${pkgs.gptfdisk}"
      lvm2 = "${pkgs.lvm2}"
      openssl = "${pkgs.openssl}"
      procps_ng = "${pkgs.procps-ng}"
      rsync = "${pkgs.rsync}"
      stow = "${pkgs.stow}"
      sudo = "${pkgs.sudo}"
      utillinux = "${pkgs.utillinux}"
    '';
  };

  pydeps = [ toml jgns-deps ];
in buildPythonPackage rec {
  name = "jgns";
  src = jgnssrc;
  nativeBuildInputs = [ black flake8 mypy ];
  propagatedBuildInputs = pydeps;
  shellHook = ''
    export MYPYPATH=$(toPythonPath "${builtins.concatStringsSep " " pydeps}")
  '';
}
