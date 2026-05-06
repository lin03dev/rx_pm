#!/bin/bash
# run_all.sh - Generate all reports including LMS batch reports

set -e

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    UNIFIED REPORTING SYSTEM - COMPLETE RUN                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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
pip install pandas openpyxl psycopg2-binary python-dotenv pyyaml sqlalchemy -q 2>/dev/null
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 2: Directory Setup
print_section "STEP 2: Setting up directories"
mkdir -p output/reports/{AG,LMS,Telios,Language}
mkdir -p output/templates/{AG,LMS,Telios,Language}
echo -e "${GREEN}✅ Directories created${NC}"

# Step 3: Generate All Excel Templates
print_section "STEP 3: Generating Excel templates"
python3 scripts/generate_templates.py
echo -e "${GREEN}✅ Templates generated${NC}"

# Step 4: Generate AG_Dev Reports
print_section "STEP 4: Generating AG_Dev Reports → ${CYAN}output/reports/AG/${NC}"
python3 run.py --report consolidated --database AG_Dev --format excel
python3 run.py --report bible-completion --database AG_Dev --format excel
python3 run.py --report obs-completion --database AG_Dev --format excel
python3 run.py --report literature-completion --database AG_Dev --format excel
python3 run.py --report grammar-completion --database AG_Dev --format excel
python3 run.py --report ag-drafting --database AG_Dev --format excel
python3 run.py --report user --database AG_Dev --format excel
python3 run.py --report worklog --database AG_Dev --format excel

# Step 5: Generate LMS Reports
print_section "STEP 5: Generating LMS Reports → ${CYAN}output/reports/LMS/${NC}"

# Generate LMS templates
python3 scripts/generate_lms_templates.py

# Generate batch detailed reports
python3 scripts/generate_lms_batch_reports.py

# Generate LMS summary report
python3 run.py --report lms --database Telios_LMS_Dev --format excel

# Step 6: Generate Language Survey Templates
print_section "STEP 6: Generating Language Survey Templates → ${CYAN}output/templates/Language/${NC}"
python3 scripts/generate_cluster_template.py
python3 scripts/generate_dynamic_language_templates.py
python3 scripts/generate_language_uploader_template.py
python3 scripts/generate_dynamic_workbook.py

# Step 7: Show Results
print_section "🎉 GENERATION COMPLETE!"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                           GENERATION SUMMARY                                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

deactivate 2>/dev/null

echo -e "${GREEN}✅ All tasks completed successfully!${NC}"
