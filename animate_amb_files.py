#!/usr/bin/python

### This program makes it possible to animate Amberlights .amb files
### - Edit just below to define the filenames and duratoins between them.
### - Only linear interp is supported.
###   Not all entites can be animated. Feel free to add more
###
### The amb file is a zip file. Inside is an Artwork.xml file which has all parameters exposed.
### This program opens that, finds differences between files, and numerically interps between them.
### The resulting amb files are numbered from 1 and constitute an animation.

### The user has to manually open, render, and save the images from each of the interpolated amb files.


### User editable section

# This file is the one that gets resaved eachframe so is the template
start_amb = "AmberlightArtwork10_20k.amb"
# These durations and filenames define the animation starting with start_amb file.
anim_list = [[10, "AmberlightArtwork11.amb"],
             [4,  "AmberlightArtwork12.amb"],
             [4,  "AmberlightArtwork11.amb"],
             [4,  "AmberlightArtwork12.amb"],
             [8,  "AmberlightArtwork13.amb"],
             [8,  "AmberlightArtwork14.amb"]
             ]
# The output file will have a numeric suffix attached to this filename
output_prefix = "Amberlight_A"



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
    label = "_%03d" % idx
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
    " return list of changes in form of label and lines"
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
            else:
                print "!! Can't interp:", lineA.strip()
    return changes

# substitute matching values
def subs(line, orig, new):
    " make one to one subs of values in line "
    print " Swapping", orig, new
    pos = line.find(orig)
    if pos == -1:
        print "!!failed to substitute:", line, orig, new
    else:
        endpos = pos+len(orig)
        line = line[:pos]+ new + line[endpos:]
    #print " newline=",line
    return line


def interp_color(pair, factor):
    " interp color value between the two using factor"
    first, second = pair
    pos_first = first.find("val='")
    pos_sec = second.find("val='")
    if pos_first == -1 or pos_sec ==-1:
        print "Failed - not a color", pair
    else:
        orig = first[pos_first+5:pos_first+12]
        new  = second[pos_sec+5:pos_sec+12]
        red_1 =   int(orig[1:3], 16)
        red_2 =   int(new [1:3], 16)
        green_1 = int(orig[3:5], 16)
        green_2 = int(new [3:5], 16)
        blue_1 =  int(orig[5:], 16)
        blue_2 =  int(new [5:], 16)
        r = int(red_1 + float(red_2 - red_1) * factor)
        g = int(green_1 + float(green_2 - green_1) * factor)
        b = int(blue_1 + float(blue_2 - blue_1) * factor)
        newvalue = "%02x%02x%02x" %(r,g,b)
        #print "interp'd", orig, new, newvalue, factor
        return [orig[1:], newvalue]
        
def interp_field(pair, factor):
    " interp color value between the two using factor"
    first, second = pair
    xpos = first.find("x='")
    x1 = int(first[xpos+3:first.find("'", xpos+3)])
    ypos = first.find("y='")
    y1 = int(first[ypos+3:first.find("'", ypos+3)])
    mass_pos = first.find("mass='")
    mass1 = float(first[mass_pos+6:first.find("'", mass_pos+6)])
    dist_z_pos = first.find("dist_z='")
    dist_z1 = float(first[dist_z_pos+8:first.find("'", dist_z_pos+8)])
    dist_leng_pos = first.find("dist_leng='")
    dist_leng1 = int(first[dist_leng_pos+11:first.find("'", dist_leng_pos+11)])
    xpos2 = second.find("x='")
    x2 = int(second[xpos2+3:second.find("'", xpos2+3)])
    ypos = second.find("y='")
    y2 = int(second[ypos+3:second.find("'", ypos+3)])
    mass_pos = second.find("mass='")
    mass2 = float(second[mass_pos+6:second.find("'", mass_pos+6)])
    dist_z_pos = second.find("dist_z='")
    dist_z2 = float(second[dist_z_pos+8:second.find("'", dist_z_pos+8)])
    dist_leng_pos = second.find("dist_leng='")
    dist_leng2 = int(second[dist_leng_pos+11:second.find("'", dist_leng_pos+11)])
    #print x1,y1,mass1,dist_z1, dist_leng1
    #print x2,y2,mass2,dist_z2, dist_leng2
    newx = int(x1 + (x2-x1)*factor)
    newy = int(y1 + (y2-y1)*factor)
    newmass = mass1 + (mass2-mass1)*factor
    newdist_z = dist_z1 + (dist_z2-dist_z1)*factor
    newdist_leng = int(dist_leng1 + (dist_leng2-dist_leng1)*factor)
    #print"becomes", newx, newy, newmass, newdist_z, newdist_leng
    newvalue = "x='%d' y='%d' mass='%2.2f' dist_z='%2.2f' dist_leng='%d'" % (newx, newy, newmass, newdist_z, newdist_leng)
    return [first[xpos:first.rfind("'")+1], newvalue]


def interp_amb(data_A, changes, factor):
    " Interp between two files. Changes already discovered. "
    data_A = data_A.splitlines()
    print " Changes:"
    for c in changes: print "", c
    # get line based array of new values for substituting
    substitutions = []
    result = False
    for c in changes:
        if c[1] == "color":
            result = interp_color(c[2:], factor) # return [orig, new]
        elif c[1] == "field":
            result = interp_field(c[2:], factor) # return [orig, new]
        if result: substitutions.append([c[0], result])
    print "Substitutions:\n ",substitutions
    # substitute values in lines
    for s in substitutions:
        line = data_A[s[0]]
        data_A[s[0]] = subs(line, s[1][0], s[1][1])
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
        #print diffs
        #print artwork
        print "Processing:",  next_amb
        # Generate the interpolated frames
        for count in range(duration):
            factor = float(count) / (duration - 1)
            new_artwork = interp_amb(last, diffs, factor)
            # save the amb file with new values
            frame_id += 1
            print "Writing frame", frame_id, "\n"
            create_ambi(basename, new_artwork, base_suffix, output_prefix, frame_id)
        last = artwork2
        
# now manually open, render, save each file
