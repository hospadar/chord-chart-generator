from lxml import etree
import sys, argparse, json

#basic grid spacing
d = 10
#Should we scale up the whole thing?
scalefactor = 1

notes = ["A", "B♭", "B", "C", "D♭", "D", "E♭", "E", "F", "G♭", "G", "A♭"]
instruments = {
    #same for concert and tenor
    "ukulele":{"strings": ["A", "E", "C", "G"], "min_frets":4},
    "baritone_ukulele":{"strings": ["D", "G", "B", "E"], "min_frets":4},
    "guitar":{"strings": ["E", "A", "D", "G", "B", "E"], "min_frets": 4},
    "tenor_guitar":{"strings":["C", "G", "D", "A"]},
    #note: not including the 5th string since most basic chords don't use it
    #and it wouldn't render well anyways
    "banjo":{"strings":["D","G","B","D"], "min_frets":4},
    #typical longneck banjo tuning which allows capot on the 3rd fret to acheive standard banjo tuning
    "longneck_banjo":{"strings": ["B", "E", "A♭", "B"], "min_frets":4}
}


def line(startx, starty, endx, endy, weight=1, stroke="rgb(0,0,0)"):
    return etree.Element("line", attrib={
        "x1":str(startx),
        "y1":str(starty),
        "x2":str(endx),
        "y2":str(endy),
        "style":"stroke-linecap:square;stroke-width:{w};stroke:{c}".format(w=weight, c=stroke)
    })

def circle(centerx, centery, radius, fill="rgb(0,0,0)"):
    return etree.Element("circle", attrib={
        "cx":str(centerx),
        "cy":str(centery),
        "r":str(radius),
        "fill":fill
    })

def text(x, y, body_text, height="{d}px".format(d=d), anchor="middle"):
    t = etree.Element("text", attrib={
        "x":str(x),
        "y":str(y),
        "style":"text-anchor:{anchor};font-size:{height}".format(anchor=anchor, height=height)
    })
    t.text = body_text
    return t


def neck(fretted, min_frets=4, string_labels=None, label=None):
    if string_labels != None and len(string_labels) != len(fretted):
        raise Exception("Got {s} strings and {l} labels - must have the same number!".format(s=len(fretted), l=len(string_labels)))
    strings = len(fretted)
    frets = max(max(fretted), min_frets)
    lines = etree.Element("g")
    lines.append(line(0,0, d*(strings-1), 0, weight=3))
    #lines.append(line(0,0, 0, d*frets, stroke="blue"))
    #lines.append(line(d*4, 0, d*4, d*frets, stroke="blue"))
    for i in range(strings):
        lines.append(line(i*d, 0, i*d, d*frets+.25*d))
    for i in range(frets):
        lines.append(line(0, i*d+d, (strings-1)*d, i*d+d))
    for string, fret in enumerate(fretted):
        if fret != 0:
            lines.append(circle(d*string, fret*d-.5*d, .4*d))
    if string_labels != None:
        for string, string_label in enumerate(string_labels):
            lines.append(text(string*d, frets*d+d, string_label, height="{h}px".format(h=d*.7)))

    container = etree.Element("g")
    container.append(lines)
    lines.attrib["transform"] = "translate({x}, {y})".format(x=.5*d, y=d*1.5)
    if label != None:
        container.append(text(.5*d, d, label, anchor="start"))
    return container

def chord_chart(instrument, label, fretted):
    base_strings = instruments[instrument]["strings"]
    if len(base_strings) != len(fretted):
        raise Exception("Wrong number of fretted strings ({f}) provided for instrument \"{i}\", expected {s}".format(
            f=len(fretted),
            i=instrument,
            s=len(base_strings)
        ))
    string_labels = []
    for string, fret in enumerate(fretted):
        base_note_index = notes.index(base_strings[string])
        fretted_note = (base_note_index + fret) % len(notes)
        string_labels.append(notes[fretted_note])
    return neck(fretted, min_frets=instruments[instrument]["min_frets"], string_labels=string_labels, label=label)

def multichart(instrument, charts):
    page = etree.Element("g")
    row_heights = []
    for rownum, row in enumerate(charts):
        max_num_frets = max(max(max(chart[1:]) for chart in row), instruments[instrument]["min_frets"])
        row_heights.append(max_num_frets * d + 4*d)
        for column, chart in enumerate(row):
            parent = etree.Element("g", attrib={"transform":"translate({x}, {y})".format(
                x=column*d*len(instruments[instrument]["strings"]) + column * d,
                y=sum(row_heights[0:rownum])
            )})
            parent.append(chord_chart(instrument, chart[0], chart[1:]))
            page.append(parent)
    return page

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate chord chart sheets")
    parser.add_argument("-i", "--instrument", required=True, help="name of instrument", default="guitar", choices=instruments.keys())
    parser.add_argument("-s", "--sheet", help="filename of json data for chord sheet", required=True)

    options = parser.parse_args()


    root = etree.Element("svg", attrib={

        "version":"1.1",
        "baseProfile":"full",
        "xmlns":"http://www.w3.org/2000/svg"
    })
    scaleup = etree.Element("g", attrib={"transform":"scale({s})".format(s=scalefactor)})
    scaleup.append(multichart(options.instrument, json.load(open(options.sheet, encoding="utf-8"))))
    root.append(scaleup)
    sys.stdout.buffer.write(etree.tostring(root))
