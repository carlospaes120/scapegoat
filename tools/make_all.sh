#!/bin/bash
# Script para executar análises de múltiplos casos
# 
# Uso:
#   bash make_all.sh
#
# Nota: Ajuste os caminhos dos arquivos de dados conforme necessário

set -e

echo "======================================"
echo "PIPELINE DE ANÁLISE DE EMERGÊNCIA"
echo "======================================"
echo ""

# Exemplo: Caso Monark
# Descomente e ajuste o caminho conforme seus dados
# echo "Analisando caso: Monark..."
# python main_case.py \
#   --case_name "Monark" \
#   --inputs data/monark/*.jsonl \
#   --bin_hours 1 \
#   --tz "America/Sao_Paulo" \
#   --pre_frac 0.2 \
#   --k_consec 2
# echo ""

# Exemplo: Caso Karol Conka
# echo "Analisando caso: KarolConka..."
# python main_case.py \
#   --case_name "KarolConka" \
#   --inputs data/karol_conka/*.jsonl \
#   --bin_hours 1 \
#   --tz "America/Sao_Paulo" \
#   --pre_frac 0.2 \
#   --k_consec 2
# echo ""

# Exemplo: Caso Wagner
# echo "Analisando caso: Wagner..."
# python main_case.py \
#   --case_name "Wagner" \
#   --inputs data/wagner/*.jsonl \
#   --bin_hours 6 \
#   --tz "America/Sao_Paulo" \
#   --pre_frac 0.2 \
#   --k_consec 2
# echo ""

# Exemplo: Caso Eduardo Bueno
# echo "Analisando caso: EduardoBueno..."
# python main_case.py \
#   --case_name "EduardoBueno" \
#   --inputs data/eduardo_bueno/*.jsonl \
#   --bin_hours 1 \
#   --tz "America/Sao_Paulo" \
#   --pre_frac 0.2 \
#   --k_consec 2
# echo ""

echo "======================================"
echo "TODAS AS ANÁLISES CONCLUÍDAS!"
echo "======================================"





