"""
The latest version of this package is available at:
<http://github.com/jantman/pizero-gpslog>

##################################################################################
Copyright 2018 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of pizero-gpslog, also known as pizero-gpslog.

    pizero-gpslog is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pizero-gpslog is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with pizero-gpslog.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pizero-gpslog> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##################################################################################
"""

import sys
import argparse
import json
import re
from gpxpy.gpx import GPX, GPXTrack, GPXTrackSegment, GPXTrackPoint
from gpxpy.gpxfield import TIME_TYPE
from xml.dom import minidom

from pizero_gpslog.version import VERSION


class GpxConverter(object):

    def __init__(self, input_fpath, output_fpath):
        self._in_fpath = input_fpath
        self._out_fpath = output_fpath

    def convert(self):
        logs = []
        with open(self._in_fpath, 'r') as fh:
            for line in fh.readlines():
                line = line.strip()
                if line == '':
                    continue
                j = json.loads(line)
                if 'tpv' not in j:
                    continue
                if j['tpv'][0].get('mode', 0) < 2:
                    continue
                logs.append(j)
        xml = self._gpx_for_logs(logs)
        with open(self._out_fpath, 'w') as fh:
            fh.write(xml)

    def _gpx_for_logs(self, logs):
        g = GPX()
        track = GPXTrack()
        track.source = 'pizero-gpslog %s' % VERSION
        g.tracks.append(track)
        seg = GPXTrackSegment()
        track.segments.append(seg)

        for item in logs:
            tpv = item['tpv'][0]
            sky = item['sky'][0]
            p = GPXTrackPoint(
                latitude=tpv['lat'],
                longitude=tpv['lon'],
                elevation=tpv['alt'],
                time=TIME_TYPE.from_string(tpv['time']),
                speed=tpv['speed'],
                horizontal_dilution=sky['hdop'],
                vertical_dilution=sky['vdop'],
                position_dilution=sky['pdop']
            )
            p.type_of_gpx_fix = '2d' if tpv['mode'] == 2 else '3d'
            p.satellites = len(sky['satellites'])
            seg.points.append(p)
        return g.to_xml()


def main(argv=sys.argv[1:]):
    args = parse_args(argv)
    if args.output is None:
        if '.' not in args.JSON_FILE:
            args.output = args.JSON_FILE + '.' + args.format
        else:
            args.output = args.JSON_FILE.rsplit('.', 1)[0] + '.' + args.format
    GpxConverter(args.JSON_FILE, args.output).convert()


def parse_args(argv):
    """parse arguments/options"""
    p = argparse.ArgumentParser(
        description='Convert pizero-gpslog (gpsd POLL format) output files to '
                    'common GPS formats.'
    )
    p.add_argument('-f', '--format', dest='format', action='store', type=str,
                   choices=['gpx'], default='gpx',
                   help='destination format (default: gpx)')
    p.add_argument('-o', '--output', dest='output', action='store', type=str,
                   default=None,
                   help='Output file path. By default, will be the input '
                        'file path with the file extension replaced with the '
                        'correct one for the output format.')
    p.add_argument('JSON_FILE', action='store', type=str,
                   help='Input file to convert')
    args = p.parse_args(argv)
    return args


if __name__ == '__main__':
    main(sys.argv[1:])