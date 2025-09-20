#!/bin/bash

echo "🔧 Ejecutando script de inicio..."

# Detectar sistema operativo
OS=$(uname)

# Crear carpeta destino
mkdir -p ~/.local/bin

# Copiar ejecutable según sistema
if [[ "$OS" == "Linux" ]]; then
    cp bin/epanet2.so ~/.local/bin/epanet2.so
    echo "✅ epanet2.so copiado a ~/.local/bin"
elif [[ "$OS" == "Darwin" ]]; then
    cp bin/epanet2.dylib ~/.local/bin/epanet2.dylib
    echo "✅ epanet2.dylib copiado a ~/.local/bin"
else
    cp bin/epanet2.dll ~/.local/bin/epanet2.dll
    echo "✅ epanet2.dll copiado a ~/.local/bin"
fi

# Exportar ruta al PATH
export PATH=$PATH:~/.local/bin
echo "📦 PATH actualizado: $PATH"