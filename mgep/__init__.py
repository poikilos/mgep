#!/usr/bin/env python
from __future__ import division  # `//` floor division

try:
    import pygame as pg
except ImportError:
    print("You must install pygame:")
    print("dnf install -y python3-pygame")
    exit(1)

import random
import math
import os
import sys
try:
    import angles
except ImportError:
    sys.path.append(os.path.abspath("mgep"))  # needed for some reason
    try:
        import angles
        print("found angles in 'mgep'")
    except ImportError:
        print("ERROR: angles library not found.")
        exit(1)
import json
import os
try:
    import save1d
except ImportError:
    print("ERROR: save1d library not found.")
    exit(1)


TAU = math.pi * 2.
NEG_TAU = -TAU
sqrt_2 = math.sqrt(2.0)
# Epydoc and Pycharm support docstring following variable:
kEpsilon = 1.0E-6
""" adjust to suit.  If you use floats, you'll probably want something
like 1.0E-7 (added by poikilos [tested: using 1.0E-6 since python 3
fails to set 3.1415927 to 3.1415926 see delta_theta in KivyGlops]
"""
# good_45deg_tile_sizes = [(17,12), (34,24), (41,29), (58,41), (75,53),
#                          (92,65)]
good_45deg_tile_sizes = []

block_rise_as_y_px = 1
tilesets = {}
heightmap_key = "cave"
heightmap = {}
data_path = os.path.dirname(os.path.abspath(__file__))
maps_path = os.path.join(data_path, "maps")
mesas_path = os.path.join(maps_path, "mesa")
if not os.path.isdir(maps_path):
    print("ERROR: no maps directory in same directory as " + __file__)
heightmap['mesa_path'] = os.path.join(mesas_path,
                                      heightmap_key + ".png")
if not os.path.isfile(heightmap['mesa_path']):
    print("ERROR: missing mesa image '" + heightmap['mesa_path'] + "'")
file_surfs = {}
surf_paths = []  # keys for file_surfs in order of loading
materials = {}
material_choose = [None]
world = {}
"""the world is a dict of lists (multiple gobs can be on one location)
"""
world['blocks'] = {}
# screen = None
player_unit_name = None
game_tile_size = None
units = {}
default_font = None
popup_text = ""
popup_showing_text = None
popup_surf = None
popup_shadow_surf = None
popup_sec = 0
popup_alpha = 0
visual_debug_enable = False
bindings = {}
bindings['draw_ui'] = []
nothing_y = -10.0
checkerboard = {}


def bind(when, f):
    """
    bind an mgep event to a function

    Keyword arguments:
    when -- an event name such as 'draw_ui'
    f -- a function with one param `def on_draw_ui(e)`, where e will be
    an event (dictionary) sent to your function from mgep.
    """
    global bindings
    q = bindings.get(when)
    if q is not None:
        q.append(f)
    else:
        print('ERROR: no "' + str(when) + '" event exists. Try ' +
              str(list(bindings)))


def _get_tile_src_size():
    global game_tile_size
    return game_tile_size


def get_tile_size():
    global scaled_b_size
    return scaled_b_size


def equal_str_content(master, other):
    if master is not None and other is not None:
        for k, v in master.items():
            if str(v) != str(other.get(k)):
                return False
    return True


def get_spare_keys(master, other):
    ret = []
    if master is not None:
        for k, v in other.items():
            if k not in master:
                ret.append(k)
    return ret


def abs_slack(f):
    if f < 0.0:
        return abs(f - float(int(f)))  # such as abs(-1.1 - -1.0) = .1
    else:
        return f - float(int(f))  # such as 1.1 - 1.0 = .1
    return None


w = 16
while w <= 1024:
    two_h = float(w) * sqrt_2
    h = two_h / 2.0
    if int(round(h)) * 2 == int(two_h) and abs_slack(two_h) < .15:
        good_45deg_tile_sizes.append((w, int(h)))
        # print(str((w, int(h))))
    # else:
        # print("NOT " + str((w, int(h))))
        # print("  abs_slack: " + str(abs_slack(two_h)))
        # print("  two_h: " + str(two_h))
    w += 1
data = None
settings_path = "settings-mgep.json"
if os.path.isfile(settings_path):
    with open(settings_path, "r") as ins:
        data = json.load(ins)
got = data
if got is None:
    got = {}
print("settings path: " + os.path.abspath(settings_path))
# print("settings loaded: " + str(got))
settings = {}
settings['popup_sec_per_glyph'] = got.get('popup_sec_per_glyph', .04)
settings['popup_alpha_per_sec'] = got.get('popup_alpha_per_sec', 128.0)
settings['text_antialiasing'] = got.get('text_antialiasing', True)
settings['human_run_slow_mps'] = got.get('human_run_slow_mps', 4.47)
"""4.47 m/s = 10 miles per hour"""
settings['human_walk_mps'] = got.get('human_walk_mps', 3.0)  # approx
settings['human_walk_accel'] = got.get('human_walk_accel', 3.0)
"""approx"""
settings['human_run_mps'] = got.get('human_run_mps', 6.7)
"""6.7 m/s = 15 miles per hour"""
settings['human_run_accel'] = got.get('human_run_accel', 3.0)  # approx
settings['human_run_max_mps'] = got.get('human_run_max_mps', 12.4)
"""12.4 m/s = 27.8 miles per hour"""
settings['sys_font_name'] = got.get('sys_font_name', 'Arial')
settings['sys_font_size'] = got.get('sys_font_size', 12)
"""pygame only accepts int"""
settings['default_world_gravity'] = got.get('default_world_gravity',
                                            9.8)
if not equal_str_content(settings, got):
    with open(settings_path, "w") as outs:
        json.dump(settings, outs)
spare_keys = get_spare_keys(settings, got)
if len(spare_keys) > 0:
    print("got the following unknown settings from '" +
          os.path.abspath(settings_path) + ":")
    print("  " + str(spare_keys))

# print("settings used: " + str(settings))
last_loaded_world_name = None
temp_screen = None
text_pos = [0, 0]
preview_tileset_i = None  # index in surf_paths list
last_loaded_path = None
gui_state = {}
gui_state['select.x'] = 0
gui_state['select.y'] = 0

camera = {}
camera['pos'] = (0, 0, 0)
b_scale_h = None
desired_scale = None
screen_half = None
camera_target_unit_name = None


prev_frame_ticks = None
min_fps_ticks = 1000
total_ticks = 0
frame_count = 0
fps_s = "?"
# scalable_surf = None
# scalable_surf_scale = None

# region reinitialized each frame
win_size = None
# scaled_size = None
scaled_b_size = None
block_half_counts = None
start_loc = None
end_loc = None
# endregion reinitialized each frame


def fmt_f(f, fmt=None, places=1):
    if fmt is None:
        fmt = "{0:." + str(places) + "f}"
    return fmt.format(round(f, places))


def fmt_vec(vec, fmt=None, places=1):
    if fmt is None:
        fmt = "{0:." + str(places) + "f}"
    ret = ""  # "<vec" + str(len(vec)) + ">"
    sep = ""
    for f in vec:
        ret += sep + fmt.format(round(f, places))
        sep = ", "
    return ret


def load(name, default=None):
        # , file_format='list', as_type='string'):
    path = name + '.json'
    ret = None
    if os.path.isfile(path):
        with open(path, "r") as ins:
            ret = json.load(ins)
    else:
        ret = default
    # return save1d.load(name, default=default, file_format=file_format,
    #                    as_type=as_type)
    return ret


def save(name, data):  # , file_format='list'):
    path = name + '.json'
    # save1d.save(name, data, file_format=file_format)
    with open(path, "w") as outs:
        json.dump(data, outs)


def get_preview_tileset_path():
    ret = None
    try:
        ret = surf_paths[preview_tileset_i]
    except TypeError:
        pass
    return ret


def cycle_preview_tileset(by=1):
    """
    If preview_tileset_i is None after calling this, you've
    reached the end, so calling this again will select the first one (or
    last if by is negative).

    Keyword arguments:
    by -- direction to cycle, positive for order loaded (default 1)
    """
    global preview_tileset_i
    was_None = False
    if preview_tileset_i is None:
        was_None = True
    if len(surf_paths) < 1:
        preview_tileset_i = None
        return
    if preview_tileset_i is None:
        if by < 0:
            preview_tileset_i = len(surf_paths) - 1
        else:
            preview_tileset_i = 0
    else:
        preview_tileset_i += by
        if preview_tileset_i >= len(surf_paths):
            preview_tileset_i = None
        elif preview_tileset_i < 0:
            preview_tileset_i = None
    # tileset cursor must be set for tileset preview to be visible:
    if gui_state.get('select.x') is None:
        gui_state['select.x'] = 0
        gui_state['select.y'] = 0
    surf = None
    path = None

    if preview_tileset_i is None:
        if visual_debug_enable is True:
            toggle_visual_debug(tileset_cycle_enable=False)
    else:
        if visual_debug_enable is False:
            toggle_visual_debug(tileset_cycle_enable=False)

    if preview_tileset_i is None:
        # gui_state['select.y'] = 0
        # gui_state['select.x'] = 0
        return
    try:
        path = surf_paths[preview_tileset_i]
    except IndexError:
        pass
    if path is not None:
        if (preview_tileset_i is not None):
            # always reset row on load even if didn't just open preview
            path = surf_paths[preview_tileset_i]
            tileset = tilesets.get(path)
            if tileset is not None:
                if gui_state['select.x'] >= tileset['cols']:
                    gui_state['select.x'] = tileset['cols'] - 1
                if by < 0:
                    gui_state['select.y'] = tileset['rows'] - 1
                else:
                    gui_state['select.y'] = 0


def change_preview_tile(move_x=None, move_y=None):
    cycle = True
    was_None = False
    move_enable = True
    orig_move_y = move_y
    by = 1
    if move_y < 0:
        by = -1
    if preview_tileset_i is None:
        move_y = 0  # don't skip rows on load
        was_None = True
        load_by = by
        if load_by > 0:
            load_by = 0
        cycle_preview_tileset(by=load_by)
        cycle = False
        if visual_debug_enable is False:
            toggle_visual_debug(tileset_cycle_enable=False)
    else:
        if visual_debug_enable is False:
            toggle_visual_debug(tileset_cycle_enable=False)

    if not visual_debug_enable:
        # do not skip upon entering the preview
        move_x = 0
        move_y = 0
    if preview_tileset_i is None:
        print("ERROR: preview_tileset_i is None in change_preview_tile")
        return
    path = surf_paths[preview_tileset_i]
    tileset = tilesets[path]
    cell_size = tileset['tile_size']  # aka _get_tile_src_size
    surf = file_surfs.get(path)
    if surf is not None:
        size = file_surfs[path].get_size()
        cols = tileset['cols']
        rows = tileset['rows']
        if (move_x is None and move_y is None):
            move_x = 1
            move_y = 0
        elif move_x is None:
            move_x = 0
        elif move_y is None:
            move_y = 0
        gui_state['select.x'] += move_x
        gui_state['select.y'] += move_y
        if gui_state['select.x'] < 0:
            gui_state['select.y'] += gui_state['select.x'] // cols
            gui_state['select.x'] = cols + gui_state['select.x']
            gui_state['select.x'] %= cols
        if gui_state['select.y'] < 0:
            if cycle:
                cycle = False
                cycle_preview_tileset(by=by)
                cols = tileset['cols']
                rows = tileset['rows']
        if gui_state['select.x'] >= cols:
            gui_state['select.y'] += gui_state['select.x'] // cols
            gui_state['select.x'] %= cols
        if gui_state['select.y'] >= rows:
            gui_state['select.y'] %= rows
            if cycle:
                cycle_preview_tileset(by=by)
    else:
        gui_state['select.x'] = 0
        gui_state['select.y'] = 0
        print("ERROR: surf is None in change_preview_tile")


def toggle_visual_debug(tileset_cycle_enable=True):
    global visual_debug_enable
    if visual_debug_enable is False:
        if preview_tileset_i is None:
            if tileset_cycle_enable:
                cycle_preview_tileset(by=0)
            # change_preview_tile()
    if visual_debug_enable:
        set_visual_debug(False)
    else:
        set_visual_debug(True)


def get_visual_debug():
    return visual_debug_enable


def set_visual_debug(boolean):
    global visual_debug_enable
    visual_debug_enable = boolean


def show_popup(s):
    global popup_text
    popup_text = s
    global popup_alpha
    popup_alpha = 255


def set_scale(whole_number):
    global b_scale_h
    global desired_scale
    b_scale_h = int(round(whole_number))
    desired_scale = b_scale_h


def get_key_at_px(vec2):
    w, h = game_tile_size  # tilesets[path]['tile_size']
    col = int(round(vec2[0] / w))
    row = int(round(vec2[2] / h))
    return str(col) + "," + str(row)


def get_key_at_pos(pos):
    col = int(round(pos[0]))
    row = int(round(pos[2]))
    return str(col) + "," + str(row)


def get_unit_crosshairs_vec3(unit):
    global game_tile_size
    pos = [
        unit['pos'][0],
        unit['pos'][1],
        unit['pos'][2]
    ]
    if visual_debug_enable:
        push_text("  crosshairs: " + fmt_vec(pos))
    # offsets = [0,0]
    offsets = (
        math.cos(math.radians(unit['yaw_deg'])),
        math.sin(math.radians(unit['yaw_deg']))
    )
    target = pos[0]+offsets[0], pos[1], pos[2]+offsets[1]
    return target


def vec2_from_vec3_via_camera(vec3, cam_vec2=None):  # src_size,
    """get 2D screen location from 3D location using camera

    Keyword arguments:
    cam_vec2 -- not required. Provide if known for performance,
    otherwise will be calculated using camera['pos']
    """
    global screen_half
    global scaled_b_size
    global block_rise_as_y_px
    if cam_vec2 is None:
        cam_vec2 = (
            int(math.round(camera['pos'][0] * scaled_b_size[0])),
            int(math.round(camera['pos'][2] * scaled_b_size[1]))
        )
    world2 = (vec3[0] * scaled_b_size[0],
              vec3[2] * scaled_b_size[1])
    x = (world2[0] - cam_vec2[0]) + screen_half[0]  # - src_size[0]/2
    y = -1*(world2[1] - cam_vec2[1]) + screen_half[1]  # - src_size[1]/2
    y += -vec3[1] * block_rise_as_y_px
    return (x, y)


def get_selected_node_key():
    unit = units[player_unit_name]
    target = get_unit_crosshairs_vec3(unit)
    col = int(round(target[0]))
    row = int(round(target[2]))
    return str(col) + "," + str(row)


def get_unit_value(name, what):
    return units[name][what]


def set_unit_value(name, what, v):
    units[name][what] = v


def vec3_changed_0(vec, f):
    return (f, vec[1], vec[2])


def vec3_changed_1(vec, f):
    return (vec[0], f, vec[2])


def vec3_changed_2(vec, f):
    return (vec[0], vec[1], f)


def get_cardinal_deg(angle):
    """This returns ('E', 'N', 'W', 'S') via right-handed angle,
    not based on real life heading angle.
    Right-handed angle is E = 0 going counter-clockwise from top
    view (camera with z>0 facing origin) which sees +x point right
    (real life heading is N = 0 going clockwise).
    """
    ret = None
    if angle is not None:
        angle = angles.normalize(angle, lower=45, upper=405)
        if angle > 225:
            if angle >= 315:
                ret = 'E'
            else:
                ret = 'S'
        else:
            if angle >= 135:
                ret = 'W'
            else:
                if angle <= 45:
                    ret = 'E'
                else:
                    ret = 'N'
    return ret
    # see also etc/angleQuantization.cpp


def auto_pose(unit, mode='walk'):
    global materials
    cardinal = get_cardinal_deg(unit['yaw_deg'])
    pose = None
    if cardinal is not None:
        pose = mode + '.' + cardinal
    # if amount > 0:
        # pose = 'walk.E'
        # unit['yaw_deg'] = 0.0
    # elif amount < 0:
        # pose = 'walk.W'
        # unit['yaw_deg'] = 180.0
    if pose is not None:
        material = materials[unit['what']]
        if pose in material['tmp']['sprites']:
            reset_enable = False
            if pose != unit['pose']:
                reset_enable = True
            unit['pose'] = pose
            if reset_enable:
                material['tmp']['sprites'][pose].iter()


def move_x(name, amount):
    unit = units.get(name)
    if unit is not None:
        # unit['tmp']['move_multipliers'] = \
        #     vec3_changed_0(unit['tmp']['move_multipliers'], amount)
        unit['tmp']['move_multipliers'][0] = amount
        # unit['pos'] = vec3_changed_0(unit['pos'], amount)
        # auto_pose(unit, "walk")
    else:
        raise ValueError("Cannot move since no unit '" +
                         name + "'")


def move_y(name, amount):
    unit = units.get(name)
    pose = None
    if unit is not None:
        # unit['tmp']['move_multipliers'] = \
        #     vec3_changed_2(unit['tmp']['move_multipliers'], amount)
        unit['tmp']['move_multipliers'][2] = amount
        # unit['pos'] = vec3_changed_2(unit['pos'], amount)
        # auto_pose(unit, "walk")
    else:
        raise ValueError("Cannot move since no unit '" + name + "'")


def move_camera_to(name):
    global camera_target_unit_name
    camera_target_unit_name = name
    unit = units.get(name)
    if unit is not None:
        camera['pos'] = unit['pos'][0], camera['pos'][1], unit['pos'][2]
    else:
        raise ValueError("Cannot move_camera_to since no unit '" +
                         name + "'")


# Spritesheet class from https://www.pygame.org/wiki/Spritesheet
# changes by poikilos: file_surfs cache
class SpriteSheet(object):
    def __init__(self, path):
        try:
            self.sheet = file_surfs.get(path)
            if self.sheet is None:
                self.sheet = pg.image.load(path)  # .convert_alpha()
                file_surfs[path] = self.sheet
                surf_paths.append(path)
        except pg.error as message:
            print('Unable to load spritesheet image:', path)
            raise SystemExit(message)

    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey=None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pg.Rect(rectangle)
        if colorkey is not None:
            image = pg.Surface(rect.size).convert()
        else:
            image = pg.Surface(rect.size, flags=pg.SRCALPHA)
            # .convert_alpha()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pg.RLEACCEL)
        return image

    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey=None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]

    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey=None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)


# SpriteStripAnim class from https://www.pygame.org/wiki/Spritesheet
# except:
# * renamed frames to delay_count
# * boundary checking for delay_count
# * added order (uses oi to go out of order); frame indices start at 1
class SpriteStripAnim(object):
    """sprite strip animator

    This class provides an iterator (iter() and next() methods), and a
    __add__() method for joining strips which comes in handy when a
    strip wraps to the next row.
    order -- a list of indices (starting at 1) in case frames should be
           used out of order
    """
    def __init__(self, path, rect, count, colorkey=None, loop=False,
                 delay_count=1, order=None):
        """construct a SpriteStripAnim

        path, rect, count, and colorkey are the same arguments used
        by spritesheet.load_strip.

        loop is a boolean that, when True, causes the next() method to
        loop. If False, the terminal case raises StopIteration.

        delay_count is the count to return the same image
        before iterator advances to the next image.
        """
        self.path = path
        ss = SpriteSheet(path)
        self.images = ss.load_strip(rect, count, colorkey)
        self.image = None
        self.i = 0  # current frame index
        self.oi = 0  # current index in the custom order
        self.order = order
        if order is not None:
            self._go_to_order()
        self.image = self.images[self.i]

        self.lowlit_surf = pg.Surface(self.image.get_size(),
                                      flags=pg.SRCALPHA)
        self.black_surf = pg.Surface(self.image.get_size(),
                                     flags=pg.SRCALPHA)
        self.lowlight = .75
        self._lowlit = None
        self._lowlit_i = None

        self.loop = loop

        self.delay_count = int(delay_count)
        if self.delay_count < 1:
            print("WARNING: setting delay_count to 1 " +
                  "since was " + str(self.delay_count))
            self.delay_count = 1
        self.f = delay_count

    def iter(self):
        self.i = 0
        self.oi = 0
        if self.order is not None:
            self._go_to_order()
        self.f = self.delay_count
        return self

    def get_lowlit_surface(self):
        if self.lowlight is not None:
            if self.lowlight < 0.0:
                self.lowlight = 0.0
            elif self.lowlight > 1.0:
                self.lowlight = 1.0
            darkness = 1.0 - self.lowlight
            if (self._lowlit is None) or \
               (self._lowlit != self.lowlight) or \
               (self._lowlit_i != self.i):
                self.black_surf.fill((darkness*255,
                                      darkness*255,
                                      darkness*255, 0))
                self.lowlit_surf.fill((0, 0, 0, 0))
                self.lowlit_surf.blit(self.image, (0, 0))
                # this blend is slow, but seems necessary so alpha
                # doesn't get overwritten:
                self.lowlit_surf.blit(self.black_surf, (0, 0),
                                      special_flags=pg.BLEND_RGBA_SUB)
                # See also https://www.reddit.com/r/pygame/comments/\
                # 4b8mnz/is_it_possible_to_make_an_image_darker/
                self._lowlit = self.lowlight
                self._lowlit_i = self.i
            return self.lowlit_surf
        else:
            return self.image

        return self.lowlit_surf

    def get_surface(self):
        # return self.images[self.i]
        return self.image

    def _go_to_order(self):
        if self.order is not None:
            if self.oi >= len(self.order):
                msg = "self.oi was " + str(self.oi)
                print("WARNING in _go_to_order: " + msg)
                # raise ValueError(msg)
                self.oi = 0
            new_i = self.order[self.oi] - 1  # -1 since starts at 1
            if new_i >= 0 and new_i < len(self.images):
                self.i = new_i
                # do NOT set self.image = self.images[self.i] here, as
                # using iterator logic (see __next__) which increments
                # only
            else:
                raise ValueError("Bad order index (should be >=1) " +
                                 str(new_i))
        else:
            raise RuntimeError("Cannot _go_to_order with no order.")

    def advance(self):
        if self.order is not None:
            if self.oi >= len(self.order):
                if not self.loop:
                    raise StopIteration
                else:
                    self.oi = 0
            self._go_to_order()
        else:
            if self.i >= len(self.images):
                if not self.loop:
                    raise StopIteration
                else:
                    self.i = 0
        self.image = self.images[self.i]
        self.f -= 1
        if self.f == 0:
            if self.order is not None:
                self.oi += 1
            else:
                self.i += 1
            self.f = self.delay_count

    def __next__(self):
        self.advance()
        return self.image

    def __add__(self, ss):
        self.images.extend(ss.images)
        return self


shown_node_graphics_warnings = {}


def set_yaw_from_pose(node, default=-90.0, always_set=False):
    """Set node['yaw'] if pose ends in ".E" (0 degrees) or other cardinal
    direction; otherwise if yaw not set already, and always_set is True,
    set to default (-90.0 faces South)
    """
    if node is not None:
        pose = node.get("pose")
        yaw = node.get("yaw")
        if pose is not None:
            parts = pose.split(".")
            if parts > 1:
                if parts[-1] == 'E':
                    node['yaw'] = 0.0
                elif parts[-1] == 'N':
                    node['yaw'] = 90.0
                elif parts[-1] == 'W':
                    node['yaw'] = 180.0
                elif parts[-1] == 'S':
                    node['yaw'] = -90.0
                elif yaw is None and always_set:
                    node['yaw'] = default
            elif yaw is None and always_set:
                node['yaw'] = default


def get_anim_from_mat_name(what, pose=None):
    global materials
    ret = None
    material = materials.get(what)
    if material is not None:
        if pose is None:
            pose = material.get('default_pose')
        if pose not in material['tmp']['sprites']:
            pose = random.choice(list(material['tmp']['sprites']))
        ret = material['tmp']['sprites'][pose]
    return ret


def get_anim_from_node(node):
    global materials
    global shown_node_graphics_warnings
    anim = None
    pose = None
    if node is None:
        return None
    if not hasattr(node, 'get'):
        print("ERROR in get_anim_from_node: " + str(node) +
              " is " + str(type(node)) + " not node dict " +
              " (maybe you sent a node key instead).")
        return None
    pose = node.get('pose')
    if pose is None:
        # print("WARNING: no pose for " + node['what'] + " at " + k)
        pose = materials[node['what']].get('default_pose')
    else:
        return materials[node['what']]['tmp']['sprites'][pose]
    if pose is None:
        yaw = node.get("yaw")
        if yaw is None:
            pose = random.choice(list(material['tmp']['sprites']))
            print("  (pose set randomly to " + pose + ")")
        else:
            direction = get_cardinal_deg(yaw)
            pose = None
            if direction is not None:
                pose = "idle." + direction
            if pose not in materials[node['what']]['tmp']['sprites']:
                pose = random.choice(list(material['tmp']['sprites']))
                print("  (pose set randomly to " + pose + ")")
            else:
                print("  (pose set by yaw to " + pose + ")")
    if pose is not None:
        anim = materials[node['what']]['tmp']['sprites'][pose]
    else:
        name = str(node.get("name"))
        if shown_node_graphics_warnings.get(name) is not True:
            print("There are no graphics for node '" + name + "'")
            shown_node_graphics_warnings[name] = True
    return anim


def unit_is_on_ground(name, double_jump_y=kEpsilon):
    """Returns True, False, or None (no ground directly under)
    for the unit with the given name.
    """
    blocks = world['blocks']
    unit = units.get(name)
    if unit is not None:
        sk = get_key_at_pos(unit['pos'])
        ground_y = nothing_y
        stack = blocks.get(sk)
        if stack is not None:
            ground_y = float(len(stack))
            # offset = len(stack) * block_rise_as_y_px
            if unit['pos'][1] - ground_y <= double_jump_y:
                return True
            else:
                return False
    return None


def unit_jump(name, vel_y, vel_x=None, vel_z=None,
              double_jump_y=kEpsilon):
    blocks = world['blocks']
    unit = units.get(name)
    if unit is not None:
        sk = get_key_at_pos(unit['pos'])
        ground_y = nothing_y
        stack = blocks.get(sk)
        if stack is not None:
            ground_y = float(len(stack))
            # offset = len(stack) * block_rise_as_y_px
        if unit['pos'][1] - ground_y <= double_jump_y:
            if (ground_y >= nothing_y) or (double_jump_y > kEpsilon):
                    # on ground, or allow double jump above nothing
                mps = unit['mps_vec3']
                if vel_y is None:
                    vel_y = 0.0
                if vel_x is None:
                    vel_x = 0.0
                if vel_z is None:
                    vel_z = 0.0
                unit['mps_vec3'] = [mps[0] + vel_x,
                                    mps[1] + vel_y,
                                    mps[2] + vel_z]
                return True
            # else:
            #     print("cannot jump: ground is not present (" +
            #           str(ground_y) + ")")
        # else:
        #     print("cannot jump: ground " + str(ground_y) + " unit " +
        #           str(unit['pos'][1]))
    return False


def draw_frame(screen):
    global settings
    global temp_screen
    global text_pos
    global win_size
    # global scaled_size
    global scaled_b_size
    global block_half_counts
    global start_loc
    global end_loc
    global block_rise_as_y_px
    global b_scale_h
    global desired_scale
    # global scalable_surf
    # global scalable_surf_scale
    global visual_debug_enable
    global default_font
    global popup_showing_text
    global popup_surf
    global popup_shadow_surf
    global popup_text
    global popup_alpha
    global popup_sec
    global prev_frame_ticks
    global total_ticks
    global frame_count
    global good_45deg_tile_sizes
    places = 2
    passed = 0.0  # seconds
    passed_ms = 0
    this_frame_ticks = pg.time.get_ticks()
    fps = 0.0  # clock.get_fps()
    global fps_s
    global world
    frame_gravity = None
    if prev_frame_ticks is not None:
        passed_ms = this_frame_ticks - prev_frame_ticks
        prev_frame_ticks = this_frame_ticks
        passed = float(passed_ms) / 1000.0
        total_ticks += passed_ms
        frame_count += 1
        if total_ticks >= min_fps_ticks:
            # avg = float(total_ticks) / float(min_fps_ticks)
            fps = frame_count / (float(total_ticks)/1000.0)
            fps_s = "{0:.1f}".format(round(fps, 1))
        # if passed > 0.0:
            # fps = 1000/passed
            # fps_s = str(fps)
            # fps_s = str(clock.get_fps())  # clock is only in game
    else:
        prev_frame_ticks = this_frame_ticks

    if default_font is None:
        default_font = pg.font.SysFont(settings['sys_font_name'],
                                       int(settings['sys_font_size']))
    text_pos = [4, 4]
    # pg.draw.rect(screen, color, pg.Rect(x, y, 64, 64))
    new_win_size = screen.get_size()
    if (win_size is None or
            win_size[0] != new_win_size[0] or
            win_size[1] != new_win_size[1]):
        win_size = screen.get_size()
        b_scale_h = None
        # scalable_surf = None
        # print("Changed window size...")
        # print("win_size: " + str(win_size))
        # print("b_scale_h: " + str(b_scale_h))
    block_aspect = math.sqrt(2.0) / 2.0
    """perspective for camera 45 degrees downward"""
    ideal_min_m = 11
    ideal_vert_m = (ideal_min_m/block_aspect)  # meters visible at 45
    # An ideal scale will have about 11 meters for smallest dimension,
    # --based on 16x16 tiles on "visible" area of 90s consoles: 256x176.
    # With perspective (11/(sqrt(2)/2)) that would be ~ideal_m_h meters.
    short_px_count = win_size[1]
    ideal_tile_h = win_size[1] / ideal_vert_m
    ideal_tile_w = ideal_tile_h / block_aspect
    if win_size[0] < win_size[1]:
        short_px_count = win_size[0]
        ideal_tile_w = win_size[0] / ideal_min_m  # no perspective
        ideal_tile_h = ideal_tile_w * block_aspect
    block_scale_vert = None
    # scaled_b_size = (game_tile_size[0] * b_scale_h,
    #                      game_tile_size[1] * block_scale_vert)
    scaled_b_size = None

    for try_size in good_45deg_tile_sizes:
        if try_size[0] >= ideal_tile_w:
            scaled_b_size = try_size
            break
    if scaled_b_size is None:
        push_text("Unknown nearest block size to ideal " +
                  "tile size " + str((ideal_tile_w, ideal_tile_h)))
        scaled_b_size = good_45deg_tile_sizes[-1]

    if b_scale_h is None:
        if desired_scale is None:
            b_scale_h = (ideal_tile_w / game_tile_size[0])
            block_scale_vert = (ideal_tile_h / game_tile_size[1])
            print("b_scale_h automatically chosen: " +
                  str(b_scale_h))
        else:
            b_scale_h = desired_scale
            block_scale_vert = b_scale_h * block_aspect
    sprite_scale = None
    try_scale = 64
    while try_scale > 0:
        if float(try_scale) - b_scale_h < .15 + kEpsilon:
            sprite_scale = float(try_scale)
            break
        try_scale = int(try_scale/2)
    if sprite_scale is None:
        sprite_scale = 1.0
        push_text("Could not find big enough sprite scale for " +
                  "b_scale_h " + str(b_scale_h))
    sprite_f = float(game_tile_size[0])*sprite_scale
    square_sprite_size = (int(round(sprite_f)), int(round(sprite_f)))
    two_h_enable = False
    if b_scale_h < .1:
        b_scale_h = .1
        block_scale_vert = b_scale_h * block_aspect
    else:
        if game_tile_size[0] == game_tile_size[1]:
            block_scale_vert = b_scale_h * block_aspect
            two_h_enable = True
        else:
            block_scale_vert = b_scale_h
    # scaled_size = win_size[0] / b_scale_h, win_size[1] / b_scale_h
    # if scalable_surf is None or b_scale_h != scalable_surf_scale:
        # scalable_surf = pg.Surface((int(scaled_size[0]),
            # int(scaled_size[1]))).convert()  # , flags=pg.SRCALPHA)
        # scalable_surf_scale = b_scale_h
        # temp_screen = scalable_surf
    temp_screen = screen

    # scalable_surf.fill((0, 0, 0))
    screen.fill((0, 0, 0))
    # camera_loc = get_loc_at_px(camera['pos'])
    camera_loc = get_loc_at_pos(camera['pos'])
    # For determining draw range:
    # block_counts = (math.ceil(scaled_size[0] / game_tile_size[0]),
    #                 math.ceil(scaled_size[1] / game_tile_size[1]))
    block_counts = (math.ceil(win_size[0] / scaled_b_size[0]),
                    math.ceil(win_size[1] / scaled_b_size[1]))
    block_half_counts = (int(block_counts[0] / 2) + 1,
                         int(block_counts[1] / 2) + 1)
    # reverse the y order so larger depth value is drawn below other
    # layers (end_loc's y is NEGATIVE on purpose due to draw order)
    offscreen_stack_count = 8
    """how high of a stack will be shown
    if starts below bottom of screen
    """
    block_rise_as_y_px = scaled_b_size[1]
    extra_count = offscreen_stack_count * block_rise_as_y_px
    start_loc = (camera_loc[0] - block_half_counts[0],
                 camera_loc[1] + block_half_counts[1])
    end_loc = (camera_loc[0] + block_half_counts[0],
               camera_loc[1] - block_half_counts[1] - extra_count)
    global screen_half
    # screen_half = scaled_size[0] / 2, scaled_size[1] / 2
    screen_half = win_size[0] / 2, win_size[0] / 2
    w, h = scaled_b_size

    blocks = world['blocks']
    # for k, v in blocks.items():
    block_y = start_loc[1]
    camera_px = (int(camera['pos'][0] * scaled_b_size[0]),
                 int(camera['pos'][2] * scaled_b_size[1]))

    while block_y >= end_loc[1]:
        block_x = start_loc[0]
        while block_x <= end_loc[0]:
            k = str(block_x) + "," + str(block_y)
            v = blocks.get(k)
            if v is not None:
                cs = k.split(",")
                sk = k  # spatial key
                col, row = (int(cs[0]), int(cs[1]))
                # offset = 0
                # rise_factor = .5
                rise = 0.0
                side = None
                for i in range(len(v)):
                    # rise_px = block_rise_as_y_px
                    node = v[i]
                    name = k + "[" + str(i) + "]"  # such as '0,0[1]'
                    pos = (float(col), rise, float(row))
                    anim = get_anim_from_node(node)
                    if anim is None:
                        rise += 1.0
                        continue
                    top = anim.get_surface()
                    src_size = top.get_size()
                    if rise > 0.0:
                        if rise >= 2.0:
                            anim.lowlight = .9
                        else:
                            anim.lowlight = .75
                        side = anim.get_lowlit_surface()
                    block_vec2 = vec2_from_vec3_via_camera(
                        pos,
                        cam_vec2=camera_px
                    )
                    x, y = block_vec2
                    x -= scaled_b_size[0]/2
                    y -= scaled_b_size[1]/2
                    # x = ((pos[0]-camera_px[0]) + screen_half[0] -
                    #      scaled_b_size[0]/2)
                    # y = (-1*(pos[2]-camera_px[1]) + screen_half[1] -
                    #      scaled_b_size[1]/2)
                    if side is not None:
                        screen.blit(pg.transform.scale(side,
                                                       scaled_b_size),
                                    (x, y))  # y-offset
                    screen.blit(pg.transform.scale(top,
                                                   scaled_b_size),
                                (x, y-block_rise_as_y_px))  # y-offset
                    animate = node.get('animate')
                    if animate is True:
                        anim.advance()
                    # offset += block_rise_as_y_px
                    rise += 1.0
            block_x += 1
        block_y -= 1
    global camera_target_unit_name
    sk = None  # must get specific one under unit
    if passed is not None:
        frame_gravity = world['gravity'] * passed
    for k, unit in units.items():
            # TODO: check for python2 units.iteritems()
        debug_unit = visual_debug_enable and (k == player_unit_name)
        material = materials[unit['what']]
        anim = material['tmp']['sprites'][unit['pose']]
        moved_vec3 = [0.0, 0.0, 0.0]
        posA = (unit['pos'][0], unit['pos'][1], unit['pos'][2])
        posB = (posA[0], posA[1], posA[2])  # new pos after physics
        skA = get_key_at_pos(posA)
        skB = get_key_at_pos(posB)
        ground_yA = None
        # ground_yA = unit['tmp'].get('prev_ground_yB')

        if ground_yA is None:
            stackA = blocks.get(skA)
            if stackA is not None:
                ground_yA = float(len(stackA))
            else:
                ground_yA = nothing_y
        aglA = posA[1] - ground_yA
        if debug_unit:
            # push_text("frame_gravity: " +
            # fmt_f(frame_gravity, places=places))
            push_text(k+":")
            # push_text("  before.ground_y:" + str(ground_yA))
            # push_text("  before.posA[1]:" + str(posA[1]))
            # push_text("  before.agl:" + str(aglA))

        on_ground = False
        if posA[1] - ground_yA < kEpsilon:
            on_ground = True
        unit['tmp']['on_ground'] = on_ground

        if passed is not None:
            input_x = unit['tmp']['move_multipliers'][0]
            input_y = unit['tmp']['move_multipliers'][2]
            dest_heading = math.atan2(input_y, input_x)
            mls = unit.get('max_land_mps', settings['human_run_mps'])
            desired_multiplier = max(abs(input_x), abs(input_y))
            if desired_multiplier > 1.0:
                if debug_unit:
                    print("WARNING: desired_multiplier is " +
                          str(desired_multiplier) + " (should be <=1)")
                desired_multiplier = 1.0
            mla = unit.get('max_land_accel',
                           settings['human_run_accel'])
            desired_accel = desired_multiplier * mla
            ls_x = unit['mps_vec3'][0]
            ls_y = unit['mps_vec3'][2]
            ls = math.sqrt(ls_x*ls_x+ls_y*ls_y)  # current land speed
            decel = 27  # TODO: make setting and override
            if desired_accel <= kEpsilon:
                ls -= (decel) * passed
            else:
                ls += desired_accel * passed
            heading = math.radians(unit['yaw_deg'])
            course = heading  # refined below if moving
            if ls > mls:
                ls = mls
                course = math.atan2(ls_y, ls_x)
            elif ls <= kEpsilon:
                ls = 0.0
            # heading = math.radians(unit['yaw_deg'])
            prev_heading = heading
            mode = 'idle'
            pose = unit.get('pose')
            parts = pose.split(".")
            prev_mode = parts[0]
            if desired_multiplier > kEpsilon:
                heading = dest_heading   # TODO: rotate toward
                unit['yaw_deg'] = math.degrees(heading)
                mode = 'walk'
                if mode != prev_mode:
                    anim.iter()  # reset to frame 0
            if (unit['move_in_air'] or on_ground or
                    (unit['tmp'].get('at_edge') is True)):
                unit['mps_vec3'][0] = ls * math.cos(heading)
                unit['mps_vec3'][2] = ls * math.sin(heading)
            unit['mps_vec3'][1] -= frame_gravity

            moved_vec3 = [unit['mps_vec3'][0] * passed,
                          unit['mps_vec3'][1] * passed,
                          unit['mps_vec3'][2] * passed]
            if on_ground:
                auto_pose(unit, mode=mode)
            pose = unit.get('pose')
            if debug_unit:
                # push_text("  before.ground_y: " + str(ground_yA))
                push_text("  unit['pos']: " +
                          fmt_vec(unit['pos'], places=places))
                push_text("  yaw_deg: " + str(unit['yaw_deg']))
                push_text("  prev_heading: " +
                          str(math.degrees(prev_heading)))
                push_text("  heading: " + str(math.degrees(heading)))
                push_text("  pose: " + str(pose))
                push_text("  max_land_mps: " + fmt_f(mls))
                push_text("  unit['tmp']['move_multipliers']: " +
                          fmt_vec(unit['tmp']['move_multipliers']))
                push_text("  dest_heading: " +
                          fmt_f(math.degrees(dest_heading)))
                push_text("  land_speed_vec3: " +
                          fmt_vec((ls_x, 0.0, ls_y)))
                push_text("  desired_accel: " +
                          fmt_f(desired_accel))
                # push_text("  unit['mps_vec3']: " +
                #           fmt_vec(unit['mps_vec3'], places=places))
                # push_text("  moved_vec3: " +
                #           fmt_vec(moved_vec3, places=places))

            # NOTE: atan2 takes y,x and returns radians
            dist_per_frame = 0.5  # TODO: make setting and override
            if on_ground or \
               (unit['tmp']['move_multipliers'][0] != 0.0) or \
               (unit['tmp']['move_multipliers'][2] != 0.0):
                if unit['animate']:
                    msa = unit['tmp'].get('moved_since_advance')
                    if msa is None:
                        msa = 0.0
                    msa += ls * passed
                    if msa >= dist_per_frame:
                        msa -= dist_per_frame
                        anim.advance()
                    unit['tmp']['moved_since_advance'] = msa

            # if unit['pose'] != 0: print("iter " + unit['pose'])
        # else:
            # if unit['pose'] != 0: print("hold " + unit['pose'])
        # screen_half = scaled_size[0] / 2, scaled_size[1] / 2
        screen_half = win_size[0] / 2, win_size[0] / 2
        w, h = game_tile_size
        # center_tile_tl_pos = win_size[0]/2-game_tile_size[0]/2,
        #                      win_size[1]/2-game_tile_size[1]/2
        # center_tile_tl_pos = (0,0)
        # unit['pos'][0] += moved_vec3[0]
        # unit['pos'][1] + moved_vec3[2]
        posB = [posA[0] + moved_vec3[0],
                posA[1] + moved_vec3[1],
                posA[2] + moved_vec3[2]]
        skB = get_key_at_pos(posB)
        stackB = blocks.get(skB)
        if stackB is not None:
            ground_yB = float(len(stackB))
        else:
            ground_yB = nothing_y

        # offset = -block_rise_as_y_px
        # prev_agl = posA[1] - ground_yA
        # agl: # above ground level

        aglB = posB[1] - ground_yB
        # if debug_unit:
        #     push_text("  processing.ground_y:" + str(ground_yB))
        #     push_text("  processing.posB[1]:" + str(posB[1]))
        #     push_text("  processing.agl:" + str(aglB))
        limited_horz = False

        push_msg = ""

        if ground_yB - posB[1] > unit['auto_climb_max']:
            push_msg += (" -- hit side since" +
                         fmt_f(ground_yB - posB[1]) +
                         "  >  " + fmt_f(unit['auto_climb_max']) +
                         " auto_climb_max")
            unit['mps_vec3'][0] = 0.0
            unit['mps_vec3'][2] = 0.0
            posB[0] = posA[0]
            posB[2] = posA[2]
            moved_vec3[0] = 0.0
            moved_vec3[2] = 0.0
            aglB = aglA
            ground_yB = ground_yA
            limited_horz = True
            unit['tmp']['at_edge'] = True
        else:
            unit['tmp']['at_edge'] = False

        if posB[1] < ground_yB:
            # push_msg = "pushed up"
            # fmt_f(posB[1]) + " to " + fmt_f(ground_yB)
            aglB = 0.0
            posB[1] = ground_yB
            moved_vec3[1] = posB[1] - posA[1]

        if aglB <= 0.0:
            if debug_unit:
                push_text("on ground " + push_msg)
            if unit['mps_vec3'][1] < 0.0:
                unit['mps_vec3'][1] = 0.0
            # else must be jumping or no vertical movement
        else:
            if debug_unit:
                push_text("airborne")

        unit['pos'] = (posB[0], posB[1], posB[2])

        if limited_horz:
            skB = get_key_at_pos(unit['pos'])
            stackB = blocks.get(skB)
            if stackB is not None:
                ground_yB = float(len(stackB))
            else:
                ground_yB = nothing_y
        if debug_unit:
            push_text("  unit['mps_vec3']: " +
                      fmt_vec(unit['mps_vec3'], places=places))
        unit['tmp']['prev_ground_yB'] = ground_yB
        src_size = anim.get_surface().get_size()
        # if x+w < 0 or x >= win_size[0]:
        #     continue

        this_size = src_size[0]*sprite_scale, src_size[1]*sprite_scale
        x, y = vec2_from_vec3_via_camera(unit['pos'],
                                         cam_vec2=camera_px)
        x -= this_size[0] / 2
        rise_factor = .125
        y -= this_size[1] - float(this_size[1]) * rise_factor
        """imaginary "center" of feet should have 1/8 tile height
        space before bottom of tile (1/8 = .125)"""
        # if y+w < 0 or y >= win_size[0]:
        #     continue
        # if k=="me":
        #     print("me at " + str((x,y)))
        # scalable_surf.blit(anim.get_surface(), (x,y-offset))
        screen.blit(pg.transform.scale(anim.get_surface(),
                                       square_sprite_size),
                    (x, y))  # y-offset
        # surface = next(anim)
        target_size = (1, 1)
        if k == player_unit_name:
            if visual_debug_enable:
                # push_text("  after.ground_y:" + str(ground_yB))
                # push_text("  after.agl:" + str(aglB))
                # push_text("  after.unit['mps_vec3']:" +
                #           fmt_vec(unit['mps_vec3'], places=places))
                # push_text("  after.unit['pos']:" +
                #           fmt_vec(unit['pos'], places=places))
                push_text("  moved_vec3:" +
                          fmt_vec(moved_vec3, places=places))
            target = get_unit_crosshairs_vec3(unit)
            x, y = vec2_from_vec3_via_camera(target, cam_vec2=camera_px)
            color = (200, 10, 0)
            pg.draw.rect(
                screen,  # scalable_surf,
                color,
                pg.Rect(x-int(target_size[0]/2),
                        y-int(target_size[1]/2),
                        target_size[0],
                        target_size[1])
            )

    if (popup_surf is None) or (popup_showing_text != popup_text):
        if popup_text is not None:
            popup_surf = default_font.render(
                popup_text, settings['text_antialiasing'],
                (255, 255, 255)
            )
            popup_shadow_surf = default_font.render(popup_text,
                                                    False, (0, 0, 0))
            popup_sec = settings["popup_sec_per_glyph"] * len(popup_text)
            popup_alpha = 255
            settings["popup_sec_per_character"] = .04
        else:
            popup_surf = default_font.render(
                "", settings['text_antialiasing'], (255, 255, 255)
            )
            popup_shadow_surf = default_font.render(
                "", settings['text_antialiasing'], (0, 0, 0)
            )
        popup_showing_text = popup_text

    if popup_surf is not None:
        if popup_sec > 0:
            popup_sec -= passed
        if popup_alpha > 0:
            if popup_sec <= 0:
                popup_shadow_surf.set_alpha(popup_alpha)
                popup_surf.set_alpha(popup_alpha)
            # scalable_surf.blit
            screen.blit(popup_shadow_surf,
                        (text_pos[0]+2, text_pos[1]+1))
            # scalable_surf.blit

            screen.blit(popup_surf, (text_pos[0], text_pos[1]))
            text_size = popup_surf.get_size()
            text_pos[1] += text_size[1]
            popup_alpha -= settings["popup_alpha_per_sec"] * passed
    global bindings
    q = bindings.get('draw_ui')
    for f in q:
        f({'screen': screen})   # formerly scalable_surf
    # screen.blit(pg.transform.scale(scalable_surf,
    #                                (int(win_size[0]),int(win_size[1]))),
    #             (0,0))
    show_stats_once()
    if camera_target_unit_name is not None:
            move_camera_to(camera_target_unit_name)

    if visual_debug_enable:
        push_text("b_scale_h: " + str(b_scale_h))
        push_text("FPS: " + fps_s)
        path = get_preview_tileset_path()
        tileset = None
        preview_surf = None
        # make checkerboard bg:
        cb_surf = checkerboard.get("surf")
        # preview_pane_size = (win_size[0] - preview_pos[0],
        #                      win_size[1] - preview_pos[1])
        if path is not None:
            preview_surf = file_surfs.get(path)
            tileset = tilesets.get(path)

        cell_size = None
        cols = None
        rows = None
        col = gui_state['select.x']
        row = gui_state['select.y']
        if (preview_surf is not None) and (tileset is not None):
            cell_size = tileset['tile_size']
            preview_pane_size = preview_surf.get_size()
            pre_box_pos = (win_size[0] / 2, win_size[1] / 2)
            hs = cell_size[0] // 2, cell_size[1] // 2
            cols = preview_surf.get_size()[0] // cell_size[0]
            rows = preview_surf.get_size()[1] // cell_size[1]
            pre_box_pos = pre_box_pos[0] - hs[0], pre_box_pos[1] - hs[1]
            pre_mov = (col*cell_size[0], row*cell_size[1])
            preview_pos = (pre_box_pos[0]-pre_mov[0],
                           pre_box_pos[1]-pre_mov[1])
            preview_rect = pg.Rect(preview_pos, preview_pane_size)
            screen.blit(preview_surf, preview_pos)

            if ((cb_surf is None) or
                    (preview_rect != checkerboard['rect'])):
                cb_surf = pg.Rect(preview_rect)
                checkerboard['surf'] = cb_surf
                checkerboard['rect'] = preview_rect.copy()

            pg.draw.rect(screen, (128, 128, 128),
                         preview_rect.inflate(2, 2), 1)
            pg.draw.rect(screen, (0, 0, 0),
                         preview_rect.inflate(4, 4), 1)
            if cell_size is not None:
                inner_rect = pg.Rect(pre_box_pos, cell_size)
                inner_rect.inflate_ip(2, 2)
                outer_rect = inner_rect.inflate(2, 2)
                pg.draw.rect(screen, (255, 255, 255), inner_rect, 1)
                pg.draw.rect(screen, (0, 0, 0), outer_rect, 1)
            push_text("preview_tileset: ")
            push_text("  preview_tileset_i: " + str(preview_tileset_i))
            push_text("  path: " + path)
            push_text("  len(file_surfs): " + str(len(file_surfs)))
            push_text("  cell_size: " + str(cell_size))
        else:
            push_text("preview_tileset: ")
            push_text("  preview_tileset_i: " + str(preview_tileset_i))
            push_text("  path: " + str(path))
            push_text("  len(file_surfs): " + str(len(file_surfs)))
            push_text("  preview_surf: " + str(preview_surf))
            push_text("  tileset: " + str(tileset))

        push_text("gui_state: " + str(gui_state))
        push_text("")
        push_text("preview_tile: ")
        if ((col >= 0) and (row >= 0)):
            push_text("  col,row: " +
                      str(col+1) + "," +
                      str(row+1))
            if cols is not None:
                push_text("  ID: " + str(row*cols+col))
        else:
            push_text("  col,row: None")


show_stats_enable = True


def show_stats_once():
    global show_stats_enable
    if show_stats_enable:
        print()
        print("win_size: " + str(win_size))
        # print("scaled_size: " + str(scaled_size))
        print("scaled_b_size: " + str(scaled_b_size))
        print("block_half_counts: " + str(block_half_counts))
        print("start_loc: " + str(start_loc))
        print("end_loc: " + str(end_loc))
        print("b_scale_h: " + str(b_scale_h))
    show_stats_enable = False


def draw_text_vec2(s, color, surf, vec2):
    global default_font
    if default_font is None:
        default_font = pg.font.SysFont(settings['sys_font_name'],
                                       int(settings['sys_font_size']))
    if surf is not None:
        s_surf = default_font.render(s, settings['text_antialiasing'],
                                     color)
        text_size = s_surf.get_size()
        surf.blit(s_surf, (vec2[0], vec2[1]))


def push_text(s, color=(255, 255, 255), screen=None):
    global text_pos
    global temp_screen
    global settings
    global default_font
    if default_font is None:
        default_font = pg.font.SysFont(settings['sys_font_name'],
                                       int(settings['sys_font_size']))
    if screen is not None:
        temp_screen = screen
    if temp_screen is not None:

        try:
            s_surf = default_font.render(s,
                                         settings['text_antialiasing'],
                                         color)
            text_size = s_surf.get_size()
            temp_screen.blit(s_surf, (text_pos[0], text_pos[1]))
            text_pos[1] += text_size[1]
        except AttributeError:
            # TODO: remove this? it is probably wrong--was put here for
            # either Pygame Zero (game engine) or pgs4a (Pygame subset
            # for Android)
            temp_screen.draw.text("Outlined text", text_pos, owidth=1.5,
                                  ocolor=(255, 255, 0), color=(0, 0, 0),
                                  fontsize=14)
            text_pos[1] += 18


def _load_sprite(what, cells, order=None, gettable=True,
                 pose=None, path=None, has_ai=False,
                 native=True, overlayable=False,
                 biome="default", series=None, loop=True,
                 default_animate=None):
    """
    Load a sprite (stored as a series of pose animations in the case of
    mgep) from a sprite sheet.

    Keyword arguments:
    series -- if more than one frame, you can pass pre-generated sprite loop
    order -- (requires len(series)>1) indices of frames specifying order
             starting at 1
    """
    # results = {}
    if path is None:
        path = last_loaded_path
    material = None
    material = materials.get(what, None)  # default to new material
    if material is None:
        material = {}
        material['tmp'] = {}
        materials[what] = material
    if pose is None:
        try_as_i = 0
        try_as = str(try_as_i)
        mfr = material.get("serials")
        if mfr is not None:
            while try_as in mfr:
                try_as_i += 1
                try_as = str(try_as_i)
        else:
            material["serials"] = {}
        pose = try_as
    else:
        if material.get("serials") is None:
            material['serials'] = {}
    prev_cells = material["serials"].get(pose)
    if prev_cells is None:
        material["serials"][pose] = cells
    else:
        material["serials"][pose].extend(cells)

    # prev_sprite = material['tmp']['sprites'].get(pose)
    w, h = tilesets[path]['tile_size']
    if series is None:
        for col, row in cells:
            rect = ((col-1)*w, (row-1)*h, w, h)
            if series is None:
                series = SpriteStripAnim(path, rect, 1, loop=loop)
            else:
                series += SpriteStripAnim(path, rect, 1, loop=loop)

    if material['tmp'].get('sprites') is None:
        material['tmp']['sprites'] = {}

    if material['tmp']['sprites'].get(pose) is None:
        material['tmp']['sprites'][pose] = series
    else:
        material['tmp']['sprites'][pose] += series

    if material.get('default_pose') is None:
        material['default_pose'] = pose
    material["overlayable"] = overlayable
    material["biome"] = biome
    surf = file_surfs.get(path)
    if surf is None:
        surf = pg.image.load(path)  # .convert_alpha()
        file_surfs[path] = surf
        surf_paths.append(path)
    # w, h = surf.get_size()
    # return results


def load_material(what, column, row, gettable=True,
                  pose=None, path=None, has_ai=False,
                  native=True, overlayable=False,
                  biome="default", count=1, order=None,
                  next_offset="right", loop=True, default_animate=None):
    """gettable allows player to get material

    Keyword arguments:
    path -- if None, then uses last loaded tileset
    """
    global game_tile_size
    if default_animate is None:
        if count > 1:
            default_animate = True
    if path is None:
        path = last_loaded_path
    cells = []
    next_offset = next_offset.lower()
    for i in range(count):
        if next_offset == "up":
            cells.append((row-i, column))
        elif next_offset == "down":
            cells.append((row+i, column))
        elif next_offset == "left":
            cells.append((row, column-i))
        elif next_offset == "right":
            cells.append((row, column+i))
        else:
            print("ERROR in load_material: unknown next_offset " +
                  str(next_offset) + " (use 'up' 'down' 'left' 'right'")
            cells.append((row+i, column))
    if native:
        material_choose.append(what)  # increase spawn odds each time
    if order is not None:
        for n in order:
            if n > count:
                count = n  # n is a counting number (starts at 1)
    w, h = tilesets[path]['tile_size']
    col = column
    rect = ((col-1)*w, (row-1)*h, w, h)
    series = SpriteStripAnim(path, rect, count, order=order, loop=loop)
    _load_sprite(what, cells, order=order, gettable=gettable,
                 pose=pose, path=path, has_ai=has_ai,
                 native=native,
                 overlayable=overlayable,
                 biome=biome, series=series, loop=loop,
                 default_animate=default_animate)
    if what not in materials:
        materials[what] = {}
    prev_path = materials[what].get('path')
    if prev_path is not None:
        if prev_path != path:
            print("ERROR: material " + what + " is trying to load a" +
                  " tile from '" + path + "' but was created using " +
                  "'" + prev_path + "'")
            materials[what]['path'] = path
    else:
        materials[what]['path'] = path
    if game_tile_size is None:
        game_tile_size = tilesets[path]['tile_size']
        print("game_tile_size from material: " + str(game_tile_size))


def load_character(what, column, row, gettable=False,
                   pose=None, path=None, has_ai=False,
                   native=False, overlayable=True,
                   biome=None, count=1, order=None,
                   next_offset="right"):
    """same as load_material but with different defaults"""
    load_material(what, column, row, gettable=gettable,
                  pose=pose, path=path, has_ai=has_ai,
                  native=native,
                  overlayable=overlayable,
                  biome=biome, count=count, order=order,
                  next_offset=next_offset, loop=True,
                  default_animate=True)


def load_character_3x4(what, column, row, order="NWSE"):
    """
    loads a "3x4" character sheet where columns
    are in standard 3-frame order:
    [idle,step1,step3] (where idle frame is also step2)
    and the rows are arranged based on Liberated Pixel Cup:
    ['walk.N','walk.W','walk.S','walk.E']  # (North, West, South, East)
    """
    load_character(what, column, row, pose='idle.'+order[0])
    load_character(what, column, row+1, pose='idle.'+order[1])
    load_character(what, column, row+2, pose='idle.'+order[2])
    load_character(what, column, row+3, pose='idle.'+order[3])
    load_character(what, column, row, order=[2, 1, 3, 1],
                   pose='walk.'+order[0])
    load_character(what, column, row+1, order=[2, 1, 3, 1],
                   pose='walk.'+order[1])
    load_character(what, column, row+2, order=[2, 1, 3, 1],
                   pose='walk.'+order[2])
    load_character(what, column, row+3, order=[2, 1, 3, 1],
                   pose='walk.'+order[3])


overrides_help_enable = False


def _place_unit(what, name, pos, pose=None, animate=True, overrides=None):
    global overrides_help_enable
    if name in units:
        raise ValueError("There is already a unit named " + name)
    units[name] = {}
    units[name]['tmp'] = {}
    units[name]['what'] = what
    if len(pos) < 3:
        units[name]['pos'] = float(pos[0]), 10.0, float(pos[1])
    else:
        units[name]['pos'] = float(pos[0]), float(pos[1]), float(pos[2])

    try:
        if pose is None:
            pose = materials[what]['default_pose']
    except TypeError:
        raise TypeError("ERROR in _place_unit: what is '" +
                        str(what) + "' is unknown unit type")
    units[name]['pose'] = pose
    units[name]['animate'] = animate
    units[name]['yaw_deg'] = -90.0
    units[name]['mps_vec3'] = [0.0, 0.0, 0.0]
    # TODO: place on ground (being below ground is a problem)
    units[name]['tmp']['move_multipliers'] = [0.0, 0.0, 0.0]
    units[name]['auto_climb_max'] = 0.2  # usually low (catch edge)
    units[name]['move_in_air'] = False
    if overrides_help_enable:
        print("Player 1 added.")
        print("Overrides dict can contain the following keys: ")
        for k, v in units[name].items():
            print("  " + k + " #default:"+str(v)+"")
        overrides_help_enable = False
    if overrides is not None:
        for k, v in overrides.items():
            units[name][k] = v


def stop_unit(name):
    unit = units[name]
    material = materials[unit['what']]
    # direction = get_cardinal_deg(unit.get('yaw_deg'))
    unit['tmp']['move_multipliers'] = [0.0, 0.0, 0.0]
    on_ground = unit['tmp'].get('on_ground')
    if on_ground is True:
        mode = 'idle'
        auto_pose(unit, mode=mode)
        pose = unit.get('pose')
        if mode + "." not in pose:
            pose = 'idle'
        # if direction is not None:
            # pose = 'idle.' + direction
        if pose in material['tmp']['sprites']:
            unit['pose'] = pose
        else:
            unit['animate'] = False


def place_character(what, name, pos, overrides=None):
    """creates a new unit based on 'what' graphic, with a unique name

    Sequential arguments:
    what -- what material to use for character graphic
            (improper noun, nonunique [type not block])
    name -- name of character
    pos -- the (x,y) cartesian (y up) position of the character

    Keyword arguments:
    overrides -- not yet implemented
    """
    # TODO: implement overrides
    _place_unit(what, name, pos)
    global player_unit_name
    if player_unit_name is None:
        player_unit_name = name


def load_tileset(path, count_x, count_y, margin_l=0, margin_t=0,
                 margin_r=0, margin_b=0, spacing_x=0, spacing_y=0):
    global last_loaded_path
    global tilesets
    last_loaded_path = path
    surf = file_surfs.get(path)
    if surf is None:
        surf = pg.image.load(path)  # s.convert_alpha()
        file_surfs[path] = surf
        surf_paths.append(path)
    w, h = surf.get_size()
    tilesets[path] = {}
    u_size = (w-margin_l-margin_r+spacing_x,
              h-margin_t-margin_b+spacing_y)
    f_s = u_size[0]/count_x-spacing_x, u_size[1]/count_y-spacing_y
    tilesets[path]['tile_size'] = int(f_s[0]), int(f_s[1])
    cell_size = tilesets[path]['tile_size']
    tilesets[path]['cols'] = w // cell_size[0]
    tilesets[path]['rows'] = h // cell_size[1]
    t_s = tilesets[path]['tile_size']
    if t_s[0] != int(f_s[0]) or t_s[1] != int(f_s[1]) or \
            t_s[0] < 1 or t_s[1] < 1:
        raise ValueError(
            "tileset geometry is nonsensical: derived "
            "tile size " + str(f_s) + " should be whole number > 0"
        )


def other_keydown(event):
    if event.key == pg.K_F3:
        tileset_cycle_enable = False
        if visual_debug_enable is False:
            tileset_cycle_enable = True
        toggle_visual_debug(tileset_cycle_enable=tileset_cycle_enable)
    elif event.key == pg.K_UP:
        change_preview_tile(move_x=0, move_y=-1)
    elif event.key == pg.K_LEFT:
        change_preview_tile(move_x=-1, move_y=0)
    elif event.key == pg.K_DOWN:
        change_preview_tile(move_x=0, move_y=1)
    elif event.key == pg.K_RIGHT:
        change_preview_tile(move_x=1, move_y=0)


def get_loc_at_pos(pos):
    world_loc = (int(pos[0]), int(pos[2]))
    return world_loc


def get_loc_at_px(vec2):
    world_loc = (int(vec2[0] / game_tile_size[0]),
                 int(vec2[1] / game_tile_size[1]))
    return world_loc


def get_gobs_at(loc):
    result = None
    # sk for spatial key
    sk = str(loc[0])+","+str(loc[1])
    raise NotImplementedError("NYI")
    return result


def _place_world():
    if last_loaded_path is None:
        raise ValueError("missing last_loaded_path (must load_tileset"
                         "before load_world can call graphics methods)")
    # blocks = world['blocks']
    # for k, block in blocks.items():
    #     cs = k.split(",")  # key is a location string
    #     col, row = (int(cs[0]), int(cs[1]))
    #     w, h = game_tile_size  # tilesets[path]['tile_size']
    #     for i in range(len(block)):
    #         node = block[i]
    #         name = k + "[" + str(i) + "]"
    #         pose = None
    #         if 'pose' in node:
    #             pose = node['pose']
    #         _place_unit(node['what'], name, (col*w, row*h), pose=pose)


def get_whats(nodes):
    results = []
    for node in nodes:
        what = node.get('what')
        results.append(what)
    return results


def get_blocks(key):
    return world['blocks'].get(key)


def pop_node(key):
    sk = key  # spatial key
    result = None
    blocks = world['blocks']
    if sk in blocks:
        if len(blocks[sk]) > 1:
            result = blocks[sk][-1]
            del blocks[sk][-1]
            # result = units[sk]
            # units.remove(sk)
    else:
        print("ERROR in pop_unit: bad key " + str(key) + "(must be "
              "'int,int' where int are whole numbers and location "
              "is a loaded part of the world")
    return result


def save_world():
    print("saving world...")
    global last_loaded_world_name
    global world
    if last_loaded_world_name is not None:
        name = last_loaded_world_name
        path = name + ".json"
        with open(path, "w") as outs:
            json.dump(world, outs)
        print("saved '" + os.path.abspath(path))


def load_world(name, generate=False):
    global world
    global last_loaded_world_name
    global settings
    last_loaded_world_name = name
    world = None
    path = name + ".json"
    print("world path: " + path)
    if os.path.isfile(path):
        print("  loading...")
        with open(path, "r") as ins:
            world = json.load(ins)
    if world is not None:
        if 'gravity' not in world:
            world['gravity'] = settings['default_world_gravity']
        print("  loaded existing world.")
        return
    else:
        print("  generating...")
    world = {}
    world['gravity'] = settings['default_world_gravity']
    world['blocks'] = {}
    blocks = world['blocks']
    # TODO: if generate:
    bedrock_what = None
    material_all = list(materials)
    if 'bedrock' in material_all:
        bedrock_what = 'bedrock'
    elif 'dirt' in material_all:
        bedrock_what = 'dirt'
    for col in range(-30, 30):
        for row in reversed(range(-30, 30)):
            sk = str(col)+","+str(row)
            blocks[sk] = []
            if len(materials) > 0:
                if bedrock_what is not None:
                    bedrock = {}  # recreate each time so not instance
                    bedrock['what'] = bedrock_what
                    if bedrock is not None:
                        blocks[sk].append(bedrock)
                    else:
                        print("WARNING: no 'bedrock' material")
                node = {}
                node['what'] = random.choice(material_choose)
                if node['what'] is not None:
                    default_animate = \
                        materials[node['what']].get('default_animate')
                    if default_animate is True:
                        node['animate'] = True
                    # else None or False so don't waste storage space
                    material = materials[node['what']]
                    # converting a dict to a list yields the keys:
                    node['pose'] = random.choice(
                        list(material['tmp']['sprites'])
                    )
                    # print("generated " + node['what'] + " pose " +
                    #       node['pose'] + " at " + sk)
                    blocks[sk].append(node)
                # else:
                    # print("generated None at " + sk)
        print("  placing...")
    _place_world()
    print("  finished (load_world).")


def dump_internals():
    print()
    print("SHOWING INTERNALS")
    print("good_45deg_tile_sizes: " + str(good_45deg_tile_sizes))
    print()
    print("Instead of running this file, use it in your program like:\n"
          "from mgep import *\n"
          "#see also example-*.pyw")
    print()


if __name__ == "__main__":
    dump_internals()