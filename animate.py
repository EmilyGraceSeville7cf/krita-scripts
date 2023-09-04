import krita
import re

# Allows to add keyframes for top-level paint layers
# and transform masks where at least one transform
# keyframe is defined.
# All options to configure script behavior.
options = {
   # Layer frames
   "keyframes": {
       # Create 10th and 100th frame for layers start with 'Ball'
       "^Ball": {
           # Keyframes for opacity
           "opacity": [10, 100],
           # Keyframes for transform mask
           "transform": [10, 100]
       }
   },
   
   # Exclude layers
   "exclude": set(),
   
   # A multiply factor for all list items in keyframes
   "scale": 1.2,
   
   # A first frame
   "start": 0,
   
   # A last frame
   "end": 100
}

def warn_when_not(condition, text):
    if not condition:
        print(f"Warning: {text}.")
    
    return condition

def warn_when_not_type(key, type, source=options):
    keys = key
    if isinstance(key, str):
        keys = [key]
    
    result_key = source[keys[0]]
    for i in range(1, len(keys)):
        result_key = result_key[keys[i]]
    
    key = ".".join(keys)
    return warn_when_not((result_key is not None) and isinstance(result_key, type), f"{key} should be {type}")

def warn_when_not_item_type(value, index, type):
    return warn_when_not((value is not None) and isinstance(value, type), f"{value} ({index}th item) should be {type}")

def warn_when_at_least_one_not_item_type(values, type):
    return all([warn_when_not_item_type(item, i, type) for i, item in enumerate(values)])

def warn_when_not_item_positive(value, index):
    return warn_when_not(value >= 0, f"{value} ({index}th item) should be equal to or greater than 0")

def warn_when_at_least_one_not_item_positive(values):
    return all([warn_when_not_item_positive(item, i) for i, item in enumerate(values)])

def warn_when_not_positive(value):
    return warn_when_not(value >= 0, f"{value} should be equal to or greater than 0")

def validate_options():
    types_correct = all([warn_when_not(options is not None, "Options can't be None"),
        warn_when_not_type("keyframes", dict),
        warn_when_not_type("exclude", set),
        warn_when_not_type("scale", float),
        warn_when_not_type("start", int),
        warn_when_not_type("end", int)])
    
    for key in options["keyframes"]:
        types_correct = types_correct and warn_when_not_type(key, dict, options["keyframes"])
        animation = options["keyframes"][key]
        types_correct = all([types_correct,
            warn_when_not_type("opacity", list, animation),
            warn_when_not_type("transform", list, animation)])
        types_correct = types_correct and warn_when_at_least_one_not_item_type(animation["opacity"], int)
        types_correct = types_correct and warn_when_at_least_one_not_item_type(animation["transform"], int)

    ranges_correct = True    
    for key in options["keyframes"]:
        animation = options["keyframes"][key]
        ranges_correct = ranges_correct and warn_when_at_least_one_not_item_positive(animation["opacity"])
        ranges_correct = ranges_correct and warn_when_at_least_one_not_item_positive(animation["transform"])
        
    return all([types_correct,
        ranges_correct,
        warn_when_not_positive(options["scale"]),
        warn_when_not_positive(options["start"]),
        warn_when_not_positive(options["end"]),
        warn_when_not(options["start"] <= options["end"], f"start should be equal to or less than end")])

def is_affected(layer, include, excludes):
    is_included = re.match(include, layer) != None
    if excludes == []:
        return is_included
    return is_included and not any([re.match(exclude, layer) for exclude in excludes])

def create_animation(document, layer, key):
    name = layer.name()
    animation = options["keyframes"][key]
    if is_affected(name, key, options["exclude"]):
        if animation["transform"] != []:
            transform = document.createTransformMask("Transform")
            layer.addChildNode(transform, None)
        
        for keyframe in animation["opacity"]:
            document.setCurrentTime(int(keyframe * options["scale"]))
            # How to create opacity curve point in Animation Curves?
            
        for keyframe in animation["transform"]:
            document.setCurrentTime(int(keyframe * options["scale"]))
            # How to create transform curve point in Animation Curves?

def create_animations(instance, layers):
    document = instance.activeDocument()
    for layer in layers:
        if layer.type() != "paintlayer":
            continue
        
        for key in options["keyframes"]:
            create_animation(document, layer, key)
                     

document = krita.Krita.instance().activeDocument()

if warn_when_not(document is not None, "Document should be opened") and validate_options():
    document.setFullClipRangeStartTime(int(options["start"] * options["scale"]))
    document.setFullClipRangeEndTime(int(options["end"] * options["scale"]))
    create_animations(krita.Krita.instance(), document.topLevelNodes())
