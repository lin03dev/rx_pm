# Fix the script and run it
cd ~/workspace/dev/scripts/python/db/reporting/Rx_PM && \
head -n -20 run_all.sh > run_all_fixed.sh && \
mv run_all_fixed.sh run_all.sh && \
sed -i 's/python /python3 /g' run_all.sh && \
chmod +x run_all.sh && \
./run_all.sh


==================
find . \
  -type f \
  \( \
    -name "*.py" \
    -o -name "*.sh" \
    -o -name "requirements.txt" \
    -o -name "*.yaml" -o -name "*.yml" \
    -o -name "*.json" \
    -o -name "*.dbml" \
  \) \
  ! -path "./venv/*" \
  ! -path "./output/*" \
  ! -path "./logs/*" \
  ! -path "*/__pycache__/*" \
  ! -name "*.pyc" \
  ! -name "passwords.env" \
  ! -name "consolidated_code.txt" \
  ! -name "analysis_*.txt" \
  -print0 | sort -z | xargs -0 -I {} sh -c 'printf "\n===== FILE: %s =====\n\n" "{}"; cat "{}"' \
  > consolidated_code.txt