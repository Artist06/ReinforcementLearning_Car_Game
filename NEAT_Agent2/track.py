import pygame
import random
import numpy as np

TRACK_COLOR = (100, 100, 100)
TRACK_WIDTH = random.randint(80, 100)

QUADRUPLE_SIZE = 4
LINE_GAP = 10  # Increased gap between line segments
LINE_SEGMENT_LENGTH = 20  # Decreased length of each line segment
LINE_WIDTH = 5  # Width of the line

def num_segments(point_chain: tuple) -> int:
    # There is 1 segment per 4 points, so we must subtract 3 from the number of points
    return len(point_chain) - (QUADRUPLE_SIZE - 1)

def flatten(list_of_lists) -> list:
    # E.g. mapping [[1, 2], [3], [4, 5]] to [1, 2, 3, 4, 5]
    return [elem for lst in list_of_lists for elem in lst]

def catmull_rom_spline(P0: tuple, P1: tuple, P2: tuple, P3: tuple, num_points: int, alpha: float = 0.5):
    """
    Compute the points in the spline segment
    :param P0, P1, P2, and P3: The (x,y) point pairs that define the Catmull-Rom spline
    :param num_points: The number of points to include in the resulting curve segment
    :param alpha: 0.5 for the centripetal spline, 0.0 for the uniform spline, 1.0 for the chordal spline.
    :return: The points
    """
    def tj(ti: float, pi: tuple, pj: tuple) -> float:
        xi, yi = pi
        xj, yj = pj
        dx, dy = xj - xi, yj - yi
        l = (dx ** 2 + dy ** 2) ** 0.5
        return ti + l ** alpha

    t0: float = 0.0
    t1: float = tj(t0, P0, P1)
    t2: float = tj(t1, P1, P2)
    t3: float = tj(t2, P2, P3)
    t = np.linspace(t1, t2, num_points).reshape(num_points, 1)

    A1 = (t1 - t) / (t1 - t0) * P0 + (t - t0) / (t1 - t0) * P1
    A2 = (t2 - t) / (t2 - t1) * P1 + (t - t1) / (t2 - t1) * P2
    A3 = (t3 - t) / (t3 - t2) * P2 + (t - t2) / (t3 - t2) * P3
    B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
    B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
    points = (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2
    return points

def catmull_rom_chain(points: tuple, num_points: int) -> list:
    """
    Calculate Catmull-Rom for a sequence of initial points and return the combined curve.
    :param points: Base points from which the quadruples for the algorithm are taken
    :param num_points: The number of points to include in each curve segment
    :return: The chain of all points (points of all segments)
    """
    point_quadruples = (  # Prepare function inputs
        (points[idx_segment_start + d] for d in range(QUADRUPLE_SIZE))
        for idx_segment_start in range(num_segments(points))
    )
    all_splines = (catmull_rom_spline(*pq, num_points) for pq in point_quadruples)
    return flatten(all_splines)

def perpendicular(v):
    return np.array([-v[1], v[0]])

def generate_track(curve_points, track_width):
    outer_points = []
    inner_points = []

    for i in range(len(curve_points)):
        # Get current and next point
        p1 = np.array(curve_points[i])
        p2 = np.array(curve_points[(i + 1) % len(curve_points)])  # Wrap around for closed shape

        # Calculate the direction (tangent vector)
        tangent = p2 - p1
        if np.linalg.norm(tangent) == 0:
            continue
        tangent = tangent / np.linalg.norm(tangent)  # Normalize

        # Get the perpendicular (normal vector)
        normal = perpendicular(tangent)

        # Offset points to create track width
        inner_points.append(tuple(p1 + normal * track_width // 2))
        outer_points.append(tuple(p1 - normal * track_width // 2))

    return outer_points, inner_points

def draw_track(screen, outer_track, inner_track, chain_points, track_width):
    # Draw the filled track area
    track_color = (100, 100, 100)  # Color for the filled track area
    for i in range(len(inner_track)):
        next_i = (i + 1) % len(inner_track)
        pygame.draw.polygon(screen, track_color, [inner_track[i], inner_track[next_i], outer_track[next_i], outer_track[i]])

    # Draw the outer track boundary
    pygame.draw.polygon(screen, track_color, outer_track, width=3)

    # Draw the inner track boundary
    pygame.draw.polygon(screen, track_color, inner_track, width=3)

    # Draw the central white line in segments
    segment_start = 0
    while segment_start < len(chain_points):
        segment_end = min(segment_start + LINE_SEGMENT_LENGTH, len(chain_points) - 1)
        pygame.draw.lines(screen, (255, 255, 255), False, chain_points[segment_start:segment_end], width=LINE_WIDTH)
        segment_start += LINE_SEGMENT_LENGTH + LINE_GAP
