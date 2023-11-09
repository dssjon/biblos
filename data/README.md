# Biblos Data Back-End

This code is responsible for processing Bible text into a Chroma database.

It intakes Bible text in Verse Per Line (VPL) format and outputs a SQLite database of verse embeddings.

To do this, it groups verses from each chapter together, then breaks them up to try to limit the amount of tokens in each document.  It then embeds each document with some metadata about the verse.

## Usage:

### For command-line options
```
python create_db.py -h
```

### For default usage
```
python create_db.py
```

### Please note
This will take a long time to generate embeddings for all 4k+ passages of scripture -- on an M1 Macbook Pro, this takes approx. 18 minutes.

## VPL Format

This script parses `v` tags from an XML document, assuming one verse per tag.

Example:
```
<verseFile>
  <v b="GEN" c="1" v="1">In the beginning, God created the heavens and the earth. </v>
  <v b="GEN" c="1" v="2">The earth was formless and empty. Darkness was on the surface of the deep and God’s Spirit was hovering over the surface of the waters. </v>
  <v b="GEN" c="1" v="3">God said, “Let there be light,” and there was light. </v>
  ...
```

Any XML file that has `<v>` elements with `b`, `c`, and `v` tags will function for this processor.