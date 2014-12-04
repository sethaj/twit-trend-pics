#!/usr/bin/env python -tt
# coding=utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from wand.image import Image
from wand.color import Color
import sqlite3 as sqlite
import os
import operator
import random
import glob
import datetime

RESULTS_STORE = '/Users/seth/SI618_project/twit-trend-pics/pictures'
IMAGE_STORE = '/Users/seth/SI618_project/twit-trend-pics/temp-pictures'


def mkdir_p(path):
    # 'mkdir -p' functionality taken from: http://stackoverflow.com/a/600612
    try:
        os.makedirs(path)
    except OSError as exc:
        #if exc.errno == errno.EEXIST and os.path.isdir(path):
        if exc.errno and os.path.isdir(path):
            pass
        else: raise Exception("mkdir_p")


''' the largest image determines the canvas size '''
def get_biggest_image(images):
    big_x = 0
    big_y = 0
    for image in images:
        print image
        with Image(filename=image) as im:
            if im.width > big_x:
                big_x = im.width
            if im.height > big_y:
                big_y = im.height
    return (big_x, big_y) 


''' 
Sample all images, decide what background the canvas should be based on this.
This matters when we start applying random filters
'''
def get_canvas_background_color(step, images):
    mkdir_p(RESULTS_STORE + '/' + step)
    mkdir_p(IMAGE_STORE + '/' + step)
    colors = dict()
    i=0
    for image in images:
        with Image(filename=image, resolution=8) as im:
            # make a small low-rez image first, otherwise histogram takes forever and
            # it's not *that* important if the background is exactly right
            im.sample(8, 8)
            im.format = 'ppm'
            # put these in the store for later
            small = IMAGE_STORE + '/' + step + '/' + 'small-' + str(i) + '.ppm'
            #print small
            try:
                im.save(filename=small)
            except Exception as e:
                print e
            i = i + 1
            for color in im.histogram:
                # TODO: this is the slow part: fix
                if color in colors:
                    colors[color] = im.histogram[color] + colors[color]
                else:
                    colors[color] = im.histogram[color]
    # http://stackoverflow.com/a/613218 sort dict by value
    sorted_colors = sorted(colors.iteritems(), key=operator.itemgetter(1))
    return sorted_colors[len(sorted_colors)-1][0]


def composite_operators():
    # wand.image.COMPOSITE_OPERATORS
    # http://docs.wand-py.org/en/latest/wand/image.html
    return ['add',
          'color_burn',
          'color_dodge',
          'darken',
          'difference',
          'exclusion',
          'hard_light',
          'lighten',
          'linear_light',
          'multiply',
          'plus',
          'screen',
          'soft_light',
          'subtract',
          'saturate',
          'replace',
          'threshold'
    ]


def add_bitmaps_to_canvas(step, canvas):
    # Thought it might be fun to add the histogram samples to the final image as a signature
    # These are really intriguing on their own, but this needs work, not sure how it fits
    bitmaps = glob.glob(IMAGE_STORE + '/' + step + '/' + 'small-*.ppm')
    x = canvas.height/50
    y = canvas.height - canvas.height/50
    for image in bitmaps:
        with Image(filename=image) as img:
            img.resize(img.width, img.height)
            #img.transparentize(.5)
            canvas.composite(img, left=x, top=y)
            x = x + img.width * 2
    return canvas


def return_images(cur, sql):
    images = list()
    cur.execute(sql)
    for row in cur:
        images.append(row[0])
    return images


def first_good(cur):
    # get first MTVStars
    return return_images(cur, """select image_file from
        pictures, trends
        where
        trends.trend_name = '#MTVStars'
        and
        trends.id = pictures.trend_id 
    LIMIT 20""")


def first_bad(cur):
    return return_images(cur, """select image_file from
        pictures, trends
        where
        trends.trend_name = 'JustinBieber'
        and trends.id = pictures.trend_id 
        LIMIT 20
    """)


def second_good(cur):
    return return_images(cur, """select image_file from 
        pictures, trends
        where
        trends.id = pictures.trend_id
        and
        trends.trend_name = '#NightChangesVideo'
        and
        trends.created = '2014-11-21 17:00:01'
    """)


def second_bad(cur):
    return return_images(cur, """select image_file from
        pictures, trends
        where
        trends.id = pictures.trend_id
        and
        trends.trend_name = 'SanaVereceğim Değer'
        and
        trends.created = '2014-11-14 17:00:26'
    """)


def third_good(cur):
    return return_images(cur, """select image_file from
        pictures
        where
        author = 'yumurtadelisi'
        limit 20
    """)


def third_bad(cur):
    # abdllhonl004               88            11               1
    # 88 posts in 11 trends but only 1 unique picture
    return return_images(cur, """select image_file from
        pictures
        where
        author = 'abdllhonl004'
        limit 20
    """)


def make_image(step, images):

    canvas_size     = get_biggest_image(images)
    bg_color        = get_canvas_background_color(step, images)

    mkdir_p(RESULTS_STORE)
    with Image(width=canvas_size[0], height=canvas_size[1], background=bg_color) as canvas:
        for image in images:
            with Image(filename=image) as img:
                x = canvas_size[0] - img.width + 1
                x = random.randint(1, x)
                y = canvas_size[1] - img.height + 1
                y = random.randint(1, y)
                # get random composite operator
                co = composite_operators()[random.randint(1, len(composite_operators()))-1]
                canvas.composite_channel(
                    channel='all_channels',
                    image=img,
                    operator=co,
                    left=x,
                    top=y
                )

        canvas = add_bitmaps_to_canvas(step, canvas)

        canvas.format = 'jpeg'
        #canvas_name = get_final_canvas_name(RESULTS_STORE + '/' + step + '/' + step)
        canvas_name = RESULTS_STORE + '/' + step + '/' + step + '_' + datetime.datetime.today().strftime("%Y-%m-%d_%H:%m:%S")
        canvas.save(filename=canvas_name + '.jpg')
        print 'wrote: ' + canvas_name + '.jpg'


def main():
    i = 1
    with sqlite.connect('trends.db') as con:
        cur = con.cursor()


        make_image(str(i) + "good", first_good(cur))
        make_image(str(i) + "bad",  first_bad(cur))
        i += 1
        make_image(str(i) + "good", second_good(cur))
        make_image(str(i) + "bad",  second_bad(cur))
        i += 1
        make_image(str(i) + "good", third_good(cur))
        make_image(str(i) + "bad",  third_bad(cur))


    print "done"


if __name__ == '__main__':
  main()
