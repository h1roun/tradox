from flask import Flask, render_template, request, jsonify
import osmnx as ox
import networkx as nx
import folium
import os
import numpy as np
from math import radians, cos, sin, asin, sqrt
import pickle

# NumPy 2.0 compatibility fix
if not hasattr(np, 'float_'):
    np.float_ = np.float64

app = Flask(__name__)

# Bejaia coordinates and settings
BEJAIA_COORDS = (36.7528, 5.0567)
AMIZOUR_COORDS = (36.6404, 4.9006)
BEJAIA_RADIUS = 30000  # 30km radius around Bejaia

# Path for cached graph
GRAPH_CACHE_PATH = 'bejaia_graph.pickle'

# Load or create graph
def get_road_graph():
    """Load graph from cache or download if not available"""
    if os.path.exists(GRAPH_CACHE_PATH):
        try:
            print("Loading graph from cache...")
            with open(GRAPH_CACHE_PATH, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading cached graph: {e}")
    
    print("Downloading road network data...")
    try:
        G = ox.graph_from_point(BEJAIA_COORDS, dist=BEJAIA_RADIUS, network_type='drive')
        with open(GRAPH_CACHE_PATH, 'wb') as f:
            pickle.dump(G, f)
        return G
    except Exception as e:
        print(f"Error downloading graph: {e}")
        return None

# Initialize graph
road_graph = get_road_graph()

# Haversine function for A* heuristic
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth specified in decimal degrees
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km * 1000  # Return in meters

# Dijkstra algorithm implementation with NetworkX
def find_path_dijkstra(graph, start_node, end_node):
    """
    Find shortest path using Dijkstra's algorithm
    Dijkstra works by exploring all possible paths, prioritizing the lowest cumulative distance
    """
    if not graph:
        return None, 0
    
    # Use NetworkX's implementation of Dijkstra's algorithm
    path = nx.dijkstra_path(graph, start_node, end_node, weight='length')
    
    # Calculate total path length
    path_length = int(sum(graph[path[i]][path[i+1]][0]['length'] for i in range(len(path)-1)))
    
    return path, path_length

# A* algorithm implementation with NetworkX
def find_path_astar(graph, start_node, end_node):
    """
    Find shortest path using A* algorithm
    A* uses a heuristic to guide the search towards the destination more efficiently
    """
    if not graph:
        return None, 0
    
    # Define heuristic function for A*: direct distance to destination
    def heuristic(n1, n2):
        x1, y1 = graph.nodes[n1]['x'], graph.nodes[n1]['y']
        x2, y2 = graph.nodes[n2]['x'], graph.nodes[n2]['y']
        return haversine(x1, y1, x2, y2)
    
    # Use NetworkX's implementation of A* algorithm
    path = nx.astar_path(graph, start_node, end_node, 
                         heuristic=lambda n, goal: heuristic(n, goal),
                         weight='length')
    
    # Calculate total path length
    path_length = int(sum(graph[path[i]][path[i+1]][0]['length'] for i in range(len(path)-1)))
    
    return path, path_length

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find_path', methods=['POST'])
def find_path():
    algorithm = request.json.get('algorithm', 'dijkstra')
    
    if not road_graph:
        return jsonify({"error": "No road network data available"}), 500
    
    try:
        # Find nearest nodes to our locations
        start_node = ox.distance.nearest_nodes(road_graph, AMIZOUR_COORDS[1], AMIZOUR_COORDS[0])
        end_node = ox.distance.nearest_nodes(road_graph, BEJAIA_COORDS[1], BEJAIA_COORDS[0])
        
        # Find path based on selected algorithm
        if algorithm == 'dijkstra':
            path, path_length = find_path_dijkstra(road_graph, start_node, end_node)
            algorithm_name = "Dijkstra's Algorithm"
            path_color = 'blue'
            weight = 5
        else:  # A* algorithm
            path, path_length = find_path_astar(road_graph, start_node, end_node)
            algorithm_name = "A* Algorithm"
            path_color = 'red'
            weight = 5
        
        if not path:
            return jsonify({"error": "No path found"}), 404
        
        # Extract coordinates for the path
        route_coords = [(road_graph.nodes[node]['y'], road_graph.nodes[node]['x']) for node in path]
        
        # Create the map with custom styling
        m = folium.Map(
            location=[(AMIZOUR_COORDS[0] + BEJAIA_COORDS[0]) / 2, (AMIZOUR_COORDS[1] + BEJAIA_COORDS[1]) / 2],
            zoom_start=11,
            tiles='CartoDB positron'  # Clean, modern map style
        )
        
        # Enhanced markers with custom icons
        folium.Marker(
            AMIZOUR_COORDS, 
            popup="<b>Amizour</b><br>Starting Point",
            tooltip="Start: Amizour", 
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)
        
        folium.Marker(
            BEJAIA_COORDS, 
            popup="<b>Bejaia</b><br>Destination",
            tooltip="End: Bejaia", 
            icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
        ).add_to(m)
        
        # Add path line with enhanced styling and animation
        path_options = {
            'color': path_color,
            'weight': weight,
            'opacity': 0.8,
            'dashArray': '5, 8' if algorithm == 'astar' else None,  # Dashed line for A*
            'lineCap': 'round',
            'className': f'{algorithm}-path'
        }
        
        tooltip_html = f"""
        <div style="font-family: 'Open Sans', sans-serif; padding: 5px;">
            <span style="font-weight: bold;">Distance:</span> {path_length/1000:.2f} km<br>
            <span style="font-weight: bold;">Algorithm:</span> {algorithm_name}
        </div>
        """
        
        folium.PolyLine(
            route_coords,
            tooltip=folium.Tooltip(tooltip_html),
            **path_options
        ).add_to(m)
        
        # Add distance circles around points for visual context
        folium.Circle(
            AMIZOUR_COORDS,
            radius=800,
            color='green',
            fill=True,
            fill_opacity=0.1
        ).add_to(m)
        
        folium.Circle(
            BEJAIA_COORDS,
            radius=800,
            color='red',
            fill=True,
            fill_opacity=0.1
        ).add_to(m)
        
        # Add custom CSS for route animation
        custom_css = """
        <style>
            .dijkstra-path {
                stroke-dasharray: 1000;
                stroke-dashoffset: 1000;
                animation: dash 3s linear forwards;
            }
            .astar-path {
                stroke-dasharray: 1000;
                stroke-dashoffset: 1000;
                animation: dash 3s linear forwards;
            }
            @keyframes dash {
                to {
                    stroke-dashoffset: 0;
                }
            }
            .leaflet-popup-content-wrapper {
                border-radius: 8px;
                padding: 5px;
            }
            .leaflet-popup-content {
                margin: 10px 12px;
                line-height: 1.5;
            }
        </style>
        """
        
        m.get_root().header.add_child(folium.Element(custom_css))
        
        map_html = m._repr_html_()
        
        return jsonify({
            "map_html": map_html,
            "distance": f"{path_length/1000:.2f} km",
            "algorithm": algorithm_name,
            "nodes": len(path),
            "path_simplified": route_coords[::10]  # Simplified path for visualization
        })
        
    except Exception as e:
        print(f"Error finding path: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
