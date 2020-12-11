========================
Project Revenue Scenario
========================

Imports::

    >>> import datetime
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company

Install project_invoice::

    >>> config = activate_modules('project_stock')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create employee::

    >>> Employee = Model.get('company.employee')
    >>> employee = Employee()
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> employee.party = party
    >>> employee.company = company
    >>> _ = employee.cost_prices.new(cost_price=Decimal('10.00'))
    >>> employee.save()
    >>> employee.cost_price
    Decimal('10.00')

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> hour, = ProductUom.find([('name', '=', 'Hour')])
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'Service'
    >>> template.default_uom = hour
    >>> template.type = 'service'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product, = template.products

    >>> good_template = ProductTemplate()
    >>> good_template.name = 'Good'
    >>> good_template.default_uom = unit
    >>> good_template.type = 'goods'
    >>> good_template.list_price = Decimal(0)
    >>> good_template.save()
    >>> good_product, = good_template.products
    >>> good_product.cost_price = Decimal(5)
    >>> good_product.save()

Create a Project::

    >>> Project = Model.get('project.work')
    >>> project = Project()
    >>> project.name = 'Test effort'
    >>> project.type = 'project'
    >>> project.party = customer
    >>> project.timesheet_available = True
    >>> project.product = product
    >>> project.list_price
    Decimal('20.0000')
    >>> project.effort_duration = datetime.timedelta(hours=1)
    >>> task = project.children.new()
    >>> task.name = 'Task 1'
    >>> task.type = 'task'
    >>> task.timesheet_available = True
    >>> task.product = product
    >>> task.list_price
    Decimal('20.0000')
    >>> task.effort_duration = datetime.timedelta(hours=5)
    >>> task_no_effort = project.children.new()
    >>> task_no_effort.name = "Task 2"
    >>> task_no_effort.type = 'task'
    >>> task_no_effort.effort_duration = None
    >>> project.save()
    >>> task, task_no_effort = project.children

Check project revenue and cost::

    >>> project.revenue
    Decimal('120.00')
    >>> task.revenue
    Decimal('100.00')
    >>> task_no_effort.revenue
    Decimal('0')
    >>> project.cost
    Decimal('0.00')
    >>> task.cost
    Decimal('0.00')
    >>> task_no_effort.cost
    Decimal('0.00')

Create timesheets::

    >>> TimesheetLine = Model.get('timesheet.line')
    >>> line = TimesheetLine()
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=3)
    >>> line.work, = task.timesheet_works
    >>> line.save()
    >>> line = TimesheetLine()
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=2)
    >>> line.work, = project.timesheet_works
    >>> line.save()

Cost should take in account timesheet lines::

    >>> project.reload()
    >>> task, task_no_effort = project.children
    >>> project.revenue
    Decimal('120.00')
    >>> task.revenue
    Decimal('100.00')
    >>> task_no_effort.revenue
    Decimal('0')
    >>> project.cost
    Decimal('50.00')
    >>> task.cost
    Decimal('30.00')
    >>> task_no_effort.cost
    Decimal('0.00')

Create stock move::

    >>> Location = Model.get('stock.location')
    >>> warehouse, = Location.find([('type', '=', 'warehouse')])
    >>> move = task.addition_moves.new()
    >>> move.from_location = warehouse.output_location
    >>> move.to_location = party.customer_location
    >>> move.product = good_product
    >>> move.quantity = 5
    >>> move.unit_price = Decimal(0)
    >>> move.save()
    >>> task.reload()

Cost should not change::

    >>> project.reload()
    >>> task.reload()
    >>> project.cost
    Decimal('50.00')
    >>> task.cost
    Decimal('30.00')

Do stock move::

    >>> move.click('do')

Cost should take into account stock moves::

    >>> project.reload()
    >>> task.reload()
    >>> project.cost
    Decimal('75.00')
    >>> task.cost
    Decimal('55.00')
