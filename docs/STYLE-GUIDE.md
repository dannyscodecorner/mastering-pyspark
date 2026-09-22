# DCC classroom visual language

Approved direction: light teaching slides, neutral charcoal cover/dividers and code panels, bold slab-serif headings. Muted section accents add orientation without becoming full-slide coloured backgrounds. No neon, glow, decorative gradients or simulated window controls.

## Foundations

| Role             | Value                                                   |
| ---------------- | ------------------------------------------------------- |
| Paper            | #FAFAF8                                                 |
| Ink / dark panel | #292D30                                                 |
| Secondary text   | #626A6D                                                 |
| Heading          | Roboto Slab, 800, typically 56px on a 1440 × 810 canvas |
| Body             | Lato, 400/700, usually 25–29px                          |
| Code             | Menlo / Consolas / system monospace, 28px               |
| Canvas           | 1440 × 810, scaled together to fit the display          |
| Safe inset       | 66px horizontal; footer separated from content          |

The concept images establish the direction, not exact font geometry. Roboto Slab is the implemented heading choice; all heading/body font assets are bundled locally.

## Section colours

| Section                              | Accent on light | Accent on charcoal |
| ------------------------------------ | --------------- | ------------------ |
| 01 Spark vs. Python                  | #257F86 teal    | #69BEC3            |
| 02 Introducing Spark                 | #257F86 teal    | #69BEC3            |
| 03 Spark’s core abstractions         | #286FAF blue    | #7BB4E3            |
| 04 Lazy Pandas                       | #925394 plum    | #C898CE            |
| 05 From Query to Execution           | #A66714 ochre   | #E2B366            |
| 06 Grouping, joining and aggregating | #167F91 teal    | #6ED5DF            |
| 07 Structured Streaming              | #4B7C35 sage    | #A3C987            |
| 08 Working with PySpark              | #B35141 clay    | #E39B88            |
| 09 Spark in AWS Glue                 | #A66714 ochre   | #E2B366            |

Use accents for section markers, thin top rules, selected diagram elements and takeaways. Keep primary headings charcoal on paper. The original logo retains its own brand colours. Labels and numbers carry section identity alongside colour.

## Syntax colours — stable across sections

Functions #83BDE3; strings #A8CE91; operators #F09588; numbers #E6BC76; keywords #C5A5E8; comments #ADB8BF; ordinary code #F3F2EE. Code panels always use charcoal. Section colours must not change syntax meaning.

## Diagrams and motion

Use accessible inline SVG with title and description, orthogonal connectors, readable labels and clear hierarchy. Preserve a complete static state. The sample diagram uses three manual emphasis steps (all labels stay readable) with optional Play, not automatic progression. Reduced-motion and print modes show the full figure. No animation should force the instructor to keep pace with it.
