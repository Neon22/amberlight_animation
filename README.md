# amberlight_animation
Animate between amb files using Amberlight from Escape motions
- http://www.escapemotions.com/products/amberlight/

Edit the python file.
- At the top is a list of amb file names and durations.
- Running the python program will generate many amb files.
- You have to open and render and save each frame manually.
- Then combine resulting images into a movie, or whatever...

#Limitations:#
- currently the internal xml file order of the fields is not maintained so your animation fields may jump about.
To fix this you need to edit the Artwork.xml file inside the amb but only if you have this problem.
(open a copy renamed from .amb to .zip. Artwork.xml is inside)

- only fields and colour values are currently animated.
- turning on and off of colour values is not supported
- next version might support base,peak, etc changes

Video here:
https://vimeo.com/154414010