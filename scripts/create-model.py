#! /usr/bin/python

"""Module docstring.

This serves as a long usage message.
"""
import sys
import getopt

# ----------------------------------------------------------------------------------------------------

def read_option(message, options = [], default = None, help = None):
    while True:
        option = raw_input(message)
        if option == "?":
            if help:
                print help
            else:
                print "Possible options: %s" % options
        elif options and option in options:
            return option
        elif not option:
            print "Please specify an option"
        else:
            print "Unknown option. Options are: {}".format(options)

def read_float(message, default = None, help = None):
    while True:
        option = raw_input(message)
        if not option:
            if default != None:
                return default
            else:
                print "Please provide a value."
        elif option == "?":
            if help:
                print help
            else:
                print "Please provide a number"
        else:
            try:
                return float(option)
            except ValueError:
                print "Expected a number."
                pass

# ----------------------------------------------------------------------------------------------------

class ShapeCreator:

    def __init__(self):
        self.f = open("model.yaml", "w")        
        self.f.write("shape:\n")
        self.f.write("    compound:\n")
        self.indent = "    "

    def add_box(self, l, w, h, x, y, z, comment = ""):
        self.f.write("%s  - box:\n" % self.indent)
        if comment:
            self.f.write("%s        # %s\n" % (self.indent, comment))
        self.f.write("%s        pose: {x: %s, y: %s, z: %s}\n" % (self.indent, x, y, z))
        self.f.write("%s        size: {x: %s, y: %s, z: %s}\n" % (self.indent, l, w, h))

# ----------------------------------------------------------------------------------------------------

def main():

    print ""
    print """Answer the questions given. If you do not understand, give '?' as input. 
A 'model.yaml' file will be created which can be used as ED model.
All lengths / distances are in meters, unless specified otherwise."""
    print ""

    model_type = read_option("Model type: ", ["table", "cabinet"])
    
    if model_type == "table":

        print ""
        height = read_float("Height: ", help = "Distance from ground to top of the table")
        length = read_float("Length: ", help = "Table length")
        width  = read_float("Width:  ", help = "Table width")

        print ""
        table_top_thickness = read_float("Table top thickness: ")

        print ""
        lt = read_float("Leg thickness: ", help = "We assume square legs. How wide / thick are the legs?")
        lx_offset = read_float("Optional: Leg offset (length): ", 0,
            help = "(Optional) How far are the legs places inwards w.r.t. the table top (in the length direction)")
        ly_offset = read_float("Optional: Leg offset (width):  ", lx_offset,
            help = "(Optional) How far are the legs places inwards w.r.t. the table top (in the width direction)")

        s = ShapeCreator()
        s.add_box(length, width, table_top_thickness, 0, 0, height - table_top_thickness / 2, "Table top")

        lx = (length - lt - lx_offset) / 2
        ly = (width  - lt - ly_offset) / 2
        lh = height - table_top_thickness
        lz = lh / 2

        s.add_box(lt, lt, lh, -lx, -ly, lz, "Leg")
        s.add_box(lt, lt, lh,  lx, -ly, lz, "Leg")
        s.add_box(lt, lt, lh, -lx,  ly, lz, "Leg")
        s.add_box(lt, lt, lh,  lx,  ly, lz, "Leg")

    elif model_type == "cabinet":
        
        print ""
        height = read_float("Height: ", help = "Distance from ground to top of the cabinet (including frame)")
        width  = read_float("Width:  ", help = "Cabinet width (including frame)")
        depth  = read_float("Depth:  ", help = "Cabinet depth (including frame)")
        thickness = read_float("Frame thickness: ", help = "How thick are the panels that define the cabinet frame (not the shelves)?")

        print ""
        shelf_heights = []
        while True:
            shelf_height = read_float("Shelf %s, height: " % (len(shelf_heights) + 1), 0,
                help = "Distance from ground to top of shelf. Leave empty if all shelves have been entered")
            if shelf_height == 0:
                break
            shelf_heights += [shelf_height]

        shelf_thickness = 0
        if shelf_heights:
            shelf_thickness = read_float("Shelf thickness: ", help = "How thick are the shelves?")

        s = ShapeCreator()
        s.add_box(depth, thickness, height, 0, -(width - thickness) / 2, height / 2, "Left side")
        s.add_box(depth, thickness, height, 0,  (width - thickness) / 2, height / 2, "Right side")
        s.add_box(thickness, width, height,  (depth - thickness) / 2, 0, height / 2, "Back side")

        pl_depth = depth - thickness
        pl_width = width - (thickness * 2)
        pl_x = -(thickness / 2)

        s.add_box(pl_depth, pl_width, thickness, pl_x, 0, height - (thickness / 2), "Top")

        for shelf_height in shelf_heights:
            s.add_box(pl_depth, pl_width, shelf_thickness, pl_x, 0, shelf_height - (shelf_thickness / 2), "Shelf")    

if __name__ == "__main__":
    sys.exit(main())
