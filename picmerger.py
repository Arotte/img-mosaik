import os
import sys
from PIL import Image

import progressbar

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

# ########################################## #
bigpic_filename = "bigpic2_182x146_26572.png" # <--- Extension should be .png
number_of_pictures = 746

bigpicW = 182
bigpicH = 146
bigpic_ratio = bigpicH/bigpicW
bigpic_pixels = bigpicW*bigpicH

subpic_minW = 128
subpic_minH = int(bigpic_ratio*subpic_minW)

pics_horizontally = bigpicW
pics_vertically = bigpicH
total_width = pics_horizontally * subpic_minW
total_height = pics_vertically * subpic_minH

# ########################################## #
bar = progressbar.ProgressBar(maxval=number_of_pictures+1, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

mergebar = progressbar.ProgressBar(maxval=bigpic_pixels+1, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

# ########################################## #
def colordiff(r1, g1, b1, r2, g2, b2):
	color1 = sRGBColor(r1, g1, b1)
	color2 = sRGBColor(r2, g2, b2)

	color1_cl = convert_color(color1, LabColor)
	color2_cl = convert_color(color2, LabColor)

	return delta_e_cie2000(color1_cl, color2_cl)

def getavgcolor(image):
	avg_color_im = image.resize((1, 1), Image.ANTIALIAS)
	return avg_color_im.getpixel((0, 0))


def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

# ########################################## #
# STEP 1: RENAME PICS (uncomment if needed)
'''
counter = 1
print("STEP 1 || Renaming images")
bar.start()
for filename in os.listdir("pics/."):
	if ("jpg" in filename or "JPG" in filename):
		os.rename(os.path.join("pics",filename), os.path.join("pics", str(counter)+".jpg"))
		bar.update(counter)
		counter += 1
		#print("DONE: " + filename)
	elif ("png" in filename or "PNG" in filename):
		os.rename(os.path.join("pics",filename), os.path.join("pics", str(counter)+".png"))
		bar.update(counter)
		counter += 1
		#print("DONE: " + filename)
bar.finish()
'''

# ########################################## #
# STEP 2: RESIZE PICS (uncomment if needed)
'''
counter = 1
print("\nSTEP 2 || Resizing images")
bar.start()
for infile in os.listdir("pics/."):
	if ("jpg" in infile or "png" in infile):
		#if ("jpg" in infile):
		outfilename = str(counter) + ".jpg"
		#elif("png" in infile):
			#outfilename = str(counter) + ".png"

		im = Image.open(os.path.join("pics",infile))
		resized = im.resize( (subpic_minW, subpic_minH), Image.ANTIALIAS )

		if not os.path.exists("resized_pics"):
			os.mkdir("resized_pics")

		resized.save(os.path.join("resized_pics",outfilename), "JPEG")

		bar.update(counter)
		counter += 1
bar.finish()
'''

# ########################################## #
# STEP 3 : CALCULATING AVERAGE COLOR FOR EACH PIC IN DATABASE

w, h = 4, number_of_pictures
avg_colors = [[0 for x in range(w)] for y in range(h)] #list of avg colors
index = 0
print ("\nSTEP 3 || Calculating average colors for pics")
bar.start()
for infile in os.listdir("resized_pics"):
	img = Image.open(os.path.join("resized_pics",infile))
	avg_color = getavgcolor(img)
	avg_colors[index][0] = avg_color[0] #R
	avg_colors[index][1] = avg_color[1] #G
	avg_colors[index][2] = avg_color[2] #B
	where = infile.find(".jpg")
	avg_colors[index][3] = int(infile[:where]) #name of file
	bar.update(index)
	index += 1
bar.finish()

# ########################################## #
# STEP 4 : GENERATING MERGED PIC

bigpic = Image.open(bigpic_filename)
merged_image = Image.new('RGB', (total_width, total_height))

x_offset = 0
y_offset = 0
counter = 1

print ("\nSTEP 4 || Generating merged picture")
mergebar.start()
if bigpic.mode in ('RGBA', 'LA') or (bigpic.mode == 'P' and 'transparency' in bigpic.info):
	pixels = list(bigpic.convert('RGBA').getdata())

	for r, g, b, a in pixels: # just ignore the alpha channel

		closest_color_diff = colordiff(r, g, b, avg_colors[0][0], avg_colors[0][1], avg_colors[0][2])
		#print (closest_color_diff)

		index_of_matching_pic = 1
		for picavg in avg_colors:
			localdiff = colordiff(r, g, b, picavg[0], picavg[1], picavg[2])
			if (localdiff < closest_color_diff):
				closest_color_diff = localdiff
				index_of_matching_pic = picavg[3]
		matching_pic_filename = str(index_of_matching_pic) + ".jpg"
		matching_pic = Image.open(os.path.join("resized_pics",matching_pic_filename))

		# now comes the merging
		merged_image.paste(matching_pic, (x_offset, y_offset))

		if (counter % bigpicW == 0):
			y_offset += subpic_minH
			x_offset = 0
		else:
			x_offset += subpic_minW
		mergebar.update(counter)
		counter += 1
mergebar.finish()

merged_image.save("merged_pics/merged_picXX.jpg")
