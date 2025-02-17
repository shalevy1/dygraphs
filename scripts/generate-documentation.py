#!/usr/bin/env python3

# Generate docs/options.html

import glob
import json
import os
import re
import sys

# Set this to the path to a test file to get debug output for just that test
# file. Can be helpful to figure out why a test is not being shown for a
# particular option.
debug_tests = []  # [ 'tests/zoom.html' ]

# Pull options reference JSON out of dygraph.js
js = ''
in_json = False
with open('src/dygraph-options-reference.js', 'rt',
          encoding='UTF-8', errors='strict', newline=None) as infile:
  for line in infile:
    if '<JSON>' in line:
      in_json = True
    elif '</JSON>' in line:
      in_json = False
    elif in_json:
      js += line

# TODO(danvk): better errors here.
assert js
docs = json.loads(js)

# Go through the tests and find uses of each option.
for opt in docs:
  docs[opt]['tests'] = []
  docs[opt]['gallery'] = []

encode_re = re.compile('[^A-Za-z0-9.-]')
def encode_cb(match):
  return ''.join(["_%02X" % x for x in match.group(0).encode('UTF-8')])
def encode_anchor(name):
  return encode_re.sub(encode_cb, name)

# This is helpful for differentiating uses of options like 'width' and 'height'
# from appearances of identically-named options in CSS.
def find_braces(txt):
  """Really primitive method to find text inside of {..} braces.
  Doesn't work if there's an unmatched brace in a string, e.g. '{'. """
  out = ''
  level = 0
  for char in txt:
    if char == '{':
      level += 1
    if level >= 1:
      out += char
    if char == '}':
      level -= 1
  return out

ext_tests = []
gallery_files = {}

def search_files(type, files):
  # Find text followed by a colon. These won't all be options, but those that
  # have the same name as a Dygraph option probably will be.
  prop_re = re.compile(r'\b([a-zA-Z0-9]+) *:')
  gf_re = re.compile(r'//galleryActive=(true|false)$', re.MULTILINE)
  for test_file in files:
    if os.path.isfile(test_file): # Basically skips directories
      with open(test_file, 'rt',
                encoding='UTF-8', errors='strict', newline=None) as infile:
        text = infile.read()

      if type == "tests":
        if text.find("src=\"http") >= 0:
          ext_tests.append(test_file)

      # Hack for slipping past gallery demos that have title in their attributes
      # so they don't appear as reasons for the demo to have 'title' options.
      if type == "gallery":
        ga = re.findall(gf_re, text)
        if ga:
          ga = ga[0] == "true"
        else:
          # not annotated
          ga = None
        gallery_files[test_file] = ga
        idx = text.find("function(")
        if idx >= 0:
          text = text[idx:]
      braced_html = find_braces(text)
      if test_file in debug_tests:
        print("\033[0m" + re.sub(prop_re, lambda m: "\033[1;31m" + m.group(0) + "\033[0m", braced_html))
        print("\033[1;34m==================================================================\033[0m")

      ms = re.findall(prop_re, braced_html)
      if test_file in debug_tests:
        print('\n'.join(sorted(set(ms))))
      for opt in ms:
        if opt in docs and test_file not in docs[opt][type]:
          docs[opt][type].append(test_file)

search_files("tests", glob.glob("tests/*.html"))
search_files("gallery", glob.glob("gallery/*.js")) #TODO add grep "Gallery.register\("

if debug_tests:
  sys.exit(0)

# Extract a labels list.
labels = []
for _, opt in docs.items():
  for label in opt['labels']:
    if label not in labels:
      labels.append(label)

print("""<!--#set var="pagetitle" value="options reference" -->
<!--#include virtual="header.html" -->

<!--
  DO NOT EDIT THIS FILE!

  This file is generated by generate-documentation.py.
-->

<link rel="stylesheet" type="text/css" href="options.css" />

<div class="col-lg-3">
<div class="dygraphs-side-nav affix-top" data-spy="affix" data-offset-top="0">
<ul class='nav'>
  <li><a href="#usage">Usage</a>
""".strip())
for label in sorted(labels):
  print('  <li><a href="#%s">%s</a>' % (encode_anchor(label), label))
print('</ul></div></div>\n')

print("""
<div id='content' class='col-lg-9'>
<h2>Options Reference</h2>
<p>Dygraphs tries to do a good job of displaying your data without any further configuration. But inevitably, you're going to want to tinker. Dygraphs provides a rich set of options for configuring its display and behavior.</p>

<a name="usage"></a><h3>Usage</h3>
<p>You specify options in the third parameter to the dygraphs constructor:</p>
<pre>g = new Dygraph(div,
                data,
                {
                  option1: value1,
                  option2: value2,
                  ...
                });
</pre>

<p>After you've created a Dygraph, you can change an option by calling the <code>updateOptions</code> method:</p>
<pre>g.updateOptions({
                  new_option1: value1,
                  new_option2: value2
                });
</pre>

<p>Some options can be set on a per-axis and per-series basis. See the docs on <a href="per-axis.html">per-axis and per-series options</a> to learn how to do this. The options which may be set in this way are marked as such on this page.</p>

<p>For options which are functions (e.g. callbacks and formatters), the value of <code>this</code> is set to the Dygraph object.</p>

<p><strong>Note:</strong> tests marked with ⚠ access external resources, such as Google’s jsapi.</p>

<p>And, without further ado, here's the complete list of options:</p>
""")

def test_name(f):
  """Takes 'tests/demo.html' -> 'demo'"""
  return f.replace('tests/', '').replace('.html', '')

def gallery_name(f):
  """Takes 'gallery/demo.js' -> 'demo'"""
  return f.replace('gallery/', '').replace('.js', '')

def urlify_gallery(f):
  """Takes 'gallery/demo.js' -> 'demo'"""
  return f.replace('gallery/', 'gallery/#g/').replace('.js', '')

def test_fmt(f):
  res = '<a href="%s">%s</a>' % (f, test_name(f))
  if f in ext_tests:
    res += '<b class="extlink" title="WARNING: accesses external resources (Google jsapi)">⚠</b>'
  return res

def gallery_fmt(f):
  if gallery_files[f]:
    res = '<a href="%s">%s</a>' % (urlify_gallery(f), gallery_name(f))
  else:
    res = '<font color="#9999FF" title="inactive">%s</a>' % gallery_name(f)
  return res

for label in sorted(labels):
  print('<a name="%s"></a><h3>%s</h3>\n' % (encode_anchor(label), label))

  for opt_name in sorted(docs.keys()):
    opt = docs[opt_name]
    if label not in opt['labels']: continue
    tests = opt['tests']
    if not tests:
      examples_html = '<font color=red>NONE</font>'
    else:
      examples_html = '; '.join(test_fmt(f) for f in sorted(tests, key=test_name))

    gallery = opt['gallery']
    if not gallery:
      gallery_html = '<font color=red>NONE</font>'
    else:
      gallery_html = '; '.join(gallery_fmt(f) for f in sorted(gallery, key=gallery_name))

    if 'parameters' in opt:
      parameters = opt['parameters']
      parameters_html = '\n'.join("<tr><th>%s:</th><td>%s</td></tr>" % (p[0], p[1]) for p in parameters)
      parameters_html = "\n  </p><div class='parameters'><table>\n%s\n  </table></div><p>" % (parameters_html);
    else:
      parameters_html = ''

    if not opt['type']: opt['type'] = '(missing)'
    if not opt['default']: opt['default'] = '(missing)'
    if not opt['description']: opt['description'] = '(missing)'

    print("""
  <div class='option'><p>
  <a name="%(namenc)s"></a><b>%(name)s</b>
  <a class="link" href="#%(namenc)s">#</a>
  </p><p>
  %(desc)s
  </p><p>
  <i>Type: %(type)s</i><br/>%(parameters)s
  <i>Default: %(default)s</i>
  </p><table class="gallerylinks">
  <tr><th>Gallery Samples:</th><td>%(gallery_html)s</td></tr>
  <tr><th>Other Examples:</th><td>%(examples_html)s</td></tr>
  </table></div>
  """ % { 'name': opt_name,
          'namenc': encode_anchor(opt_name),
          'type': opt['type'],
          'parameters': parameters_html,
          'default': opt['default'],
          'desc': opt['description'],
          'examples_html': examples_html,
          'gallery_html': gallery_html})

print("""
<a name="point_properties"></a><h3>Point Properties</h3>
Some callbacks take a point argument. Its properties are:<br/>
<ul>
<li>xval/yval: The data coordinates of the point (with dates/times as millis since epoch)</li>
<li>canvasx/canvasy: The canvas coordinates at which the point is drawn.</li>
<li>name: The name of the data series to which the point belongs</li>
<li>idx: The row number of the point in the data set</li>
</ul>
</div> <!-- #content -->

<!--#include virtual="footer.html" -->""")

# This page was super-helpful:
# http://jsbeautifier.org/
