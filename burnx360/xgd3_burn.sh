#!/bin/bash

#       
#       Copyright 2009 Daniel Dereziński <daniel.derezinski@gmial.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

# $6 - path to iso

truncate --size=$1 "$6"
growisofs -use-the-force-luke=dao -use-the-force-luke=break:$2 --use-the-force-luke=bufsize:$3M -dvd-compat -speed=$4 -Z $5="$6"

echo " "
echo "Press any Key to continue"
read -n1 any_key
