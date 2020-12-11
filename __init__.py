# This file is part project_stock module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import work

def register():
    Pool.register(
        work.Project,
        work.Move,
        work.ShipmentOut,
        module='project_stock', type_='model')
