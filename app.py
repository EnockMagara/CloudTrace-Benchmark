from flask import Flask, render_template, request, jsonify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import json
import os

from src.benchmark import run_benchmark
from src.endpoints import get_endpoints

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/benchmark', methods=['POST'])
def run_benchmark_endpoint():
    data = request.json
    selected_providers = data.get('providers', ['aws', 'azure', 'gcp'])
    
    endpoints = get_endpoints(selected_providers)
    results = run_benchmark(endpoints)
    
    # Save to a temporary file
    result_path = Path('data/latest_results.json')
    result_path.parent.mkdir(exist_ok=True)
    
    with open(result_path, 'w') as f:
        json_results = {k: {kk: vv for kk, vv in v.items() if kk != 'hops'} for k, v in results.items()}
        hops_data = {k: v['hops'] for k, v in results.items()}
        
        # Store processed hop data for visualization
        hop_viz_data = {}
        for endpoint, hops in hops_data.items():
            valid_hops = [h for h in hops if h["status"] == "success"]
            hop_viz_data[endpoint] = {
                'ttls': [h["ttl"] for h in valid_hops],
                'rtts': [h["rtt"] for h in valid_hops],
                'ips': [h["ip"] for h in valid_hops]
            }
        
        json_results['hop_data'] = hop_viz_data
        json.dump(json_results, f)
    
    return jsonify(results)

@app.route('/results')
def get_results():
    result_path = Path('data/latest_results.json')
    if not result_path.exists():
        return jsonify({"error": "No results found. Run a benchmark first."})
    
    with open(result_path, 'r') as f:
        results = json.load(f)
    
    return jsonify(results)

@app.route('/visualize')
def visualize():
    result_path = Path('data/latest_results.json')
    if not result_path.exists():
        return render_template('no_results.html')
    
    with open(result_path, 'r') as f:
        results = json.load(f)
    
    # Create RTT bar chart
    endpoints = [k for k in results.keys() if k != 'hop_data']
    avg_rtts = [results[e]["avg_rtt_ms"] for e in endpoints]
    
    rtt_bar = go.Figure(data=[
        go.Bar(x=endpoints, y=avg_rtts, marker_color='skyblue')
    ])
    rtt_bar.update_layout(
        title="Average RTT by Cloud Provider",
        xaxis_title="Endpoint",
        yaxis_title="Average RTT (ms)",
        template="plotly_white"
    )
    
    # Create hop latency line chart
    hop_data = results['hop_data']
    
    hop_latency = go.Figure()
    for endpoint, data in hop_data.items():
        hop_latency.add_trace(go.Scatter(
            x=data['ttls'],
            y=data['rtts'],
            mode='lines+markers',
            name=endpoint,
            hovertext=[f"IP: {ip}<br>RTT: {rtt:.2f} ms" for ip, rtt in zip(data['ips'], data['rtts'])]
        ))
    
    hop_latency.update_layout(
        title="RTT per Hop by Cloud Provider",
        xaxis_title="Hop Number (TTL)",
        yaxis_title="RTT (ms)",
        template="plotly_white",
        legend_title="Cloud Provider"
    )
    
    # Create success rate gauge
    success_rates = [results[e]["success_rate"] for e in endpoints]
    
    gauges = []
    for i, endpoint in enumerate(endpoints):
        gauges.append(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=results[endpoint]["success_rate"],
                title={"text": f"{endpoint} Success Rate"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "red"},
                        {'range': [50, 80], 'color': "orange"},
                        {'range': [80, 100], 'color': "green"}
                    ]
                }
            ))
        )
        gauges[i].update_layout(height=300)
    
    # Convert to JSON
    charts = {
        'rtt_bar': rtt_bar.to_json(),
        'hop_latency': hop_latency.to_json(),
        'gauges': [gauge.to_json() for gauge in gauges]
    }
    
    return render_template('visualize.html', 
                          charts=charts, 
                          results=results,
                          endpoints=endpoints)

if __name__ == '__main__':
    app.run(debug=True)