#!/usr/bin/env python
'''
w3c-validator - Validate HTML and CSS files using the WC3 validators

Copyright: Stuart Rackham (c) 2011
License:   MIT
Email:     srackham@gmail.com
'''

from __future__ import (print_function,)

import os
import sys
import time
import json
import commands
import urllib

html_validator_url = 'http://validator.w3.org/check'
css_validator_url = 'http://jigsaw.w3.org/css-validator/validator'

verbose_option = False

def message(msg):
    print(msg, file=sys.stderr)

def verbose(msg):
    if verbose_option:
        message(msg)

def validate(filename):
    '''
    Validate file and return JSON result as dictionary.
    'filename' can be a file name or an HTTP URL.
    Return '' if the validator does not return valid JSON.
    Raise OSError if curl command returns an error status.
    '''
    quoted_filename = urllib.quote(filename)
    if filename.startswith('http://'):
        # Submit URI with GET.
        if filename.endswith('.css'):
            cmd = ('curl -sG -d uri={0} -d output=json -d warning=0 {1}'.format(quoted_filename, css_validator_url))
        else:
            cmd = ('curl -sG -d uri={0} -d output=json {1}'.format(quoted_filename, html_validator_url))
    else:
        # Upload file as multipart/form-data with POST.
        if filename.endswith('.css'):
            cmd = ('curl -sF "file=@{0};type=text/css" -F output=json -F warning=0 {1}'.format(quoted_filename, css_validator_url))
        else:
            cmd = ('curl -sF "uploaded_file=@{0};type=text/html" -F output=json {1}'.format(quoted_filename, html_validator_url))
    verbose(cmd)
    status,output = commands.getstatusoutput(cmd)
    if status != 0:
        raise OSError (status, 'failed: {0}'.format(cmd))
    verbose(output)
    try:
        result = json.loads(output)
    except ValueError:
        result = ''
    time.sleep(2)   # Be nice and don't hog the free validator service.
    return result


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--verbose':
        verbose_option = True
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    if len(args) == 0:
        message('usage: {0} [--verbose] FILE|URL...'.format(os.path.basename(sys.argv[0])))
        exit(1)
    errors = 0
    warnings = 0
    for f in args:
        message('validating: {0} ...'.format(f))
        retrys = 0
        while retrys < 2:
            result = validate(f)
            if result:
                break
            retrys += 1
            message('retrying: {0} ...'.format(f))
        else:
            message('failed: {0}'.format(f))
            errors += 1
            continue
        if f.endswith('.css'):
            errorcount = result['cssvalidation']['result']['errorcount']
            warningcount = result['cssvalidation']['result']['warningcount']
            errors += errorcount
            warnings += warningcount
            if errorcount > 0:
                message('errors: {0!n}'.format(errorcount))
            if warningcount > 0:
                message('warnings: {0!n}'.format(warningcount))
        else:
            for msg in result['messages']:
                if 'lastLine' in nmsg:
                    message('{type!s}: line {lastLine!d}: {message!s}'.format(**msg))
                else:
                    message('{type!s}: {message!s}'.format(msg))
                if msg['type'] == 'error':
                    errors += 1
                else:
                    warnings += 1
    if errors:
        exit(1)
