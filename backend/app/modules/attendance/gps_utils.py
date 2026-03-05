"""GPS utility functions for attendance module (WP-11-10)

Provides distance calculation for de-duplication logic.
"""

import math
from typing import Tuple, Optional


def calculate_distance(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """Calculate distance between two GPS coordinates using Haversine formula
    
    Args:
        coord1: (latitude, longitude) tuple for first point
        coord2: (latitude, longitude) tuple for second point
    
    Returns:
        Distance in meters
    
    Example:
        >>> calculate_distance((25.0330, 121.5654), (25.0340, 121.5664))
        141.42  # approximately 141 meters
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def is_within_distance(
    coord1: Optional[Tuple[float, float]],
    coord2: Optional[Tuple[float, float]],
    max_distance_m: float
) -> bool:
    """Check if two coordinates are within specified distance
    
    Args:
        coord1: (latitude, longitude) tuple for first point (or None)
        coord2: (latitude, longitude) tuple for second point (or None)
        max_distance_m: Maximum distance in meters
    
    Returns:
        True if within distance, False otherwise
        Returns False if either coordinate is None
    """
    if coord1 is None or coord2 is None:
        return False
    
    distance = calculate_distance(coord1, coord2)
    return distance < max_distance_m
