{ jgnssrc, python3Packages, runCommand, coreutils, cryptsetup, dosfstools
, e2fsprogs, gptfdisk, lvm2, openssl, procps-ng, rsync, stow, sudo, utillinux }:
let
  gen-package = { name, text }:
    let
      pysrc = runCommand "${name}-gen-package" {
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
    in python3Packages.buildPythonPackage rec {
      inherit name;
      src = "${pysrc}";
    };

  jgns-deps = gen-package {
    name = "jgns_deps";
    text = ''
      coreutils = "${coreutils}"
      cryptsetup = "${cryptsetup}"
      dosfstools = "${dosfstools}"
      e2fsprogs = "${e2fsprogs}"
      gptfdisk = "${gptfdisk}"
      lvm2 = "${lvm2}"
      openssl = "${openssl}"
      procps_ng = "${procps-ng}"
      rsync = "${rsync}"
      stow = "${stow}"
      sudo = "${sudo}"
      utillinux = "${utillinux}"
    '';
  };

  pydeps = with python3Packages; [ toml jgns-deps ];
in python3Packages.buildPythonPackage rec {
  name = "jgns";
  src = jgnssrc;
  nativeBuildInputs = with python3Packages; [ black flake8 mypy ];
  propagatedBuildInputs = pydeps;
  shellHook = ''
    export MYPYPATH=$(toPythonPath "${builtins.concatStringsSep " " pydeps}")
  '';
}
