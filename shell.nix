with import <nixpkgs> { };
mkShell {
  name="beso";
  buildInputs = [
    python3
    python3Packages.numpy
    python3Packages.matplotlib
  ];
}
