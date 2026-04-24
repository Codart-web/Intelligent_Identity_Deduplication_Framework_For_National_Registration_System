#!/bin/bash
# =============================================================
# INCEPTION PHASE SETUP SCRIPT
# Intelligent Identity Deduplication Framework
# Nathan Sachitembe · 2022090446
# Run this from inside your cloned GitHub repository
# =============================================================

echo "Creating project folder structure..."

# Root-level folders
mkdir -p poc
mkdir -p tier1_terminals/templates
mkdir -p tier1_terminals/static
mkdir -p tier2_central/api_gateway
mkdir -p tier2_central/deduplication_engine
mkdir -p tier2_central/bantu_normalisation
mkdir -p tier2_central/batch_audit_scanner
mkdir -p tier2_central/database/migrations
mkdir -p tier2_central/admin_dashboard/templates
mkdir -p tier2_central/admin_dashboard/static
mkdir -p tier3_api
mkdir -p dataset/synthetic_faces
mkdir -p evaluation/results
mkdir -p tests
mkdir -p docs

echo "Creating placeholder files..."

# poc/
touch poc/faiss_poc.ipynb
touch poc/lsh_poc.ipynb
touch poc/bantu_poc.ipynb
# poc_results.md copied from docs below

# tier1_terminals/
touch tier1_terminals/app.py
touch tier1_terminals/slot_id.py
touch tier1_terminals/local_db.py
touch tier1_terminals/sync_worker.py
touch tier1_terminals/conflict_handler.py
touch tier1_terminals/Dockerfile.terminal

# tier2_central/api_gateway/
touch tier2_central/api_gateway/app.py
touch tier2_central/api_gateway/auth.py
touch tier2_central/api_gateway/rate_limiter.py

# tier2_central/deduplication_engine/
touch tier2_central/deduplication_engine/pipeline.py
touch tier2_central/deduplication_engine/quality_assessment.py
touch tier2_central/deduplication_engine/channel_a_lsh.py
touch tier2_central/deduplication_engine/channel_b_faiss.py
touch tier2_central/deduplication_engine/facenet_encoder.py
touch tier2_central/deduplication_engine/demographic_scorer.py
touch tier2_central/deduplication_engine/biometric_scorer.py
touch tier2_central/deduplication_engine/fusion.py
touch tier2_central/deduplication_engine/decision.py
touch tier2_central/deduplication_engine/xai_payload.py

# tier2_central/bantu_normalisation/ (original contribution)
touch tier2_central/bantu_normalisation/normaliser.py
touch tier2_central/bantu_normalisation/rules.json
touch tier2_central/bantu_normalisation/test_normaliser.py

# tier2_central/batch_audit_scanner/ [NEW]
touch tier2_central/batch_audit_scanner/scanner.py
touch tier2_central/batch_audit_scanner/test_scanner.py

# tier2_central/database/
touch tier2_central/database/models.py
touch tier2_central/database/seed.py

# tier2_central/admin_dashboard/
touch tier2_central/admin_dashboard/app.py
touch tier2_central/admin_dashboard/resolver.py
touch tier2_central/admin_dashboard/Dockerfile.central

# tier3_api/
touch tier3_api/app.py
touch tier3_api/auth.py
touch tier3_api/Dockerfile.api

# dataset/
touch dataset/duplicate_injector.py
touch dataset/zambian_names.csv
touch dataset/citizens_1000.csv
touch dataset/ground_truth.csv
touch dataset/bantu_variants_50.csv

# evaluation/
touch evaluation/baseline_a.py
touch evaluation/baseline_b.py
touch evaluation/evaluate_framework.py
touch evaluation/metrics.py
touch evaluation/confusion_matrices.py

# tests/
touch tests/test_bantu.py
touch tests/test_fusion.py
touch tests/test_decision.py
touch tests/test_pipeline.py
touch tests/test_scanner.py
touch tests/test_type5_conflict.py

# Root files
touch start.sh
touch requirements.txt
touch config.json
touch .env

echo "Writing config.json..."
cat > config.json << 'EOF'
{
  "thresholds": {
    "clear_below": 0.55,
    "block_above": 0.85
  },
  "fusion": {
    "w_bio_min": 0.40,
    "w_bio_max": 0.70,
    "quality_scale": 0.30
  },
  "lsh": {
    "num_perm": 128,
    "threshold": 0.5
  },
  "faiss": {
    "nprobe": 10,
    "top_k": 5
  },
  "batch_scanner": {
    "cosine_threshold": 0.55
  }
}
EOF

echo "Writing .env template..."
cat > .env << 'EOF'
# PostgreSQL connection
DATABASE_URL=postgresql://nrc_user:nrc_pass@localhost/nrc_db
POSTGRES_DB=nrc_db
POSTGRES_USER=nrc_user
POSTGRES_PASSWORD=nrc_pass

# Flask
FLASK_SECRET_KEY=change-this-to-a-random-string
FLASK_ENV=development

# Central server URL (used by terminals)
CENTRAL_URL=http://localhost:5000

# Terminal IDs
TERMINAL_ID=LUSAKA
EOF

echo "Writing start.sh..."
cat > start.sh << 'EOF'
#!/bin/bash
# =============================================
# Start all NRC Deduplication Framework services
# Run from project root with: ./start.sh
# =============================================

source venv/bin/activate

echo "Starting PostgreSQL..."
sudo systemctl start postgresql

echo "Starting central server (port 5000)..."
cd tier2_central && python api_gateway/app.py &
CENTRAL_PID=$!
cd ..

sleep 2

echo "Starting Lusaka terminal (port 5001)..."
cd tier1_terminals
TERMINAL_ID=LUSAKA PORT=5001 python app.py &
LUSAKA_PID=$!

echo "Starting Kitwe terminal (port 5002)..."
TERMINAL_ID=KITWE PORT=5002 python app.py &
KITWE_PID=$!

echo "Starting Ndola terminal (port 5003)..."
TERMINAL_ID=NDOLA PORT=5003 python app.py &
NDOLA_PID=$!
cd ..

echo "Starting Tier 3 API stub (port 5004)..."
cd tier3_api && python app.py &
TIER3_PID=$!
cd ..

echo ""
echo "============================================"
echo "All services running. Access at:"
echo "  Admin dashboard : http://localhost:5000"
echo "  Lusaka terminal : http://localhost:5001"
echo "  Kitwe terminal  : http://localhost:5002"
echo "  Ndola terminal  : http://localhost:5003"
echo "  Tier 3 API      : http://localhost:5004"
echo "============================================"
echo "Press Ctrl+C to stop all services."
echo ""

trap "echo 'Stopping all services...'; kill 0" EXIT
wait
EOF
chmod +x start.sh

echo "Writing requirements.txt..."
cat > requirements.txt << 'EOF'
# Core framework
flask==3.0.0
python-dotenv==1.0.0
requests==2.31.0

# Database
sqlalchemy==2.0.0
psycopg2-binary==2.9.9
pgvector==0.2.4

# Machine learning
tensorflow-cpu==2.15.0
facenet-pytorch==2.5.3
faiss-cpu==1.7.4
numpy==1.26.0

# Computer vision
opencv-python-headless==4.9.0.80

# NLP / similarity
datasketch==1.6.4
jellyfish==1.0.3

# Data generation
faker==24.0.0

# Evaluation
scikit-learn==1.4.0

# Development
jupyter==1.0.0
EOF

echo ""
echo "============================================"
echo "Project structure created successfully."
echo ""
echo "NEXT STEPS:"
echo "1. Copy docs/ files into your docs/ folder"
echo "2. Copy README.md to project root"
echo "3. git add . && git commit -m 'Inception complete: project structure, all docs, config'"
echo "4. git push"
echo ""
echo "THEN — Week 3 Day 1:"
echo "5. source venv/bin/activate"
echo "6. jupyter notebook  →  open poc/faiss_poc.ipynb"
echo "7. Run KILL RISK experiment before anything else"
echo "============================================"
