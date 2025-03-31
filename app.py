from flask import Flask, render_template, request, jsonify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
import json
import os

from src.benchmark import run_benchmark
from src.endpoints import get_endpoints
from src.constants import PROVIDERS

app = Flask(__name__)

@app.route('/')
def index():
    providers = {k: v for k, v in PROVIDERS.items()}
    return render_template('index.html', providers=providers)

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
        # Create a version of results suitable for JSON serialization
        json_results = {}
        for k, v in results.items():
            json_results[k] = {kk: vv for kk, vv in v.items() if kk != 'hops'}
            # Extract key hop data with geo info for visualization
            hops = []
            countries_traversed = set()
            for hop in v['hops']:
                hop_data = {
                    'ttl': hop.get('ttl'),
                    'ip': hop.get('ip'),
                    'rtt': hop.get('rtt'),
                    'status': hop.get('status')
                }
                # Add geo data if available
                if 'geo' in hop:
                    hop_data['geo'] = hop['geo']
                    if 'country' in hop['geo']:
                        countries_traversed.add(hop['geo']['country'])
                    if 'lat' in hop and 'lon' in hop:
                        hop_data['lat'] = hop['lat']
                        hop_data['lon'] = hop['lon']
                hops.append(hop_data)
            json_results[k]['hops'] = hops
            json_results[k]['countries_traversed'] = len(countries_traversed)
            json_results[k]['countries_list'] = list(countries_traversed)
        
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
    
    # Create bar chart comparing avg RTT
    endpoints = list(results.keys())
    provider_names = [PROVIDERS.get(endpoint.split('.')[0], endpoint) for endpoint in endpoints]
    avg_rtts = [results[e]["avg_rtt_ms"] for e in endpoints]
    
    rtt_bar = go.Figure(data=[
        go.Bar(x=provider_names, y=avg_rtts, marker_color='skyblue', 
               text=[f"{rtt:.1f} ms" for rtt in avg_rtts],
               textposition='auto')
    ])
    rtt_bar.update_layout(
        title="Average Response Time by Cloud Provider",
        xaxis_title="Cloud Provider",
        yaxis_title="Average RTT (ms)",
        template="plotly_white"
    )
    
    # Create hop latency line chart
    hop_latency = go.Figure()
    
    for endpoint in endpoints:
        provider = endpoint.split('.')[0]
        display_name = PROVIDERS.get(provider, provider)
        
        # Extract valid hops with RTT values and sort by TTL
        valid_hops = [h for h in results[endpoint]["hops"] if h.get("status") == "success" and h.get("rtt") is not None]
        valid_hops.sort(key=lambda x: x.get("ttl", 0))
        
        if valid_hops:
            ttls = [h["ttl"] for h in valid_hops]
            rtts = [h["rtt"] for h in valid_hops]
            
            # Create hover text with geo info when available
            hover_texts = []
            for hop in valid_hops:
                text = f"TTL: {hop['ttl']}<br>IP: {hop['ip']}<br>RTT: {hop['rtt']:.2f} ms"
                if 'geo' in hop:
                    geo = hop['geo']
                    if 'city' in geo and 'country' in geo:
                        text += f"<br>Location: {geo.get('city')}, {geo.get('country')}"
                    elif 'country' in geo:
                        text += f"<br>Country: {geo.get('country')}"
                    if 'org' in geo:
                        text += f"<br>Organization: {geo.get('org')}"
                hover_texts.append(text)
            
            hop_latency.add_trace(go.Scatter(
                x=ttls, 
                y=rtts,
                mode='lines+markers',
                name=display_name,
                hovertext=hover_texts,
                hoverinfo='text'
            ))
    
    hop_latency.update_layout(
        title="RTT per Hop by Cloud Provider",
        xaxis_title="Hop Number (TTL)",
        yaxis_title="RTT (ms)",
        template="plotly_white",
        legend_title="Cloud Provider"
    )
    
    # Create hop latency differential chart to show latency added by each hop
    hop_differential = go.Figure()
    
    for endpoint in endpoints:
        provider = endpoint.split('.')[0]
        display_name = PROVIDERS.get(provider, provider)
        
        # Extract valid hops with hop_latency values
        latency_hops = [h for h in results[endpoint]["hops"] 
                        if h.get("status") == "success" and "hop_latency" in h]
        
        if latency_hops:
            # Sort by TTL to ensure correct order
            latency_hops.sort(key=lambda x: x.get("ttl", 0))
            
            ttls = [h["ttl"] for h in latency_hops]
            latencies = [h["hop_latency"] for h in latency_hops]
            
            # Create hover text with geo info when available
            hover_texts = []
            for hop in latency_hops:
                text = f"TTL: {hop['ttl']}<br>IP: {hop['ip']}<br>Added Latency: {hop['hop_latency']:.2f} ms"
                if 'geo' in hop:
                    geo = hop['geo']
                    if 'city' in geo and 'country' in geo:
                        text += f"<br>Location: {geo.get('city')}, {geo.get('country')}"
                    elif 'country' in geo:
                        text += f"<br>Country: {geo.get('country')}"
                    if 'org' in geo:
                        text += f"<br>Organization: {geo.get('org')}"
                hover_texts.append(text)
            
            hop_differential.add_trace(go.Bar(
                x=ttls,
                y=latencies,
                name=display_name,
                hovertext=hover_texts,
                hoverinfo='text'
            ))
    
    hop_differential.update_layout(
        title="Latency Added by Each Hop",
        xaxis_title="Hop Number (TTL)",
        yaxis_title="Latency Added (ms)",
        template="plotly_white",
        legend_title="Cloud Provider",
        barmode='group'
    )
    
    # Create world map with route visualization
    # First, create a dataframe with all the hop points
    map_data = []
    
    for endpoint in endpoints:
        provider = endpoint.split('.')[0]
        display_name = PROVIDERS.get(provider, provider)
        
        # Extract valid hops with geo data
        geo_hops = [h for h in results[endpoint]["hops"] 
                   if h.get("status") == "success" and "lat" in h and "lon" in h]
        
        # Sort by TTL to ensure correct path order
        geo_hops.sort(key=lambda x: x.get("ttl", 0))
        
        for hop in geo_hops:
            hop_data = {
                'provider': display_name,
                'endpoint': endpoint,
                'ttl': hop['ttl'],
                'lat': hop['lat'],
                'lon': hop['lon'],
                'rtt': hop.get('rtt', 0),
            }
            
            # Add location information if available
            if 'geo' in hop:
                geo = hop['geo']
                location_parts = []
                
                if 'city' in geo and geo['city']:
                    location_parts.append(geo['city'])
                if 'region' in geo and geo['region']:
                    location_parts.append(geo['region'])
                if 'country' in geo and geo['country']:
                    location_parts.append(geo['country'])
                
                hop_data['location'] = ', '.join(location_parts) if location_parts else 'Unknown'
                hop_data['org'] = geo.get('org', 'Unknown')
            else:
                hop_data['location'] = 'Unknown'
                hop_data['org'] = 'Unknown'
            
            map_data.append(hop_data)
    
    if map_data:
        df = pd.DataFrame(map_data)
        
        # Create the map
        geo_map = px.scatter_geo(
            df,
            lat='lat',
            lon='lon',
            color='provider',
            hover_name='location',
            hover_data={
                'provider': True,
                'ttl': True,
                'rtt': ':.2f',
                'org': True,
                'lat': False,
                'lon': False,
                'endpoint': False
            },
            size='rtt',
            size_max=15,
            projection='natural earth',
            title='Network Path Visualization'
        )
        
        # Add lines connecting hops for each provider
        for endpoint in endpoints:
            provider = endpoint.split('.')[0]
            display_name = PROVIDERS.get(provider, provider)
            
            # Filter for this provider's hops with geo data and sort by TTL
            provider_hops = [h for h in results[endpoint]["hops"] 
                            if h.get("status") == "success" and "lat" in h and "lon" in h]
            
            if len(provider_hops) >= 2:
                # Sort by TTL
                provider_hops.sort(key=lambda x: x.get("ttl", 0))
                
                # Extract coordinates
                lats = [h['lat'] for h in provider_hops]
                lons = [h['lon'] for h in provider_hops]
                
                # Add the line trace
                geo_map.add_trace(
                    go.Scattergeo(
                        lat=lats,
                        lon=lons,
                        mode='lines',
                        line=dict(width=2, color=px.colors.qualitative.Plotly[endpoints.index(endpoint) % len(px.colors.qualitative.Plotly)]),
                        name=f"{display_name} Path"
                    )
                )
        
        geo_map.update_layout(
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            legend_title_text='Cloud Provider',
            geo=dict(
                showland=True,
                landcolor='rgb(243, 243, 243)',
                countrycolor='rgb(204, 204, 204)',
                showocean=True,
                oceancolor='rgb(230, 230, 250)',
                showlakes=True,
                lakecolor='rgb(230, 230, 250)',
                showrivers=True,
                rivercolor='rgb(230, 230, 250)'
            )
        )
    else:
        # Create empty map if no geo data
        geo_map = go.Figure(go.Scattergeo())
        geo_map.update_layout(
            title="No geolocation data available",
            height=600
        )
    
    # Create success rate gauges
    gauges = []
    for i, endpoint in enumerate(endpoints):
        provider = endpoint.split('.')[0]
        display_name = PROVIDERS.get(provider, provider)
        
        gauges.append(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=results[endpoint]["success_rate"],
                title={"text": f"{display_name} Success Rate"},
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
        'hop_differential': hop_differential.to_json(),
        'geo_map': geo_map.to_json(),
        'gauges': [gauge.to_json() for gauge in gauges]
    }
    
    # Create a mapping of endpoints to provider display names
    provider_display = {endpoint: PROVIDERS.get(endpoint.split('.')[0], endpoint) for endpoint in endpoints}
    
    return render_template('visualize.html', 
                          charts=charts, 
                          results=results,
                          endpoints=endpoints,
                          provider_display=provider_display)

if __name__ == '__main__':
    app.run(debug=True)