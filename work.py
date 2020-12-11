from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


class Project(metaclass=PoolMeta):
    __name__ = 'project.work'
    moves = fields.One2Many('stock.move', 'origin', 'Moves')
    supply_locations = fields.Function(fields.Many2Many('stock.location', None,
            None, 'Output Locations'), 'on_change_with_supply_locations')
    addition_moves = fields.Function(fields.One2Many('stock.move', 'origin',
            'Addition Moves', domain=[
                ('from_location', 'in', Eval('supply_locations')),
                ('to_location', '=', Eval('location')),
                ('company', '=', Eval('company')),
                ], depends=['supply_locations', 'location', 'company']),
        'get_moves', setter='set_moves')
    removal_moves = fields.Function(fields.One2Many('stock.move', 'origin',
            'Removal Moves', domain=[
                ('from_location', '=', Eval('location')),
                ('to_location', 'in', Eval('supply_locations')),
                ('company', '=', Eval('company')),
                ], depends=['location', 'supply_locations', 'company']),
        'get_moves', setter='set_moves')
    # TODO: project_location should become readonly once there are moves in any
    # of the child projects. Or raise an error when trying to change it.
    project_location = fields.Many2One('stock.location', 'Location', states={
            'invisible': Eval('type') != 'project',
            }, depends=['type'])
    location = fields.Function(fields.Many2One('stock.location', 'Location'),
        'on_change_with_location')

    @classmethod
    def _get_cost(cls, works):
        costs = super()._get_cost(works)
        for work_id, cost in cls._stock_cost(works).items():
            costs[work_id] += cost
        return costs

    @classmethod
    def _stock_cost(cls, works):
        costs = {x.id: Decimal(0) for x in works}
        for work in works:
            for move in work.addition_moves:
                if move.state == 'done':
                    costs[work.id] += (move.cost_price
                        * Decimal(str(move.quantity)))
        return costs

    @fields.depends('type')
    def on_change_with_supply_locations(self, name=None):
        pool = Pool()
        Location = pool.get('stock.location')
        warehouses = Location.search([('type', '=', 'warehouse')])
        return [x.output_location.id for x in warehouses]

    @fields.depends('type', 'party', 'project_location', 'parent',
        '_parent_parent.project_location', '_parent_parent.location')
    def on_change_with_location(self, name=None):
        if self.type == 'project' and self.project_location:
            return self.project_location.id
        elif self.parent:
            parent_location = self.parent.location
            return parent_location.id if parent_location else None
        else:
            if self.party and self.party.customer_location:
                return self.party.customer_location.id

    @classmethod
    def get_moves(cls, works, names):
        res = {
            'addition_moves': {x.id: [] for x in works},
            'removal_moves': {x.id: [] for x in works},
            }
        for work in works:
            for move in work.moves:
                if move.from_location == work.location:
                    res['removal_moves'][work.id].append(move.id)
                else:
                    res['addition_moves'][work.id].append(move.id)
        for name in list(res.keys()):
            if name not in names:
                del res[name]
        return res

    @classmethod
    def set_moves(cls, works, name, value):
        if not value:
            return
        cls.write(works, {
                'moves': value,
                })


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    def _get_origin(cls):
        models = super(Move, cls)._get_origin()
        models.append('project.work')
        return models


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'
    # TODO: Allow selecting projects from the given customer only
    project = fields.Many2One('project.work', 'Project', states={
            'readonly': ((Eval('state') != 'draft')
                | Eval('outgoing_moves', [0]) | Eval('inventory_moves', [0])),
            })

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # TODO: add_remove should only allow to select moves from the given
        # project (if any)
        cls.outgoing_moves.add_remove = []

    @fields.depends('project')
    def on_change_with_customer_location(self, name=None):
        res = super().on_change_with_customer_location(name)
        if self.project:
            return self.project.location.id if self.project.location else res
        return res
