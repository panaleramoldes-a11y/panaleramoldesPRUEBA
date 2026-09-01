import streamlit as st
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from utils.geo_helpers import calcular_distancia_haversine

def optimizar_ruta(origen: tuple, destinos: list, destino_final: tuple = None):
    """
    Calcula el orden óptimo de visita para una lista de coordenadas usando OR-Tools.
    destinos: Lista de tuplas (lat, lng) o diccionarios con la info de cada parada.
    """
    if not destinos:
        return []

    puntos = [origen] + [d['coords'] if isinstance(d, dict) else d for d in destinos]
    if destino_final:
        puntos.append(destino_final)

    num_locations = len(puntos)
    matriz_distancias = []

    for i in range(num_locations):
        fila = []
        for j in range(num_locations):
            if i == j:
                fila.append(0)
            else:
                dist = int(calcular_distancia_haversine(puntos[i], puntos[j]) * 1000) # En metros
                fila.append(dist)
        matriz_distancias.append(fila)

    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matriz_distancias[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        orden_indices = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            orden_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))

        # Filtramos los índices omitiendo el punto de partida (0)
        # y el destino final si se incluyó
        indices_destinos = [i - 1 for i in orden_indices if 0 < i <= len(destinos)]
        return [destinos[i] for i in indices_destinos]
    else:
        st.warning("No se pudo encontrar una ruta óptima automática, devolviendo el orden original.")
        return destinos
