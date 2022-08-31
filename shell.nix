with import <nixpkgs> { };

let
  majorVersion = "9.5";
in
let gurobi9 = stdenv.mkDerivation rec {
  pname = "gurobi";
  version = "${majorVersion}.0";

  src = with lib; fetchurl {
    url = "http://packages.gurobi.com/${versions.majorMinor version}/gurobi${version}_linux64.tar.gz";
    sha256 = "17n2icl41jzkkhb4a8ksqgzqa92pqnk5xw7ackizd18nbmd2wm5v";
  };

  sourceRoot = "gurobi${builtins.replaceStrings ["."] [""] version}/linux64";

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ (python.withPackages (ps: [ ps.gurobipy ])) ];

  buildPhase = ''
    cd src/build
    make
    cd ../..
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp bin/* $out/bin/
    rm $out/bin/gurobi.sh
    rm $out/bin/python3.7
    cp lib/gurobi.py $out/bin/gurobi.sh
    mkdir -p $out/include
    cp include/gurobi*.h $out/include/
    mkdir -p $out/lib
    cp lib/*.jar $out/lib/
    cp lib/libGurobiJni*.so $out/lib/
    cp lib/libgurobi*.so* $out/lib/
    cp lib/libgurobi*.a $out/lib/
    cp src/build/*.a $out/lib/
    mkdir -p $out/share/java
    ln -s $out/lib/gurobi.jar $out/share/java/
    ln -s $out/lib/gurobi-javadoc.jar $out/share/java/
  '';

  passthru.libSuffix = lib.replaceStrings ["."] [""] majorVersion;

  meta = with lib; {
    description = "Optimization solver for mathematical programming";
    homepage = "https://www.gurobi.com";
    license = licenses.unfree;
    platforms = [ "x86_64-linux" ];
    maintainers = with maintainers; [ jfrankenau ];
  };
};
in

let
  pythonPackages = python37Packages;
in pkgs.mkShell rec {
  venvDir = "./.venv";
  buildInputs = [
    pythonPackages.python
    pythonPackages.venvShellHook
    gurobi9
  ];

  LD_LIBRARY_PATH = "${stdenv.cc.cc.lib}/lib/";

  GUROBI_HOME = "${gurobi9}";

  # Now we can execute any commands within the virtual environment.
  # This is optional and can be left out to run pip manually.
  postShellHook = ''
    pip install --upgrade pip
    pip install -r requirements.txt
  '';
}
