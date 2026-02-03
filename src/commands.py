import turtle

##########################################
#   CARAPACE COMMANDS IMPLEMENTATION
##########################################

def init_graphics():
    """Turtle initialization"""
    turtle.title("Carapace DSL")
    turtle.shape("turtle")
    turtle.color("green")
    turtle.pensize(3)
    turtle.speed(3) 

def execute_forward(distance: int):
    """Move forward"""
    turtle.forward(distance)

def execute_left(angle: int):
    """Turn right"""
    turtle.left(angle)

def finish_graphics():
    """Finish drawning (so window won't close automatically)"""
    turtle.done()