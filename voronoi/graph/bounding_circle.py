from math import sqrt

from voronoi import Polygon, Point, Coordinate
from voronoi.graph import Vertex
from voronoi.visualization import vis

DEBUG = False


class BoundingCircle(Polygon):

    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.polygon_vertices = []
        self.center = Coordinate(self.x, self.y)
        self.max_x = self.x + 2 * self.radius
        self.min_x = self.x - 2 * self.radius
        self.max_y = self.y + 2 * self.radius
        self.min_y = self.y - 2 * self.radius

    def inside(self, point):
        return (self.x - point.x)**2 + (self.y - point.y)**2 < self.radius**2

    def finish_edges(self, edges, verbose=False, vertices=None, points=None, event_queue=None):
        resulting_edges = []
        for edge in edges:
            result = True
            A = edge.get_origin(y=-1000)
            B = edge.twin.get_origin(y=-1000)
            if DEBUG:
                if vertices and points and event_queue:
                    vis.visualize(y=-1000, current_event="nothing",
                            bounding_poly=self,
                            points=points,
                            vertices=vertices + self.polygon_vertices,
                            edges=edges, arc_list=[],
                            event_queue=event_queue)
                vis.highlight_edge(-1000, self, edge)

            if A is None :
                if B is None:
                    continue
                result = result and self.trim_edge(edge)
            elif not self.inside(A):
                result = result and self.trim_edge(edge)
            if result :
                resulting_edges.append(edge)

            if DEBUG:
                if vertices and points and event_queue:
                    vis.visualize(y=-1000, current_event="nothing",
                            bounding_poly=self,
                            points=points,
                            vertices=vertices + self.polygon_vertices,
                            edges=edges, arc_list=[],
                            event_queue=event_queue)
                vis.highlight_edge(-1000, self, edge)

            if B is None or not self.inside(B):
                result = self.trim_edge(edge.twin)
                if result :
                    resulting_edges.append(edge.twin)

            if DEBUG:
                if vertices and points and event_queue:
                    vis.visualize(y=-1000, current_event="nothing", bounding_poly=self,
                              points=points, vertices=vertices + self.polygon_vertices, edges=edges, arc_list=[], event_queue=event_queue)

        # Re-order polygon vertices
        self.polygon_vertices = self.get_ordered_vertices(self.polygon_vertices)

        if DEBUG:
            if vertices and points and event_queue:
                vis.visualize(y=-1000, current_event="nothing", bounding_poly=self,
                        points=points, vertices=vertices + self.polygon_vertices,
                        edges=edges, arc_list=[], event_queue=event_queue)
        return resulting_edges, self.polygon_vertices


    def trim_edge(self, edge, twisted=False):

        point = self.cut_line(edge)

        if point is None:
            return False
        # Create vertex
        v = Vertex(point=point)
        v.incident_edges.append(edge)
        edge.origin = v
        self.polygon_vertices.append(v)

        return True

    def get_line(self, A, B):
        if (B.y - A.y) == 0 :
            a = 0
            b = 1.
            c = A.y
        elif (B.x - A.x) == 0 :
            a = 1
            b = 0
            c = A.x
        else:
            a = -(B.y - A.y) / (B.x - A.x)
            b = 1.
            c = A.x * a + A.y

        return a, b, c

    def get_ray(self, edge):
        A = edge.origin.breakpoint[0]
        B = edge.origin.breakpoint[1]
        center = Point(x=(A.x+B.x)/2., y=(A.y+B.y)/2.)

        if edge.twin.get_origin() is None:
            ray_start = center
        else:
            ray_start = edge.twin.origin.point
        a,b,c = self.get_line(ray_start, center)

        if DEBUG:
            vis.plot_helper_points(A,B, center, ray_start, a, b, c )

        return ray_start, center, a, b, c

    def on_line(self, A, B, C):
        def is_on(a, b, c):
            "Return true iff point c intersects the line segment from a to b."
            # (or the degenerate case that all 3 points are coincident)
            return ((within(a.x, c.x, b.x) if a.x != b.x else
                         within(a.y, c.y, b.y)))

        def within(p, q, r):
            "Return true iff q is between p and r (inclusive)."
            return (p <= q <= r) or (r <= q <= p)

        return is_on(A,B,C)


    def cut_line(self, edge):
        A = edge.get_origin(-1000)
        B = edge.twin.get_origin(-1000)
        a, b, c = self.get_line(A, B)

        point1, point2 = self.cut_circle(a, b, c)
        if DEBUG:
            vis.plot_points( point1, point2 )
        if point1 is None :
            return None
        points = []
        if self.on_line(A, B, point1):
            points.append(point1)
        if self.on_line(A, B, point2):
            points.append(point2)
        if len(points) == 0:
            return None
        elif len(points) == 1:
            return points[0]
        else:
            dist_0 = (A.x - points[0].x)**2. + (A.y - points[0].y)**2.
            dist_1 = (A.x - points[1].x)**2. + (A.y - points[1].y)**2.
            if dist_0 < dist_1 :
                return points[0]
            else:
                return points[1]


    def cut_circle(self, a, b, c):
        d = c - a * self.x - b * self.y
        a_sq_b_sq = a**2 + b**2
        try:
            big_sqrt = sqrt(self.radius**2 * a_sq_b_sq - d**2).real
        except ValueError:
            return None, None

        x1 = self.x + (a * d + b * big_sqrt)/a_sq_b_sq
        y1 = self.y + (b * d - a * big_sqrt)/a_sq_b_sq
        point1 = Point(x=x1, y=y1)
        x2 = self.x + (a * d - b * big_sqrt)/a_sq_b_sq
        y2 = self.y + (b * d + a * big_sqrt)/a_sq_b_sq
        point2 = Point(x=x2, y=y2)

        return point1, point2
