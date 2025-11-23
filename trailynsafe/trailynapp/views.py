"""
Vista para generación de rutas optimizadas con k-Means
"""
import math
import requests
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sklearn.cluster import KMeans


@api_view(['GET'])
def health_check(request):
    """Endpoint de health check para Railway"""
    return Response({
        'status': 'ok',
        'service': 'TrailynSafe k-Means',
        'version': '1.0.0'
    })


@api_view(['POST'])
@csrf_exempt
def generar_ruta(request):
    """
    Genera una ruta optimizada usando k-Means clustering y TSP
    
    Request body:
    {
        "viaje_id": int,
        "capacidad_unidad": int,
        "destino": {
            "nombre": str,
            "direccion": str,
            "latitud": float,
            "longitud": float
        },
        "puntos_recogida": [
            {
                "confirmacion_id": int,
                "hijo_id": int,
                "nombre": str,
                "direccion": str,
                "referencia": str,
                "latitud": float,
                "longitud": float,
                "prioridad": str
            },
            ...
        ],
        "hora_salida": str (HH:MM:SS)
    }
    """
    try:
        data = request.data
        
        # Validar datos de entrada
        viaje_id = data.get('viaje_id')
        capacidad = data.get('capacidad_unidad')
        destino = data.get('destino')
        puntos = data.get('puntos_recogida', [])
        hora_salida = data.get('hora_salida', '07:00:00')
        
        if not all([viaje_id, capacidad, destino, puntos]):
            return Response({
                'success': False,
                'error': 'Datos incompletos',
                'message': 'Faltan campos requeridos'
            }, status=422)
        
        # Validar capacidad
        if len(puntos) > capacidad:
            return Response({
                'success': False,
                'error': 'Capacidad insuficiente',
                'message': f'Se requieren {len(puntos)} lugares pero la unidad solo tiene {capacidad} asientos'
            }, status=422)
        
        if len(puntos) == 0:
            return Response({
                'success': False,
                'error': 'Sin puntos de recogida',
                'message': 'No hay confirmaciones para este viaje'
            }, status=422)
        
        # Ejecutar algoritmo k-Means
        ruta_optimizada = ejecutar_kmeans_tsp(puntos, destino, hora_salida, capacidad)
        
        # Enviar resultado a Laravel (webhook)
        enviar_resultado_a_laravel(viaje_id, ruta_optimizada)
        
        # Retornar resultado
        return Response({
            'success': True,
            'viaje_id': viaje_id,
            'ruta_optimizada': ruta_optimizada['paradas'],
            'distancia_total_km': ruta_optimizada['distancia_total_km'],
            'tiempo_total_min': ruta_optimizada['tiempo_total_min'],
            'parametros': ruta_optimizada['parametros']
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error al generar ruta',
            'message': str(e)
        }, status=500)


def ejecutar_kmeans_tsp(puntos, destino, hora_salida, capacidad):
    """
    Ejecuta el algoritmo k-Means + TSP para optimizar la ruta
    """
    # 1. Extraer coordenadas
    coordenadas = np.array([
        [p['latitud'], p['longitud']] 
        for p in puntos
    ])
    
    # 2. Calcular número óptimo de clusters
    # Un cluster por cada grupo de ~10 niños (ajustable)
    n_clusters = max(1, min(math.ceil(len(puntos) / 10), len(puntos)))
    
    # 3. Aplicar k-Means clustering
    if n_clusters > 1:
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        labels = kmeans.fit_predict(coordenadas)
        centros = kmeans.cluster_centers_
    else:
        # Si solo hay un cluster, todos los puntos pertenecen a él
        labels = np.zeros(len(puntos), dtype=int)
        centros = np.array([np.mean(coordenadas, axis=0)])
    
    # 4. Ordenar clusters por distancia al destino (más lejano primero)
    destino_coord = np.array([destino['latitud'], destino['longitud']])
    distancias_clusters = []
    
    for i, centro in enumerate(centros):
        dist = calcular_distancia_haversine(centro, destino_coord)
        distancias_clusters.append((i, dist))
    
    # Ordenar de más lejano a más cercano
    clusters_ordenados = [
        cluster_id for cluster_id, _ 
        in sorted(distancias_clusters, key=lambda x: x[1], reverse=True)
    ]
    
    # 5. Ordenar puntos dentro de cada cluster usando TSP
    ruta_optimizada = []
    punto_anterior = None
    
    for cluster_id in clusters_ordenados:
        # Obtener puntos del cluster
        indices_cluster = np.where(labels == cluster_id)[0]
        puntos_cluster = [puntos[i] for i in indices_cluster]
        
        # Agregar cluster_id a cada punto
        for punto in puntos_cluster:
            punto['cluster'] = int(cluster_id)
        
        # Resolver TSP para el cluster (vecino más cercano)
        puntos_ordenados = resolver_tsp_vecino_cercano(
            puntos_cluster, 
            punto_inicial=punto_anterior
        )
        
        ruta_optimizada.extend(puntos_ordenados)
        punto_anterior = puntos_ordenados[-1] if puntos_ordenados else None
    
    # 6. Calcular distancias y tiempos
    ruta_con_tiempos = calcular_distancias_tiempos(
        ruta_optimizada, 
        hora_salida,
        destino
    )
    
    # 7. Calcular totales
    distancia_total = sum(p['distancia_desde_anterior_km'] for p in ruta_con_tiempos)
    tiempo_total = sum(p['tiempo_desde_anterior_min'] for p in ruta_con_tiempos)
    
    return {
        'paradas': ruta_con_tiempos,
        'distancia_total_km': round(distancia_total, 2),
        'tiempo_total_min': round(tiempo_total),
        'parametros': {
            'n_clusters': n_clusters,
            'metodo_ordenamiento': 'tsp-nearest-neighbor',
            'total_puntos': len(puntos),
            'capacidad_utilizada': len(puntos)
        }
    }


def calcular_distancia_haversine(coord1, coord2):
    """
    Calcula distancia entre dos coordenadas usando fórmula Haversine
    Retorna distancia en kilómetros
    """
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    radio_tierra_km = 6371
    return radio_tierra_km * c


def resolver_tsp_vecino_cercano(puntos, punto_inicial=None):
    """
    Resuelve el problema del vendedor viajero (TSP) usando algoritmo del vecino más cercano
    """
    if not puntos:
        return []
    
    if len(puntos) == 1:
        return puntos
    
    puntos_restantes = puntos.copy()
    ruta = []
    
    # Determinar punto inicial
    if punto_inicial:
        # Buscar punto más cercano al anterior
        actual = min(
            puntos_restantes,
            key=lambda p: calcular_distancia_haversine(
                [punto_inicial['latitud'], punto_inicial['longitud']],
                [p['latitud'], p['longitud']]
            )
        )
    else:
        # Empezar con punto más al norte (mayor latitud)
        actual = max(puntos_restantes, key=lambda p: p['latitud'])
    
    ruta.append(actual)
    puntos_restantes.remove(actual)
    
    # Continuar con vecinos más cercanos
    while puntos_restantes:
        siguiente = min(
            puntos_restantes,
            key=lambda p: calcular_distancia_haversine(
                [actual['latitud'], actual['longitud']],
                [p['latitud'], p['longitud']]
            )
        )
        ruta.append(siguiente)
        puntos_restantes.remove(siguiente)
        actual = siguiente
    
    return ruta


def calcular_distancias_tiempos(ruta, hora_inicial, destino):
    """
    Calcula distancias y tiempos entre paradas
    Si Google Maps API está disponible, la usa. Sino, usa Haversine.
    """
    hora_actual = datetime.strptime(hora_inicial, '%H:%M:%S')
    ruta_con_datos = []
    
    for i, parada in enumerate(ruta):
        if i == 0:
            # Primera parada
            distancia_km = 0
            tiempo_min = 5  # Tiempo fijo de inicio
        else:
            # Calcular distancia desde parada anterior
            parada_anterior = ruta[i-1]
            
            # Intentar usar Google Maps API
            if settings.GOOGLE_MAPS_API_KEY:
                try:
                    distancia_km, tiempo_min = calcular_con_google_maps(
                        parada_anterior, parada
                    )
                except Exception:
                    # Fallback a Haversine
                    distancia_km = calcular_distancia_haversine(
                        [parada_anterior['latitud'], parada_anterior['longitud']],
                        [parada['latitud'], parada['longitud']]
                    )
                    # Estimar tiempo: ~20 km/h en ciudad + tiempo de parada
                    tiempo_min = (distancia_km / 20) * 60
            else:
                # Usar Haversine
                distancia_km = calcular_distancia_haversine(
                    [parada_anterior['latitud'], parada_anterior['longitud']],
                    [parada['latitud'], parada['longitud']]
                )
                # Estimar tiempo: ~20 km/h en ciudad
                tiempo_min = (distancia_km / 20) * 60
        
        # Agregar tiempo de parada (2 minutos por niño)
        tiempo_min += 2
        
        # Calcular hora estimada
        hora_actual += timedelta(minutes=tiempo_min)
        
        ruta_con_datos.append({
            'confirmacion_id': parada['confirmacion_id'],
            'hijo_id': parada['hijo_id'],
            'direccion': parada['direccion'],
            'latitud': parada['latitud'],
            'longitud': parada['longitud'],
            'hora_estimada': hora_actual.strftime('%H:%M:%S'),
            'distancia_desde_anterior_km': round(distancia_km, 2),
            'tiempo_desde_anterior_min': round(tiempo_min),
            'cluster': parada.get('cluster', 0)
        })
    
    return ruta_con_datos


def calcular_con_google_maps(origen, destino):
    """
    Calcula distancia y tiempo usando Google Maps Directions API
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{origen['latitud']},{origen['longitud']}",
        'destination': f"{destino['latitud']},{destino['longitud']}",
        'key': settings.GOOGLE_MAPS_API_KEY,
        'mode': 'driving',
        'departure_time': 'now'
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if data['status'] == 'OK':
        leg = data['routes'][0]['legs'][0]
        distancia_km = leg['distance']['value'] / 1000  # Metros a km
        tiempo_min = leg['duration']['value'] / 60  # Segundos a minutos
        return distancia_km, tiempo_min
    else:
        raise Exception(f"Google Maps API error: {data['status']}")


def enviar_resultado_a_laravel(viaje_id, resultado):
    """
    Envía el resultado de la ruta generada a Laravel mediante webhook
    """
    if not settings.LARAVEL_WEBHOOK_URL:
        return  # No enviar si no está configurado
    
    try:
        payload = {
            'viaje_id': viaje_id,
            'distancia_total_km': resultado['distancia_total_km'],
            'tiempo_estimado_minutos': resultado['tiempo_total_min'],
            'algoritmo_utilizado': 'k-means-tsp',
            'parametros_algoritmo': resultado['parametros'],
            'paradas': resultado['paradas']
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Secret': settings.WEBHOOK_SECRET
        }
        
        response = requests.post(
            settings.LARAVEL_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error al enviar webhook a Laravel: {response.status_code}")
    
    except Exception as e:
        print(f"Excepción al enviar webhook: {str(e)}")
