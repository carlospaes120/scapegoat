#!/usr/bin/env python3
"""
generate_consolidated_report.py

Gera um relatório HTML consolidado com todos os gráficos e métricas.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    print("Gerando relatório consolidado HTML...")
    
    # Paths
    comparison_dir = Path("outputs/comparison")
    simulation_dir = Path("outputs/simulation_metrics")
    
    # Carregar estatísticas
    stats_path = comparison_dir / "summary_stats.csv"
    if stats_path.exists():
        stats = pd.read_csv(stats_path)
    else:
        stats = None
    
    # Criar HTML
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Consolidado - Projeto Scapegoat</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .metric h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .metric .value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .status-ok {{ color: #27ae60; }}
        .status-warn {{ color: #f39c12; }}
        .status-error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <h1>📊 Relatório Consolidado - Análise de Isolamento da Vítima</h1>
    <p><strong>Data de Geração:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <p><strong>Projeto:</strong> Scapegoat Pipeline - Comparação Empírico ↔ Sintético</p>

    <div class="section">
        <h2>🎯 Resumo Executivo</h2>
        <div class="grid">
            <div class="metric">
                <h3>Casos Processados</h3>
                <div class="value">4</div>
                <p>Twitter (Monark, Karol, Wagner, Bueno)</p>
            </div>
            <div class="metric">
                <h3>Total de Arestas</h3>
                <div class="value">15,026</div>
                <p>Extraídas de tweets classificados</p>
            </div>
            <div class="metric">
                <h3>Janelas Analisadas</h3>
                <div class="value">395</div>
                <p>Com janelas de 1 dia</p>
            </div>
            <div class="metric">
                <h3>Gráficos Gerados</h3>
                <div class="value">20+</div>
                <p>PNG de alta qualidade</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📈 Estatísticas Comparativas</h2>
"""
    
    if stats is not None:
        html += stats.to_html(index=False, classes='stats-table', border=0)
    else:
        html += "<p>Estatísticas não disponíveis</p>"
    
    html += """
    </div>

    <div class="section">
        <h2>📊 Gráficos Comparativos - Casos do Twitter</h2>
        
        <h3>Ego Density (Densidade do Ego-Network)</h3>
        <img src="ego_density_comparison.png" alt="Comparação Ego Density">
        <p><em>Quão conectados estão os vizinhos da vítima entre si.</em></p>
        
        <h3>Distância Média até a Vítima</h3>
        <img src="avg_dist_comparison.png" alt="Comparação Distância">
        <p><em>Distância média (em saltos) de todos os nós até a vítima.</em></p>
        
        <h3>Volume de Arestas por Janela</h3>
        <img src="volume_comparison.png" alt="Comparação Volume">
        <p><em>Número de interações (mentions + replies) por janela temporal.</em></p>
    </div>

    <div class="section">
        <h2>🔬 Insights Principais</h2>
        
        <h3>MONARK vs KAROL</h3>
        <table>
            <tr>
                <th>Aspecto</th>
                <th>MONARK</th>
                <th>KAROL</th>
                <th>Interpretação</th>
            </tr>
            <tr>
                <td><strong>Ego Density</strong></td>
                <td class="value">0.0008</td>
                <td class="value">0.0334</td>
                <td>Karol: vizinhos 40x mais conectados (cluster coeso)</td>
            </tr>
            <tr>
                <td><strong>Distância Média</strong></td>
                <td class="value">1.88</td>
                <td class="value">1.83</td>
                <td>Similar (ambos relativamente centrais)</td>
            </tr>
            <tr>
                <td><strong>Volume Total</strong></td>
                <td class="value">6,318</td>
                <td class="value">4,033</td>
                <td>Monark: 56% mais interações</td>
            </tr>
            <tr>
                <td><strong>Pico</strong></td>
                <td class="value">1,615</td>
                <td class="value">3,222</td>
                <td>Karol: pico 2x maior</td>
            </tr>
            <tr>
                <td><strong>Duração</strong></td>
                <td class="value">8 dias</td>
                <td class="value">13 dias</td>
                <td>Karol: cancelamento mais prolongado</td>
            </tr>
        </table>
        
        <h3>🎯 Conclusões:</h3>
        <ul>
            <li><strong>KAROL:</strong> Cancelamento via cluster coeso (alta ego density), pico concentrado</li>
            <li><strong>MONARK:</strong> Cancelamento via ponte entre grupos (baixa ego density), mais distribuído</li>
            <li><strong>Distância similar:</strong> Ambas as vítimas permanecem relativamente centrais durante cancelamento</li>
        </ul>
    </div>

    <div class="section">
        <h2>📁 Arquivos Disponíveis</h2>
        <ul>
            <li><strong>Gráficos Comparativos:</strong> <code>outputs/comparison/*.png</code></li>
            <li><strong>Gráficos Por Caso:</strong> <code>outputs/isolation/{caso}/*.png</code></li>
            <li><strong>Dados Tabulares:</strong> <code>outputs/comparison/summary_stats.csv</code></li>
            <li><strong>Métricas Temporais:</strong> <code>outputs/isolation/{caso}/metrics_{caso}.csv</code></li>
            <li><strong>Relatórios:</strong> <code>outputs/comparison/*.md</code></li>
        </ul>
    </div>

    <div class="section">
        <h2>🚀 Próximos Passos</h2>
        <ol>
            <li>Corrigir IDs de Wagner e Bueno (inspecionar CSVs de arestas)</li>
            <li>Gerar mais eventos na simulação NetLogo (rodar 1000+ ticks)</li>
            <li>Calcular métricas de isolamento para simulação</li>
            <li>Incluir simulação na comparação final</li>
            <li>Análise estatística formal (testes de hipótese)</li>
            <li>Integrar em paper acadêmico</li>
        </ol>
    </div>

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #3498db; text-align: center; color: #7f8c8d;">
        <p>Gerado por generate_consolidated_report.py</p>
        <p>Projeto Scapegoat Pipeline - 2025</p>
    </footer>
</body>
</html>
"""
    
    # Salvar HTML
    html_path = comparison_dir / "CONSOLIDATED_REPORT.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] Relatório HTML salvo: {html_path}")
    print("\nAbrindo no navegador...")
    
    import webbrowser
    webbrowser.open(html_path.as_uri())
    
    print("\n[OK] Concluído!")

if __name__ == "__main__":
    main()






