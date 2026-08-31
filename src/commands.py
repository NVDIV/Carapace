"""Thin adapter between the Carapace interpreter and Python's turtle module.

This module intentionally contains no Carapace language semantics. The
interpreter validates user values before delegation; these functions only map
validated operations to the graphical backend.
"""

import turtle


def init_graphics():
    """Initialize the turtle window with Carapace's default appearance."""
    turtle.title("Carapace DSL")
    turtle.shape("turtle")
    turtle.color("green")
    turtle.pensize(3)
    turtle.speed(3)


def execute_forward(distance: int):
    """Move the turtle forward by ``distance`` units."""
    turtle.forward(distance)


def execute_left(angle: int):
    """Rotate the turtle left by ``angle`` degrees."""
    turtle.left(angle)


def finish_graphics():
    """Enter turtle's event loop and keep the graphics window open."""
    turtle.done()


def execute_backward(distance: int):
    """Move the turtle backward by ``distance`` units."""
    turtle.backward(distance)


def execute_right(angle: int):
    """Rotate the turtle right by ``angle`` degrees."""
    turtle.right(angle)


def execute_penup():
    """Lift the pen so movement no longer draws a line."""
    turtle.penup()


def execute_pendown():
    """Lower the pen so movement draws a line."""
    turtle.pendown()


def execute_color(name: str):
    """Set the turtle drawing color by name."""
    turtle.color(name.lower())


def execute_width(w: int):
    """Set the pen width used for subsequent drawing operations."""
    turtle.pensize(w)


def execute_speed(s: int):
    """Set turtle animation speed using the backend's ``0..10`` scale."""
    turtle.speed(s)
