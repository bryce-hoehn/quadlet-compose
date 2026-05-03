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
          pyyaml
          rich
        ];

        runtimeDeps = with pkgs; [
          podlet
          podman
        ];

        podlet-compose = pkgs.python312Packages.buildPythonApplication {
          pname = "podlet-compose";
          version = "0.1.0";
          format = "pyproject";

          src = ./.;

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
            homepage = "https://github.com/bryce-hoehn/podlet-compose";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };
      in
      {
        packages = {
          default = podlet-compose;
          podlet-compose = podlet-compose;
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python312
            python312Packages.pip
            python312Packages.pytest
            podlet
            podman
          ] ++ pythonDeps;

          shellHook = ''
            echo "podlet-compose dev shell"
            echo "Run: python podlet_compose.py --help"
          '';
        };
      }
    );
}
