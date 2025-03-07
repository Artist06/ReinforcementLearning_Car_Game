import pygame
import random
import math

TRACK_COLOR = (50, 50, 50)
TRACK_WIDTH = random.randint(80, 120)

def generate_oval(screen_width, screen_height, num_points=20):
    """Generate an initial oval shape as the base of the track"""
    cx, cy = screen_width // 2, screen_height // 2
    a, b = screen_width // 3, screen_height // 4  # Oval radii

    points = []
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        x = cx + a * math.cos(angle)
        y = cy + b * math.sin(angle)
        points.append((x, y))

    return points

def perturb_points(points, max_offset=40):
    """Add randomness to the points to create a natural-looking track"""
    perturbed = []
    for x, y in points:
        new_x = x + random.uniform(-max_offset, max_offset)
        new_y = y + random.uniform(-max_offset, max_offset)
        perturbed.append((new_x, new_y))
    return perturbed

def generate_bezier_curve(p0, p1, p2, num_points=30):
    """Generate points along a quadratic Bézier curve"""
    curve = []
    for t in range(num_points + 1):
        t /= num_points
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        curve.append((x, y))
    return curve

def generate_track(screen_width, screen_height, num_curves=10):
    """Create a track by perturbing an oval and smoothing it with Bézier curves"""
    base_points = generate_oval(screen_width, screen_height, num_curves)
    perturbed_points = perturb_points(base_points, max_offset=50)

    track_center = []
    for i in range(len(perturbed_points)):
        p0 = perturbed_points[i]
        p1 = perturbed_points[(i + 1) % len(perturbed_points)]  # Next point (looping)
        p2 = perturbed_points[(i + 2) % len(perturbed_points)]  # Next-next point

        curve = generate_bezier_curve(p0, p1, p2)
        track_center.extend(curve)

    return track_center

def get_track_edges(centerline, track_width):
    """Generate left and right edges based on the centerline"""
    left_edge = []
    right_edge = []

    for i in range(len(centerline) - 1):
        x1, y1 = centerline[i]
        x2, y2 = centerline[i + 1]

        dx = x2 - x1
        dy = y2 - y1
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            continue
        perp_x = -dy / length
        perp_y = dx / length

        left_edge.append((x1 + perp_x * (track_width // 2), y1 + perp_y * (track_width // 2)))
        right_edge.append((x1 - perp_x * (track_width // 2), y1 - perp_y * (track_width // 2)))

    return left_edge, right_edge

def draw_track(screen, centerline, track_width):
    """Draw the track using the centerline and width"""
    left_edge, right_edge = get_track_edges(centerline, track_width)

    for i in range(len(left_edge) - 1):
        pygame.draw.polygon(screen, TRACK_COLOR, [left_edge[i], left_edge[i + 1], right_edge[i + 1], right_edge[i]])

    pygame.draw.aalines(screen, (255, 255, 255), True, left_edge, 2)
    pygame.draw.aalines(screen, (255, 255, 255), True, right_edge, 2)

