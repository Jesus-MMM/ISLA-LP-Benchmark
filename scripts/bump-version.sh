#!/bin/bash
# Script para actualizar versión del proyecto siguiendo SemVer
# Uso: ./scripts/bump-version.sh [major|minor|patch]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validar argumentos
if [[ $# -ne 1 ]]; then
    echo -e "${RED} Error: Debes especificar el tipo de bump${NC}"
    echo "Uso: ./scripts/bump-version.sh [major|minor|patch]"
    echo "Ejemplos:"
    echo "  ./scripts/bump-version.sh major   # 1.8.1 → 2.0.0"
    echo "  ./scripts/bump-version.sh minor   # 1.8.1 → 1.9.0"
    echo "  ./scripts/bump-version.sh patch   # 1.8.1 → 1.8.2"
    exit 1
fi

BUMP_TYPE=$1

# Validar que sea un tipo válido
if [[ ! $BUMP_TYPE =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED} Error: Tipo inválido '$BUMP_TYPE'${NC}"
    echo "Valores permitidos: major, minor, patch"
    exit 1
fi

# Obtener versión actual de pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [[ -z $CURRENT_VERSION ]]; then
    echo -e "${RED} Error: No se pudo leer la versión de pyproject.toml${NC}"
    exit 1
fi

echo -e "${YELLOW} Versión actual: $CURRENT_VERSION${NC}"

# Separar en MAJOR, MINOR, PATCH
IFS='.' read -r MAJOR MINOR PATCH <<<"$CURRENT_VERSION"

# Calcular nueva versión
case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo -e "${GREEN} Nueva versión: $NEW_VERSION${NC}"

# Actualizar pyproject.toml
sed -i "s/^version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
echo -e "${GREEN} Actualizado pyproject.toml${NC}"

# Generar requirements.txt desde pyproject.toml si pip-tools está disponible
if command -v pip-compile &> /dev/null; then
    echo -e "${YELLOW}🔄 Regenerando requirements.txt...${NC}"
    pip-compile pyproject.toml --output-file=requirements.txt --quiet 2>/dev/null || {
        echo -e "${YELLOW}  No se pudo regenerar requirements.txt automáticamente${NC}"
        echo "   Ejecuta: pip-compile pyproject.toml --output-file=requirements.txt"
    }
else
    echo -e "${YELLOW}  pip-tools no está instalado, saltando regeneración de requirements.txt${NC}"
    echo "   Instala con: pip install pip-tools"
fi

# Crear commit
git add pyproject.toml requirements.txt 2>/dev/null || git add pyproject.toml
git commit -m "chore(release): bump version $CURRENT_VERSION → $NEW_VERSION"
echo -e "${GREEN} Commit creado${NC}"

# Crear tag
TAG="v$NEW_VERSION"
git tag -a "$TAG" -m "Release version $NEW_VERSION"
echo -e "${GREEN} Tag creado: $TAG${NC}"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN} ¡Versionado completado!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Próximos pasos:"
echo "  1. Revisar cambios: git log --oneline -n 2"
echo "  2. Push a repositorio: git push origin && git push origin $TAG"
echo "  3. GitHub Actions se activará automáticamente"
echo ""
