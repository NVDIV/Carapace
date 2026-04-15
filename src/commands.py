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

def execute_backward(distance: int): 
    turtle.backward(distance)

def execute_right(angle: int): 
    turtle.right(angle)

def execute_penup(): 
    turtle.penup()

def execute_pendown(): 
    turtle.pendown()

def execute_color(name: str): 
    turtle.color(name.lower())

def execute_width(w: int): 
    turtle.pensize(w)

def execute_speed(s: int): 
    turtle.speed(s)