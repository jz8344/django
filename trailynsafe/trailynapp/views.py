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
    Genera ruta optimizada con k-Means + TSP
    
    Payload esperado:
    {
        "viaje_id": 1,
        "puntos": [
            {
                "confirmacion_id": 1,
                "hijo_id": 1,
                "hijo_nombre": "Juan Perez",
                "latitud": 20.6736,
                "longitud": -103.3444,
                "direccion": "Av. Juárez 123",
                "referencia": "Casa azul"
            }
        ],
        "destino": {
            "escuela_id": 1,
            "nombre": "COBAEJ 21",
            "latitud": 20.6597,
            "longitud": -103.3496,
            "direccion": "Av. Mariano Otero 1555"
        },
        "hora_salida": "07:00:00",
        "capacidad": 50,
        "webhook_url": "https://tu-laravel-backend.com/api/webhook/ruta-generada"
    }
    """
    try:
        # 1. Validar datos recibidos
        data = request.data
        
        viaje_id = data.get('viaje_id')
        puntos = data.get('puntos', [])
        destino = data.get('destino')
        hora_salida = data.get('hora_salida', '07:00:00')
        capacidad = data.get('capacidad', 50)
        webhook_url = data.get('webhook_url')
        
        if not viaje_id or not puntos or not destino:
            return Response({
                'error': 'Datos incompletos',
                'message': 'Se requiere viaje_id, puntos y destino'
            }, status=400)
        
        if len(puntos) < 1:
            return Response({
                'error': 'Sin confirmaciones',
                'message': 'Debe haber al menos 1 punto de recogida'
            }, status=400)
        
        # 2. Ejecutar algoritmo k-Means + TSP
        resultado = ejecutar_kmeans_tsp(puntos, destino, hora_salida, capacidad)
        
        # 3. Enviar resultado a Laravel vía webhook
        if webhook_url:
            resultado['viaje_id'] = viaje_id
            enviar_resultado_a_laravel(webhook_url, viaje_id, resultado)
        
        # 4. Retornar resultado
        return Response({
            'success': True,
            'viaje_id': viaje_id,
            'ruta': resultado
        }, status=200)
        
    except Exception as e:
        return Response({
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


def enviar_resultado_a_laravel(webhook_url, viaje_id, resultado):
    """
    Envía el resultado de la generación de ruta a Laravel mediante webhook
    """
    try:
        payload = {
            'viaje_id': viaje_id,
            'ruta': resultado
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Ruta enviada exitosamente a Laravel para viaje {viaje_id}")
        else:
            print(f"⚠️ Error al enviar ruta a Laravel: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error al enviar resultado a Laravel: {str(e)}")
