import krita
import re
import string

# Allows to rename several layers at once to unify naming schema in a file.
# All options to configure script behavior.
options = {
     # Whether to rename the bottom layer to renameBackgroundLayerOptions.name
    "renameBackgroundLayer": True,
    "renameBackgroundLayerOptions": {
        # A background layer name
        "name": "Background"
    },
    
    # Whether to rename layers
    "renameLayer": True,
    "renameLayerOptions": {
        # Layers to include
        # If a layer is included it can be excluded via exclude
        "include": [".*"],
        
        # Layers to exclude
        # If a layer is excluded via exclude it can't be included via include
        "exclude": [],
        
        # Whether to squeeze spaces
        "shorten": True,
        
        # Whether to replace punctuation by replacePunctuationOptions.delimiter
        "replacePunctuation": True,
        "replacePunctuationOptions": {
            # A word delimiter
            "delimiter": ","
        }
    },
    
    # Whether to rename transform layers by the following rules:
    # - omit any words except renameTransformMaskOptions.words
    # - sort words in the order they listed in renameTransformMaskOptions.words
    #
    # Enabling this options implies that renameLayer is on. If not, it fails to work.
    "renameTransformMask": True,
    "renameTransformMaskOptions": {
        # Transform masks to include
        # If a transform mask is included it can be excluded via exclude
        "include": [".*"],
        
        # Transform masks to exclude
        # If a transform mask is excluded via exclude it can't be included via include
        "exclude": [],
        
        # Words for transform masks
        "words": ["Move", "Rotate", "Scale"]
     }
}


def warn_when_not(condition, text):
    if not condition:
        print(f"Warning: {text}.")
    
    return condition

def warn_when_not_type(key, type):
    keys = key
    if isinstance(key, str):
        keys = [key]
    
    result_key = options[keys[0]]
    for i in range(1, len(keys)):
        result_key = result_key[keys[i]]
    
    key = ".".join(keys)
    return warn_when_not((result_key is not None) and isinstance(result_key, type), f"{key} should be {type}")

def warn_when_not_item_type(value, index, type):
    return warn_when_not((value is not None) and isinstance(value, type), f"{value} ({index}th item) should be {type}")

def warn_when_at_least_one_not_item_type(values, type):
    return all([warn_when_not_item_type(item, i, type) for i, item in enumerate(values)])

def validate_options():
    return all([warn_when_not(options is not None, "Options can't be None"),
        warn_when_not_type("renameBackgroundLayer", bool),
        warn_when_not_type("renameBackgroundLayerOptions", dict),
        warn_when_not_type(["renameBackgroundLayerOptions", "name"], str),
        warn_when_not_type("renameLayer", bool),
        warn_when_not_type("renameLayerOptions", dict),
        warn_when_not_type(["renameLayerOptions", "include"], list),
        warn_when_at_least_one_not_item_type(options["renameLayerOptions"]["include"], str),
        warn_when_at_least_one_not_item_type(options["renameLayerOptions"]["exclude"], str),
        warn_when_not_type(["renameLayerOptions", "exclude"], list),
        warn_when_not_type(["renameLayerOptions", "shorten"], bool),
        warn_when_not_type(["renameLayerOptions", "replacePunctuation"], bool),
        warn_when_not_type(["renameLayerOptions", "replacePunctuationOptions", "delimiter"], str),
        warn_when_not_type("renameTransformMask", bool),
        warn_when_not_type("renameTransformMaskOptions", dict),
        warn_when_not_type(["renameTransformMaskOptions", "include"], list),
        warn_when_not_type(["renameTransformMaskOptions", "exclude"], list),
        warn_when_at_least_one_not_item_type(options["renameTransformMaskOptions"]["include"], str),
        warn_when_at_least_one_not_item_type(options["renameTransformMaskOptions"]["exclude"], str),
        warn_when_not_type(["renameTransformMaskOptions", "words"], list),
        warn_when_at_least_one_not_item_type(options["renameTransformMaskOptions"]["words"], str),])

def is_affected(layer, includes, excludes):
    is_included = any([re.match(include, layer) for include in includes])
    if excludes == []:
        return is_included
    return is_included and not any([re.match(exclude, layer) for exclude in excludes])
    

def rename_background_layer(layers):
    name = options["renameBackgroundLayerOptions"]["name"]
    background = layers[0]
    if not warn_when_not(background.name() == name, f"'{background.name()}' background layer should be named '{name}'"):
        background.setName(name)

def rename_layers(layers):
    for layer in layers:
        name = layer.name()
        if is_affected(name, options["renameLayerOptions"]["include"], options["renameLayerOptions"]["exclude"]):
            if options["renameLayerOptions"]["replacePunctuation"]:
                delimiter = re.escape(options["renameLayerOptions"]["replacePunctuationOptions"]["delimiter"])
                name = re.sub("[" + re.escape(string.punctuation) + "]", delimiter, name)
                name = re.sub(f"({delimiter})+", delimiter, name)
                name = re.sub(f"\s+{delimiter}", f"{delimiter} ", name)
            if options["renameLayerOptions"]["shorten"]:
                name = re.sub("\s+", " ", name)

            if not warn_when_not(layer.name() == name, f"'{layer.name()}' layer should be named '{name}'"):
                layer.setName(name)

        if layer.childNodes() != []:
            rename_layers(layer.childNodes())

def rename_transform_masks(layers):
    if not warn_when_not(options["renameLayer"], "'renameLayer' should be turned on to use 'renameTransformMask'"):
        return

    for layer in layers:
        name = layer.name()
        if is_affected(name, options["renameTransformMaskOptions"]["include"], options["renameTransformMaskOptions"]["exclude"]) and layer.type() == "transformmask":
            delimiter = options["renameLayerOptions"]["replacePunctuationOptions"]["delimiter"]
            words = name.split(delimiter)
            allowed_words = options["renameTransformMaskOptions"]["words"]
            words = list(set([word.strip() for word in words if word.strip() in allowed_words]))
            words = [word for word in allowed_words if word in words]
            name = f"{delimiter} ".join(words)
            
            allowed = ", ".join(allowed_words)
            if warn_when_not(name != "", f"'{layer.name()}' transform mask should contain at least one of '{allowed}' words"):
                if not warn_when_not(layer.name() == name, f"'{layer.name()}' transform mask should be named '{name}'"):
                    layer.setName(name)

        if layer.childNodes() != []:
            rename_transform_masks(layer.childNodes())


document = krita.Krita.instance().activeDocument()
if warn_when_not(document is not None, "Document should be opened") and validate_options():
    top_layers = document.topLevelNodes()

    if options["renameBackgroundLayer"]:
        rename_background_layer(top_layers)
    if options["renameLayer"]:
        rename_layers(top_layers)
    if options["renameTransformMask"]:
        rename_transform_masks(top_layers)
