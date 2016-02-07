#!/usr/bin/python

### This program makes it possible to animate Amberlights .amb files
### - Edit section just below this to define the filenames and durations between them.
### - Only linear interp is supported.
###   Not all entites can be animated. Feel free to add more...
###
### The amb file is a zip file. Inside is an Artwork.xml file which has all parameters exposed.
### This program opens that, finds differences between files, and numerically interps between them.
### The resulting amb files are numbered from 1 and constitute an animation.

### The user has to manually open, render, and save the images from each of the interpolated amb files.

### Author: Neon22 Feb 2016


###----------------------
### User editable section

# This file is the initial amb file for frame 1
start_amb = "AD1.amb"
# These durations and filenames define the animation starting with start_amb
anim_list = [[12, "AD2.amb"],
             [30, "AD3.amb"]
             ]
# The resulting numbered amb files will start with this prefix.
output_prefix = "AC" # E.g. "AC_001" for frame 1
framecount_padding = 3  # how many leading zeros in padded numeric field.


###----------------------------------------------------
### Code
import zipfile
import os.path

# for examination (unused)
def open_ambi(fname):
    " look inside to see "
    datafname = "artwork.xml"
    if zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        print zf.namelist()
        info = zf.getinfo(datafname)
        print info.create_version, info.compress_type, info.extract_version
        print dir(info)
        print zf.read(datafname)
    #
    zf.close()

def pretty_substitutions(subslist, factor):
    " pretty print the actual inline substitutions we are doing (for debug) "
    for lineno, s in subslist:
        print "Line:", lineno, "Factor =", factor
        items = s[0].split()
        for idx in range(len(items)):
            second = s[1].split()[idx]
            print "",items[idx], second[(second.find("=") if second.find("=") != -1 else 0):]

def pretty_changes(changelist):
    " pretty print the changes(diffs) found "
    print "Found",len(changelist), "changes"
    for lineno, label, line1, line2 in changelist:
        print "On line:", lineno, "detected type:", label
        items = line1.split()[1:]
        for i in range(len(items)):
            print " ",items[i], line2.split()[1:][i]
    
def extract_artwork_from_amb(fname, interior_fname = "artwork.xml"):
    " extract interior_fname from zip file and return "
    if zipfile.is_zipfile(fname):
        zf = zipfile.ZipFile(fname)
        return zf.read(interior_fname)

# to make animations we need a base amb file without Atrwork.xml inside it
def make_base_ambi_zip(ambfname, suffix='_base'):
    " extract any xml files from zip and resave without them with name suffix"
    zin = zipfile.ZipFile (ambfname, 'r')
    stub, ext = os.path.splitext(ambfname)
    newname = stub+suffix+ext
    zout = zipfile.ZipFile (newname, 'w')
    for item in zin.infolist():
        buffer = zin.read(item.filename)
        if (item.filename[-4:] != '.xml'):
            zout.writestr(item, buffer)
    zout.close()
    zin.close()
    return newname

# make one per frame output
def create_ambi(basename, artwork_list, base_suffix, namestub, idx=1):
    " artwork in list form. append to base file"
    label = '_{0:0{1}d}'.format(idx,framecount_padding)  #"_%03d" % idx
    zin = zipfile.ZipFile (basename, 'r')
    newname = namestub+label+".amb"
    zout = zipfile.ZipFile (newname, 'w')
    for item in zin.infolist():
        buffer = zin.read(item.filename)
        zout.writestr(item, buffer)
    # writeout artwork.xml
    buffer = ""
    # list to line conversion
    for line in artwork_list:
        buffer += line+"\n"
    zout.writestr("artwork.xml", buffer)
    zout.close()
    zin.close()

    
def find_diff(data_A, data_B):
    """ return list of changes in form of label and lines
        - just finding the differences and characterising them.
    """
    data_A = data_A.splitlines()
    data_B = data_B.splitlines()
    changes = []
    #print "Differences:\nLengths:", len(data_A), len(data_B)
    size = len(data_A)
    for i in range(size):
        lineA = data_A[i]
        lineB = data_B[i]
        if lineA != lineB:
            first = lineA.strip().split()[0]
            if first == "<color":
                changes.append([i,"color", lineA.strip(), lineB.strip()])
            elif first == "<field":
                changes.append([i,"field", lineA.strip(), lineB.strip()])
            elif first == "<fields":
                changes.append([i,"fields", lineA.strip(), lineB.strip()])
            else:
                print "!! Can't interp:", lineA.strip()
    return changes

# substitute matching values
def substitute(line, orig, new):
    " make one to one subs of values in line "
    #print " Swapping", orig, new
    pos = line.find(orig)
    if pos == -1:
        print "!!failed to substitute:", line, orig, new
    else:
        endpos = pos+len(orig)
        line = line[:pos]+ new + line[endpos:]
    #print " newline=",line
    return line

def interp_color_values(orig, new, factor):
    " just the values "
    #print "interp color",orig, new
    red_1 =   int(orig[1:3], 16)
    red_2 =   int(new [1:3], 16)
    green_1 = int(orig[3:5], 16)
    green_2 = int(new [3:5], 16)
    blue_1 =  int(orig[5:], 16)
    blue_2 =  int(new [5:], 16)
    r = int(red_1 + float(red_2 - red_1) * factor)
    g = int(green_1 + float(green_2 - green_1) * factor)
    b = int(blue_1 + float(blue_2 - blue_1) * factor)
    #print orig, hex(red_1), hex(green_1), hex(blue_1)
    newvalue = "%02x%02x%02x" %(r,g,b)
    return newvalue
    
def interp_color(pair, factor):
    """ Interp color value between the two using factor
        - color is the gradient
        - has a color value and a switch - ignored
    """
    first, second = pair
    pos_first = first.find("val='")
    pos_sec = second.find("val='")
    if pos_first == -1 or pos_sec ==-1:
        print "Failed - not a color", pair
    else:
        orig = first[pos_first+5:pos_first+12]
        new  = second[pos_sec+5:pos_sec+12]
        newvalue = interp_color_values(orig, new, factor)
        return [orig[1:], newvalue]

def read_field(field, label):
    """ look for label in xml tag
        - return value between '' delimeters
    """
    length = len(label)+2
    pos = field.find(label+"='")
    value = field[pos+length:field.find("'", pos+length)]
    return value

def interp_field(pair, factor):
    """ Interp color value between the two using factor
        - field holds each of the on-screen density fields
    """
    first, second = pair
    xpos = first.find("x='")
    x1 = float(read_field(first, "x"))
    y1 = float(read_field(first, "y"))
    mass1 = float(read_field(first, "mass"))
    dist_z1 = float(read_field(first, "dist_z"))
    dist_leng1 = float(read_field(first, "dist_leng"))
    x2 = float(read_field(second, "x"))
    y2 = float(read_field(second, "y"))
    mass2 = float(read_field(second, "mass"))
    dist_z2 = float(read_field(second, "dist_z"))
    dist_leng_pos = second.find("dist_leng='")
    dist_leng2 = float(read_field(second, "dist_leng"))
    newx = float(x1 + (x2-x1)*factor)
    newy = float(y1 + (y2-y1)*factor)
    newmass = mass1 + (mass2-mass1)*factor
    newdist_z = dist_z1 + (dist_z2-dist_z1)*factor
    newdist_leng = float(dist_leng1 + (dist_leng2-dist_leng1)*factor)
    #print"becomes", newx, newy, newmass, newdist_z, newdist_leng
    newvalue = "x='%d' y='%d' mass='%2.2f' dist_z='%2.2f' dist_leng='%d'" % (newx, newy, newmass, newdist_z, newdist_leng)
    return [first[xpos:first.rfind("'")+1], newvalue]
    
def interp_fields(pair, factor):
    """ Interp color value between the two using factor
        - fields holds Base, Peak and many more params
    """
    #Fields in this line are:
    #count=int, target_iterations=int, do_tint='1'/0, do_glow='1'/0
    #opacity, tint_strength, glow_strength, glow_radius, seed,
    #grad_coeff1, grad_coeff2, grad_norm_max,
    #tint_color='#5f00ff', tint_direction='DOWN',
    first, second = pair
    ## first file
    countpos = first.find("count='")
    count1 = int(read_field(first, "count"))
    opacity1 = float(read_field(first, "opacity"))
    target_iterations1 = int(read_field(first, "target_iterations"))
    do_tint1 = int(read_field(first, "do_tint")) # 1 or 0
    do_glow1 = int(read_field(first, "do_glow")) # 1 or 0
    # floats
    tint_strength1 = float(read_field(first, "tint_strength"))
    glow_strength1 = float(read_field(first, "glow_strength"))
    glow_radius1 = float(read_field(first, "glow_radius"))
    seed1 = float(read_field(first, "seed"))
    grad_coeff1_1 = float(read_field(first, "grad_coeff1"))
    grad_coeff2_1 = float(read_field(first, "grad_coeff2"))
    grad_norm_max1 = float(read_field(first, "grad_norm_max"))
    # weirds
    tint_color1 = read_field(first, "tint_color") # color
    tint_direction1 = read_field(first, "tint_direction") # word
    
    ## second file
    count2 = int(read_field(second, "count"))
    opacity2 = float(read_field(second, "opacity"))
    target_iterations2 = int(read_field(second, "target_iterations"))
    do_tint2 = int(read_field(second, "do_tint")) # 1 or 0
    do_glow2 = int(read_field(second, "do_glow")) # 1 or 0
    # floats
    tint_strength2 = float(read_field(second, "tint_strength"))
    glow_strength2 = float(read_field(second, "glow_strength"))
    glow_radius2 = float(read_field(second, "glow_radius"))
    seed2 = float(read_field(second, "seed"))
    grad_coeff1_2 = float(read_field(second, "grad_coeff1"))
    grad_coeff2_2 = float(read_field(second, "grad_coeff2"))
    grad_norm_max2 = float(read_field(second, "grad_norm_max"))
    # weirds
    tint_color2 = read_field(second, "tint_color") # color
    tint_direction2 = read_field(second, "tint_direction") # word
    
    ## interpolate by factor
    newcount = int(count1 + (count2-count1)*factor)
    newtarget_iterations = int(target_iterations1 + (target_iterations2-target_iterations1)*factor)
    newdo_tint = int(do_tint1 + (do_tint2-do_tint1)*factor)
    newdo_glow = int(do_glow1 + (do_glow2-do_glow1)*factor)
    newopacity = float(opacity1 + (opacity2-opacity1)*factor)
    newtint_strength = float(tint_strength1 + (tint_strength2-tint_strength1)*factor)
    newglow_strength = float(glow_strength1 + (glow_strength2-glow_strength1)*factor)
    newglow_radius = int(glow_radius1 + (glow_radius2-glow_radius1)*factor)
    newseed = float(seed1 + (seed2-seed1)*factor)
    newgrad_coeff1 = float(grad_coeff1_1 + (grad_coeff1_2-grad_coeff1_1)*factor)
    newgrad_coeff2 = float(grad_coeff2_1 + (grad_coeff2_2-grad_coeff2_1)*factor)
    newgrad_norm_max = float(grad_norm_max1 + (grad_norm_max2-grad_norm_max1)*factor)
    # color
    newtint_color = interp_color_values(tint_color1, tint_color2, factor)
    # use tint_direction from first pair.
    newvalue = "count='%d' opacity='%2.2f' target_iterations='%d' do_tint='%d' do_glow='%d' tint_strength='%2.2f' tint_color='%s' tint_direction='%s' glow_strength='%2.2f' glow_radius='%d' seed='%2.2f' grad_coeff1='%2.4f' grad_coeff2='%2.4f' grad_norm_max='%2.4f'" % (
                 newcount, newopacity, newtarget_iterations, newdo_tint, newdo_glow, newtint_strength, "#"+newtint_color,
                 tint_direction1,
                 newglow_strength, newglow_radius, newseed, newgrad_coeff1, newgrad_coeff2, newgrad_norm_max)
    #print first[countpos:first.rfind("'")+1], "\n", newvalue
    return [first[countpos:first.rfind("'")+1], newvalue]
    
    
def interp_amb(data_A, changes, factor):
    " Interp between two files. Changes already discovered. "
    data_A = data_A.splitlines()
    # get line based array of new values for substituting
    substitutions = []
    result = False
    for c in changes:
        if c[1] == "color":
            result = interp_color(c[2:], factor) # return [orig, new]
        elif c[1] == "field":
            result = interp_field(c[2:], factor) # return [orig, new]
        elif c[1] == "fields":
            result = interp_fields(c[2:], factor) # return [orig, new]
        if result: substitutions.append([c[0], result])
    print "Substitutions: "
    pretty_substitutions(substitutions, factor)
    # substitute values in lines
    for s in substitutions:
        line = data_A[s[0]]
        data_A[s[0]] = substitute(line, s[1][0], s[1][1])
    return data_A
        


###-------------------
if __name__ == "__main__":
    #open_ambi(fname)
    frame_id = 0
    base_suffix = "_base" # label for base zipfile
    fname = start_amb
    #
    total_frames = sum([a for a,ignore in anim_list])
    print "Processing", total_frames, "frames from", len(anim_list)+1, "files"
    
    last = extract_artwork_from_amb(fname)
    basename = make_base_ambi_zip(fname, base_suffix)
    print " made base zipfile:", basename
    
    for duration, next_amb in anim_list:
        # detect differences between two files
        artwork2 = extract_artwork_from_amb(next_amb)
        diffs = find_diff(last, artwork2)
        print "Changes:"
        pretty_changes(diffs)
        #print artwork
        print "Processing:", next_amb
        # Generate the interpolated frames
        for count in range(duration):
            print "\nStarting frame", frame_id+1
            factor = float(count) / (duration - 1)
            new_artwork = interp_amb(last, diffs, factor)
            # save the amb file with new values
            frame_id += 1
            print "Writing frame", frame_id
            create_ambi(basename, new_artwork, base_suffix, output_prefix, frame_id)
        last = artwork2
        
# now manually open, render, save each file
