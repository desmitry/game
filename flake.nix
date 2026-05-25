{
  description = "Eclipsed Evolution: Top-Down 2D Stealth Survival";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            stdenv.cc.cc.lib
            zlib
          ];

          packages = with pkgs; [
            python314
            uv
            ruff
            SDL2
            SDL2_image
            SDL2_mixer
            SDL2_ttf
            freetype
            pkg-config
            libX11
            libxrandr
            libxrender
            libxext
            libxcursor
            libxi
            libxfixes
            libxinerama
            libxscrnsaver
            mesa
            libpulseaudio
          ];

          shellHook = ''
            export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath (with pkgs; [ stdenv.cc.cc.lib zlib ])}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
          '';
        };
      }
    );
}
