@echo off
REM Script para executar análises de múltiplos casos no Windows
REM 
REM Uso:
REM   make_all.bat
REM
REM Nota: Ajuste os caminhos dos arquivos de dados conforme necessário

echo ======================================
echo PIPELINE DE ANALISE DE EMERGENCIA
echo ======================================
echo.

REM Exemplo: Caso Monark
REM Descomente e ajuste o caminho conforme seus dados
REM echo Analisando caso: Monark...
REM python main_case.py ^
REM   --case_name "Monark" ^
REM   --inputs data/monark/*.jsonl ^
REM   --bin_hours 1 ^
REM   --tz "America/Sao_Paulo" ^
REM   --pre_frac 0.2 ^
REM   --k_consec 2
REM echo.

REM Exemplo: Caso Karol Conka
REM echo Analisando caso: KarolConka...
REM python main_case.py ^
REM   --case_name "KarolConka" ^
REM   --inputs data/karol_conka/*.jsonl ^
REM   --bin_hours 1 ^
REM   --tz "America/Sao_Paulo" ^
REM   --pre_frac 0.2 ^
REM   --k_consec 2
REM echo.

REM Exemplo: Caso Wagner
REM echo Analisando caso: Wagner...
REM python main_case.py ^
REM   --case_name "Wagner" ^
REM   --inputs data/wagner/*.jsonl ^
REM   --bin_hours 6 ^
REM   --tz "America/Sao_Paulo" ^
REM   --pre_frac 0.2 ^
REM   --k_consec 2
REM echo.

REM Exemplo: Caso Eduardo Bueno
REM echo Analisando caso: EduardoBueno...
REM python main_case.py ^
REM   --case_name "EduardoBueno" ^
REM   --inputs data/eduardo_bueno/*.jsonl ^
REM   --bin_hours 1 ^
REM   --tz "America/Sao_Paulo" ^
REM   --pre_frac 0.2 ^
REM   --k_consec 2
REM echo.

echo ======================================
echo TODAS AS ANALISES CONCLUIDAS!
echo ======================================
pause





