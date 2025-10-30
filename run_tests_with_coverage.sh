#!/bin/bash

# Script pour lancer les tests avec coverage
# Usage: ./run_tests_with_coverage.sh

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "🧪 Test Coverage Runner"
echo -e "==========================================${NC}\n"

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest n'est pas installé${NC}"
    echo "Installation en cours..."
    pip install pytest pytest-cov coverage
fi

# Nettoyer les anciens rapports
echo -e "${YELLOW}🧹 Nettoyage des anciens rapports...${NC}"
rm -rf htmlcov
rm -f .coverage coverage.xml
echo -e "${GREEN}✅ Nettoyage terminé${NC}\n"

# Lancer les tests avec coverage
echo -e "${BLUE}🚀 Lancement des tests avec coverage...${NC}"
echo ""

pytest tests/ \
    --cov=src \
    --cov=code \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    --cov-fail-under=70 \
    -v

TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}==========================================${NC}"

# Afficher le résumé
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les tests ont réussi !${NC}"
else
    echo -e "${RED}❌ Certains tests ont échoué${NC}"
fi

echo ""
echo -e "${BLUE}📊 Rapports de coverage générés :${NC}"
echo -e "  ${GREEN}✓${NC} Terminal   : Voir ci-dessus"
echo -e "  ${GREEN}✓${NC} HTML       : ${YELLOW}htmlcov/index.html${NC}"
echo -e "  ${GREEN}✓${NC} XML        : ${YELLOW}coverage.xml${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${YELLOW}💡 Commandes utiles :${NC}"
echo ""
echo -e "  ${GREEN}# Ouvrir le rapport HTML :${NC}"
echo -e "  xdg-open htmlcov/index.html"
echo ""
echo -e "  ${GREEN}# Voir seulement le résumé :${NC}"
echo -e "  coverage report"
echo ""
echo -e "  ${GREEN}# Voir les détails d'un fichier :${NC}"
echo -e "  coverage report --include='src/geneweb/application/services.py'"
echo ""
echo -e "  ${GREEN}# Relancer les tests :${NC}"
echo -e "  ./run_tests_with_coverage.sh"
echo -e "${BLUE}==========================================${NC}"

exit $TEST_EXIT_CODE
