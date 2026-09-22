# Footer artwork edits

The chapter 03 covers contained embedded footer text. The built-in image generation tool removed that text so the covers can use the same HTML footer and CSS geometry as the teaching slides. Original assets remain available.

| Original                                           | Edited asset                                                 |
| -------------------------------------------------- | ------------------------------------------------------------ |
| `slides/web/assets/core-abstractions-two-apis.png` | `slides/web/assets/core-abstractions-two-apis-unbranded.png` |
| `slides/web/assets/core-abstractions-intro.png`    | `slides/web/assets/core-abstractions-intro-unbranded.png`    |

## Main cover edit prompt

Use case: precise-object-edit. Edit target: the provided 1672 by 941 presentation cover. Make one tiny localized removal only: erase the blue all-caps DANNY’S CODE CORNER label in the bottom-left corner (approximately x60 to315, y887 to906), AND erase its short blue horizontal rule immediately above (approximately x61 to113,y864 to871). Seamlessly restore the dark textured floor/background in those two tiny areas. Do not add replacement text. Preserve everything else exactly: canvas dimensions and crop, all title and subtitle typography, the 03 number, all RDD tiles and colors, the full DataFrames table and every cell, RDDs and DataFrames captions and their underlines, lighting, texture, composition, colors. Do not redesign, recrop, upscale, recolor, or change any other text or content. Output the same complete slide artwork, with only the small bottom-left footer branding removed. A code-rendered footer will be overlaid later; do not create one.

## Reference cover edit prompt

Use case: precise-object-edit. Edit target: this presentation cover. Make exactly one tiny localized removal: erase the blue DANNY’S CODE CORNER label at bottom-left (approximately x60 to315,y887 to906) and its short blue horizontal rule just above (x61 to113,y864 to871). Restore matching dark textured floor in those two small areas. Do not add replacement text. Preserve the entire rest of the image: exact canvas dimensions/crop, all title/subtitle/03 typography, RDD numbered tiles, DataFrame table including every cell, Dataset typed record cards and all code on them, captions RDD / DataFrame / Dataset and their colored underlines, colors, texture, lighting and positions. No redesign or other edits. Output the original full cover with only the bottom-left brand label and its rule removed.
