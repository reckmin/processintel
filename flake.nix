{
  description = "PM Insight";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  nixConfig = {
    extra-substituters = [
      "https://nix-community.cachix.org"
    ];
    extra-trusted-public-keys = [
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };

  outputs =
    inputs@{ nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;

      eachSystem =
        fn:
        lib.foldl'
          (acc: system: lib.recursiveUpdate acc (lib.mapAttrs (_: value: { ${system} = value; }) (fn system)))
          { }
          [
            "aarch64-darwin"
            "aarch64-linux"
            "x86_64-linux"
          ];
    in
    {
      nixosModules.pm-insight = import ./module.nix inputs;
    }
    // eachSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages = rec {
          pm-insight = pkgs.callPackage ./package.nix { inherit (pkgs) python3; };
        };
      }
    );

}
