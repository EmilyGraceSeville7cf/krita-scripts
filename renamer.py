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
    "renameLayersOptions": {
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
        # Words for transform masks
        "words": ["Move", "Rotate", "Scale"]
     }
}


def warn_when_not(condition, text):
    if not condition:
        print(f"Warning: {text}.")
    
    return condition

def renameBackgroundLayer(layers):
    name = options["renameBackgroundLayerOptions"]["name"]
    background = layers[0]
    if not warn_when_not(background.name() == name, f"'{background.name()}' background layer should be named '{name}'"):
        background.setName(name)

def renameLayers(layers):
    for layer in layers:
        name = layer.name()
        if options["renameLayersOptions"]["replacePunctuation"]:
            delimiter = re.escape(options["renameLayersOptions"]["replacePunctuationOptions"]["delimiter"])
            name = re.sub("[" + re.escape(string.punctuation) + "]", delimiter, name)
            name = re.sub(f"({delimiter})+", delimiter, name)
            name = re.sub(f"\s+{delimiter}", f"{delimiter} ", name)
        if options["renameLayersOptions"]["shorten"]:
            name = re.sub("\s+", " ", name)

        if not warn_when_not(layer.name() == name, f"'{layer.name()}' layer should be named '{name}'"):
            layer.setName(name)

        if layer.childNodes() != []:
            renameLayers(layer.childNodes())

def renameTransformMasks(layers):
    if not warn_when_not(options["renameLayer"], "'renameLayer' should be turned on to use 'renameTransformMask'"):
        return

    for layer in layers:        
        if layer.type() == "transformmask":
            delimiter = options["renameLayersOptions"]["replacePunctuationOptions"]["delimiter"]
            words = layer.name().split(delimiter)
            allowed_words = options["renameTransformMaskOptions"]["words"]
            words = list(set([word.strip() for word in words if word.strip() in allowed_words]))
            words = [word for word in allowed_words if word in words]
            name = f"{delimiter} ".join(words)
            
            allowed = ", ".join(allowed_words)
            if warn_when_not(name != "", f"'{layer.name()}' transform mask should contain at least one of '{allowed}' words"):
                if not warn_when_not(layer.name() == name, f"'{layer.name()}' transform mask should be named '{name}'"):
                    layer.setName(name)

        if layer.childNodes() != []:
            renameTransformMasks(layer.childNodes())


document = krita.Krita.instance().activeDocument()
top_layers = document.topLevelNodes()

if options["renameBackgroundLayer"]:
    renameBackgroundLayer(top_layers)
if options["renameLayer"]:
    renameLayers(top_layers)
if options["renameTransformMask"]:
    renameTransformMasks(top_layers)
