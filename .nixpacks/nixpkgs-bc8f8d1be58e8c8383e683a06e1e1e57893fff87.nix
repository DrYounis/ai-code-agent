# Nix packages configuration
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.pip
  ];
}
