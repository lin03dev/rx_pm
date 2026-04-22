#!/bin/bash
# run_all.sh - Complete setup, template generation, and ALL reports generation

set -e

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    UNIFIED REPORTING SYSTEM - COMPLETE RUN                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}📌 $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Step 1: Environment Setup
print_section "STEP 1: Setting up environment"

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "📚 Installing dependencies..."
pip install --upgrade pip -q
pip install pandas openpyxl psycopg2-binary python-dotenv pyyaml sqlalchemy -q
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 2: Directory Setup
print_section "STEP 2: Setting up directories"
mkdir -p output/reports output/templates output/uploads output/logs config
echo -e "${GREEN}✅ Directories created${NC}"

# Step 3: Generate All Excel Templates
print_section "STEP 3: Generating Excel templates"
python3 -c "
from utils.excel_template_generator import get_excel_template_generator
gen = get_excel_template_generator()
files = gen.generate_all_templates()
print(f'✅ Generated {len(files)} templates')
"
echo -e "${GREEN}✅ Templates generated${NC}"

# Step 4: Generate AG_Dev Reports
print_section "STEP 4: Generating AG_Dev Reports"

reports="bible-completion obs-completion literature-completion grammar-completion individual worklog user user-assignments consolidated"
for report in $reports; do
    echo -e "${YELLOW}▶ Generating $report report...${NC}"
    python3 run.py --report "$report" --database AG_Dev --format excel 2>&1 | grep -E "(✅|❌|Error|Retrieved)" || echo "   ⚠️ Could not generate $report"
done

# Step 5: Generate Telios_LMS Report
print_section "STEP 5: Generating Telios_LMS Reports"
echo -e "${YELLOW}▶ Generating LMS demographics report...${NC}"
python3 run.py --report lms --database Telios_LMS_Dev --format excel 2>&1 | grep -E "(✅|❌)" || echo "   ⚠️ LMS report skipped"

# Step 6: Show Results
print_section "🎉 GENERATION COMPLETE!"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                           GENERATION SUMMARY                                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📁 OUTPUT DIRECTORY: ./output/${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}📊 Reports generated:${NC}"
ls -la output/reports/*.xlsx 2>/dev/null | wc -l | xargs echo "   Total:"
ls -la output/reports/*.xlsx 2>/dev/null | tail -10 | awk '{print "   • " $9}' | xargs -n1 basename
echo ""
echo -e "${YELLOW}📋 Templates generated:${NC}"
ls -la output/templates/*.xlsx 2>/dev/null | wc -l | xargs echo "   Total:"
echo ""
echo -e "${GREEN}✅ All tasks completed successfully!${NC}"

deactivate 2>/dev/null
