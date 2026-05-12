{
  description = "A thin wrapper around podlet that acts as a drop-in for docker/podman-compose";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonDeps = with pkgs.python312Packages; [
          rich
          ruamel-yaml
        ];

        runtimeDeps = with pkgs; [
          podlet
          podman
        ];

        quadlet-compose = pkgs.python312Packages.buildPythonApplication {
          pname = "quadlet-compose";
          version = "0.2.1";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs.python312Packages; [
            setuptools
          ];

          propagatedBuildInputs = pythonDeps;

          # Runtime dependencies needed on PATH
          makeWrapperArgs = [
            "--prefix"
            "PATH"
            ":"
            (pkgs.lib.makeBinPath runtimeDeps)
          ];

          # No tests in the repo yet
          doCheck = false;

          meta = with pkgs.lib; {
            description = "A thin wrapper around podlet that acts as a drop-in for docker/podman-compose";
            homepage = "https://github.com/bryce-hoehn/quadlet-compose";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };
      in
      {
        packages = {
          default = quadlet-compose;
          quadlet-compose = quadlet-compose;
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python312
            python312Packages.pip
            python312Packages.pytest
            python312Packages.pytest-timeout
            podlet
            podman
          ] ++ pythonDeps;

          shellHook = ''
            echo "quadlet-compose dev shell"
            echo "Run: python podlet_compose.py --help"
          '';
        };
      }
    );
}
